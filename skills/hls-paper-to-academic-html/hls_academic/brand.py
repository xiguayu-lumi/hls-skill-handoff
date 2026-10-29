from dataclasses import dataclass
from collections import deque
from pathlib import Path

from PIL import Image


@dataclass(frozen=True)
class PreparedLogo:
    source_path: str
    output_path: str
    width: int
    height: int
    transparent_pixels: int


def _alpha_for_near_white(
    red: int,
    green: int,
    blue: int,
    white_threshold: int,
    feather: int,
) -> int:
    distance = 255 - min(red, green, blue)
    transparent_distance = 255 - white_threshold
    if distance <= transparent_distance:
        return 0
    if distance >= transparent_distance + feather:
        return 255
    return round(255 * (distance - transparent_distance) / feather)


def _remove_edge_connected_artifacts(image: Image.Image) -> None:
    width, height = image.size
    pixels = image.load()
    queue: deque[tuple[int, int]] = deque()
    visited: set[tuple[int, int]] = set()
    for x in range(width):
        queue.append((x, 0))
        queue.append((x, height - 1))
    for y in range(height):
        queue.append((0, y))
        queue.append((width - 1, y))

    while queue:
        x, y = queue.popleft()
        if (x, y) in visited:
            continue
        visited.add((x, y))
        red, green, blue, alpha = pixels[x, y]
        if alpha == 0:
            continue
        pixels[x, y] = (red, green, blue, 0)
        for neighbor_x, neighbor_y in (
            (x - 1, y),
            (x + 1, y),
            (x, y - 1),
            (x, y + 1),
        ):
            if 0 <= neighbor_x < width and 0 <= neighbor_y < height:
                queue.append((neighbor_x, neighbor_y))


def prepare_logo(
    source_path: Path | str,
    output_path: Path | str,
    *,
    white_threshold: int = 248,
    feather: int = 20,
) -> PreparedLogo:
    source = Path(source_path)
    output = Path(output_path)
    if not source.is_file():
        raise FileNotFoundError(f"Logo not found: {source}")
    if not 0 <= white_threshold <= 255:
        raise ValueError("white_threshold must be between 0 and 255")
    if feather <= 0:
        raise ValueError("feather must be greater than 0")

    with Image.open(source).convert("RGB") as image:
        rgba = Image.new("RGBA", image.size)
        prepared_pixels = []
        transparent_pixels = 0
        for red, green, blue in image.get_flattened_data():
            alpha = _alpha_for_near_white(
                red,
                green,
                blue,
                white_threshold,
                feather,
            )
            if alpha == 0:
                transparent_pixels += 1
            prepared_pixels.append((red, green, blue, alpha))
        rgba.putdata(prepared_pixels)
        _remove_edge_connected_artifacts(rgba)
        transparent_pixels = sum(
            1 for *_, alpha in rgba.get_flattened_data() if alpha == 0
        )
        output.parent.mkdir(parents=True, exist_ok=True)
        rgba.save(output, format="PNG", optimize=True)
        width, height = rgba.size

    return PreparedLogo(
        source_path=str(source.resolve()),
        output_path=str(output.resolve()),
        width=width,
        height=height,
        transparent_pixels=transparent_pixels,
    )
