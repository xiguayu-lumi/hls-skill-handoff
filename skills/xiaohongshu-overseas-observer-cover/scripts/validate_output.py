#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys

import yaml
from PIL import Image


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def open_image(path: Path) -> Image.Image:
    if not path.exists():
        fail(f"Image not found: {path}")
    try:
        return Image.open(path)
    except Exception as exc:
        fail(f"Image cannot be decoded: {path}: {exc}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", required=True)
    parser.add_argument("--illustration", required=True)
    parser.add_argument("--cover", required=True)
    args = parser.parse_args()

    spec_path = Path(args.spec)
    if not spec_path.exists():
        fail(f"Spec not found: {spec_path}")
    spec = yaml.safe_load(spec_path.read_text(encoding="utf-8"))

    width = int(spec["canvas"]["width"])
    height = int(spec["canvas"]["height"])
    panel_height = int(spec["layout"]["illustration_height"])

    cover = open_image(Path(args.cover))
    illustration = open_image(Path(args.illustration))

    if cover.size != (width, height):
        fail(f"Cover size is {cover.size}, expected {(width, height)}")
    if cover.format != "PNG":
        fail(f"Cover must be PNG, got {cover.format}")
    if illustration.width < width:
        fail(f"Illustration width {illustration.width} is smaller than canvas width {width}")
    if illustration.height < panel_height:
        print(
            f"WARNING: illustration height {illustration.height} is smaller than panel height "
            f"{panel_height}; the renderer will letterbox it instead of cropping"
        )

    cover.verify()
    illustration.verify()
    print("Output validation passed")
    print("Manual QA still required for text accuracy, random lettering, anatomy, and originality")


if __name__ == "__main__":
    main()
