"""Generate Android launcher icons for the DSH phone app.

Source art: F:\\Deepseek\\resources\\icon.png (the DeepSeek Harness app icon, 1024x1024 RGBA
with a transparent surround - the artwork is already a rounded shape).
"""
import os
import sys

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = r"F:\Deepseek\resources\icon.png"

DENSITIES = {
    "mdpi": 48,
    "hdpi": 72,
    "xhdpi": 96,
    "xxhdpi": 144,
    "xxxhdpi": 192,
}


def main() -> int:
    art = Image.open(SRC).convert("RGBA")
    # Trim fully transparent margins so the artwork is optically centred at every size.
    bbox = art.getchannel("A").getbbox()
    if bbox:
        art = art.crop(bbox)

    for density, size in DENSITIES.items():
        out_dir = os.path.join(ROOT, "res", f"mipmap-{density}")
        os.makedirs(out_dir, exist_ok=True)
        icon = art.resize((size, size), Image.LANCZOS)
        icon.save(os.path.join(out_dir, "ic_launcher.png"), "PNG", optimize=True)
        print(f"mipmap-{density}/ic_launcher.png  {size}x{size}")

    # A large copy is handy for the store / README screenshot.
    os.makedirs(os.path.join(ROOT, "artifacts"), exist_ok=True)
    art.resize((512, 512), Image.LANCZOS).save(
        os.path.join(ROOT, "artifacts", "icon-512.png"), "PNG", optimize=True
    )
    print("artifacts/icon-512.png")
    return 0


if __name__ == "__main__":
    sys.exit(main())
