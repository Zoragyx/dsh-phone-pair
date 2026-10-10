#!/usr/bin/env python3
"""Fetch the DSH web client shell and every static asset it needs, for bundling into the APK.

Why: a cold WebView load of the remote GUI pulls ~30 MB (identity; ~10 MB gzipped) of
content-hashed bundles - two eager `plugins/??<modules>&rev=<hash>` combos, the 78 lazy module
URLs in `globalThis["__DSH_BOOT__"]`, `assets/*.js|css`. On a phone link that measures 4-12 KB/s
that is many minutes of blank screen, and the WebView cache only helps after the first successful
load. Those URLs are content-addressed, so they can ship inside the APK and be served locally by
`shouldInterceptRequest` (see AssetIndex.java).

The shell itself (/pair-app) is dynamic (`Cache-Control: no-store`) and is NOT bundled, and neither
is `/.webmcp/bridge.js`, whose URL carries no content hash (see UNBUNDLED).

All references are resolved to absolute same-origin URLs (`urllib.parse.urljoin`) before being
stored, so the relative spellings in the shell, the `&amp;` entities of the tags and the WebView's
own re-encoding all hit the same index entry.

Output: <out>/index.txt, one line per asset:
<absolute-url>\t<file-name>\t<mime-type>\t<eager|lazy>
("eager" = referenced by a <link>/<script> tag in the shell; the build fails if one of those is
missing, while a missing lazy URL is only reported).

Usage:
  bundle_web_assets.py --base https://<id>.dsh-market.com --cookie <dsh_pair value> --out <dir>
"""

import argparse
import hashlib
import os
import re
import sys
import time
import urllib.parse
import urllib.request

RELATIVE_PATTERNS = [
    re.compile(r"plugins/\?\?[^\"'<>\\ ]+"),
    re.compile(r"\.?/?assets/[A-Za-z0-9._-]+\.(?:js|mjs|css|woff2?|svg|png)"),
    re.compile(r"\.?/?\.webmcp/bridge\.js"),
    re.compile(r"\.?/?manifest\.webmanifest"),
    re.compile(r"\.?/?favicon(?:-dark)?\.svg"),
]

TAG = re.compile(r"<(?:link|script)\b[^>]*>", re.I)

# Same-origin URLs that must stay on the network: /.webmcp/bridge.js carries no content hash in
# its URL, so serving a bundled copy with max-age=1y would freeze the bridge across DSH upgrades.
# It is ~73 KB and revalidates with an ETag, so the network cost is one conditional request.
UNBUNDLED = [
    re.compile(r"^/\.webmcp/bridge\.js$"),
]

MIME = {
    ".js": "application/javascript",
    ".mjs": "application/javascript",
    ".json": "application/json",
    ".webmanifest": "application/manifest+json",
    ".css": "text/css",
    ".html": "text/html",
    ".svg": "image/svg+xml",
    ".png": "image/png",
    ".woff2": "font/woff2",
}


def fetch(url, cookie, timeout=180):
    request = urllib.request.Request(url, headers={
        "Cookie": "dsh_pair=" + cookie,
        "User-Agent": "DSH-Phone-App-Bundler/1.4",
        "Accept-Encoding": "identity",
    })
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.status, response.read(), response.headers.get("Content-Type")


def absolute(html_url, base):
    """Absolute same-origin URL for an HTML reference, or None when it is third party.

    The shell mixes reference styles - `plugins/??a,b&rev=1`, `./assets/x.js`,
    `https://<id>.dsh-market.com/./assets/x.js` - and `index.txt` must hold the canonical
    absolute form, because the WebView asks for the resolved URL (`https://<id>.dsh-market.com/...`)
    and AssetIndex.canonical() reduces both sides to the same rooted path.
    """
    value = html_url.replace("&amp;", "&").strip()
    if "://" in value:
        if not (value == base or value.startswith(base + "/")):
            return None  # third party (e.g. the Cloudflare beacon) - never bundled
        return value
    return urllib.parse.urljoin(base + "/", value)


def unbundled(url):
    """True for same-origin URLs we deliberately keep on the network."""
    return any(pattern.search(urllib.parse.urlparse(url).path) for pattern in UNBUNDLED)


