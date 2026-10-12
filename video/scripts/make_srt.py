"""Write one .srt per episode next to the rendered mp4 files.

Times come from work/manifest.json (the same numbers ffmpeg used when each
scene clip was cut), text comes from the storyboard subtitles so the file
says exactly what is burned into the picture.
"""

from __future__ import annotations

import json
import pathlib
import sys

VIDEO = pathlib.Path(__file__).resolve().parent.parent
WORK = VIDEO / "work"
OUT = VIDEO / "out"

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import storyboard  # noqa: E402


def stamp(seconds: float) -> str:
    ms = int(round(seconds * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def cue_text(scene: dict) -> list[str]:
    lines = scene.get("subtitle")
    if lines:
        return list(lines)
    words = scene.get("narration", "")
    out, cur = [], ""
    for ch in words:
        cur += ch
        if len(cur) >= 22 and ch in "，。；：、！？,.;:":
            out.append(cur)
            cur = ""
    if cur:
        out.append(cur)
    return out or [""]


def cue_blocks(entries: list[tuple[dict, float]], offset: float,
               first_number: int = 1) -> tuple[list[str], int]:
    """Subtitle blocks for a run of scenes, starting `offset` seconds into the film."""
    lines: list[str] = []
    number = first_number
    clock = offset
    for scene, duration in entries:
        start = clock + 0.30
        end = max(start + 0.5, clock + duration - 0.55)
        body = cue_text(scene) or [""]
        lines.append(str(number))
        lines.append(f"{stamp(start)} --> {stamp(end)}")
        lines.extend(body)
        lines.append("")
        number += 1
        clock += duration
    return lines, number


def main() -> int:
    manifest = json.loads((WORK / "manifest.json").read_text(encoding="utf-8"))
    stories = list(getattr(storyboard, "EPISODES", []))
    written = 0
    merged_lines: list[str] = []
    merged_number = 1
    clock = 0.0

    for story in stories:
        record = manifest.get(story["id"])
        if not record or not record.get("scenes"):
            continue
        scenes = story.get("scenes", [])
        entries = [(scenes[i] if i < len(scenes) else {}, float(entry["seconds"]))
                   for i, entry in enumerate(record["scenes"])]

        if story.get("standalone", True):
            lines, _ = cue_blocks(entries, 0.0)
            srt = (OUT / story["file"]).with_suffix(".srt")
            srt.write_text("\n".join(lines), encoding="utf-8")
            written += 1
            print(f"  srt    {srt.name}  cues={len(entries)}  "
                  f"ends={stamp(float(record['seconds']))}")
        else:
            print(f"  srt    {story['id']} folded into the full film "
                  f"({len(entries)} cue(s) moving to {stamp(clock)})")

        blocks, merged_number = cue_blocks(entries, clock, merged_number)
        merged_lines.extend(blocks)
        clock += float(record["seconds"])

    if merged_lines and len([s for s in stories if s.get("standalone", True)]) > 1:
        target = OUT / "dsh-phone-pair-完整版.srt"
        target.write_text("\n".join(merged_lines), encoding="utf-8")
        written += 1
        print(f"  srt    {target.name}  cues={merged_number - 1}  ends={stamp(clock)}")

    print(f"{written} subtitle file(s) written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
