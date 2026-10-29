"""Assemble 01.png through 05.png into one verified five-page PDF."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from pypdf import PdfReader
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas


EXPECTED_SIZE = (1242, 1660)
EXPECTED_FILES = [f"{index:02d}.png" for index in range(1, 6)]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--title", default="Course Analysis Carousel")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_dir = args.input_dir.resolve()
    output = args.output.resolve()
    image_paths = [input_dir / filename for filename in EXPECTED_FILES]
    missing = [path.name for path in image_paths if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Missing carousel PNGs: {missing}")

    output.parent.mkdir(parents=True, exist_ok=True)
    pdf = canvas.Canvas(
        str(output),
        pagesize=EXPECTED_SIZE,
        pageCompression=1,
        invariant=1,
    )
    pdf.setTitle(args.title)
    pdf.setAuthor("HLS")
    pdf.setSubject("Five-page university course analysis carousel")
    pdf.setCreator("hls-course-analysis-carousel")

    image_results = []
    for image_path in image_paths:
        image = ImageReader(str(image_path))
        width, height = image.getSize()
        if (width, height) != EXPECTED_SIZE:
            raise ValueError(
                f"Wrong image dimensions for {image_path.name}: "
                f"{width}x{height}; expected {EXPECTED_SIZE[0]}x{EXPECTED_SIZE[1]}"
            )
        pdf.setPageSize(EXPECTED_SIZE)
        pdf.drawImage(image, 0, 0, width=width, height=height, mask="auto")
        pdf.showPage()
        image_results.append({"file": image_path.name, "width": width, "height": height})

    pdf.save()

    reader = PdfReader(str(output))
    if len(reader.pages) != 5:
        raise ValueError(f"PDF page count is {len(reader.pages)}; expected 5")
    page_sizes = []
    for index, page in enumerate(reader.pages, start=1):
        width = float(page.mediabox.width)
        height = float(page.mediabox.height)
        page_sizes.append({"page": index, "width": width, "height": height})
        if round(width) != EXPECTED_SIZE[0] or round(height) != EXPECTED_SIZE[1]:
            raise ValueError(f"Wrong PDF page size on page {index}: {width}x{height}")

    print(
        json.dumps(
            {
                "status": "PASS",
                "output": str(output),
                "pageCount": len(reader.pages),
                "images": image_results,
                "pageSizes": page_sizes,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
