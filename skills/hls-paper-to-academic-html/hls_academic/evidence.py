from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any, Iterable

from .issues import ValidationIssue


def _number_values(value: Any) -> Iterable[str]:
    if isinstance(value, dict):
        for nested in value.values():
            yield from _number_values(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from _number_values(nested)
    elif isinstance(value, (int, float, str)) and not isinstance(value, bool):
        text = str(value).strip()
        if text:
            yield text


def _normalized_numeric_text(value: str) -> str:
    return value.replace(",", "").replace(" ", "").replace("−", "-")


def validate_evidence_map(data: dict) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    items = data.get("items") or []
    paper_page_count = data.get("paper_page_count")
    ids = [str(item.get("id", "")) for item in items]
    for evidence_id, count in Counter(ids).items():
        if evidence_id and count > 1:
            issues.append(
                ValidationIssue(
                    severity="error",
                    code="duplicate_evidence_id",
                    message=f"Evidence ID appears {count} times: {evidence_id}",
                    item_id=evidence_id,
                )
            )

    for index, item in enumerate(items):
        evidence_id = item.get("id") or f"items[{index}]"
        source_page = item.get("source_page")
        if (
            isinstance(paper_page_count, int)
            and isinstance(source_page, int)
            and not 1 <= source_page <= paper_page_count
        ):
            issues.append(
                ValidationIssue(
                    severity="error",
                    code="source_page_out_of_range",
                    message=(
                        f"Source page {source_page} is outside "
                        f"1-{paper_page_count}"
                    ),
                    item_id=str(evidence_id),
                    location=f"items[{index}].source_page",
                )
            )

        excerpt = _normalized_numeric_text(str(item.get("original_excerpt", "")))
        for number in _number_values(item.get("numbers", {})):
            normalized = _normalized_numeric_text(number)
            if normalized and normalized not in excerpt:
                issues.append(
                    ValidationIssue(
                        severity="error",
                        code="number_not_in_excerpt",
                        message=f"Reported value is absent from excerpt: {number}",
                        item_id=str(evidence_id),
                        location=f"items[{index}].numbers",
                    )
                )
    return issues


def validate_deck_evidence(
    deck: dict,
    evidence_map: dict,
) -> list[ValidationIssue]:
    known = {
        str(item.get("id"))
        for item in evidence_map.get("items", [])
        if item.get("id")
    }
    issues: list[ValidationIssue] = []
    root_ids = set(deck.get("evidence_ids") or [])
    references = set(root_ids)
    for slide in deck.get("slides") or []:
        references.update(slide.get("evidence_ids") or [])
    for evidence_id in sorted(references - known):
        issues.append(
            ValidationIssue(
                severity="error",
                code="unknown_evidence_id",
                message=f"Deck references unknown evidence: {evidence_id}",
                item_id=evidence_id,
            )
        )
    return issues


def validate_deck_assets(
    deck: dict,
    output_root: Path | str,
) -> list[ValidationIssue]:
    root = Path(output_root)
    issues: list[ValidationIssue] = []
    for slide in deck.get("slides") or []:
        data = slide.get("visual", {}).get("data", {})
        for key in ("source_image", "figure_image"):
            relative = data.get(key)
            if relative and not (root / relative).is_file():
                issues.append(
                    ValidationIssue(
                        severity="error",
                        code="missing_deck_asset",
                        message=f"Deck visual asset is missing: {relative}",
                        item_id=slide.get("id"),
                        location=f"visual.data.{key}",
                    )
                )
    return issues


def validate_deck_structure(deck: dict) -> list[ValidationIssue]:
    slides = deck.get("slides") or []
    positions = {
        str(slide.get("id")): f"{index:02d}"
        for index, slide in enumerate(slides, start=1)
    }
    issues: list[ValidationIssue] = []
    for slide in slides:
        visual = slide.get("visual", {})
        if visual.get("component") != "agenda-reading":
            continue
        for index, item in enumerate(visual.get("data", {}).get("items", [])):
            target = str(item.get("target_slide_id") or "")
            declared_page = str(item.get("page") or "")
            actual_page = positions.get(target)
            if actual_page is None:
                issues.append(
                    ValidationIssue(
                        severity="error",
                        code="agenda_target_missing",
                        message=f"Agenda target slide does not exist: {target}",
                        item_id=slide.get("id"),
                        location=f"visual.data.items[{index}]",
                    )
                )
            elif declared_page != actual_page:
                issues.append(
                    ValidationIssue(
                        severity="error",
                        code="agenda_page_mismatch",
                        message=(
                            f"Agenda page {declared_page} does not match "
                            f"{target} at page {actual_page}"
                        ),
                        item_id=slide.get("id"),
                        location=f"visual.data.items[{index}].page",
                    )
                )
    return issues
