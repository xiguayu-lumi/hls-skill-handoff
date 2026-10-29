from __future__ import annotations

from pathlib import Path

from PIL import Image


def build_contact_sheets(
    slides_dir: Path | str,
    output_dir: Path | str,
) -> list[Path]:
    source = Path(slides_dir)
    destination = Path(output_dir)
    slide_files = sorted(source.glob("*.png"))
    if not slide_files:
        raise FileNotFoundError(f"No slide PNG files found in: {source}")
    destination.mkdir(parents=True, exist_ok=True)

    created: list[Path] = []
    positions = [(0, 0), (1080, 0)]
    for sheet_index in range(0, len(slide_files), 2):
        canvas = Image.new("RGB", (2160, 1440), "#FAF8F3")
        for position, slide_path in zip(positions, slide_files[sheet_index:sheet_index + 2]):
            with Image.open(slide_path).convert("RGB") as slide:
                if slide.size != (1080, 1440):
                    raise ValueError(
                        f"Slide must be 1080x1440: {slide_path} is {slide.size}"
                    )
                canvas.paste(slide, position)
        output_path = destination / f"{sheet_index // 2 + 1:02d}.png"
        canvas.save(output_path, format="PNG", optimize=True)
        created.append(output_path)
    return created
