#!/usr/bin/env python3
"""List every remaining damaged Java string literal (and any damaged comment text)
in the reversed source, with the best-matching string from a known-good dex pool."""
import difflib
import json
import re
import sys

sys.path.insert(0, r"C:\Users\Zora\Documents\deepseek-harness\default-workspace\dsh-phone-app\tools")
from repair_encoding import build_cp936_inverse, dex_strings, reverse_corruption

PROJ = r"C:\Users\Zora\Documents\deepseek-harness\default-workspace\dsh-phone-app"
MARKERS = "\ue000\ufffd"


def clean(s):
    return "".join("" if ch in MARKERS else ch for ch in s)


def main():
    raw = open(PROJ + r"\java\com\dsh\phone\MainActivity.java", "rb").read()
    table = build_cp936_inverse()
    text, unknown = reverse_corruption(raw, table)
    pool = dex_strings(PROJ + r"\artifacts\dsh-phone-1.3.apk")
    cjk_pool = [s for s in pool if any("\u4e00" <= c <= "\u9fff" for c in s)]

    out = {"unknown_bytes": unknown, "literals": [], "outside": []}

    # damaged regions outside string literals (comments / code)
    spans = [m.span() for m in re.finditer(r'"(?:[^"\\\n]|\\.)*"', text)]
    for m in re.finditer("[" + MARKERS + "]+", text):
        if not any(a <= m.start() < b for a, b in spans):
            line = text.count("\n", 0, m.start()) + 1
            out["outside"].append(
                {"line": line, "ctx": text[max(0, m.start() - 60):m.end() + 60].encode("unicode_escape").decode()}
            )

    for m in re.finditer(r'"((?:[^"\\\n]|\\.)*)"', text):
        lit = m.group(1)
        if not any(ch in lit for ch in MARKERS):
            continue
        base = clean(lit)
        cands = sorted(
            cjk_pool,
            key=lambda s: difflib.SequenceMatcher(None, base, s).ratio(),
            reverse=True,
        )[:4]
        out["literals"].append(
            {
                "line": text.count("\n", 0, m.start()) + 1,
                "damaged": lit.encode("unicode_escape").decode(),
                "clean": base.encode("unicode_escape").decode(),
                "candidates": [
                    {"s": c.encode("unicode_escape").decode(), "ratio": round(difflib.SequenceMatcher(None, base, c).ratio(), 3)}
                    for c in cands
                ],
            }
        )

    with open(r"C:\Users\Zora\AppData\Local\Temp\damage_report.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print("damaged literals:", len(out["literals"]), "| damaged non-literal regions:", len(out["outside"]))


if __name__ == "__main__":
    main()
