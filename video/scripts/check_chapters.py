"""核对合辑里「时间节点」那一页写的数字对不对。

做法：从成片里按节点时间抽帧，和分镜渲染出来的设计帧做逐像素比较；
再顺手把节点页本身抽出来存到 work/ 下，方便肉眼看一眼。

    python scripts/check_chapters.py
"""

from __future__ import annotations

import json
import pathlib
import subprocess
import sys

VIDEO = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(VIDEO / ".deps"))
sys.path.insert(0, str(VIDEO / "scripts"))

from PIL import Image, ImageChops  # noqa: E402

import storyboard  # noqa: E402

FFMPEG = VIDEO / "tools" / "ffmpeg.exe"
OUT = VIDEO / "out"
FRAMES = VIDEO / "work" / "frames"
WORK = VIDEO / "work"
COMBINED = OUT / "dsh-phone-pair-完整版.mp4"


def shot(seconds: float, target: pathlib.Path) -> None:
    subprocess.run(
        [str(FFMPEG), "-y", "-hide_banner", "-loglevel", "error",
         "-ss", f"{seconds:.3f}", "-i", str(COMBINED), "-frames:v", "1", str(target)],
        check=True)


def mean_diff(a: pathlib.Path, b: pathlib.Path) -> float:
    left = Image.open(a).convert("L")
    right = Image.open(b).convert("L")
    diff = ImageChops.difference(left, right)
    data = diff.getdata()
    return sum(data) / len(data)


def main() -> int:
    if not COMBINED.exists():
        print(f"missing {COMBINED}; run build.py first")
        return 2

    # 各集在合辑里的起点：用 manifest 的实测时长重算，和 build.py 的口径一致
    manifest = json.loads((WORK / "manifest.json").read_text(encoding="utf-8"))
    clock = 0.0
    starts: dict[str, float] = {}
    for episode in storyboard.EPISODES:
        starts[episode["id"]] = clock
        clock += manifest[episode["id"]]["seconds"]

    print("chapter starts (from manifest): "
          + ", ".join(f"{k}={v:.1f}s" for k, v in starts.items()))
    print(f"combined length: {clock:.1f}s")

    problems = 0
    checks = [
        ("declaration first", starts["ep0"] + 2.0, "ep0_01.png"),
        ("ep0-2 timeline card", starts["ep0"] + manifest["ep0"]["seconds"] - 18.0, "ep0_02.png"),
        ("computer node -> ep2", starts["ep2"] + 1.5, "ep2_01.png"),
        ("phone node -> ep3", starts["ep3"] + 1.5, "ep3_01.png"),
    ]
    for label, seconds, frame_name in checks:
        scratch = WORK / f"chapter_probe_{frame_name}"
        shot(seconds, scratch)
        diff = mean_diff(scratch, FRAMES / frame_name)
        verdict = "ok" if diff < 8.0 else "MISMATCH"
        if verdict != "ok":
            problems += 1
        print(f"  {label:<22} t={seconds:7.2f}s  diff={diff:6.2f}  {verdict}")

    card = WORK / "chapter_card.png"
    shot(starts["ep0"] + manifest["ep0"]["seconds"] - 18.0, card)
    print(f"timeline card written to {card}")
    print(f"{problems} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
