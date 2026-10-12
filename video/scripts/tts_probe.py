"""Probe: which Chinese TTS voices are usable, and how good is the output.

Try edge-tts (Microsoft Edge online neural voices) first; it is far more natural
than the offline SAPI5 voice (Microsoft Huihui Desktop).
"""
import asyncio
import pathlib
import sys

VIDEO = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(VIDEO / ".deps"))

WORK = VIDEO / "work"
WORK.mkdir(parents=True, exist_ok=True)

TEXT = (
    "这是一段中文配音测试。装好手机上的 App 之后，只要扫一次码，"
    "就算人在外面，也能连回这台电脑。"
)


async def main() -> None:
    import edge_tts

    voices = await edge_tts.list_voices()
    zh = sorted(v["ShortName"] for v in voices if v["Locale"].startswith("zh-CN"))
    print("zh-CN voices:", ", ".join(zh))

    for voice in ("zh-CN-XiaoxiaoNeural", "zh-CN-YunxiNeural"):
        out = WORK / f"sample_{voice.split('-')[-1]}.mp3"
        communicate = edge_tts.Communicate(TEXT, voice)
        await communicate.save(str(out))
        print(f"{voice}: {out} ({out.stat().st_size} bytes)")


if __name__ == "__main__":
    asyncio.run(main())
