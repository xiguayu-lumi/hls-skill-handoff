from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from preview_core import ALLOWED_FONT_SIZES, ALLOWED_LINE_HEIGHTS, snapshot_locked_structure


def inspect_html(source: str) -> dict[str, bool]:
    snapshot = snapshot_locked_structure(source)
    ids = re.findall(r'<h[1-3]\b[^>]*\bid="([^"]+)"', source, re.I)
    hrefs = re.findall(r'<a\b[^>]*\bhref="#([^"]+)"', source, re.I)
    font_values = re.findall(r'\bdata-font-size="([^"]+)"', source, re.I)
    line_values = re.findall(r'\bdata-line-height="([^"]+)"', source, re.I)
    opening_tags = re.findall(r'<[a-z][^>]*>', source, re.I)
    manual_classes = sum(
        1 for tag in opening_tags if re.search(r'class="[^"]*\bmanual-page-break\b[^"]*"', tag, re.I)
    )
    manual_attrs = sum(
        1 for tag in opening_tags if re.search(r'data-manual-page-break="true"', tag, re.I)
    )
    residue = re.search(
        r'contenteditable|data-editor-|id="hls-editor-toolbar"|<script\b|\son[a-z]+=', source, re.I
    )
    unsafe_paths = re.search(r'(?:src|href)="(?:file:|[a-z]:\\|/mnt/data/|/tmp/)', source, re.I)
    table_count = len(re.findall(r'<table\b', source, re.I))
    thead_count = len(re.findall(r'<thead\b', source, re.I))
    return {
        "no_banned_source_wording": "原资料" not in source,
        "no_editor_residue": residue is None,
        "unique_heading_ids": bool(ids) and len(ids) == len(set(ids)),
        "toc_links_resolve": bool(hrefs) and all(anchor in set(ids) for anchor in hrefs),
        "locked_cover_present": int(snapshot["cover_regions"]) > 0,
        "table_headers_preserved": table_count == thead_count,
        "manual_page_breaks_semantic": manual_classes == manual_attrs,
        "controlled_font_sizes": all(value in ALLOWED_FONT_SIZES for value in font_values),
        "controlled_line_heights": all(value in ALLOWED_LINE_HEIGHTS for value in line_values),
        "no_temporary_absolute_assets": unsafe_paths is None,
    }


def _flatten_outline(items: list[Any]):
    for item in items:
        if isinstance(item, list):
            yield from _flatten_outline(item)
        else:
            yield item


def inspect_pdf(pdf_path: Path, expected_links: int) -> tuple[dict[str, bool], dict[str, Any]]:
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise RuntimeError("pypdf is required for PDF QA") from exc
    reader = PdfReader(str(pdf_path))
    page_sizes: list[list[float]] = []
    text_counts: list[int] = []
    internal_links = 0
    external_links = 0
    for page in reader.pages:
        page_sizes.append([round(float(page.mediabox.width), 2), round(float(page.mediabox.height), 2)])
        text_counts.append(len((page.extract_text() or "").strip()))
        for ref in page.get("/Annots", []):
            annotation = ref.get_object()
            if annotation.get("/Subtype") != "/Link":
                continue
            action = annotation.get("/A")
            if action and action.get("/URI"):
                external_links += 1
            elif annotation.get("/Dest") is not None or (action and action.get("/D") is not None):
                internal_links += 1
    outline_items = list(_flatten_outline(reader.outline))
    checks = {
        "pdf_exists": pdf_path.is_file() and pdf_path.stat().st_size > 0,
        "pdf_has_pages": len(reader.pages) > 0,
        "pdf_a4_all_pages": all(abs(w - 595.28) < 2 and abs(h - 841.89) < 2 for w, h in page_sizes),
        "pdf_searchable_text": all(count > 20 for count in text_counts),
        "pdf_internal_links": internal_links >= expected_links,
        "pdf_no_external_links": external_links == 0,
        "pdf_bookmarks_present": len(outline_items) >= expected_links,
    }
    details = {
        "pages": len(reader.pages),
        "page_sizes_pt": page_sizes,
        "text_chars_by_page": text_counts,
        "internal_links": internal_links,
        "external_links": external_links,
        "bookmarks": len(outline_items),
    }
    return checks, details


def run_qa(project: Path) -> Path:
    root = project.expanduser().resolve()
    html_path = root / "dist" / "teaching-handout.html"
    pdf_path = root / "dist" / "teaching-handout.pdf"
    if not html_path.is_file():
        raise FileNotFoundError(html_path)
    source = html_path.read_text(encoding="utf-8")
    html_checks = inspect_html(source)
    expected_links = len(re.findall(r'<a\b[^>]*\bhref="#[^"]+"', source, re.I))
    pdf_checks, details = inspect_pdf(pdf_path, expected_links)
    checks = {**html_checks, **pdf_checks}
    overall = all(checks.values())
    qa_dir = root / "qa"
    qa_dir.mkdir(parents=True, exist_ok=True)
    summary = {"overall": "PASS" if overall else "FAIL", "checks": checks, **details}
    summary_path = qa_dir / "qa-summary.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = ["# HLS 教学讲义 QA 报告", "", f"- 结论：**{summary['overall']}**", "", "## 自动检查", ""]
    lines.extend(f"- [{'x' if passed else ' '}] {name}" for name, passed in checks.items())
    lines += ["", "## PDF", "", f"- 页数：{details['pages']}", f"- 内部链接：{details['internal_links']}", f"- 书签：{details['bookmarks']}"]
    report_path = qa_dir / "qa-report.md"
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    if not overall:
        raise RuntimeError(f"QA failed; see {report_path}")
    return report_path


def main() -> None:
    parser = argparse.ArgumentParser(description="QA an approved HLS handout")
    parser.add_argument("--project", required=True)
    args = parser.parse_args()
    print(run_qa(Path(args.project)))


if __name__ == "__main__":
    main()
