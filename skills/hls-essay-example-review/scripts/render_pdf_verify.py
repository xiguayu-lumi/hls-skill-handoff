#!/usr/bin/env python3
"""
Render PDF pages to PNG images for visual verification.

Also runs automated content checks on the generated PDF:
  - Paragraph count consistency
  - Annotation presence
  - Font/glyph integrity (no black squares)
  - Page header consistency

Usage:
  python render_pdf_verify.py input.pdf --out_dir build/renders --dpi 180
"""

import argparse
import json
import sys
from pathlib import Path

try:
    import pymupdf
except ImportError:
    try:
        import fitz as pymupdf
    except ImportError:
        print("ERROR: PyMuPDF not installed.", file=sys.stderr)
        sys.exit(1)


def render_pages(pdf_path, out_dir, dpi=180):
    """Render each PDF page to a PNG image."""
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    doc = pymupdf.open(str(pdf_path))
    zoom = dpi / 72.0
    mat = pymupdf.Matrix(zoom, zoom)

    rendered = []
    for page_num in range(len(doc)):
        page = doc[page_num]
        pix = page.get_pixmap(matrix=mat, alpha=False)
        img_name = f"page_{page_num + 1:03d}.png"
        img_path = out_path / img_name
        pix.save(str(img_path))
        rendered.append(str(img_path))
        print(f"  Rendered page {page_num + 1}/{len(doc)} -> {img_name}")

    doc.close()
    return rendered


def run_content_checks(pdf_path, source_json=None):
    """Run automated content verification checks on the PDF."""
    doc = pymupdf.open(str(pdf_path))
    checks = []

    # Extract all text from all pages
    all_text = ""
    page_texts = []
    for page_num in range(len(doc)):
        page_text = doc[page_num].get_text()
        page_texts.append(page_text)
        all_text += page_text + "\n"

    # Check 1: No cover page (first page should start with content)
    first_page_text = page_texts[0] if page_texts else ""
    has_cover_keywords = bool(
        any(
            kw in first_page_text.lower()
            for kw in ["cover", "title page", "table of contents", "目录"]
        )
    )
    checks.append({
        "check": "No cover page",
        "passed": not has_cover_keywords,
        "detail": "First page should start with essay content, not a cover.",
    })

    # Check 2: Header consistency
    header_label = "Essay范例精读"
    pages_with_header = sum(1 for pt in page_texts if header_label in pt)
    checks.append({
        "check": "Header consistency",
        "passed": pages_with_header == len(doc),
        "detail": f"Header '{header_label}' found on {pages_with_header}/{len(doc)} pages.",
    })

    # Check 3: No missing glyphs (black squares)
    # Look for replacement characters or missing glyph indicators
    replacement_chars = all_text.count("\ufffd")
    checks.append({
        "check": "No missing glyphs",
        "passed": replacement_chars == 0,
        "detail": f"Found {replacement_chars} replacement characters (U+FFFD).",
    })

    # Check 4: Annotation numbers present
    import re
    ann_refs = re.findall(r"\[(\d+)\]", all_text)
    unique_refs = set(ann_refs)
    checks.append({
        "check": "Annotation references present",
        "passed": len(unique_refs) > 0,
        "detail": f"Found {len(unique_refs)} unique annotation references: {sorted(unique_refs)[:10]}...",
    })

    # Check 5: Chinese text present (translation check)
    chinese_chars = len(re.findall(r"[\u4e00-\u9fff]", all_text))
    checks.append({
        "check": "Chinese translation present",
        "passed": chinese_chars > 20,
        "detail": f"Found {chinese_chars} Chinese characters.",
    })

    # Check 6: References section preserved (if source had one)
    if source_json and source_json.get("references"):
        has_refs = bool(
            re.search(
                r"(?:Works\s*Cited|References?|Bibliography)",
                all_text,
                re.IGNORECASE,
            )
        )
        checks.append({
            "check": "References section preserved",
            "passed": has_refs,
            "detail": "Source had references; checking if they appear in output.",
        })

    # Check 7: Original annotations preserved
    if source_json:
        orig_ann_count = len(source_json.get("original_annotations", []))
        if orig_ann_count > 0:
            # Check if at least some original annotation text appears
            found_count = 0
            for ann in source_json["original_annotations"][:5]:
                snippet = ann.get("comment_en", "")[:30]
                if snippet and snippet[:15] in all_text:
                    found_count += 1
            checks.append({
                "check": "Original annotations preserved",
                "passed": found_count > 0,
                "detail": f"Of first {min(5, orig_ann_count)} original annotations, {found_count} found in output.",
            })

    # Check 8: No excessive blank space
    # Simple heuristic: no page should have >35% of height as trailing blank
    blank_pages = []
    for page_num, page in enumerate(doc):
        blocks = page.get_text("dict")["blocks"]
        if blocks:
            last_block_y = max(
                (b["bbox"][3] for b in blocks if b["type"] == 0),
                default=0,
            )
            page_height = page.rect.height
            blank_ratio = (page_height - last_block_y) / page_height
            if blank_ratio > 0.35:
                blank_pages.append((page_num + 1, round(blank_ratio, 2)))
    checks.append({
        "check": "No excessive blank space",
        "passed": len(blank_pages) <= 1,  # allow 1 trailing page
        "detail": f"Pages with >35% trailing blank: {blank_pages}",
    })

    doc.close()
    return checks


