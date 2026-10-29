from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from jsonschema import Draft202012Validator

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hls_academic.evidence import validate_evidence_map
from hls_academic.issues import ValidationIssue
from hls_academic.language import validate_evidence_language


def _paper_pages(path: Path) -> dict[int, str]:
    text = path.read_text(encoding="utf-8")
    matches = list(re.finditer(r"<!-- page: (\d+) -->", text))
    pages: dict[int, str] = {}
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        pages[int(match.group(1))] = text[match.end():end]
    return pages


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()


def _schema_issues(data: dict, schema: dict) -> list[ValidationIssue]:
    issues = []
    for error in Draft202012Validator(schema).iter_errors(data):
        location = ".".join(str(part) for part in error.absolute_path)
        issues.append(
            ValidationIssue(
                severity="error",
                code="schema_error",
                message=error.message,
                location=location or "$",
            )
        )
    return issues


def _markdown(issues: list[ValidationIssue], total: int) -> str:
    errors = [issue for issue in issues if issue.severity == "error"]
    lines = [
        "# QA Evidence Report",
        "",
        f"- Evidence items: {total}",
        f"- Errors: {len(errors)}",
        f"- Status: {'PASS' if not errors else 'FAIL'}",
        "",
    ]
    if issues:
        lines.extend(
            [
                "| Severity | Code | Evidence | Location | Message |",
                "|---|---|---|---|---|",
            ]
        )
        for issue in issues:
            lines.append(
                f"| {issue.severity} | {issue.code} | {issue.item_id or ''} | "
                f"{issue.location or ''} | {issue.message.replace('|', '/')} |"
            )
    else:
        lines.append("No evidence validation issues found.")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate evidence map and source excerpts.")
    parser.add_argument("evidence", type=Path)
    parser.add_argument("--paper", type=Path)
    parser.add_argument("--schema", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    schema_path = args.schema or root / "schemas" / "evidence-map.schema.json"
    data = json.loads(args.evidence.read_text(encoding="utf-8"))
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    issues = _schema_issues(data, schema)
    issues.extend(validate_evidence_map(data))
    for item in data.get("items", []):
        issues.extend(validate_evidence_language(item))

    if args.paper:
        pages = _paper_pages(args.paper)
        for item in data.get("items", []):
            page = int(item.get("source_page", 0))
            excerpt = _normalize(str(item.get("original_excerpt", "")))
            if page not in pages:
                issues.append(
                    ValidationIssue("error", "source_page_missing", "Page marker is absent", item.get("id"))
                )
            elif excerpt and excerpt not in _normalize(pages[page]):
                issues.append(
                    ValidationIssue(
                        "error",
                        "excerpt_not_on_source_page",
                        "Stored excerpt was not found on the declared page",
                        item.get("id"),
                    )
                )

    report = _markdown(issues, len(data.get("items", [])))
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(report, encoding="utf-8")
    print(report, end="")
    return 1 if any(issue.severity == "error" for issue in issues) else 0


if __name__ == "__main__":
    raise SystemExit(main())
