from __future__ import annotations

import base64
import json
import mimetypes
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape

from .models import Deck


def compact_evidence_ids(evidence_ids: list[str]) -> str:
    if not evidence_ids:
        return ""
    numbers = [int(item[1:]) for item in evidence_ids]
    groups: list[list[int]] = [[numbers[0]]]
    for number in numbers[1:]:
        if number == groups[-1][-1] + 1:
            groups[-1].append(number)
        else:
            groups.append([number])

    labels: list[str] = []
    for group in groups:
        if len(group) >= 3:
            labels.append(f"E{group[0]:03d}–E{group[-1]:03d}")
        else:
            labels.extend(f"E{number:03d}" for number in group)
    return " · ".join(labels)


def section_meta_for_slide(slide_id: str, page_type: str) -> dict[str, str]:
    number = int(slide_id[1:])
    if number == 2:
        return {"zh": "研究设计", "en": "STUDY DESIGN", "number": "01"}
    if number == 3 and page_type == "mediation":
        return {"zh": "研究模型", "en": "RESEARCH MODEL", "number": "02"}
    if number == 4 and page_type == "finding":
        return {"zh": "核心结果", "en": "RESULTS", "number": "03"}
    if number == 3:
        return {"zh": "研究一", "en": "STUDY 1", "number": "02"}
    if number == 4:
        return {"zh": "研究二", "en": "STUDY 2", "number": "03"}
    if number == 5:
        return {"zh": "总结边界", "en": "TAKEAWAY", "number": "04"}
    return {"zh": "", "en": page_type.replace("_", " ").upper(), "number": ""}


def _data_uri(path: Path) -> str | None:
    if not path.is_file():
        return None
    mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def _visual_asset_uris(deck: dict, deck_file: Path) -> dict[str, str]:
    uris: dict[str, str] = {}
    for slide in deck.get("slides", []):
        data = slide.get("visual", {}).get("data", {})
        for key in ("source_image", "figure_image"):
            relative = data.get(key)
            if not relative:
                continue
            path = deck_file.parent / relative
            uri = _data_uri(path)
            if uri is None:
                raise FileNotFoundError(f"Missing deck visual asset: {path}")
            uris[relative] = uri
        for figure in data.get("feature_figures", []):
            relative = figure.get("image")
            if not relative:
                continue
            path = deck_file.parent / relative
            uri = _data_uri(path)
            if uri is None:
                raise FileNotFoundError(f"Missing deck visual asset: {path}")
            uris[relative] = uri
    return uris


def render_deck(
    deck_path: Path | str,
    output_path: Path | str,
    *,
    template_path: Path | str,
) -> Path:
    deck_file = Path(deck_path)
    target = Path(output_path)
    template_file = Path(template_path)
    data = json.loads(deck_file.read_text(encoding="utf-8"))
    deck = Deck.model_validate(data)

    environment = Environment(
        loader=FileSystemLoader(str(template_file.parent)),
        autoescape=select_autoescape(["html", "j2"]),
        undefined=StrictUndefined,
        keep_trailing_newline=True,
    )
    template = environment.get_template(template_file.name)
    project_root = template_file.parent.parent
    logo = _data_uri(project_root / "assets" / "brand" / "hls-logo-transparent.png")
    deck_data = deck.model_dump(mode="json")
    for slide in deck_data["slides"]:
        override = slide.get("section")
        if isinstance(override, dict) and override.get("zh") is not None:
            slide["section_meta"] = override
        else:
            slide["section_meta"] = section_meta_for_slide(
                slide["id"],
                slide["page_type"],
            )
        slide["evidence_label"] = compact_evidence_ids(slide["evidence_ids"])
    html = template.render(
        deck=deck_data,
        logo_data_uri=logo,
        asset_data_uris=_visual_asset_uris(deck_data, deck_file),
    )
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(html, encoding="utf-8", newline="\n")
    return target