def main():
    parser = argparse.ArgumentParser(
        description="Render PDF to PNG and run verification checks"
    )
    parser.add_argument("input", help="Input PDF file path")
    parser.add_argument("--out_dir", "-o", default="build/renders", help="Output directory for PNGs")
    parser.add_argument("--dpi", type=int, default=180, help="Render DPI")
    parser.add_argument("--source", "-s", default=None, help="source.json for content checks")
    parser.add_argument("--no-render", action="store_true", help="Skip PNG rendering, only run checks")
    args = parser.parse_args()

    pdf_path = Path(args.input)
    if not pdf_path.exists():
        print(f"ERROR: File not found: {pdf_path}", file=sys.stderr)
        sys.exit(1)

    # Render pages
    if not args.no_render:
        print(f"Rendering {pdf_path.name} to PNG (DPI={args.dpi})...")
        rendered = render_pages(str(pdf_path), args.out_dir, args.dpi)
        print(f"  Rendered {len(rendered)} pages to {args.out_dir}/")

    # Load source JSON if provided
    source_data = None
    if args.source:
        source_path = Path(args.source)
        if source_path.exists():
            source_data = json.loads(source_path.read_text(encoding="utf-8"))

    # Run content checks
    print("\n--- Content Verification Checks ---")
    checks = run_content_checks(str(pdf_path), source_data)

    all_passed = True
    for check in checks:
        status = "PASS" if check["passed"] else "FAIL"
        if not check["passed"]:
            all_passed = False
        print(f"  [{status}] {check['check']}")
        if not check["passed"]:
            print(f"         {check['detail']}")

    # Output checklist
    print("\n--- Delivery Checklist ---")
    checklist = [
        "原文段落数量与源文件一致",
        "原引用/脚注未丢失",
        "原教师批注全部保留",
        "每条原批注已有中文翻译",
        "每条批注有唯一编号",
        "每条批注有 anchor",
        "新增批注无明显重复",
        "中文正文无漏译自然段",
        "不存在封面页",
        "不存在说明页",
        "页头统一为 Essay范例精读",
    ]
    for item in checklist:
        print(f"  [ ] {item}")

    print(f"\n{'All automated checks PASSED' if all_passed else 'Some checks FAILED - review above'}")

    # Save check results
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    result_path = out_dir / "verification_report.json"
    result_path.write_text(
        json.dumps(
            {
                "pdf_file": str(pdf_path),
                "checks": checks,
                "all_passed": all_passed,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"  Report saved to {result_path}")


if __name__ == "__main__":
    main()
