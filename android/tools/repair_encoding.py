#!/usr/bin/env python3
"""Repair a UTF-8 source file that PowerShell decoded as cp936/GBK and rewrote as UTF-8.

Stage 1: exact inverse of the corruption (cp936 char -> original UTF-8 bytes) using a
         table built from cp936 *decoding* all byte pairs, so vendor PUA chars work too.
         Bytes lost to the decoder's '?' substitution are marked with U+E000.
Stage 2: for every damaged region inside a Java string literal, match against the string
         pool of a known-good dex (built from the previous APK) and restore the literal.

Usage:
  python repair_encoding.py --file <corrupt.java> --dex-apk <apk> --out <repaired.java>
"""
import argparse
import re
import struct
import sys
import zipfile


def build_cp936_inverse():
    table = {}
    for b1 in range(0x81, 0x100):
        for b2 in range(0x40, 0x100):
            if b2 == 0x7F:
                continue
            try:
                s = bytes([b1, b2]).decode("cp936")
            except UnicodeDecodeError:
                continue
            if len(s) == 1 and s not in table:
                table[s] = bytes([b1, b2])
    return table


def reverse_corruption(raw, table):
    text = raw.decode("utf-8-sig")
    out = bytearray()
    unknown = 0
    for i, c in enumerate(text):
        o = ord(c)
        if o < 0x80:
            if c == "?" and (
                (i > 0 and ord(text[i - 1]) > 0x7F) or (i + 1 < len(text) and ord(text[i + 1]) > 0x7F)
            ):
                out += b"\xff"          # byte swallowed by the decoder's replacement
                unknown += 1
            else:
                out.append(o)
        else:
            pair = table.get(c)
            if pair is None:
                out += b"\xff"
                unknown += 1
            else:
                out += pair
    pieces = bytes(out).split(b"\xff")
    return "\ue000".join(p.decode("utf-8", "replace") for p in pieces), unknown


def dex_strings(apk_path):
    with zipfile.ZipFile(apk_path) as z:
        data = z.read("classes.dex")
    if data[:8] != b"dex\n035\x00" and not data.startswith(b"dex\n"):
        raise SystemExit("not a dex file")
    string_ids_size, string_ids_off = struct.unpack_from("<II", data, 0x38)
    strings = []
    for i in range(string_ids_size):
        off = struct.unpack_from("<I", data, string_ids_off + 4 * i)[0]
        # ULEB128 utf16 length, then MUTF-8 bytes, NUL terminated
        j = off
        shift = 0
        while True:
            b = data[j]
            j += 1
            if not (b & 0x80):
                break
            shift += 7
        end = data.index(b"\x00", j)
        strings.append(data[j:end].decode("utf-8", "replace"))
    return strings


LITERAL = re.compile(r'"((?:[^"\\\n]|\\.)*)"')


def repair_literals(text, dex, report):
    bad_markers = "\ue000\ufffd"
    fixed = 0
    unresolved = []
    index = {}

    def damage_runs(lit):
        return [m for m in re.finditer("[" + bad_markers + "]+", lit)]

    for m in LITERAL.finditer(text):
        lit = m.group(1)
        if not any(ch in lit for ch in bad_markers):
            continue
        if all(ord(ch) < 0x80 for ch in lit if ch not in bad_markers):
            continue  # only ASCII + markers: not a Chinese literal, leave for manual review
        pattern = "^"
        for ch in lit:
            if ch in bad_markers:
                pattern += ".{0,3}"
            elif ch == "\\":
                pattern += re.escape(ch)
            else:
                pattern += re.escape(ch)
        pattern = re.sub(r"(\.\{0,3\})+", ".{0,4}", pattern) + "$"
        if pattern not in index:
            rx = re.compile(pattern)
            index[pattern] = [s for s in dex if rx.match(s)]
        hits = index[pattern]
        if len(hits) == 1:
            report.append(("FIXED", lit, hits[0]))
            fixed += 1
        else:
            unresolved.append((lit, hits[:6]))
    return fixed, unresolved


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", required=True)
    ap.add_argument("--dex-apk", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    table = build_cp936_inverse()
    raw = open(args.file, "rb").read()
    text, unknown = reverse_corruption(raw, table)
    print("stage1: unknown bytes marked = %d, U+FFFD left = %d" % (unknown, text.count("\ufffd")))

    dex = dex_strings(args.dex_apk)
    print("dex strings: %d" % len(dex))
    report = []
    fixed, unresolved = repair_literals(text, dex, report)
    print("literals matched uniquely: %d" % fixed)

    for kind, old, new in report:
        print("  %s: %s -> %s" % (kind, old.encode("unicode_escape").decode(), new.encode("unicode_escape").decode()))
    for old, hits in unresolved:
        print("  UNRESOLVED: %s" % old.encode("unicode_escape").decode())
        for h in hits:
            print("       candidate: %s" % h.encode("unicode_escape").decode())

    open(args.out, "wb").write(text.encode("utf-8"))
    print("wrote %s (%d bytes, no BOM)" % (args.out, len(text.encode("utf-8"))))


if __name__ == "__main__":
    main()
