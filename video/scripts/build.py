"""Build the tutorial videos: frames -> narration -> per-scene clips -> episodes.

Usage (from the video directory):
    python scripts\\build.py --frames-only            # just render the PNGs
    python scripts\\build.py --episodes ep1           # build one episode end to end
    python scripts\\build.py                          # build everything

The pipeline is idempotent: frames, narration and scene clips are cached and
only rebuilt when missing or when --force is given.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import math
import pathlib
import subprocess
import sys
import time

import storyboard
from theme import FPS, H, W
import visuals

VIDEO = pathlib.Path(__file__).resolve().parent.parent
DEPS = VIDEO / ".deps"
if DEPS.exists() and str(DEPS) not in sys.path:
    sys.path.insert(0, str(DEPS))
WORK = VIDEO / "work"
FRAMES = WORK / "frames"
TTS = WORK / "tts"
SCENES = WORK / "scenes"
CONCAT = WORK / "concat"
OUT = VIDEO / "out"
FFMPEG = VIDEO / "tools" / "ffmpeg.exe"
FFPROBE = VIDEO / "tools" / "ffprobe.exe"

VOICE_DEFAULT = "zh-CN-XiaoxiaoNeural"
RATE_DEFAULT = "+10%"
LEAD_SILENCE = 0.30
TAIL_SILENCE = 0.80


def log(message: str) -> None:
    print(message, flush=True)


def run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                          errors="replace")


def audio_seconds(path: pathlib.Path) -> float:
    proc = run([str(FFPROBE), "-v", "error", "-show_entries", "format=duration",
                "-of", "csv=p=0", str(path)])
    if proc.returncode != 0:
        raise RuntimeError(f"ffprobe failed on {path}: {proc.stderr.strip()}")
    return float(proc.stdout.strip())


# --------------------------------------------------------------------------- frames


CHAPTER_KIND = "chapters"


def clock_text(seconds: float) -> str:
    total = int(seconds)
    hours, rest = divmod(total, 3600)
    minutes, secs = divmod(rest, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def render_frames(episodes: list[dict], force: bool = False,
                  chapter_times: dict[str, str] | None = None,
                  allow_placeholder: bool = False) -> list[tuple[dict, int, pathlib.Path]]:
    FRAMES.mkdir(parents=True, exist_ok=True)
    todo: list[tuple[dict, int, pathlib.Path]] = []
    for episode in episodes:
        for index, scene in enumerate(episode["scenes"], 1):
            path = FRAMES / f"{episode['id']}_{index:02d}.png"
            todo.append((episode, index, path))
            visual = scene.get("visual", {})
            if visual.get("kind") == CHAPTER_KIND:
                if chapter_times is None and not allow_placeholder:
                    log(f"  defer  {path.name} (waits for episode start times)")
                    continue
                for item in visual.get("items", []):
                    if item.get("ep"):
                        item["time"] = (chapter_times or {}).get(item["ep"], "--:--")
                # 总是重画：数字会随成片长度变化
                visuals.compose(episode["label"], scene).save(path)
                log(f"  frame  {path.name}")
                continue
            if path.exists() and not force:
                continue
            img = visuals.compose(episode["label"], scene)
            img.save(path)
            log(f"  frame  {path.name}")
    return todo


def episode_lengths(episodes: list[dict]) -> dict[str, float]:
    """Total length of each episode, from the (already synthesised) narration."""
    lengths: dict[str, float] = {}
    for episode in episodes:
        total = 0.0
        for index in range(1, len(episode["scenes"]) + 1):
            speech = TTS / episode["id"] / f"{index:02d}.mp3"
            if not speech.exists():
                return {}
            total += audio_seconds(speech) + LEAD_SILENCE + TAIL_SILENCE
        lengths[episode["id"]] = total
    return lengths


def chapter_starts(episodes: list[dict]) -> dict[str, str]:
    """Where each episode begins inside the merged film, as mm:ss."""
    lengths = episode_lengths(episodes)
    if not lengths:
        return {}
    starts: dict[str, str] = {}
    clock = 0.0
    for episode in episodes:
        starts[episode["id"]] = clock_text(clock)
        clock += lengths[episode["id"]]
    return starts


# --------------------------------------------------------------------------- narration


async def synth(text: str, path: pathlib.Path, voice: str, rate: str) -> None:
    import edge_tts

    last: Exception | None = None
    for attempt in range(1, 4):
        try:
            communicate = edge_tts.Communicate(text, voice, rate=rate)
            await communicate.save(str(path))
            if path.stat().st_size > 2000:
                return
            last = RuntimeError(f"audio too small: {path.stat().st_size} bytes")
        except Exception as exc:  # noqa: BLE001 - retry any transport error
            last = exc
        log(f"    retry {attempt}/3 for {path.name}: {last}")
        await asyncio.sleep(2.0 * attempt)
    raise RuntimeError(f"TTS failed for {path.name}: {last}")


async def build_narration(episodes: list[dict], voice: str, rate: str,
                          force: bool = False) -> None:
    TTS.mkdir(parents=True, exist_ok=True)
    for episode in episodes:
        episode_dir = TTS / episode["id"]
        episode_dir.mkdir(parents=True, exist_ok=True)
        for index, scene in enumerate(episode["scenes"], 1):
            path = episode_dir / f"{index:02d}.mp3"
            if path.exists() and path.stat().st_size > 2000 and not force:
                continue
            log(f"  voice  {episode['id']}/{path.name}")
            await synth(scene["narration"], path, voice, rate)


# --------------------------------------------------------------------------- clips


def scene_filter(fade_in: bool, fade_out: bool, duration: float) -> str:
    """Still frame + short fades. No camera motion by default.

    zoompan was re-sampling the PNG at sub-pixel offsets on every frame, which
    showed up as a constant shimmer/jitter on text. A still image is stable and
    is what was asked for; `--motion` brings the old Ken-Burns back.
    """
    chain = [f"scale={W}:{H}", "format=yuv420p"]
    if fade_in:
        chain.append("fade=t=in:st=0:d=0.7")
    if fade_out:
        chain.append(f"fade=t=out:st={max(duration - 0.8, 0.1):.2f}:d=0.8")
    return ",".join(chain)


def zoom_filter(variant: int, frames: int, fade_in: bool, fade_out: bool,
                duration: float) -> str:
    """Optional Ken-Burns motion (`--motion`); off by default."""
    n = max(frames, 2)
    if variant == 0:
        motion = (f"zoompan=z='min(1+0.00045*on,1.05)':d={n + 5}:"
                  f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={W}x{H}:fps={FPS}")
    elif variant == 1:
        motion = (f"zoompan=z='1.06':d={n + 5}:x='(iw-iw/zoom)*on/{n}':"
                  f"y='(ih-ih/zoom)/2':s={W}x{H}:fps={FPS}")
    else:
        motion = (f"zoompan=z='max(1.06-0.0004*on,1.01)':d={n + 5}:"
                  f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={W}x{H}:fps={FPS}")
    chain = [f"scale={int(W * 1.25)}:{int(H * 1.25)}", motion, "format=yuv420p"]
    if fade_in:
        chain.append("fade=t=in:st=0:d=0.7")
    if fade_out:
        chain.append(f"fade=t=out:st={max(duration - 0.8, 0.1):.2f}:d=0.8")
    return ",".join(chain)


def build_clips(episodes: list[dict], force: bool = False,
                motion: bool = False) -> dict:
    SCENES.mkdir(parents=True, exist_ok=True)
    manifest: dict[str, dict] = {}
    for episode in episodes:
        ep_manifest = {"file": episode["file"], "label": episode["label"], "scenes": []}
        total = 0.0
        scene_count = len(episode["scenes"])
        for index, scene in enumerate(episode["scenes"], 1):
            frame = FRAMES / f"{episode['id']}_{index:02d}.png"
            speech = TTS / episode["id"] / f"{index:02d}.mp3"
            clip = SCENES / f"{episode['id']}_{index:02d}.mp4"
            if not frame.exists():
                raise FileNotFoundError(f"missing frame {frame}; run --frames-only first")
            if not speech.exists():
                raise FileNotFoundError(f"missing narration {speech}")
            speech_len = audio_seconds(speech)
            duration = speech_len + LEAD_SILENCE + TAIL_SILENCE
            frames = int(math.ceil(duration * FPS))
            if clip.exists() and not force:
                actual = audio_seconds(clip)
                if abs(actual - duration) < 0.35:
                    log(f"  clip   {clip.name} (cached, {actual:.1f}s)")
                    total += actual
                    ep_manifest["scenes"].append(
                        {"index": index, "title": scene["title"], "seconds": round(actual, 2),
                         "narration": scene["narration"]})
                    continue
            variant = (index - 1) % 3
            if motion:
                video_filter = zoom_filter(variant, frames, index == 1,
                                           index == scene_count, duration)
            else:
                video_filter = scene_filter(index == 1, index == scene_count, duration)
            cmd = [
                str(FFMPEG), "-y", "-hide_banner", "-loglevel", "error",
                "-loop", "1", "-framerate", str(FPS), "-i", str(frame),
                "-i", str(speech),
                "-filter_complex",
                f"[0:v]{video_filter}[v]",
                "-map", "[v]", "-map", "1:a",
                "-af", f"adelay={int(LEAD_SILENCE * 1000)}|{int(LEAD_SILENCE * 1000)},apad",
                "-c:v", "libx264", "-preset", "faster", "-crf", "20", "-pix_fmt", "yuv420p",
                "-c:a", "aac", "-b:a", "160k", "-ar", "44100", "-ac", "2",
                "-t", f"{duration:.3f}", "-movflags", "+faststart", str(clip),
            ]
            started = time.time()
            proc = run(cmd)
            if proc.returncode != 0:
                raise RuntimeError(f"ffmpeg failed for {clip.name}:\n{proc.stderr}")
            actual = audio_seconds(clip)
            total += actual
            log(f"  clip   {clip.name}  {actual:.1f}s  ({time.time() - started:.1f}s encode)")
            ep_manifest["scenes"].append(
                {"index": index, "title": scene["title"], "seconds": round(actual, 2),
                 "narration": scene["narration"]})
        ep_manifest["seconds"] = round(total, 2)
        manifest[episode["id"]] = ep_manifest
    return manifest


# --------------------------------------------------------------------------- concat


def concat(episodes: list[dict], pieces: list[pathlib.Path], target: pathlib.Path) -> float:
    CONCAT.mkdir(parents=True, exist_ok=True)
    listing = CONCAT / (target.stem + ".txt")
    with listing.open("w", encoding="utf-8") as handle:
        for piece in pieces:
            handle.write("file '" + piece.as_posix() + "'\n")
    target.parent.mkdir(parents=True, exist_ok=True)
    proc = run([str(FFMPEG), "-y", "-hide_banner", "-loglevel", "error",
                "-f", "concat", "-safe", "0", "-i", str(listing),
                "-c", "copy", "-movflags", "+faststart", str(target)])
    if proc.returncode != 0:
        raise RuntimeError(f"concat failed for {target.name}:\n{proc.stderr}")
    return audio_seconds(target)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--episodes", nargs="*", default=None,
                        help="episode ids, e.g. ep1 ep3 (default: all)")
    parser.add_argument("--voice", default=VOICE_DEFAULT)
    parser.add_argument("--rate", default=RATE_DEFAULT)
    parser.add_argument("--frames-only", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--motion", action="store_true",
                        help="bring back the Ken-Burns zoom/pan (off by default: it shimmered)")
    parser.add_argument("--no-combined", action="store_true")
    args = parser.parse_args()

    episodes = storyboard.EPISODES
    if args.episodes:
        wanted = set(args.episodes)
        episodes = [ep for ep in episodes if ep["id"] in wanted]
        missing = wanted - {ep["id"] for ep in episodes}
        if missing:
            log(f"unknown episode ids: {sorted(missing)}")
            return 2
    if not FFMPEG.exists():
        log(f"ffmpeg not found at {FFMPEG}")
        return 2

    log(f"rendering frames for {len(episodes)} episode(s)")
    render_frames(episodes, force=args.force, allow_placeholder=args.frames_only)
    if args.frames_only:
        log("frames done (--frames-only)")
        return 0

    log("synthesising narration")
    asyncio.run(build_narration(episodes, args.voice, args.rate, force=args.force))

    if any(scene.get("visual", {}).get("kind") == CHAPTER_KIND
           for episode in episodes for scene in episode["scenes"]):
        starts = chapter_starts(episodes)
        if starts:
            log("chapter timeline: " + ", ".join(f"{k}={v}" for k, v in starts.items()))
        else:
            log("chapter timeline unavailable (narration missing); keeping placeholders")
        render_frames(episodes, force=args.force, chapter_times=starts, allow_placeholder=True)

    log("encoding scene clips")
    manifest = build_clips(episodes, force=args.force, motion=args.motion)

    log("joining episodes")
    OUT.mkdir(parents=True, exist_ok=True)
    all_pieces: list[pathlib.Path] = []
    for episode in episodes:
        pieces = [SCENES / f"{episode['id']}_{i:02d}.mp4"
                  for i in range(1, len(episode["scenes"]) + 1)]
        all_pieces.extend(pieces)
        if episode.get("standalone", True) is False:
            # 只作为合辑的开头，不单独出片
            log(f"  merged {episode['id']}  {len(pieces)} scene(s) folded into the full film")
            continue
        target = OUT / episode["file"]
        seconds = concat(episodes, pieces, target)
        size_mb = target.stat().st_size / 1024 / 1024
        manifest[episode["id"]]["mb"] = round(size_mb, 2)
        manifest[episode["id"]]["seconds"] = round(seconds, 2)
        log(f"  episode {target.name}  {seconds / 60:.2f} min  {size_mb:.1f} MB")

    if not args.no_combined and len(episodes) > 1:
        combined = OUT / "dsh-phone-pair-完整版.mp4"
        seconds = concat(episodes, all_pieces, combined)
        log(f"  combined {combined.name}  {seconds / 60:.2f} min  "
            f"{combined.stat().st_size / 1024 / 1024:.1f} MB")

    manifest["_voice"] = {"voice": args.voice, "rate": args.rate}
    (WORK / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    log(f"manifest: {WORK / 'manifest.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
