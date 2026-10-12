"""Drawing toolkit for the DSH Phone tutorial videos (16:9, 1080p).

Everything is drawn with Pillow so that Chinese text is rendered exactly
(no AI image generation, which garbles CJK glyphs).
"""
from __future__ import annotations

from pathlib import Path
from typing import Callable, Sequence

from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1920, 1080
FPS = 25

FONT_DIR = Path("C:/Windows/Fonts")
FONT_REGULAR = FONT_DIR / "msyh.ttc"
FONT_BOLD = FONT_DIR / "msyhbd.ttc"
FONT_MONO = FONT_DIR / "consola.ttf"

BG_TOP = (8, 15, 27)
BG_BOTTOM = (17, 34, 57)
CARD = (24, 38, 58)
CARD_EDGE = (58, 88, 124)
INK = (233, 240, 248)
INK_DIM = (152, 174, 198)
ACCENT = (77, 208, 225)
ACCENT_DARK = (18, 66, 82)
AMBER = (255, 176, 64)
OK = (94, 214, 138)
WARN = (255, 138, 128)
WHITE = (255, 255, 255)

_fonts: dict[tuple[str, int], ImageFont.FreeTypeFont] = {}


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    key = ("b" if bold else "r", size)
    if key not in _fonts:
        _fonts[key] = ImageFont.truetype(str(FONT_BOLD if bold else FONT_REGULAR), size)
    return _fonts[key]


def fitted_font(text: str, max_width: int, size: int, bold: bool = False,
                min_size: int = 13) -> ImageFont.FreeTypeFont:
    """Shrink the font until the text fits, so single-line labels never overflow."""
    while size > min_size and font(size, bold).getlength(text) > max_width:
        size -= 1
    return font(size, bold)


def mono(size: int) -> ImageFont.FreeTypeFont:
    """Monospaced digits — used for clock values such as 03:07."""
    key = ("m", size)
    if key not in _fonts:
        _fonts[key] = ImageFont.truetype(str(FONT_MONO), size)
    return _fonts[key]


# --------------------------------------------------------------------------- canvas


def gradient_canvas(top: tuple[int, int, int] = BG_TOP,
                    bottom: tuple[int, int, int] = BG_BOTTOM) -> Image.Image:
    """Vertical gradient background with a soft accent glow in the corner."""
    base = Image.new("RGB", (W, H), top)
    draw = ImageDraw.Draw(base)
    for y in range(H):
        t = y / (H - 1)
        draw.line([(0, y), (W, y)], fill=tuple(
            int(top[i] + (bottom[i] - top[i]) * t) for i in range(3)))
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse((-300, -420, 900, 520), fill=(30, 120, 150, 70))
    gd.ellipse((1150, 520, 2200, 1400), fill=(30, 90, 160, 55))
    glow = glow.filter(ImageFilter.GaussianBlur(120))
    return Image.alpha_composite(base.convert("RGBA"), glow).convert("RGB")


def draw_rgba(img: Image.Image) -> ImageDraw.ImageDraw:
    return ImageDraw.Draw(img, "RGBA")


# --------------------------------------------------------------------------- text