def parse_assets(html, base):
    """(ordered absolute URLs, set of eager absolute URLs)."""
    eager = set()
    for tag in TAG.findall(html):
        for pattern in RELATIVE_PATTERNS:
            for match in pattern.finditer(tag):
                url = absolute(match.group(0), base)
                if url and not unbundled(url):
                    eager.add(url)

    ordered, seen = [], set()
    for pattern in RELATIVE_PATTERNS:
        for match in pattern.finditer(html):
            url = absolute(match.group(0), base)
            if url and not unbundled(url) and url not in seen:
                seen.add(url)
                ordered.append(url)
    # Anything the shell only reaches through __DSH_BOOT__ is eager too when it sits in a tag.
    for url in eager:
        if url not in seen:
            seen.add(url)
            ordered.append(url)
    return ordered, eager


def file_name(url):
    digest = hashlib.sha1(url.encode("utf-8")).hexdigest()
    tail = url.split("??")[-1].rsplit("/", 1)[-1]
    ext = os.path.splitext(urllib.parse.urlparse(url).path)[1] or ".js"
    if ext not in MIME:
        ext = ".js"
    tail = re.sub(r"[^A-Za-z0-9._-]", "_", tail)
    if len(tail) > 40:
        tail = tail[:40]
    return digest + "-" + tail + ext


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", required=True, help="relay base URL, e.g. https://<id>.dsh-market.com")
    parser.add_argument("--cookie", required=True, help="value of the dsh_pair cookie")
    parser.add_argument("--out", required=True, help="directory to write assets + index.txt into")
    args = parser.parse_args()

    base = args.base.rstrip("/")
    os.makedirs(args.out, exist_ok=True)

    status, shell, _ = fetch(base + "/pair-app", args.cookie)
    html = shell.decode("utf-8", "replace")
    print("shell: http=%s bytes=%d" % (status, len(html)))
    assets, eager = parse_assets(html, base)
    print("assets referenced: %d (%d eager)" % (len(assets), len(eager)))
    if not assets:
        print("ERROR: no asset URLs found - the shell layout changed", file=sys.stderr)
        return 1

    lines, total, missing_eager, missing_lazy = [], 0, [], []
    for url in assets:
        eager_asset = url in eager
        label = urllib.parse.urlparse(url).path.split("??")[-1][:58]
        try:
            started = time.time()
            code, body, content_type = fetch(url, args.cookie)
        except Exception as error:  # noqa: BLE001 - collect and continue
            (missing_eager if eager_asset else missing_lazy).append((url, str(error)))
            print("  FAIL %-58s %s" % (label, error))
            continue
        if code != 200 or not body:
            (missing_eager if eager_asset else missing_lazy).append(
                (url, "http=%s bytes=%d" % (code, len(body))))
            print("  FAIL %-58s http=%s bytes=%d" % (label, code, len(body)))
            continue
        name = file_name(url)
        with open(os.path.join(args.out, name), "wb") as handle:
            handle.write(body)
        mime = (content_type or "").split(";")[0].strip()
        if not mime or mime == "application/octet-stream":
            mime = MIME.get(os.path.splitext(name)[1], "application/javascript")
        lines.append("%s\t%s\t%s\t%s" % (url, name, mime, "eager" if eager_asset else "lazy"))
        total += len(body)
        print("  ok %-4s %-52s %8d B %5.1fs" %
              ("eager" if eager_asset else "lazy", label[:52], len(body), time.time() - started))

    header = [
        "# DSH web client assets bundled into the APK, fetched from %s" % base,
        "# one line per asset: <absolute-url> <TAB> <file> <TAB> <mime> <TAB> <eager|lazy>",
        "# eager entries are referenced by a <link>/<script> tag in the shell; lazy ones only",
        "# through the __DSH_BOOT__ registry. Lookups go through AssetIndex.canonical(), which",
        "# reduces both the stored URL and the WebView's request to the same rooted path.",
    ]
    for pattern in UNBUNDLED:
        header.append("# not bundled (kept on the network, unhashed URL): %s" % pattern.pattern)
    with open(os.path.join(args.out, "index.txt"), "w", encoding="utf-8", newline="\n") as handle:
        handle.write("\n".join(header + lines) + "\n")
    print("bundled %d/%d assets, %d bytes (%.1f MB) -> %s" %
          (len(lines), len(assets), total, total / 1048576.0, args.out))
    for url, why in missing_lazy:
        print("  missing (lazy, tolerated): %s (%s)" % (url[:70], why))
    for url, why in missing_eager:
        print("  MISSING EAGER: %s (%s)" % (url[:70], why), file=sys.stderr)
    if missing_eager:
        return 1
    return 0 if lines else 1


if __name__ == "__main__":
    sys.exit(main())
