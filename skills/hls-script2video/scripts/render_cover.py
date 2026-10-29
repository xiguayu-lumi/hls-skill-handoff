#!/usr/bin/env python3
"""Render the HLS overseas-observer style 1080x1440 video cover from a JSON brief."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1440
PAPER = "#F6F2E8"
INK = "#11110F"
GRAY = "#85827A"
OLIVE = "#7E8768"
CN_SERIF = "C:/Windows/Fonts/NotoSerifSC-VF.ttf"
CN_SANS = "C:/Windows/Fonts/NotoSansSC-VF.ttf"
EN_SERIF = "C:/Windows/Fonts/times.ttf"
MARGIN = 72
CONTENT_W = W - 2 * MARGIN
LATIN_TOKEN = re.compile(r"[A-Za-z0-9]+|[^\sA-Za-z0-9]")


def font(path: str, size: int, variation: str | None = None) -> ImageFont.FreeTypeFont:
    out = ImageFont.truetype(path, size=size)
    if variation:
        try:
            out.set_variation_by_name(variation)
        except (AttributeError, OSError, ValueError):
            pass
    return out


def wrap_mixed(draw: ImageDraw.ImageDraw, value: str, f: ImageFont.FreeTypeFont, width: int) -> list[str]:
    lines: list[str] = []
    current = ""
    for token in LATIN_TOKEN.findall(value):
        trial = current + token
        if not current or draw.textlength(trial, font=f) <= width:
            current = trial
        else:
            lines.append(current)
            current = token
    if current:
        lines.append(current)
    return lines


def draw_wrapped(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    value: str,
    f: ImageFont.FreeTypeFont,
    width: int,
    fill: str = INK,
    gap: int = 10,
) -> int:
    x, y = xy
    for line in wrap_mixed(draw, value, f, width):
        draw.text((x, y), line, font=f, fill=fill, anchor="la")
        box = draw.textbbox((x, y), line, font=f)
        y += box[3] - box[1] + gap
    return y


def render(data: dict, output: Path) -> None:
    kicker = str(data.get("kicker", "")).strip()
    title = str(data.get("title", "")).strip()
    subtitle = str(data.get("subtitle", "")).strip()
    account = str(data.get("account", "Dissertation写作技巧 · 拆解实操")).strip()
    if not title:
        raise ValueError("cover_content.json 缺少 title 字段")

    im = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(im)

    d.text((MARGIN, 46), "HLS STUDY ABROAD", font=font(EN_SERIF, 27), fill=INK, anchor="la")
    d.text((W - MARGIN, 52), "ACADEMIC WRITING", font=font(EN_SERIF, 18), fill=GRAY, anchor="ra")
    d.line((MARGIN, 96, W - MARGIN, 96), fill=OLIVE, width=2)

    if kicker:
        d.text((MARGIN, 140), kicker, font=font(EN_SERIF, 22), fill=OLIVE, anchor="la")

    title_font = font(CN_SERIF, 64, "Black")
    y = draw_wrapped(d, (MARGIN, 210), title, title_font, CONTENT_W, INK, 10)
    d.line((MARGIN, y + 20, 190, y + 20), fill=OLIVE, width=5)

    if subtitle:
        draw_wrapped(d, (MARGIN, y + 70), subtitle, font(CN_SANS, 30), CONTENT_W, INK, 10)

    d.rounded_rectangle((104, 1230, 976, 1330), radius=24, fill=INK)
    d.text((W // 2, 1280), account, font=font(CN_SERIF, 34, "Black"), fill=PAPER, anchor="mm")

    output.parent.mkdir(parents=True, exist_ok=True)
    im.save(output, "PNG", optimize=True)
    print(f"Saved {output}")


def main() -> None:
    parser = argparse.ArgumentParser(description="渲染海乐思外刊风 1080×1440 视频封面")
    parser.add_argument("--input", required=True, help="cover_content.json 路径")
    parser.add_argument("--output", required=True, help="输出 PNG 路径")
    args = parser.parse_args()
    data = json.loads(Path(args.input).read_text(encoding="utf-8"))
    render(data, Path(args.output))


if __name__ == "__main__":
    main()