def wrap(text: str, fnt: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    """Wrap text; CJK has no spaces, so wrap per character. Respects \\n."""
    lines: list[str] = []
    for paragraph in text.split("\n"):
        if not paragraph:
            lines.append("")
            continue
        current = ""
        for ch in paragraph:
            probe = current + ch
            if fnt.getlength(probe) <= max_width or not current:
                current = probe
            else:
                lines.append(current)
                current = ch
        lines.append(current)
    return lines


def text_block(img: Image.Image, xy: tuple[int, int], text: str,
               fnt: ImageFont.FreeTypeFont, fill=INK, max_width: int = 1200,
               line_gap: int = 14, anchor: str = "la") -> int:
    """Draw wrapped text; returns the y coordinate below the block."""
    draw = draw_rgba(img)
    x, y = xy
    lines = wrap(text, fnt, max_width)
    step = fnt.size + line_gap
    for i, line in enumerate(lines):
        draw.text((x, y + i * step), line, font=fnt, fill=fill, anchor=anchor)
    return y + len(lines) * step


def center_text(img: Image.Image, cy: int, text: str, fnt: ImageFont.FreeTypeFont,
                fill=INK) -> None:
    draw_rgba(img).text((W // 2, cy), text, font=fnt, fill=fill, anchor="mm")


# --------------------------------------------------------------------------- shapes


def card(img: Image.Image, box: tuple[int, int, int, int], radius: int = 28,
         fill=CARD, outline=CARD_EDGE, width: int = 2) -> None:
    draw_rgba(img).rounded_rectangle(box, radius=radius, fill=fill,
                                     outline=outline, width=width)


def pill(img: Image.Image, xy: tuple[int, int], text: str, fg: tuple = INK,
         bg: tuple = ACCENT_DARK, size: int = 30, pad: int = 18) -> tuple[int, int]:
    """Small rounded label; xy is the top-left corner. Returns the box."""
    fnt = font(size, bold=True)
    draw = draw_rgba(img)
    tw = int(fnt.getlength(text))
    box = (xy[0], xy[1], xy[0] + tw + pad * 2, xy[1] + size + pad)
    draw.rounded_rectangle(box, radius=(size + pad) // 2, fill=bg)
    draw.text((xy[0] + pad, xy[1] + pad // 2 + size // 2), text, font=fnt, fill=fg,
              anchor="lm")
    return box


def sketch_badge(img: Image.Image, xy: tuple[int, int],
                 text: str = "示意图 · 非真机截图") -> None:
    pill(img, xy, text, fg=(20, 26, 34), bg=(255, 196, 92), size=26, pad=14)


def arrow(img: Image.Image, start: tuple[int, int], end: tuple[int, int],
          color: tuple = ACCENT, width: int = 8) -> None:
    draw = draw_rgba(img)
    draw.line([start, end], fill=color, width=width)
    import math
    ang = math.atan2(end[1] - start[1], end[0] - start[0])
    size = 26
    pts = [
        end,
        (end[0] - size * math.cos(ang - 0.45), end[1] - size * math.sin(ang - 0.45)),
        (end[0] - size * math.cos(ang + 0.45), end[1] - size * math.sin(ang + 0.45)),
    ]
    draw.polygon(pts, fill=color)


def check_row(img: Image.Image, xy: tuple[int, int], text: str, ok: bool = True,
              size: int = 40, max_width: int = 980, color: tuple | None = None) -> int:
    draw = draw_rgba(img)
    x, y = xy
    r = size // 2
    mark_color = OK if ok else WARN
    if color is not None:
        mark_color = color
    draw.ellipse((x, y, x + size, y + size), outline=mark_color, width=4)
    if ok:
        draw.line([(x + size * 0.26, y + size * 0.52),
                   (x + size * 0.45, y + size * 0.72),
                   (x + size * 0.76, y + size * 0.30)],
                  fill=mark_color, width=6, joint="curve")
    else:
        draw.line([(x + size * 0.3, y + size * 0.3), (x + size * 0.7, y + size * 0.7)],
                  fill=mark_color, width=6)
        draw.line([(x + size * 0.7, y + size * 0.3), (x + size * 0.3, y + size * 0.7)],
                  fill=mark_color, width=6)
    bottom = text_block(img, (x + size + 22, y - 4), text, font(size + 2), fill=INK,
                        max_width=max_width)
    return max(bottom, y + size + 12)


def number_step(img: Image.Image, xy: tuple[int, int], index: int, text: str,
                size: int = 44, max_width: int = 1000) -> int:
    draw = draw_rgba(img)
    x, y = xy
    draw.ellipse((x, y, x + size + 8, y + size + 8), fill=ACCENT_DARK,
                 outline=ACCENT, width=3)
    draw.text((x + (size + 8) / 2, y + (size + 8) / 2), str(index), font=font(size - 4, True),
              fill=ACCENT, anchor="mm")
    bottom = text_block(img, (x + size + 34, y + 2), text, font(size - 2), fill=INK,
                        max_width=max_width)
    return max(bottom, y + size + 30)


# --------------------------------------------------------------------------- frames


def subtitle(img: Image.Image, lines: Sequence[str], size: int = 46) -> None:
    """Burn the subtitle band into the bottom of the frame."""
    if not lines:
        return
    draw = draw_rgba(img)
    fnt = font(size, bold=True)
    wrapped: list[str] = []
    for line in lines:
        wrapped.extend(wrap(line, fnt, W - 260))
    line_h = size + 18
    band_h = line_h * len(wrapped) + 34
    y0 = H - band_h - 56
    draw.rounded_rectangle((90, y0, W - 90, y0 + band_h), radius=26,
                           fill=(0, 0, 0, 165))
    for i, line in enumerate(wrapped):
        draw.text((W // 2, y0 + 17 + line_h * i + line_h / 2), line, font=fnt,
                  fill=WHITE, anchor="mm")


def header(img: Image.Image, episode: str, title: str) -> int:
    """Draw the episode tag + scene title. Returns the y below the header."""
    pill(img, (96, 78), episode, fg=(10, 20, 26), bg=ACCENT, size=28, pad=14)
    bottom = text_block(img, (96, 146), title, font(64, True), fill=INK,
                        max_width=W - 260)
    draw_rgba(img).line([(96, bottom + 18), (W - 96, bottom + 18)],
                        fill=(60, 92, 128), width=3)
    return bottom + 46


def header_compact(img: Image.Image, episode: str, title: str) -> int:
    """Slim header for scenes whose body needs the full frame height."""
    pill(img, (96, 46), episode, fg=(10, 20, 26), bg=ACCENT, size=26, pad=13)
    draw_rgba(img).text((96, 124), title, font=font(50, True), fill=INK)
    return 196


def footer(img: Image.Image, text: str) -> None:
    """Small download hint in the top-right corner (the bottom is subtitle space)."""
    fnt = fitted_font(text, 860, 26)
    draw_rgba(img).text((W - 140, 88), text, font=fnt, fill=INK_DIM, anchor="ra")


def phone_mock(img: Image.Image, box: tuple[int, int, int, int],
               screen_fn: Callable[[ImageDraw.ImageDraw, tuple[int, int, int, int]], None],
               status_left: str = "9:41") -> tuple[int, int, int, int]:
    """Draw a phone outline and hand the inner screen rect to screen_fn.

    Every element is sized from the phone width (u = 1% of the screen width), so
    the mock stays legible no matter how small the frame is.
    """
    draw = draw_rgba(img)
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    shell = max(6, int(min(w, h) * 0.012))
    draw.rounded_rectangle((x0 - shell, y0 - shell, x1 + shell, y1 + shell),
                           radius=int(min(w, h) * 0.09), fill=(16, 20, 28),
                           outline=(96, 112, 134), width=max(3, shell // 2))
    draw.rounded_rectangle(box, radius=int(min(w, h) * 0.082), fill=(10, 15, 24))
    inset = max(10, int(w * 0.035))
    screen = (x0 + inset, y0 + inset, x1 - inset, y1 - inset)
    draw.rounded_rectangle(screen, radius=int(min(w, h) * 0.06), fill=(14, 20, 32))
    u = (screen[2] - screen[0]) / 100.0
    sb_h = int(u * 14)
    bar = (screen[0], screen[1], screen[2], screen[1] + sb_h)
    mid = bar[1] + sb_h // 2
    draw.text((bar[0] + 5 * u, mid), status_left,
              font=fitted_font(status_left, int(30 * u), max(15, int(7 * u)), True),
              fill=INK, anchor="lm")
    bat_w, bat_h = 13 * u, 6.4 * u
    bat = (bar[2] - 5 * u - bat_w, mid - bat_h / 2, bar[2] - 5 * u, mid + bat_h / 2)
    draw.rounded_rectangle(bat, radius=max(2, int(bat_h * 0.3)), outline=INK,
                           width=max(2, int(bat_h * 0.16)))
    draw.rounded_rectangle((bat[2] + 1.5 * u, mid - bat_h * 0.18,
                            bat[2] + 3.6 * u, mid + bat_h * 0.18),
                           radius=max(1, int(bat_h * 0.08)), fill=INK)
    for i in range(4):
        bh = (3 + i * 1.2) * u
        bx = bat[0] - 5 * u - (4 - i) * 2.7 * u
        draw.rounded_rectangle((bx, mid + 3 * u - bh, bx + 1.6 * u, mid + 3 * u),
                               radius=max(1, int(u * 0.3)),
                               fill=INK if i < 3 else INK_DIM)
    content = (screen[0] + 6.5 * u, screen[1] + sb_h + 5 * u,
               screen[2] - 6.5 * u, screen[3] - 6 * u)
    screen_fn(draw, content)
    draw.rounded_rectangle((screen[0] + (screen[2] - screen[0]) / 2 - 14 * u,
                            screen[3] - 3.4 * u,
                            screen[0] + (screen[2] - screen[0]) / 2 + 14 * u,
                            screen[3] - 1.6 * u), radius=int(u), fill=(70, 82, 100))
    return content


def window_mock(img: Image.Image, box: tuple[int, int, int, int], title: str,
                content_fn: Callable[[ImageDraw.ImageDraw, tuple[int, int, int, int]], None]) -> tuple[int, int, int, int]:
    """Draw a desktop window (DSH 设置面板示意) and hand over the content rect."""
    draw = draw_rgba(img)
    x0, y0, x1, y1 = box
    draw.rounded_rectangle((x0, y0, x1, y1), radius=26, fill=CARD,
                           outline=CARD_EDGE, width=3)
    bar_h = 76
    draw.rounded_rectangle((x0, y0, x1, y0 + bar_h), radius=26, fill=(20, 32, 50))
    draw.rectangle((x0, y0 + bar_h - 26, x1, y0 + bar_h), fill=(20, 32, 50))
    for i, color in enumerate(((255, 95, 86), (255, 189, 46), (39, 201, 63))):
        cx = x0 + 34 + i * 34
        draw.ellipse((cx - 10, y0 + bar_h // 2 - 10, cx + 10, y0 + bar_h // 2 + 10),
                     fill=color)
    draw.text((x0 + 150, y0 + bar_h // 2), title, font=font(32, True), fill=INK,
              anchor="lm")
    content = (x0 + 40, y0 + bar_h + 34, x1 - 40, y1 - 34)
    content_fn(draw, content)
    return content


def qr_placeholder(img: Image.Image, box: tuple[int, int, int, int], seed: int = 7) -> None:
    """Deterministic fake QR pattern — clearly not a scannable code."""
    draw = draw_rgba(img)
    x0, y0, x1, y1 = box
    draw.rounded_rectangle(box, radius=18, fill=WHITE)
    n = 25
    cell = (x1 - x0 - 40) / n
    state = seed
    for row in range(n):
        for col in range(n):
            state = (state * 1103515245 + 12345) & 0x7FFFFFFF
            solid = (state >> 16) % 2 == 0
            if row < 7 and col < 7 or row < 7 and col >= n - 7 or row >= n - 7 and col < 7:
                solid = not ((2 <= row % 7 <= 4) and (2 <= col % 7 <= 4))
            if solid:
                cx = x0 + 20 + col * cell
                cy = y0 + 20 + row * cell
                draw.rectangle((cx, cy, cx + cell * 0.86, cy + cell * 0.86),
                               fill=(16, 20, 26))


def real_qr(data: str, size: int) -> Image.Image | None:
    """Real QR (needs the qrcode package); returns None when unavailable."""
    try:
        import qrcode  # type: ignore
    except Exception:
        return None
    qr = qrcode.QRCode(border=1, box_size=10,
                       error_correction=qrcode.constants.ERROR_CORRECT_M)
    qr.add_data(data)
    qr.make(fit=True)
    return qr.make_image(fill_color=(10, 14, 20), back_color=(255, 255, 255)) \
        .convert("RGB").resize((size, size), Image.NEAREST)
