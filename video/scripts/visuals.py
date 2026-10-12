"""Scene visuals.

Each visual kind draws into a body rect (the area between the header and the
subtitle band). Phone and window mockups carry a 「示意图」 badge because no
real device screenshot exists yet.

Phone-style scenes use a "tall" layout: the header shrinks to a tag + one short
line so the mockup can use the full frame height, and the explanation moves
into the column beside the phone.
"""
from __future__ import annotations

from typing import Any, Callable, Sequence

from PIL import Image, ImageDraw

import theme as T

Rect = tuple[int, int, int, int]

PHONE_REFERENCE_WIDTH = 330  # design width the phone-screen sizes are written for


def _size(item: dict, key: str, default: int, scale: float) -> int:
    return max(int(item.get(key, default) * scale), 11)


# --------------------------------------------------------------------------- widgets


def widgets(img: Image.Image, rect: Rect, items: Sequence[dict],
            scale: float = 1.0) -> int:
    """Draw a vertical stack of widgets inside rect; returns the bottom y."""
    draw = T.draw_rgba(img)
    x0, y0, x1, y1 = rect
    width = x1 - x0
    y = y0
    for item in items:
        kind = item.get("t", "text")
        if kind == "spacer":
            y += int(item.get("h", 24) * scale)
        elif kind == "heading":
            fnt = T.font(_size(item, "size", 44, scale), True)
            for line in T.wrap(item["text"], fnt, width):
                draw.text((x0, y), line, font=fnt, fill=item.get("fill", T.INK))
                y += fnt.size + int(14 * scale)
            y += int(10 * scale)
        elif kind == "text":
            fnt = T.font(_size(item, "size", 32, scale), item.get("bold", False))
            y = T.text_block(img, (x0, y), item["text"], fnt,
                             fill=item.get("fill", T.INK_DIM), max_width=width,
                             line_gap=int(12 * scale)) + int(item.get("gap", 14) * scale)
        elif kind == "field":
            fnt = T.fitted_font(item["text"], width - int(44 * scale),
                                _size(item, "size", 30, scale))
            h = fnt.size + int(34 * scale)
            draw.rounded_rectangle((x0, y, x1, y + h), radius=int(14 * scale),
                                   fill=(18, 26, 40), outline=(74, 98, 128), width=2)
            draw.text((x0 + int(22 * scale), y + h // 2), item["text"], font=fnt,
                      fill=item.get("fill", (120, 140, 164)), anchor="lm")
            y += h + int(item.get("gap", 18) * scale)
        elif kind == "dots":
            n = item.get("count", 6)
            r = max(int(item.get("r", 18) * scale), 4)
            gap = max(int(item.get("gap", 26) * scale), 6)
            total = n * r * 2 + (n - 1) * gap
            cx = x0 + width // 2 - total // 2 + r
            for _ in range(n):
                draw.ellipse((cx - r, y + r, cx + r, y + r * 2),
                             fill=item.get("fill", T.INK))
                cx += r * 2 + gap
            y += r * 2 + int(item.get("pad", 26) * scale)
        elif kind == "button":
            fnt = T.fitted_font(item["text"], width - int(36 * scale),
                                _size(item, "size", 34, scale), True)
            h = fnt.size + int(42 * scale)
            accent = item.get("accent", True)
            draw.rounded_rectangle((x0, y, x1, y + h), radius=h // 2,
                                   fill=T.ACCENT if accent else (30, 44, 64),
                                   outline=None if accent else T.CARD_EDGE, width=2)
            draw.text((x0 + width // 2, y + h // 2), item["text"], font=fnt,
                      fill=(8, 18, 24) if accent else T.INK, anchor="mm")
            y += h + int(item.get("gap", 18) * scale)
        elif kind == "address":
            fnt = T.fitted_font(item["text"], width - int(40 * scale),
                                _size(item, "size", 30, scale), True)
            h = fnt.size + int(36 * scale)
            draw.rounded_rectangle((x0, y, x1, y + h), radius=int(14 * scale),
                                   fill=(16, 40, 52), outline=T.ACCENT, width=2)
            draw.text((x0 + int(20 * scale), y + h // 2), item["text"], font=fnt,
                      fill=T.ACCENT, anchor="lm")
            y += h + int(item.get("gap", 18) * scale)
        elif kind == "rows":
            for row in item["items"]:
                y = T.check_row(img, (x0, y), row["text"], ok=row.get("ok", True),
                                size=_size(item, "size", 40, scale),
                                max_width=width - int(90 * scale))
            y += int(item.get("gap", 10) * scale)
        elif kind == "callout":
            color = item.get("color", T.ACCENT)
            fnt = T.font(_size(item, "size", 30, scale), True)
            lines = T.wrap(item["text"], fnt, width - int(64 * scale))
            line_gap = int(12 * scale)
            h = len(lines) * (fnt.size + line_gap) + int(44 * scale)
            draw.rounded_rectangle((x0, y, x1, y + h), radius=int(18 * scale),
                                   fill=(24, 40, 60), outline=color, width=3)
            draw.rounded_rectangle((x0 + int(4 * scale), y + int(8 * scale),
                                    x0 + int(13 * scale), y + h - int(8 * scale)),
                                   radius=int(5 * scale), fill=color)
            yy = y + int(22 * scale)
            for line in lines:
                draw.text((x0 + int(36 * scale), yy), line, font=fnt, fill=T.INK)
                yy += fnt.size + line_gap
            y += h + int(item.get("gap", 16) * scale)
        elif kind == "qr":
            size = int(item.get("size", 300) * scale)
            img_qr = T.real_qr(item["data"], size) if item.get("data") else None
            pad = int(18 * scale)
            if img_qr is not None:
                px = x0 + width // 2 - size // 2
                img.paste(img_qr, (px, y))
                draw.rectangle((px - 2, y - 2, px + size + 2, y + size + 2),
                               outline=(255, 255, 255), width=2)
            else:
                box = (x0 + width // 2 - size // 2, y,
                       x0 + width // 2 + size // 2, y + size)
                T.qr_placeholder(img, box)
            y += size + pad + int(item.get("gap", 10) * scale)
        elif kind == "chatmock":
            h = int(item.get("h", 260) * scale)
            draw.rounded_rectangle((x0, y, x1, y + h), radius=int(18 * scale),
                                   fill=(16, 22, 34), outline=(60, 84, 112), width=2)
            bubble_w = int(width * 0.74)
            bx = x0 + int(24 * scale)
            by = y + int(26 * scale)
            lines = item.get("lines", ["你在做什么？", "正在跑测试，3 分钟给你结果。"])
            for line in lines:
                fnt = T.font(max(int(26 * scale), 12))
                bh = fnt.size + int(26 * scale)
                mine = line.startswith(">")
                text = line[1:] if mine else line
                bw = min(int(fnt.getlength(text)) + int(40 * scale), bubble_w)
                left = x1 - int(24 * scale) - bw if mine else bx
                draw.rounded_rectangle((left, by, left + bw, by + bh),
                                       radius=int(14 * scale),
                                       fill=(26, 68, 84) if mine else (32, 44, 62))
                draw.text((left + int(20 * scale), by + bh // 2), text, font=fnt,
                          fill=T.INK, anchor="lm")
                by += bh + int(18 * scale)
            y += h + int(item.get("gap", 14) * scale)
        else:
            raise ValueError(f"unknown widget: {kind}")
    return y


# --------------------------------------------------------------------------- kinds


def _fit(box: Rect, h: int, ratio: float, align: str = "center") -> Rect:
    x0, y0, x1, y1 = box
    h = min(h, y1 - y0)
    w = int(h * ratio)
    if align == "center":
        cx = (x0 + x1) // 2
    elif align == "left":
        cx = x0 + w // 2
    else:
        cx = x1 - w // 2
    cy = (y0 + y1) // 2
    return (cx - w // 2, cy - h // 2, cx + w // 2, cy + h // 2)


def _dashes(draw: ImageDraw.ImageDraw, start: tuple[int, int], end: tuple[int, int],
            color: tuple = T.AMBER, width: int = 6, dash: int = 20, gap: int = 14) -> None:
    import math
    length = math.hypot(end[0] - start[0], end[1] - start[1])
    if length <= 0:
        return
    ux, uy = (end[0] - start[0]) / length, (end[1] - start[1]) / length
    pos = 0.0
    while pos < length:
        stop = min(pos + dash, length)
        draw.line([(start[0] + ux * pos, start[1] + uy * pos),
                   (start[0] + ux * stop, start[1] + uy * stop)], fill=color, width=width)
        pos = stop + gap


def _art_pair(img: Image.Image, box: Rect) -> None:
    """Laptop + phone + dashed link, used on the opening title card."""
    draw = T.draw_rgba(img)
    x0, y0, x1, y1 = box
    lw, lh = 400, 250
    lx, ly = x0, y0 + 40
    draw.rounded_rectangle((lx, ly, lx + lw, ly + lh), radius=16, fill=(20, 30, 46),
                           outline=(120, 142, 168), width=5)
    draw.rounded_rectangle((lx - 34, ly + lh, lx + lw + 34, ly + lh + 18), radius=9,
                           fill=(46, 62, 86))
    draw.text((lx + 24, ly + 22), "电脑 · DSH", font=T.font(30, True), fill=T.INK)
    draw.text((lx + 24, ly + 74), "Agent 在这里工作", font=T.font(26), fill=T.INK_DIM)
    draw.rounded_rectangle((lx + 24, ly + 122, lx + lw - 24, ly + 234), radius=12,
                           fill=(14, 22, 36), outline=(58, 84, 116), width=2)
    for i, text in enumerate(("· 会话", "· 产出物", "· 工具")):
        draw.text((lx + 48, ly + 140 + i * 30), text, font=T.font(22), fill=T.INK_DIM)

    pw, ph = 210, 410
    px, py = x0 + lw + 150, y0
    draw.rounded_rectangle((px, py, px + pw, py + ph), radius=34, fill=(16, 22, 34),
                           outline=(120, 142, 168), width=5)
    draw.text((px + 22, py + 24), "手机", font=T.font(28, True), fill=T.INK)
    draw.rounded_rectangle((px + 22, py + 78, px + pw - 22, py + 150), radius=12,
                           fill=(26, 68, 84))
    draw.text((px + 38, py + 100), "密码锁", font=T.font(24, True), fill=T.INK)
    draw.rounded_rectangle((px + 22, py + 170, px + pw - 22, py + 242), radius=12,
                           fill=(32, 44, 62))
    draw.text((px + 38, py + 192), "DSH 界面", font=T.font(24), fill=T.INK)
    draw.rounded_rectangle((px + 22, py + 262, px + pw - 22, py + 334), radius=12,
                           fill=(32, 44, 62))
    draw.text((px + 38, py + 284), "随时查看", font=T.font(24), fill=T.INK)

    _dashes(draw, (lx + lw + 30, ly + lh // 2), (px - 26, py + 200))
    label = "配对一次"
    fnt = T.font(30, True)
    cx, cy = (lx + lw + 30 + px - 26) // 2, (ly + lh // 2 + py + 200) // 2 - 46
    draw.rounded_rectangle((cx - int(fnt.getlength(label)) // 2 - 16, cy - 22,
                            cx + int(fnt.getlength(label)) // 2 + 16, cy + 22),
                           radius=22, fill=T.AMBER)
    draw.text((cx, cy), label, font=fnt, fill=(26, 18, 4), anchor="mm")
    T.sketch_badge(img, (x0, y1 - 30), "示意图 · 界面以真机为准")


def vis_title(img: Image.Image, box: Rect, p: dict) -> None:
    draw = T.draw_rgba(img)
    x0, y0, x1, y1 = box
    y = y0 + 40
    for line in p.get("lines", []):
        fnt = T.font(line.get("size", 96), True)
        draw.text((x0 + 20, y), line["text"], font=fnt, fill=line.get("fill", T.INK))
        y += fnt.size + 26
    y += 24
    for line in p.get("sub", []):
        fnt = T.font(line.get("size", 40))
        draw.text((x0 + 22, y), line["text"], font=fnt, fill=line.get("fill", T.INK_DIM))
        y += fnt.size + 18
    if p.get("art") == "pair":
        _art_pair(img, (x0 + 1010, y0 + 30, x1, y0 + 560))


def vis_notice(img: Image.Image, box: Rect, p: dict) -> None:
    """Standalone notice card: headline, a few points, and a takeaway callout."""
    draw = T.draw_rgba(img)
    x0, y0, x1, y1 = box
    y = y0 + 10
    for line in p.get("lines", []):
        fnt = T.font(line.get("size", 84), True)
        draw.text((x0 + 20, y), line["text"], font=fnt, fill=line.get("fill", T.INK))
        y += fnt.size + 20
    y += 24
    for item in p.get("items", []):
        draw.ellipse((x0 + 26, y + 22, x0 + 40, y + 36), fill=item.get("dot", T.ACCENT))
        y = T.text_block(img, (x0 + 68, y), item["text"], T.font(item.get("size", 42)),
                         fill=item.get("fill", T.INK),
                         max_width=x1 - x0 - 150) + 26
    if p.get("note"):
        widgets(img, (x0 + 20, y + 4, x1 - 20, y1),
                [{"t": "callout", "color": p.get("note_color", T.AMBER),
                  "text": p["note"]}])


def vis_chapters(img: Image.Image, box: Rect, p: dict) -> None:
    """Two time nodes on the same backdrop: a clock value, a label, a note."""
    draw = T.draw_rgba(img)
    x0, y0, x1, y1 = box
    y = y0 + 10
    for line in p.get("lines", []):
        fnt = T.font(line.get("size", 84), True)
        draw.text((x0 + 20, y), line["text"], font=fnt, fill=line.get("fill", T.INK))
        y += fnt.size + 18
    y += 36
    for item in p.get("items", []):
        h = 200
        draw.rounded_rectangle((x0 + 20, y, x1 - 20, y + h), radius=22,
                               fill=(24, 38, 58), outline=(58, 88, 124), width=2)
        clock = T.mono(96)
        draw.text((x0 + 64, y + h // 2), item.get("time", "--:--"), font=clock,
                  fill=item.get("fill", T.ACCENT), anchor="lm")
        text_x = x0 + 64 + int(clock.getlength("00:00")) + 70
        draw.text((text_x, y + 44), item.get("label", ""), font=T.font(48, True),
                  fill=T.INK)
        T.text_block(img, (text_x, y + 118), item.get("note", ""), T.font(32),
                     fill=T.INK_DIM, max_width=x1 - text_x - 70)
        y += h + 30


def vis_phone(img: Image.Image, box: Rect, p: dict) -> None:
    x0, y0, x1, y1 = box
    align = p.get("align", "center")
    height = p.get("height", (y1 - y0) - 64)
    rect = _fit(box, height, 0.50, align)
    inner = (rect[2] - rect[0]) * 0.80
    scale = max(min(inner / PHONE_REFERENCE_WIDTH, 1.0), 0.5) * p.get("scale", 1.0)
    T.phone_mock(img, rect, lambda d, content: widgets(img, content, p["widgets"], scale))
    if p.get("badge", True):
        T.sketch_badge(img, (box[0], min(rect[3] + 24, y1 - 44)))
    if p.get("side"):
        side_x = rect[2] + 96
        side_w = x1 - side_x
        widgets(img, (side_x, rect[1] + 10, side_x + side_w, y1), p["side"])
    del x0, y0


def vis_panel(img: Image.Image, box: Rect, p: dict) -> None:
    height = p.get("height", 660)
    width_ratio = p.get("width", 1180)
    rect = _fit(box, height, width_ratio / height, p.get("align", "center"))
    T.window_mock(img, rect, p.get("title", "DSH"),
                  lambda d, content: widgets(img, content, p["widgets"]))
    if p.get("badge", True):
        T.sketch_badge(img, (rect[0], min(rect[3] + 26, box[3] - 46)))
    if p.get("side"):
        side_x = rect[2] + 70
        widgets(img, (side_x, rect[1], side_x + (box[2] - side_x), box[3]), p["side"])


def vis_pair(img: Image.Image, box: Rect, p: dict) -> None:
    """Desktop panel on the left, phone on the right, arrow in between."""
    x0, y0, x1, y1 = box
    gap = 190
    half = (x1 - x0 - gap) // 2
    left = (x0, y0 + 30, x0 + half, y1 - 60)
    right = (x0 + half + gap, y0 + 20, x1, y1 - 60)
    vis_panel(img, left, {"title": p.get("panel_title", "DSH · 设置 → 远程访问"),
                          "height": y1 - y0 - 90, "width": half - 40,
                          "widgets": p["panel"], "badge": False, "align": "center"})
    vis_phone(img, right, {"height": y1 - y0 - 40, "widgets": p["phone"],
                           "badge": False})
    T.arrow(img, (left[2] + 26, (y0 + y1) // 2), (right[0] - 26, (y0 + y1) // 2),
            color=T.AMBER, width=10)
    draw = T.draw_rgba(img)
    label = p.get("arrow_label", "配对链接")
    fnt = T.font(32, True)
    cx = (left[2] + right[0]) // 2
    draw.rounded_rectangle((cx - int(fnt.getlength(label)) // 2 - 18, (y0 + y1) // 2 - 74,
                            cx + int(fnt.getlength(label)) // 2 + 18, (y0 + y1) // 2 - 26),
                           radius=24, fill=T.AMBER)
    draw.text((cx, (y0 + y1) // 2 - 50), label, font=fnt, fill=(24, 16, 4), anchor="mm")
    T.sketch_badge(img, (x0, y1 - 40), p.get("badge_text", "电脑端与手机端界面均为示意图"))


def vis_bullets(img: Image.Image, box: Rect, p: dict) -> None:
    y = box[1] + 16
    for item in p["items"]:
        mark = item.get("mark")
        if mark == "ok":
            y = T.check_row(img, (box[0], y), item["text"], ok=True, size=46,
                            max_width=box[2] - box[0] - 90)
        elif mark == "no":
            y = T.check_row(img, (box[0], y), item["text"], ok=False, size=46,
                            max_width=box[2] - box[0] - 90)
        else:
            draw = T.draw_rgba(img)
            draw.ellipse((box[0] + 14, y + 20, box[0] + 28, y + 34), fill=T.ACCENT)
            y = T.text_block(img, (box[0] + 56, y), item["text"], T.font(44),
                             fill=T.INK, max_width=box[2] - box[0] - 140) + 26
        y += p.get("gap", 12)


def vis_steps(img: Image.Image, box: Rect, p: dict) -> None:
    y = box[1] + 16
    for i, item in enumerate(p["items"], 1):
        y = T.number_step(img, (box[0], y), i, item["text"], size=52,
                          max_width=box[2] - box[0] - 140)
        if item.get("note"):
            y = T.text_block(img, (box[0] + 92, y), item["note"], T.font(32),
                             fill=T.INK_DIM, max_width=box[2] - box[0] - 160) + 22


def vis_table(img: Image.Image, box: Rect, p: dict) -> None:
    draw = T.draw_rgba(img)
    x0, y0, x1, y1 = box
    col = int((x1 - x0) * 0.34)
    row_h = 104
    head_fnt = T.font(36, True)
    head = p.get("head", ["电脑的状态", "手机侧会看到什么"])
    draw.rounded_rectangle((x0, y0, x1, y0 + row_h), radius=18, fill=(28, 46, 70))
    draw.text((x0 + 30, y0 + row_h // 2), head[0], font=head_fnt, fill=T.ACCENT,
              anchor="lm")
    draw.text((x0 + col + 30, y0 + row_h // 2), head[1], font=head_fnt,
              fill=T.ACCENT, anchor="lm")
    y = y0 + row_h + 12
    for i, row in enumerate(p["rows"]):
        h = row_h if not row.get("note") else row_h + 44
        draw.rounded_rectangle((x0, y, x1, y + h), radius=16,
                               fill=(22, 34, 52) if i % 2 == 0 else (18, 28, 44),
                               outline=(46, 72, 104), width=2)
        draw.text((x0 + 30, y + (row_h // 2 if not row.get("note") else 40)),
                  row["state"], font=T.font(38, True),
                  fill=row.get("color", T.INK), anchor="lm")
        T.text_block(img, (x0 + col + 30, y + (30 if not row.get("note") else 24)),
                     row["phone"], T.font(34), fill=T.INK, max_width=x1 - x0 - col - 70,
                     line_gap=10)
        y += h + 10


def vis_outro(img: Image.Image, box: Rect, p: dict) -> None:
    draw = T.draw_rgba(img)
    x0, y0, x1, y1 = box
    qr_size = 320
    code = T.real_qr(p["url"], qr_size)
    if code is not None:
        img.paste(code, (x0 + 40, y0 + 30))
        draw.rectangle((x0 + 38, y0 + 28, x0 + 42 + qr_size, y0 + 32 + qr_size),
                       outline=(255, 255, 255), width=2)
        draw.text((x0 + 40, y0 + 30 + qr_size + 22), "用手机相机扫码打开下载页",
                  font=T.font(28), fill=T.INK_DIM)
    tx = x0 + (qr_size + 120 if code is not None else 40)
    y = y0 + 40
    for line in p.get("lines", []):
        fnt = T.font(line.get("size", 46), line.get("bold", False))
        draw.text((tx, y), line["text"], font=fnt, fill=line.get("fill", T.INK))
        y += fnt.size + 22
    y += 10
    draw.rounded_rectangle((tx, y, x1, y + 96), radius=18, fill=(16, 40, 52),
                           outline=T.ACCENT, width=2)
    draw.text((tx + 26, y + 48), p["url"], font=T.font(34, True), fill=T.ACCENT,
              anchor="lm")


VISUALS: dict[str, Callable[[Image.Image, Rect, dict], None]] = {
    "title": vis_title,
    "notice": vis_notice,
    "chapters": vis_chapters,
    "phone": vis_phone,
    "panel": vis_panel,
    "pair": vis_pair,
    "bullets": vis_bullets,
    "steps": vis_steps,
    "table": vis_table,
    "outro": vis_outro,
}

# Kinds whose body can use the full frame height (slim header instead of a big one)
TALL_KINDS = {"phone", "pair"}


def compose(episode_label: str, scene: dict) -> Image.Image:
    """Render one full frame (1080p) for a scene."""
    img = T.gradient_canvas()
    visual = scene["visual"]
    kind = visual["kind"]
    if kind in ("title", "outro", "notice", "chapters"):
        body = (110, 150, T.W - 110, T.H - 210)
        VISUALS[kind](img, body, visual)
    elif kind in TALL_KINDS:
        bottom = T.header_compact(img, episode_label, scene["title"])
        body = (96, bottom, T.W - 96, T.H - 206)
        VISUALS[kind](img, body, visual)
    else:
        bottom = T.header(img, episode_label, scene["title"])
        body = (96, bottom, T.W - 96, T.H - 206)
        VISUALS[kind](img, body, visual)
    if scene.get("badge"):
        T.pill(img, (96, scene.get("badge_at", 96)), scene["badge"],
               fg=(20, 26, 34), bg=(255, 196, 92), size=26, pad=14)
    T.subtitle(img, scene.get("subtitle", []))
    if scene.get("footer"):
        T.footer(img, scene["footer"])
    return img
