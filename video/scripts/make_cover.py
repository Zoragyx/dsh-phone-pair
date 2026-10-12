"""Render the cover image for the release page / video platform (16:9).

    python scripts/make_cover.py

Writes out/封面-1920x1080.png and out/封面-1146x717.png (the size the
Bilibili submission form asks for).
"""

from __future__ import annotations

import pathlib
import sys

VIDEO = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(VIDEO / ".deps"))
sys.path.insert(0, str(VIDEO / "scripts"))

from PIL import Image  # noqa: E402

import storyboard as S  # noqa: E402
import theme as T  # noqa: E402

OUT = VIDEO / "out"


def screen(draw, rect) -> None:
    """Lock screen of the phone mock."""
    x0, y0, x1, _y1 = rect
    w = x1 - x0
    pad = int(w * 0.02)

    draw.text((x0 + pad, y0 + int(w * 0.12)), "DSH 手机版",
              font=T.font(int(w * 0.17), True), fill=T.INK)
    draw.text((x0 + pad, y0 + int(w * 0.34)), "输入进入密码",
              font=T.font(int(w * 0.105), True), fill=T.AMBER)

    dots_y = y0 + int(w * 0.56)
    step = int(w * 0.145)
    for i in range(6):
        cx = x0 + pad + int(w * 0.07) + i * step
        r = int(w * 0.032)
        filled = i < 4
        draw.ellipse((cx - r, dots_y - r, cx + r, dots_y + r),
                     fill=T.ACCENT if filled else None,
                     outline=T.ACCENT, width=max(2, int(w * 0.008)))

    top = y0 + int(w * 0.72)
    draw.rounded_rectangle((x0 + pad, top, x1 - pad, top + int(w * 0.20)),
                           radius=int(w * 0.05), fill=T.ACCENT)
    label = "解锁"
    font = T.font(int(w * 0.11), True)
    draw.text(((x0 + x1) / 2, top + int(w * 0.10)), label, font=font,
              fill=(10, 18, 28), anchor="mm")

    draw.text((x0 + pad, top + int(w * 0.28)), "密码只保存在这台手机上",
              font=T.font(int(w * 0.058)), fill=T.INK_DIM)


def main() -> int:
    img = T.gradient_canvas()
    draw = T.draw_rgba(img)

    T.pill(img, (110, 108), "DSH 手机版 · 配对版 1.0", fg=(10, 18, 28),
           bg=T.ACCENT, size=34, pad=20)

    draw.text((110, 190), "手机上看它干活", font=T.font(124, True), fill=T.INK)
    draw.text((110, 350), "在外面也能连回来", font=T.font(80, True), fill=T.ACCENT)

    rows = [
        ("电脑端装插件，手机端装 App", True),
        ("配对一次，之后不用再配", True),
        ("打开就上锁，界面已内置", True),
    ]
    y = 490
    for text, ok in rows:
        T.check_row(img, (112, y), text, ok=ok, size=48)
        y += 84

    qr_box = (112, 780, 342, 1010)
    T.card(img, qr_box, radius=22, fill=(255, 255, 255))
    qr = T.real_qr(S.DOWNLOAD_PAGE, 196)
    if qr is not None:
        img.paste(qr, (int((qr_box[0] + qr_box[2]) / 2 - 98),
                       int((qr_box[1] + qr_box[3]) / 2 - 98)))
    draw.text((376, 812), "扫码下载 APK", font=T.font(52, True), fill=T.INK)
    draw.text((378, 886), "github.com/Zoragyx/dsh-phone-pair", font=T.font(32),
              fill=T.INK_DIM)
    draw.text((378, 936), "releases/latest", font=T.font(32), fill=T.INK_DIM)

    T.phone_mock(img, (1236, 150, 1694, 1006), screen)
    T.sketch_badge(img, (1236, 1040))

    OUT.mkdir(parents=True, exist_ok=True)
    wide = OUT / "封面-1920x1080.png"
    img.save(wide)
    small = OUT / "封面-1146x717.png"
    img.resize((1146, 717), Image.LANCZOS).save(small)
    for path in (wide, small):
        print(f"  cover  {path.name}  {path.stat().st_size / 1024:.0f} KB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
