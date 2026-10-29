#!/usr/bin/env python3
from __future__ import annotations
import argparse
from pathlib import Path
import re
import sys
import yaml


def fail(msg: str) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)
    raise SystemExit(1)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", required=True)
    args = parser.parse_args()
    p = Path(args.spec)
    if not p.exists():
        fail(f"Spec not found: {p}")
    data = yaml.safe_load(p.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        fail("Spec root must be a mapping")

    canvas = data.get("canvas", {})
    w, h = canvas.get("width"), canvas.get("height")
    if not isinstance(w, int) or not isinstance(h, int):
        fail("canvas.width and canvas.height must be integers")
    if abs((w / h) - 0.75) > 0.002:
        fail(f"Canvas is not 3:4: {w}x{h}")
    if not re.fullmatch(r"#[0-9A-Fa-f]{6}", str(canvas.get("background", ""))):
        fail("canvas.background must be a six-digit hex color")

    content = data.get("content", {})
    zh_lines = content.get("chinese_headline_lines", [])
    en_lines = content.get("english_headline_lines", [])
    if not (2 <= len(zh_lines) <= 3):
        fail("Chinese headline must have 2 or 3 manual lines")
    if not (1 <= len(en_lines) <= 2):
        fail("English headline must have 1 or 2 manual lines")
    if any(not str(x).strip() for x in zh_lines + en_lines):
        fail("Headline lines may not be empty")
    if any(len(str(x).strip()) == 1 for x in zh_lines):
        fail("Chinese headline may not contain a one-character orphan line")
    if len("".join(zh_lines)) > 28:
        print("WARNING: Chinese headline is long; check title scale")
    for key in ("english_summary", "chinese_summary", "tagline", "year", "journal_label"):
        if not str(content.get(key, "")).strip():
            fail(f"content.{key} is required")

    layout = data.get("layout", {})
    illustration_y = layout.get("illustration_y")
    illustration_h = layout.get("illustration_height")
    if illustration_y is None or illustration_h is None:
        fail("layout.illustration_y and illustration_height are required")
    if illustration_y + illustration_h != h:
        fail("Illustration panel must end exactly at canvas bottom")
    if illustration_y <= 0 or illustration_h <= 0:
        fail("Illustration panel coordinates must be positive")
    if layout.get("right_rule_x", 0) >= layout.get("right_rail_x", 0):
        fail("right_rule_x must be left of right_rail_x")
    left_margin = int(layout.get("left_margin", 0))
    right_rule_x = int(layout.get("right_rule_x", 0))
    right_rail_x = int(layout.get("right_rail_x", 0))
    if left_margin < 20:
        fail("layout.left_margin must be at least 20 px")
    if not (left_margin < right_rule_x < right_rail_x < w):
        fail("Column coordinates must remain inside the canvas in left-to-right order")

    ordered_y = [
        "masthead_line1_y",
        "masthead_line2_y",
        "tagline_y",
        "top_rule_y",
        "english_headline_y",
        "chinese_headline_y",
        "summary_rule_y",
        "english_summary_y",
        "chinese_summary_y",
        "illustration_y",
    ]
    values = [int(layout.get(key, -1)) for key in ordered_y]
    if values != sorted(values) or any(value < 0 for value in values):
        fail("Major layout y-coordinates must be present and ordered from top to bottom")

    rail = content.get("rail", [])
    if len(rail) != 4:
        fail("Default house rail must contain exactly four sections")
    for index, item in enumerate(rail, start=1):
        if not isinstance(item, dict):
            fail(f"Rail item {index} must be a mapping")
        for key in ("number", "english", "chinese"):
            if not str(item.get(key, "")).strip():
                fail(f"Rail item {index} is missing {key}")

    palette = data.get("palette", {})
    for key in ("ink", "gray", "olive", "divider", "illustration_background"):
        if not re.fullmatch(r"#[0-9A-Fa-f]{6}", str(palette.get(key, ""))):
            fail(f"palette.{key} must be a six-digit hex color")

    font_sizes = data.get("font_sizes", {})
    if not font_sizes:
        fail("font_sizes is required")
    for key, value in font_sizes.items():
        if not isinstance(value, int) or value < 12:
            fail(f"font_sizes.{key} must be an integer of at least 12")

    print("Spec validation passed")


if __name__ == "__main__":
    main()
