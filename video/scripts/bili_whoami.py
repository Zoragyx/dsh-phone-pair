"""读 biliup 的 cookies.json，调 nav 接口确认当前登录的是哪个账号。

用法：python scripts\\bili_whoami.py [--cookies 路径]
"""

from __future__ import annotations

import argparse
import json
import urllib.request
from pathlib import Path

NAV = "https://api.bilibili.com/x/web-interface/nav"
UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"
)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cookies", default=r"C:\Users\Zora\.dsh\biliup\cookies.json")
    args = ap.parse_args()

    data = json.loads(Path(args.cookies).read_text(encoding="utf-8"))
    pairs = [(c["name"], c["value"]) for c in data["cookie_info"]["cookies"]]
    cookie = "; ".join(f"{k}={v}" for k, v in pairs)

    op = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    req = urllib.request.Request(NAV, headers={"User-Agent": UA, "Cookie": cookie, "Referer": "https://www.bilibili.com/"})
    with op.open(req, timeout=20) as resp:
        nav = json.loads(resp.read().decode("utf-8"))

    if nav.get("code") != 0 or not nav.get("data", {}).get("isLogin"):
        print(f"NOT LOGGED IN: code={nav.get('code')} message={nav.get('message')}")
        return 1
    d = nav["data"]
    print(f"uname={d.get('uname')} mid={d.get('mid')} vip={d.get('vipStatus')} level={d.get('level_info', {}).get('current_level')}")
    print(f"coins={d.get('money')} logged_in={d.get('isLogin')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
