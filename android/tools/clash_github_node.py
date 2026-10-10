"""Pick a Clash (mihomo) node that can actually reach GitHub, and switch to it.

Why this exists: the machine's current global node answers google/npm/gitee but not github.com, so
publishing to GitHub fails with a bare "000". Clash Verge exposes no TCP control port here
(`external-controller: ''` in clash-verge.yaml), only the named pipe `\\\\.\\pipe\\verge-mihomo`,
so this talks HTTP/1.1 over that pipe.

    python clash_github_node.py                 # probe the group, switch to the fastest GitHub-capable node
    python clash_github_node.py --list          # probe and print, change nothing
    python clash_github_node.py --pick "NAME"   # switch to an explicit node
    python clash_github_node.py --restore       # go back to the node recorded before the last switch
    python clash_github_node.py --group GLOBAL --url https://api.github.com/ --timeout 6000
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.parse
from pathlib import Path

PIPE = r"\\.\pipe\verge-mihomo"
SECRET = "set-your-secret"
STATE = Path(__file__).with_name(".clash-node-before.txt")

# Node names carry flag emoji; this console defaults to GBK and would crash on print().
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):  # pragma: no cover - old/odd interpreters
        pass


def call(method: str, path: str, body: dict | None = None) -> dict | None:
    """One HTTP/1.1 request over the Clash named pipe (byte-exact, Content-Length framed)."""
    payload = json.dumps(body).encode("utf-8") if body is not None else None
    head = (
        f"{method} {path} HTTP/1.1\r\n"
        "Host: localhost\r\n"
        f"Authorization: Bearer {SECRET}\r\n"
        "Connection: close\r\n"
    ).encode("ascii")
    if payload is not None:
        head += b"Content-Type: application/json\r\nContent-Length: %d\r\n" % len(payload)
    head += b"\r\n"
    with open(PIPE, "r+b", buffering=0) as pipe:
        pipe.write(head + (payload or b""))
        raw = b""
        while b"\r\n\r\n" not in raw:
            chunk = pipe.read(1)
            if not chunk:
                break
            raw += chunk
        header, _, rest = raw.partition(b"\r\n\r\n")
        status = 0
        lines = header.split(b"\r\n")
        if lines and lines[0].startswith(b"HTTP/"):
            status = int(lines[0].split(b" ")[1])
        length = 0
        for line in lines:
            if line.lower().startswith(b"content-length:"):
                length = int(line.split(b":", 1)[1])
        body_bytes = rest
        while len(body_bytes) < length:
            chunk = pipe.read(length - len(body_bytes))
            if not chunk:
                break
            body_bytes += chunk
    if status != 200:
        raise SystemExit(f"mihomo returned HTTP {status} for {method} {path}")
    if not body_bytes:
        return None
    return json.loads(body_bytes.decode("utf-8"))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--group", default="GLOBAL")
    ap.add_argument("--url", default="https://api.github.com/")
    ap.add_argument("--timeout", type=int, default=6000, help="per-node probe timeout in ms")
    ap.add_argument("--list", action="store_true", help="print results, do not switch")
    ap.add_argument("--pick", help="switch to this node name")
    ap.add_argument("--restore", action="store_true", help="switch back to the recorded node")
    args = ap.parse_args()

    group = call("GET", f"/proxies/{args.group}")
    if group is None:
        raise SystemExit(f"could not read group {args.group} over {PIPE}")
    now = group.get("now") or ""
    nodes = group.get("all") or []
    print(f"group {args.group}: now = {now!r} ; {len(nodes)} entries")

    if args.restore:
        if not STATE.exists():
            raise SystemExit(f"no recorded previous node at {STATE}")
        previous = STATE.read_text(encoding="utf-8").strip()
        call("PUT", f"/proxies/{args.group}", {"name": previous})
        print(f"restored {args.group} -> {previous}")
        return 0

    def switch(name: str) -> None:
        if not STATE.exists():
            STATE.write_text(now, encoding="utf-8")
        call("PUT", f"/proxies/{args.group}", {"name": name})
        print(f"switched {args.group} -> {name} (previous node saved in {STATE.name})")

    if args.pick:
        switch(args.pick)
        return 0

    probe = urllib.parse.quote(args.url, safe="")
    result = call("GET", f"/group/{args.group}/delay?url={probe}&timeout={args.timeout}")
    if not result:
        raise SystemExit("group delay probe returned nothing")
    ok, bad = [], []
    for node, value in result.items():
        if isinstance(value, int):
            ok.append((value, node))
        else:
            bad.append((node, (value or {}).get("message", str(value))))
    for node, message in bad:
        print(f"  fail  {node:<44} {message}")
    if not ok:
        raise SystemExit(f"no node in {args.group} could reach {args.url}")
    for delay, node in sorted(ok):
        print(f"  ok    {node:<44} {delay} ms")
    if args.list:
        print("(--list: nothing switched)")
        return 0
    switch(sorted(ok)[0][1])
    return 0


if __name__ == "__main__":
    sys.exit(main())
