"""Render the cover image for the release page / video platform (16:9).

    python scripts/make_cover.py

Writes out/封面-1920x1080.png and out/封面-1146x717.png (the size the
Bilibili submission form asks for).

审核规则：**封面上不放二维码、网址、联系方式，也不做站外引导**（B 站封面最
常见的打回原因就是这几样）。所以这一版把原来左下角的「扫码下载 APK + GitHub
地址」整块拿掉，换成纯画面内容：三步流程图 + 一句时长说明。下载入口只放在
简介和置顶评论里（见 out/bilibili-投稿信息.md）。
"""

from __future__ import annotations

import pathlib
import sys

VIDEO = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(VIDEO / ".deps"))
sys.path.insert(0, str(VIDEO / "scripts"))

from PIL import Image  # noqa: E402

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


def steps_row(img: Image.Image, xy: tuple[int, int], items: list[str],
              size: int = 42, gap: int = 48) -> int:
    """Chips joined by arrows — the bottom-left "三步" graphic (no text links)."""
    draw = T.draw_rgba(img)
    fnt = T.font(size, True)
    x, y = xy
    h = size + 46
    for i, text in enumerate(items):
        w = int(fnt.getlength(text)) + 52
        draw.rounded_rectangle((x, y, x + w, y + h), radius=h // 2,
                               fill=T.ACCENT_DARK, outline=T.ACCENT, width=3)
        draw.text((x + w / 2, y + h / 2), text, font=fnt, fill=T.INK, anchor="mm")
        x += w
        if i < len(items) - 1:
            T.arrow(img, (x + 10, y + h // 2), (x + gap - 10, y + h // 2), width=6)
            x += gap
    return y + h


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

    draw.text((112, 752), "三步搞定", font=T.font(34, True), fill=T.AMBER)
    steps_row(img, (112, 818), ["装插件", "装 App", "配对成功"])
    draw.text((112, 952), "全程中文讲解 · 6 集 · 约 8 分钟",
              font=T.font(32), fill=T.INK_DIM)

    T.phone_mock(img, (1236, 150, 1694, 1006), screen)
    T.sketch_badge(img, (1236, 1016))

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
