"""Audit a pairing-mode APK before it is published.

A pairing-mode build must carry *no* pairing credential and no reference to the machine it was
built on: anyone can download it, and the phone learns its own computer from the link the user
pastes. This script fails loudly if the build-time credential ever leaks into the package.

Usage:
    python tools/audit_pair_build.py --apk artifacts/dsh-phone-pair-1.0.apk --device-id-file device-id.txt
"""

from __future__ import annotations

import argparse
import hashlib
import re
import sys
import zipfile
from pathlib import Path

DEFAULT_APK = Path("artifacts/dsh-phone-pair-1.0.apk")
DEFAULT_ID = Path("device-id.txt")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apk", type=Path, default=DEFAULT_APK)
    parser.add_argument("--device-id-file", type=Path, default=DEFAULT_ID)
    args = parser.parse_args()

    apk: Path = args.apk
    if not apk.is_file():
        print(f"error: apk not found: {apk}")
        return 2

    raw = apk.read_bytes()
    print(f"apk     : {apk}")
    print(f"bytes   : {len(raw)}")
    print(f"sha256  : {hashlib.sha256(raw).hexdigest().upper()}")

    build_id = ""
    if args.device_id_file.is_file():
        build_id = args.device_id_file.read_text(encoding="utf-8").strip()
    print(f"build id: {build_id or '(none)'}")

    leaks: dict[str, list[str]] = {}
    informational: dict[str, list[str]] = {}
    checks = {
        # A pairing-mode build must not carry the credential it was built with, nor any cookie
        # *value*. The literal cookie *name* ("dsh_pair=") is expected in the code that writes it.
        "build-time device id": build_id.encode() if build_id else b"",
        "baked cookie value": None,  # regex below
    }
    cookie_value = re.compile(rb"dsh_pair=[0-9a-fA-F]{16,}")

    with zipfile.ZipFile(apk) as z:
        names = z.namelist()
        for name in names:
            data = z.read(name)
            for label, needle in checks.items():
                if needle and needle in data:
                    leaks.setdefault(label, []).append(name)
            if cookie_value.search(data):
                leaks.setdefault("baked cookie value", []).append(name)
            if b"dsh_pair=" in data:
                informational.setdefault("cookie name literal", []).append(name)

        dex = z.read("classes.dex")
        index = z.read("assets/web/index.txt").decode("utf-8")
        entries = [line for line in index.splitlines() if line and not line.startswith("#")]
        html = [n for n in names if n.endswith(".html")]

    print(f"entries : {len(names)} package entries, {len(entries)} bundled assets, {len(html)} html")
    print(f"ua      : pairing-mode ua present = {b'DSH-Phone-Pair/1.0' in dex}")
    print(f"symbols : BASE_HOST/BASE_URL/DEVICE_ID present = "
          f"{b'BASE_HOST' in dex or b'BASE_URL' in dex or b'DEVICE_ID' in dex}")

    if informational:
        for label, where in sorted(informational.items()):
            print(f"note    : {label} present in {', '.join(where[:4])} (expected - the app writes it)")

    if leaks:
        print("\nLEAKS FOUND:")
        for label, where in sorted(leaks.items()):
            sample = ", ".join(where[:4])
            print(f"  - {label}: {len(where)} file(s) ({sample})")
        print("\nverdict : FAIL - do not publish this apk")
        return 1

    print("\nverdict : OK - no build-time credential or cookie inside the package")
    return 0


if __name__ == "__main__":
    sys.exit(main())
