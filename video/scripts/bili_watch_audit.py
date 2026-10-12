"""盯着一条稿件的审核状态：通过（state=0）或被打回（有 reject_reason）就退出。

用法：python scripts\\bili_watch_audit.py --bvid BV1RCpE6NEwu [--minutes 40] [--interval 60]

审核状态用 `biliup show <bvid>` 拿（它走 App 接口，带登录信息）。
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

EXE = Path.home() / "AppData" / "Local" / "Temp" / "biliupR" / "biliupR-v0.2.4-x86_64-windows" / "biliup.exe"
VIEW = "https://api.bilibili.com/x/web-interface/view?bvid={bvid}"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"


def archive_state(cookies: Path, bvid: str) -> dict:
    proc = subprocess.run(
        [str(EXE), "-u", str(cookies), "show", bvid],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    lines = [ln for ln in (proc.stdout or "").splitlines() if "INFO " not in ln]
    return json.loads("\n".join(lines))["archive"]


def public_view(bvid: str) -> dict:
    op = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    req = urllib.request.Request(VIEW.format(bvid=bvid), headers={"User-Agent": UA, "Referer": "https://www.bilibili.com/"})
    with op.open(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main() -> int:
    ap = argparse.ArgumentParser(description="盯 B 站稿件审核状态")
    ap.add_argument("--bvid", required=True)
    ap.add_argument("--cookies", default=r"C:\Users\Zora\.dsh\biliup\cookies.json")
    ap.add_argument("--minutes", type=int, default=40)
    ap.add_argument("--interval", type=int, default=60)
    args = ap.parse_args()

    deadline = time.time() + args.minutes * 60
    while time.time() < deadline:
        stamp = time.strftime("%H:%M:%S")
        try:
            arc = archive_state(Path(args.cookies), args.bvid)
            state = arc.get("state")
            print(f"[{stamp}] state={state} ({arc.get('state_desc')}) reject={arc.get('reject_reason')!r}", flush=True)
            if state == 0:
                try:
                    view = public_view(args.bvid)
                    if view.get("code") == 0:
                        d = view["data"]
                        print(f"PUBLISHED title={d.get('title')!r} views={d.get('stat', {}).get('view')} pic={d.get('pic')}", flush=True)
                        return 0
                except Exception as exc:
                    print(f"  (public view not ready yet: {exc!r})", flush=True)
            elif arc.get("reject_reason"):
                print(f"REJECTED {arc.get('reject_reason')}", flush=True)
                return 3
        except Exception as exc:
            print(f"[{stamp}] check failed: {exc!r}", flush=True)
        time.sleep(args.interval)
    print("TIMEOUT still not public")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
