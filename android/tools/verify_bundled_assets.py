#!/usr/bin/env python3
"""Verify that the web assets packaged in the APK are intact and match what the server serves.

Guards the v1.4 promise from the packaging side: every line of assets/web/index.txt must resolve to
a file that really is inside the APK, with a MIME type the WebView will accept for that extension,
and byte-identical to a fresh fetch. Catches truncated downloads, file-name mix-ups and wrong
Content-Types (a JS module served as the wrong MIME is blocked by the WebView's strict MIME check,
which would break the UI in a way that only shows up on a phone).

Usage:
  verify_bundled_assets.py --apk artifacts/dsh-phone-pair-1.0.apk --base https://<id>.dsh-market.com \
      --cookie <dsh_pair value>

Add --loopback to fetch each asset from the local webserver instead of the public relay. The index
records absolute public URLs, and the pairing relay drops long responses when it is re-registering
(HTTP 530 / truncated bodies), so the byte-for-byte comparison is more trustworthy over loopback:
the same webserver produces the bytes, only the origin differs.
"""

import argparse
import hashlib
import os
import posixpath
import sys
import urllib.parse
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bundle_web_assets as bundler  # noqa: E402 - needs the path tweak above

# What the WebView accepts for each extension; a JS module or stylesheet needs the right family.
EXPECTED_MIME = {
    ".js": ("application/javascript", "text/javascript", "application/x-javascript"),
    ".mjs": ("application/javascript", "text/javascript"),
    ".css": ("text/css",),
    ".json": ("application/json",),
    ".webmanifest": ("application/manifest+json", "application/json"),
    ".svg": ("image/svg+xml",),
    ".png": ("image/png",),
    ".woff2": ("font/woff2", "application/font-woff2", "application/octet-stream"),
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apk", required=True)
    parser.add_argument("--base", required=True)
    parser.add_argument("--cookie", required=True)
    parser.add_argument("--loopback", action="store_true",
                        help="fetch from http://127.0.0.1:19387 instead of the host in the index")
    parser.add_argument("--retries", type=int, default=2)
    args = parser.parse_args()

    base = args.base.rstrip("/")
    with zipfile.ZipFile(args.apk) as apk:
        index = apk.read("assets/web/index.txt").decode("utf-8")
        lines = [line for line in index.splitlines() if line.strip() and not line.startswith("#")]

        ok, stale, absent, bad_mime, bad_fetch = 0, [], [], [], []
        total = 0
        for line in lines:
            fields = line.split("\t")
            if len(fields) < 4:
                print("MALFORMED index line: %r" % line[:100])
                return 1
            url, name, mime, kind = fields[0], fields[1], fields[2], fields[3]
            entry_path = "assets/web/" + name
            if entry_path not in apk.namelist():
                absent.append(name)
                continue
            body = apk.read(entry_path)
            total += len(body)

            ext = posixpath.splitext(name)[1].lower()
            allowed = EXPECTED_MIME.get(ext)
            if allowed and mime not in allowed:
                bad_mime.append((name, mime))

            fetch_url = url
            if args.loopback:
                parsed = urllib.parse.urlsplit(url)
                fetch_url = "http://127.0.0.1:19387" + parsed.path
                if parsed.query:
                    fetch_url += "?" + parsed.query

            try:
                code, fresh, content_type = bundler.fetch(fetch_url, args.cookie)
            except Exception as error:  # noqa: BLE001 - report and continue
                fresh, content_type = None, None
                code = None
                last = error
                for _ in range(max(0, args.retries)):
                    try:
                        code, fresh, content_type = bundler.fetch(fetch_url, args.cookie)
                        break
                    except Exception as retry_error:  # noqa: BLE001
                        last = retry_error
                if fresh is None:
                    bad_fetch.append((name, str(last)))
                    continue
            if code != 200 or hashlib.sha256(fresh).digest() != hashlib.sha256(body).digest():
                stale.append((name, code, len(body), len(fresh or b"")))
                continue
            served = (content_type or "").split(";")[0].strip()
            if served and served != mime:
                bad_mime.append((name, "index=%s served=%s" % (mime, served)))
            ok += 1

    print("index entries: %d ; verified byte-identical: %d ; packaged bytes: %d (%.1f MB)"
          % (len(lines), ok, total, total / 1048576.0))
    for name in absent:
        print("  MISSING FROM APK: %s" % name)
    for name, mime in bad_mime:
        print("  SUSPECT MIME: %s -> %s" % (name, mime))
    for name, error in bad_fetch:
        print("  FETCH FAILED: %s (%s)" % (name, error))
    for name, code, packed, fresh in stale:
        print("  DIFFERS FROM SERVER: %s (http=%s packed=%d fresh=%d)" % (name, code, packed, fresh))
    failed = len(absent) + len(bad_mime) + len(bad_fetch) + len(stale)
    if failed:
        print("%d problem(s)" % failed, file=sys.stderr)
        return 1
    print("all packaged assets match the server, with WebView-safe MIME types")
    return 0


if __name__ == "__main__":
    sys.exit(main())
