#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import os
import sys
from typing import Iterable

import yaml
from PIL import Image, ImageDraw, ImageFont, ImageOps


FONT_DIRS = [
    Path("/usr/share/fonts"), Path("/usr/local/share/fonts"), Path.home() / ".fonts",
    Path("C:/Windows/Fonts"), Path("/System/Library/Fonts"), Path("/Library/Fonts"),
    Path.home() / "Library/Fonts",
]

EXCLUDE_FONT_WORDS = {"initial", "ornament", "symbol", "dingbat", "allsc", "smallcaps", "italic"}

CANDIDATES = {
    "cn_title": ["NotoSerifSC-VF", "NotoSerifCJK-Black", "NotoSerifCJK-Bold", "SourceHanSerifSC-Heavy", "SourceHanSerifSC-Bold", "Songti", "simsun", "uming"],
    "cn_body": ["NotoSerifCJK-Regular", "SourceHanSerifSC-Regular", "Songti", "simsun", "uming"],
    "en_display": ["NotoSerifDisplay-Black", "LibreBodoni", "Bodoni", "Didot", "EBGaramond", "DejaVuSerif-Bold"],
    "en_body": ["EBGaramond", "NotoSerif-Regular", "Times", "DejaVuSerif"],
}


def find_font(kind: str, explicit: str | None = None) -> str:
    if explicit:
        p = Path(explicit).expanduser()
        if not p.exists():
            raise FileNotFoundError(f"Font not found: {p}")
        return str(p)
    candidates = [x.lower() for x in CANDIDATES[kind]]
    matches: list[Path] = []
    for root in FONT_DIRS:
        if not root.exists():
            continue
        for ext in ("*.ttf", "*.otf", "*.ttc"):
            try:
                for p in root.rglob(ext):
                    stem = p.stem.lower()
                    if any(bad in stem for bad in EXCLUDE_FONT_WORDS):
                        continue
                    if any(c in stem for c in candidates):
                        matches.append(p)
            except PermissionError:
                continue
    if not matches:
        raise FileNotFoundError(
            f"No suitable {kind} font found. Pass an explicit --font-{kind.replace('_', '-')} path."
        )
    # Respect candidate ordering and prefer exact stems before substring matches.
    # This prevents Windows `simsunb.ttf` (Ext-B) from winning over `simsun.ttc`.
    for c in candidates:
        for p in matches:
            if c == p.stem.lower():
                return str(p)
    for c in candidates:
        for p in matches:
            if c in p.stem.lower():
                return str(p)
    return str(matches[0])


def font(path: str, size: int, variation: str | None = None) -> ImageFont.FreeTypeFont:
    loaded = ImageFont.truetype(path, size=size)
    if variation:
        try:
            loaded.set_variation_by_name(variation)
        except (AttributeError, OSError, ValueError):
            # Static fonts already encode their weight in the selected file.
            pass
    return loaded


def require_common_chinese_glyphs(path: str) -> None:
    probe = font(path, 48)
    fingerprints = []
    for ch in "留学论文导师节奏":
        mask = probe.getmask(ch)
        if mask.getbbox() is None:
            raise ValueError(f"Chinese font has no visible glyph for {ch}: {path}")
        fingerprints.append((mask.size, bytes(mask)))
    if len(set(fingerprints)) < 5:
        raise ValueError(f"Chinese font appears to return repeated missing-glyph boxes: {path}")


def fit_font(
    draw: ImageDraw.ImageDraw,
    path: str,
    start_size: int,
    lines: Iterable[str],
    max_width: int,
    min_size: int = 18,
    variation: str | None = None,
) -> ImageFont.FreeTypeFont:
    size = int(start_size)
    while size >= min_size:
        candidate = font(path, size, variation)
        if all(draw.textlength(str(line), font=candidate) <= max_width for line in lines):
            return candidate
        size -= 1
    return font(path, min_size, variation)


def draw_lines(draw: ImageDraw.ImageDraw, xy: tuple[int, int], lines: Iterable[str], fnt, fill, gap: int = 0) -> int:
    x, y = xy
    for line in lines:
        draw.text((x, y), str(line), font=fnt, fill=fill, anchor="la")
        box = draw.textbbox((x, y), str(line), font=fnt, anchor="la")
        y += (box[3] - box[1]) + gap
    return y


