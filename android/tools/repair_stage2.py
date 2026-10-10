#!/usr/bin/env python3
"""Stage 2 repair: restore every damaged Java string literal from a known-good dex pool.

Strategy: reverse the cp936 corruption (unknown bytes -> U+E000 markers), then for each
literal that still contains markers, build a regex where every marker run is '.{0,4}' and
search the dex string pool for it (substring search, so fragments of a longer pool string
also match). A unique search hit decides the replacement; anything ambiguous or missing is
reported for manual handling.
"""
import difflib
import re
import sys

sys.path.insert(0, r"C:\Users\Zora\Documents\deepseek-harness\default-workspace\dsh-phone-app\tools")
from repair_encoding import build_cp936_inverse, dex_strings

PROJ = r"C:\Users\Zora\Documents\deepseek-harness\default-workspace\dsh-phone-app"
SRC = PROJ + r"\java\com\dsh\phone\MainActivity.java"
APK = PROJ + r"\artifacts\dsh-phone-1.3.apk"
OUT = r"C:\Users\Zora\AppData\Local\Temp\MainActivity.stage2.java"

UNKNOWN = "\ue000"
MARKERS = UNKNOWN + "\ufffd"
LIT = re.compile(r'"((?:[^"\\\n]|\\.)*)"')


def reverse_corruption(raw):
    table = build_cp936_inverse()
    table["\u20ac"] = b"\x80"          # cp936 single byte 0x80 (euro sign)
    text = raw.decode("utf-8-sig")
    out = bytearray()
    for i, c in enumerate(text):
        o = ord(c)
        if o < 0x80:
            if c == "?" and (
                (i > 0 and ord(text[i - 1]) > 0x7F) or (i + 1 < len(text) and ord(text[i + 1]) > 0x7F)
            ):
                out += b"\xff"
            else:
                out.append(o)
        else:
            pair = table.get(c)
            out += pair if pair else b"\xff"
    return UNKNOWN.join(p.decode("utf-8", "replace") for p in bytes(out).split(b"\xff"))


def pattern_for(core):
    parts = []
    for ch in core:
        parts.append(".{0,4}" if ch in MARKERS else re.escape(ch))
    pat = "".join(parts)
    return re.sub(r"(\.\{0,4\})+", ".{0,5}", pat)


def main():
    text = reverse_corruption(open(SRC, "rb").read())
    pool = dex_strings(APK)
    cjk_pool = [s for s in pool if any("\u4e00" <= c <= "\u9fff" for c in s)]

    fixed, unresolved = 0, []
    for m in LIT.finditer(text):
        lit = m.group(1)
        if not any(ch in lit for ch in MARKERS):
            continue
        if not any("\u4e00" <= c <= "\u9fff" for c in lit):
            unresolved.append((lit, []))
            continue
        core = re.sub(r"^[\x00-\x7f]+", "", lit)
        core = re.sub(r"[\x00-\x7f]+$", "", core)
        pat = re.compile(pattern_for(core))
        hits = []
        for s in cjk_pool:
            mm = pat.search(s)
            if mm:
                hits.append(mm.group(0))
        hits = list(dict.fromkeys(hits))
        if len(hits) == 1:
            fixed += 1
            print("FIX  %-70s -> %s" % (lit.encode("unicode_escape").decode(), hits[0].encode("unicode_escape").decode()))
        else:
            unresolved.append((lit, hits))

    print("\nfixed=%d unresolved=%d" % (fixed, len(unresolved)))
    lines = text.split("\n")
    for lit, hits in unresolved:
        pos = text.find(lit)
        line = text.count("\n", 0, pos) + 1
        print("\n--- line %d: %s" % (line, lit.encode("unicode_escape").decode()))
        for i in range(max(0, line - 2), min(len(lines), line + 1)):
            print("    %4d | %s" % (i + 1, lines[i].strip().encode("unicode_escape").decode()))
        for h in hits[:5]:
            print("      cand: %s" % h.encode("unicode_escape").decode())

    open(OUT, "wb").write(text.encode("utf-8"))
    print("\nwrote %s" % OUT)


if __name__ == "__main__":
    main()
