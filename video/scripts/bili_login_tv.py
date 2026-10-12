"""B 站「TV 端」扫码登录（biliup-rs v0.2.4 用的就是这条路）。

为什么不用 `biliup login`：它第一步是 dialoguer 的交互菜单，需要一个真终端，
在本 harness 里跑必然报 `Error: IO error: not a terminal`。

为什么必须走 TV 端而不是网页端：biliup-rs v0.2.4 的投稿接口只有 APP 一条
（`submit_by_app` → `member.bilibili.com/x/vu/app/add`，需要 `token_info.access_token`），
而它的 cookies.json 是 `LoginInfo`：`cookie_info` / `sso` / `token_info{access_token,
expires_in, mid, refresh_token}` 全部必填、无默认值，所以纯网页 cookie 那份文件它根本解析不了。
TV 端 poll 成功时返回的 `data` 就是完整的 `LoginInfo`，直接落盘即可。

用法：
  python scripts\\bili_login_tv.py              # 生成二维码，轮询等待扫码（默认 600 秒）
  python scripts\\bili_login_tv.py --qr-only     # 只生成二维码

产物：
  <out>/qr-login-tv.png      二维码（手机 B 站客户端 → 扫一扫）
  <cookies>                  biliup 的 cookies.json（默认 C:\\Users\\Zora\\.dsh\\biliup\\cookies.json）
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

VIDEO = Path(__file__).resolve().parents[1]
DEPS = VIDEO / ".deps"
if DEPS.exists() and str(DEPS) not in sys.path:
    sys.path.insert(0, str(DEPS))

APPKEY = "4409e2ce8ffd12b8"
APPSEC = "59b43e04ad6965f34319062b478f83dd"
AUTH_CODE = "https://passport.bilibili.com/x/passport-tv-login/qrcode/auth_code"
POLL = "https://passport.bilibili.com/x/passport-tv-login/qrcode/poll"

# TV 端 poll 的 code
STATUS = {
    0: "登录成功",
    86039: "已扫码，等待确认",
    86038: "二维码已过期",
}

UA = "Mozilla/5.0 BiliDroid/7.66.0 (bbcallen@gmail.com) os/android model/Pixel ui/v2.5"


def signed_body(extra: dict | None = None) -> str:
    """biliup 的 sign：把表单按键排序后 urlencode，拼上 appsec 取 md5。"""
    form = {"appkey": APPKEY, "local_id": "0", "ts": str(int(time.time()))}
    if extra:
        form.update(extra)
    query = urllib.parse.urlencode(sorted(form.items()))
    return query + "&sign=" + hashlib.md5((query + APPSEC).encode("utf-8")).hexdigest()


def post(url: str, body: str) -> dict:
    op = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    req = urllib.request.Request(
        url,
        data=body.encode("utf-8"),
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": UA,
            "Referer": "https://www.bilibili.com/",
        },
    )
    with op.open(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


def make_qr(url: str, out_png: Path, box: int = 12) -> None:
    import qrcode

    qr = qrcode.QRCode(border=3, box_size=box, error_correction=qrcode.constants.ERROR_CORRECT_M)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    out_png.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_png)
    print(f"QR_PNG {out_png} ({out_png.stat().st_size} bytes, {img.size[0]}x{img.size[1]})")


def main() -> int:
    ap = argparse.ArgumentParser(description="B 站 TV 端扫码登录")
    ap.add_argument("--out", default=str(VIDEO / "out" / "bili-upload" / "qr-login-tv.png"))
    ap.add_argument("--cookies", default=r"C:\Users\Zora\.dsh\biliup\cookies.json")
    ap.add_argument("--timeout", type=int, default=600)
    ap.add_argument("--interval", type=float, default=2.0)
    ap.add_argument("--qr-only", action="store_true")
    args = ap.parse_args()

    payload = post(AUTH_CODE, signed_body())
    if payload.get("code") != 0:
        print(f"ERROR auth_code failed: {payload}")
        return 1
    info = payload["data"]
    url, auth_code = info["url"], info["auth_code"]
    print(f"QR_URL {url}")
    make_qr(url, Path(args.out))
    if args.qr_only:
        return 0

    deadline = time.time() + args.timeout
    last = None
    while time.time() < deadline:
        time.sleep(args.interval)
        try:
            payload = post(POLL, signed_body({"auth_code": auth_code}))
        except Exception as exc:
            print(f"poll error: {exc!r}", flush=True)
            continue
        code = int(payload.get("code", -1))
        if code != last:
            print(f"STATUS {code} {STATUS.get(code, payload.get('message'))}", flush=True)
            last = code
        if code == 0:
            data = payload["data"]
            path = Path(args.cookies)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            token = data.get("token_info", {})
            cookies = [c["name"] for c in data.get("cookie_info", {}).get("cookies", [])]
            print(f"cookies written: {path}")
            print(f"COOKIES {cookies}")
            print(f"TOKEN mid={token.get('mid')} expires_in={token.get('expires_in')} access_token_len={len(token.get('access_token',''))}")
            print("DONE")
            return 0
    print("TIMEOUT 没等到扫码")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
