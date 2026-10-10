#!/usr/bin/env python3
"""List every asset URL a live /pair-app shell references, for tools/IndexMatchCheck.java.

Regression guard for the bundled web assets: run it against the running DSH instance, then feed the
output plus the APK's assets/web/index.txt to IndexMatchCheck. Every URL that bundle_web_assets.py
bundles must hit, and the ones it deliberately leaves out (see UNBUNDLED) must miss - a mismatch
means the APK ships assets that will silently never be used.

The URLs are written in their resolved absolute form, which is what the WebView actually requests
(the shell's own spellings are relative and entity-escaped; AssetIndex.canonical() collapses both).

Usage:
  shell_urls.py --base https://<id>.dsh-market.com --cookie <dsh_pair value> --out <urls.txt>
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bundle_web_assets as bundler  # noqa: E402 - needs the path tweak above


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", required=True, help="relay base URL, e.g. https://<id>.dsh-market.com")
    parser.add_argument("--cookie", required=True, help="value of the dsh_pair cookie")
    parser.add_argument("--out", required=True, help="file to write the URL list to")
    args = parser.parse_args()

    base = args.base.rstrip("/")
    status, shell, _ = bundler.fetch(base + "/pair-app", args.cookie)
    html = shell.decode("utf-8", "replace")

    seen, urls = set(), []
    for pattern in bundler.RELATIVE_PATTERNS:
        for match in pattern.finditer(html):
            url = bundler.absolute(match.group(0), base)
            if url and url not in seen:
                seen.add(url)
                urls.append(url)
    if not urls:
        print("ERROR: no asset URLs found - the shell layout changed", file=sys.stderr)
        return 1

    with open(args.out, "w", encoding="utf-8", newline="\n") as handle:
        handle.write("\n".join(urls) + "\n")

    unbundled = [url for url in urls if bundler.unbundled(url)]
    print("shell: http=%s bytes=%d urls=%d (expected hits=%d, expected misses=%d)"
          % (status, len(html), len(urls), len(urls) - len(unbundled), len(unbundled)))
    for url in unbundled:
        print("  not bundled by design: %s" % url)
    return 0


if __name__ == "__main__":
    sys.exit(main())
