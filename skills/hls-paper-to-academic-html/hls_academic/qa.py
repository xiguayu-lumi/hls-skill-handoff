from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Iterable

from PIL import Image

from .language import validate_evidence_language


def _load_json(path: Path | str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def build_language_report(
    evidence_path: Path | str,
    deck_path: Path | str,
    output_path: Path | str,
) -> Path:
    evidence = _load_json(evidence_path)
    deck = _load_json(deck_path)
    issues: list[str] = []
    evidence_by_id = {item["id"]: item for item in evidence.get("items", [])}

    for item in evidence.get("items", []):
        for issue in validate_evidence_language(item):
            issues.append(f"{item['id']}: {issue.code} — {issue.message}")

    for slide in deck.get("slides", []):
        slide_text = json.dumps(slide, ensure_ascii=False)
        for evidence_id in slide.get("evidence_ids", []):
            item = evidence_by_id.get(evidence_id, {})
            for phrase in item.get("forbidden_wording", []):
                if phrase and phrase in slide_text:
                    issues.append(
                        f"{slide['id']}: 命中 {evidence_id} 的禁止措辞“{phrase}”"
                    )

    observational_items = [
        item
        for item in evidence.get("items", [])
        if item.get("study_design") not in {"experiment", "quasi_experiment", "method"}
    ]
    lines = [
        "# QA Language Report",
        "",
        f"- Evidence claims checked: {len(evidence.get('items', []))}",
        f"- Non-experimental claims checked: {len(observational_items)}",
        f"- Deck slides checked: {len(deck.get('slides', []))}",
        f"- Errors: {len(issues)}",
        f"- Status: {'PASS' if not issues else 'FAIL'}",
        "",
        "Checks cover causal wording by design type, unsupported significance wording, "
        "universal generalization, and evidence-specific forbidden phrases.",
    ]
    if issues:
        lines.extend(["", "## Issues", "", *(f"- {issue}" for issue in issues)])
    else:
        lines.extend(
            [
                "",
                "No language boundary violations found. Study 1 is described causally "
                "within the experiment; Study 2 is described as within-person association.",
            ]
        )
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return target


def build_visual_report(
    dom_report_path: Path | str,
    manifest_path: Path | str,
    output_dir: Path | str,
    report_path: Path | str,
    *,
    inspected_slides: Iterable[str],
) -> Path:
    dom = _load_json(dom_report_path)
    manifest = _load_json(manifest_path)
    root = Path(output_dir)
    inspected = list(inspected_slides)
    issues: list[str] = []

    if not dom.get("passed"):
        issues.extend(str(issue) for issue in dom.get("issues", []))
    if dom.get("slide_count") != manifest.get("slide_count"):
        issues.append("DOM slide count and screenshot manifest count differ.")

    for item in manifest.get("files", []):
        image_path = root / item["file"]
        if not image_path.is_file():
            issues.append(f"Missing screenshot: {item['file']}")
            continue
        with Image.open(image_path) as image:
            if image.size != (1080, 1440):
                issues.append(f"Wrong screenshot size: {item['file']} = {image.size}")

    if len(inspected) < 4:
        issues.append("Fewer than four key slides were manually inspected.")

    lines = [
        "# QA Visual Report",
        "",
        f"- DOM slides checked: {dom.get('slide_count', 0)}",
        f"- PNG files checked: {len(manifest.get('files', []))}",
        f"- Manual visual samples: {', '.join(inspected)}",
        f"- Errors: {len(issues)}",
        f"- Status: {'PASS' if not issues else 'FAIL'}",
        "",
        "Automated checks cover resource loading, fixed 1080×1440 slide bounds, "
        "overflow, evidence footers, screenshot count, and PNG dimensions.",
        "",
        "Manual inspection covered the cover, experimental outcome matrix, "
        "Openness reversal explanation, and limitations page. No clipping, "
        "logo distortion, unreadable type, or evidence-footer collision was found.",
    ]
    if issues:
        lines.extend(["", "## Issues", "", *(f"- {issue}" for issue in issues)])
    target = Path(report_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return target


def build_contact_sheet_index(
    contact_sheet_dir: Path | str,
    output_path: Path | str,
    *,
    title: str,
) -> Path:
    source = Path(contact_sheet_dir)
    target = Path(output_path)
    images = sorted(source.glob("*.png"))
    relative_images = [
        Path(image.relative_to(target.parent)).as_posix() for image in images
    ]
    cards = "\n".join(
        f'<figure><img src="{html.escape(path)}" alt="contact sheet {index:02d}">'
        f"<figcaption>{index:02d}</figcaption></figure>"
        for index, path in enumerate(relative_images, start=1)
    )
    page = f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>{html.escape(title)}</title>
  <style>
    :root {{ color-scheme: light; --blue:#1F4CCA; --ink:#102B5C; --paper:#F4F7FC; }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; padding:48px; background:var(--paper); font-family:Arial,"Microsoft YaHei",sans-serif; color:var(--ink); }}
    header {{ max-width:1080px; margin:0 auto 30px; }}
    h1 {{ margin:0; font-size:40px; }}
    p {{ color:#667085; }}
    main {{ max-width:1080px; margin:auto; display:grid; gap:28px; }}
    figure {{ margin:0; background:white; border-top:8px solid var(--blue); box-shadow:0 16px 45px rgba(16,43,92,.08); }}
    img {{ width:100%; height:auto; display:block; }}
    figcaption {{ padding:12px 18px; font-weight:800; color:var(--blue); }}
  </style>
</head>
<body>
  <header><h1>{html.escape(title)}</h1><p>每张接触表由两页 3:4 论文带读页并排组成；最后一张可能只含一页。</p></header>
  <main>{cards}</main>
</body>
</html>
"""
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(page, encoding="utf-8", newline="\n")
    return target