def wrap_text(draw: ImageDraw.ImageDraw, text: str, fnt, max_width: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        trial = word if not current else f"{current} {word}"
        if draw.textlength(trial, font=fnt) <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def wrap_cjk(draw: ImageDraw.ImageDraw, text: str, fnt, max_width: int) -> list[str]:
    lines: list[str] = []
    current = ""
    for ch in text:
        trial = current + ch
        if draw.textlength(trial, font=fnt) <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = ch
    if current:
        lines.append(current)
    return lines


def draw_globe(draw: ImageDraw.ImageDraw, cx: int, cy: int, olive: str, ink: str) -> None:
    r = 42
    draw.ellipse((cx-r, cy-r, cx+r, cy+r), outline=olive, width=3)
    draw.arc((cx-r//2, cy-r, cx+r//2, cy+r), 90, 270, fill=olive, width=2)
    draw.arc((cx-r//2, cy-r, cx+r//2, cy+r), 270, 90, fill=olive, width=2)
    draw.line((cx-r, cy, cx+r, cy), fill=olive, width=2)
    draw.arc((cx-r, cy-r//2, cx+r, cy+r//2), 180, 360, fill=olive, width=2)
    draw.arc((cx-r, cy-r//2, cx+r, cy+r//2), 0, 180, fill=olive, width=2)
    draw.arc((cx-r-7, cy-r-7, cx+r+7, cy+r+7), 220, 40, fill=ink, width=3)
    draw.line((cx, cy+r+8, cx, cy+r+27), fill=ink, width=3)
    draw.line((cx-25, cy+r+27, cx+25, cy+r+27), fill=ink, width=3)


def fit_panel(img: Image.Image, size: tuple[int, int], background: str) -> Image.Image:
    """Contain the full illustration instead of cropping away heads or props."""
    fitted = ImageOps.contain(img.convert("RGB"), size, method=Image.Resampling.LANCZOS)
    panel = Image.new("RGB", size, background)
    x = (size[0] - fitted.width) // 2
    y = size[1] - fitted.height
    panel.paste(fitted, (x, y))
    return panel


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", required=True)
    ap.add_argument("--illustration", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--font-cn-title")
    ap.add_argument("--font-cn-body")
    ap.add_argument("--font-en-display")
    ap.add_argument("--font-en-body")
    args = ap.parse_args()

    spec = yaml.safe_load(Path(args.spec).read_text(encoding="utf-8"))
    canvas = spec["canvas"]
    content = spec["content"]
    palette = spec["palette"]
    layout = spec["layout"]
    sizes = spec["font_sizes"]
    w, h = int(canvas["width"]), int(canvas["height"])

    paths = {
        "cn_title": find_font("cn_title", args.font_cn_title),
        "cn_body": find_font("cn_body", args.font_cn_body),
        "en_display": find_font("en_display", args.font_en_display),
        "en_body": find_font("en_body", args.font_en_body),
    }
    require_common_chinese_glyphs(paths["cn_title"])
    require_common_chinese_glyphs(paths["cn_body"])

    im = Image.new("RGB", (w, h), canvas["background"])
    draw = ImageDraw.Draw(im)
    left_max = int(layout["right_rule_x"]) - int(layout["left_margin"]) - 26
    rail_max = w - int(layout["right_rail_x"]) - 24
    f = {
        "masthead1": fit_font(draw, paths["en_display"], sizes["masthead_line1"], [content["masthead_lines"][0]], left_max - 120, 42),
        "masthead2": fit_font(draw, paths["en_display"], sizes["masthead_line2"], [content["masthead_lines"][1]], left_max - 120, 52),
        "tagline": fit_font(draw, paths["en_body"], sizes["tagline"], [content["tagline"]], left_max - 130, 18),
        "en_head": fit_font(draw, paths["en_display"], sizes["english_headline"], content["english_headline_lines"], left_max, 28),
        "cn_head": fit_font(
            draw,
            paths["cn_title"],
            sizes["chinese_headline"],
            content["chinese_headline_lines"],
            left_max,
            58,
            variation="Black",
        ),
        "en_sum": font(paths["en_body"], sizes["english_summary"]),
        "cn_sum": font(paths["cn_body"], sizes["chinese_summary"]),
        "rail_year": fit_font(draw, paths["en_body"], sizes["rail_year"], [f"Year / {content['year']}"], rail_max, 18),
        "rail_journal": fit_font(draw, paths["en_display"], sizes["rail_journal"], [content["journal_label"]], rail_max, 20),
        "rail_number": font(paths["en_body"], sizes["rail_number"]),
        "rail_en": font(paths["en_display"], sizes["rail_english"]),
        "rail_cn": font(paths["cn_body"], sizes["rail_chinese"]),
        "rail_footer": font(paths["en_body"], sizes["rail_footer"]),
    }
    ink, gray, olive = palette["ink"], palette["gray"], palette["olive"]
    lm = int(layout["left_margin"])
    rr = int(layout["right_rule_x"])
    rx = int(layout["right_rail_x"])

    # Illustration first, clipped strictly to the panel.
    iy, ih = int(layout["illustration_y"]), int(layout["illustration_height"])
    illustration = fit_panel(
        Image.open(args.illustration),
        (w, ih),
        palette["illustration_background"],
    )
    im.paste(illustration, (0, iy))
    draw = ImageDraw.Draw(im)

    # Paper area.
    draw.rectangle((0, 0, w, iy-1), fill=canvas["background"])

    mast = content["masthead_lines"]
    draw.text((lm, layout["masthead_line1_y"]), mast[0], font=f["masthead1"], fill=ink)
    draw.text((lm, layout["masthead_line2_y"]), mast[1], font=f["masthead2"], fill=ink)
    draw.text((lm+4, layout["tagline_y"]), content["tagline"], font=f["tagline"], fill=gray)
    draw.line((lm, layout["top_rule_y"], rr-28, layout["top_rule_y"]), fill=palette["divider"], width=3)

    draw_globe(draw, int(layout["globe_center_x"]), int(layout["globe_center_y"]), olive, ink)

    draw_lines(draw, (lm, int(layout["english_headline_y"])), content["english_headline_lines"], f["en_head"], ink, gap=5)
    draw_lines(draw, (lm, int(layout["chinese_headline_y"])), content["chinese_headline_lines"], f["cn_head"], ink, gap=int(layout["chinese_headline_line_gap"]))

    sy = int(layout["summary_rule_y"])
    draw.line((lm+10, sy, lm+118, sy), fill=olive, width=4)
    summary_max = min(int(layout.get("summary_max_width", rr-lm-45)), rr-lm-45)
    en_lines = wrap_text(draw, content["english_summary"], f["en_sum"], summary_max)
    en_bottom = draw_lines(draw, (lm+10, int(layout["english_summary_y"])), en_lines, f["en_sum"], ink, gap=5)
    zh_lines = wrap_cjk(draw, content["chinese_summary"], f["cn_sum"], summary_max)
    zh_y = max(
        int(layout["chinese_summary_y"]),
        en_bottom + int(layout.get("summary_block_gap", 12)),
    )
    zh_bottom = draw_lines(draw, (lm+10, zh_y), zh_lines, f["cn_sum"], ink, gap=4)
    if en_bottom >= iy - 12 or zh_bottom >= iy - 12:
        raise ValueError("Summary text reaches the illustration boundary; shorten text or adjust layout")

    # Right rail.
    draw.line((rr, 26, rr, iy-22), fill=olive, width=2)
    draw.text((rx, 39), f"Year / {content['year']}", font=f["rail_year"], fill=ink)
    draw.text((rx, 75), content["journal_label"], font=f["rail_journal"], fill=ink)
    draw.line((rx, 111, w-34, 111), fill=gray, width=2)

    base_y = 177
    step = 171
    for i, item in enumerate(content["rail"]):
        y = base_y + i*step
        draw.text((rx, y), item["number"], font=f["rail_number"], fill=olive)
        rail_item_font = fit_font(draw, paths["en_display"], sizes["rail_english"], [item["english"]], rail_max, 17)
        draw.text((rx, y+42), item["english"], font=rail_item_font, fill=ink)
        draw.text((rx, y+77), item["chinese"], font=f["rail_cn"], fill=ink)

    fy = 819
    for line in content.get("rail_footer_lines", []):
        draw.text((rx, fy), line, font=f["rail_footer"], fill="#B7B4AA")
        fy += 27

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    im.save(out, quality=95)
    print(f"Saved {out}")
    print("Fonts used:")
    for k, v in paths.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
