from __future__ import annotations

import io
from pathlib import Path

import pymupdf
from PIL import Image

from .models import SourceAssetManifest


class SourceAssetError(RuntimeError):
    pass


def render_source_assets(
    pdf_path: Path | str,
    manifest_data: dict,
    output_dir: Path | str,
    *,
    scale: float = 3.0,
) -> list[Path]:
    manifest = SourceAssetManifest.model_validate(manifest_data)
    target_root = Path(output_dir)
    document = pymupdf.open(pdf_path)
    outputs: list[Path] = []
    try:
        for asset in manifest.assets:
            if asset.page > document.page_count:
                raise SourceAssetError(f"{asset.id}: page out of range")
            target = target_root / asset.output
            target.parent.mkdir(parents=True, exist_ok=True)
            if asset.kind == "text_crop":
                page = document[asset.page - 1]
                clip = pymupdf.Rect(asset.clip)
                if clip.is_empty or not page.rect.contains(clip):
                    raise SourceAssetError(f"{asset.id}: invalid clip")
                pixmap = page.get_pixmap(
                    matrix=pymupdf.Matrix(scale, scale),
                    clip=clip,
                    alpha=False,
                )
                pixmap.save(target)
            else:
                try:
                    extracted = document.extract_image(asset.xref)
                except (RuntimeError, ValueError) as exc:
                    raise SourceAssetError(
                        f"{asset.id}: figure xref cannot be extracted"
                    ) from exc
                if not extracted or not extracted.get("image"):
                    raise SourceAssetError(
                        f"{asset.id}: figure xref cannot be extracted"
                    )
                with Image.open(io.BytesIO(extracted["image"])) as source:
                    source.convert("RGB").save(target, format="PNG")
            outputs.append(target)
    finally:
        document.close()
    return outputs
