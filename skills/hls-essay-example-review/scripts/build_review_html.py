#!/usr/bin/env python3
"""
Build an HTML preview of the Essay范例精读 from review_data.json.

The HTML uses the same CSS design tokens as references/layout_template.html.
Open in a browser for visual debugging before generating the final PDF.

Usage:
  python build_review_html.py review_data.json --out build/review.html
"""

import argparse
import html
import json
import re
import sys
from pathlib import Path


CSS = """
:root {
  --page-bg: #ffffff;
  --text-main: #1d1f22;
  --text-translation: #666b72;
  --annotation-text: #25282d;
  --annotation-cn: #555b63;
  --rule: #25282d;
  --translation-rule: #c5cad0;
  --annotation-underline: #55C0F4;
  --annotation-column-bg: #EEF4FF;
  --disclosure-text: #aab0b6;
  --font-en: "Arial", "Helvetica", sans-serif;
  --font-zh: "Noto Sans CJK SC", "Source Han Sans SC", "Microsoft YaHei", sans-serif;
}
body { margin: 0; padding: 20px; background: #e8e8e8; font-family: var(--font-en); }
.page {
  width: 210mm; min-height: 297mm; max-height: 297mm;
  background: var(--page-bg); margin: 12px auto; padding: 13mm 15mm;
  box-sizing: border-box; position: relative; overflow: hidden;
  box-shadow: 0 2px 12px rgba(0,0,0,0.12);
  display: flex; flex-direction: column;
}
.page-header {
  display: flex; justify-content: space-between; align-items: baseline;
  font-size: 10pt; color: var(--text-main);
  padding-bottom: 3mm; border-bottom: 0.5pt solid var(--rule);
  margin-bottom: 6mm; flex-shrink: 0;
}
.page-header .label { font-weight: 600; font-family: var(--font-zh); }
.page-header .title { flex: 1; text-align: center; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; padding: 0 8mm; }
.page-header .page-num { font-variant-numeric: tabular-nums; }
.page-body { flex: 1; display: flex; gap: 7.5mm; overflow: hidden; }
.essay-column { flex: 0 0 68%; overflow: hidden; }
.annotation-column { flex: 0 0 28%; background: var(--annotation-column-bg); padding: 0 5mm; overflow: hidden; }
.paragraph-unit { margin-bottom: 0; }
.essay-en {
  font-size: 10.5pt; line-height: 1.52; color: var(--text-main);
  margin: 0 0 3mm 0; text-align: justify;
}
.translation-zh {
  font-family: var(--font-zh); font-size: 9.3pt; line-height: 1.62;
  color: var(--text-translation); margin: 1.5mm 0 5mm 0;
  padding-left: 3.5mm; border-left: 0.8pt solid var(--translation-rule);
}
.essay-question {
  font-size: 10.2pt; font-weight: 500; margin-bottom: 6mm;
  color: var(--text-main); line-height: 1.5; padding-left: 3.5mm;
  border-left: 1.5pt solid var(--annotation-underline);
}
.essay-meta { font-size: 9.5pt; line-height: 1.6; color: var(--text-main); margin-bottom: 5mm; }
.essay-meta .meta-line { margin: 0; }
.essay-meta .meta-label { font-weight: 600; margin-right: 4px; }
.references {
  font-size: 8.5pt; line-height: 1.35; color: var(--text-main);
  margin-top: 6mm; border-top: 0.3pt solid var(--translation-rule); padding-top: 3mm;
}
.references h3 { font-size: 9pt; font-weight: 600; margin: 0 0 2mm 0; }
.annotated-text {
  text-decoration: underline; text-decoration-color: var(--annotation-underline);
  text-decoration-thickness: 0.7pt; text-underline-offset: 2px; text-decoration-skip-ink: none;
}
.annotation-ref {
  font-size: 7pt; font-weight: 600; color: var(--annotation-underline);
  vertical-align: super; margin-left: 1px; line-height: 0;
}
.annotation { margin-bottom: 5mm; }
.annotation-number { font-size: 8.5pt; font-weight: 600; color: var(--annotation-text); margin-bottom: 1mm; }
.annotation-en { font-size: 8.5pt; line-height: 1.42; color: var(--annotation-text); margin: 0 0 1.5mm 0; text-align: left; }
.annotation-zh { font-family: var(--font-zh); font-size: 8.2pt; line-height: 1.45; color: var(--annotation-cn); margin: 0; }
.disclosure { position: absolute; bottom: 4mm; left: 0; right: 0; text-align: center; font-size: 6.8pt; color: var(--disclosure-text); font-family: var(--font-zh); }
@media print { body { background: white; } .page { margin: 0; box-shadow: none; page-break-after: always; } }
"""


def insert_anchor_markers(text, annotations):
    """Insert [n] markers after anchor text in the paragraph."""
    if not annotations:
        return html.escape(text)

    # Find all anchor positions
    markers = []
    for ann in annotations:
        anchor = ann.get("anchor_text", "").strip()
        if not anchor or len(anchor) < 5:
            continue
        idx = text.lower().find(anchor.lower())
        if idx >= 0:
            end = idx + len(anchor)
            markers.append((end, ann["id"], anchor))

    markers.sort(key=lambda x: x[0])

    # Build output with markers
    result = ""
    last_pos = 0
    for pos, ann_id, anchor in markers:
        # Escape the text before the marker
        result += html.escape(text[last_pos:pos])
        # Wrap anchor text with underline span
        anchor_escaped = html.escape(text[pos - len(anchor):pos])
        result += f'<span class="annotated-text" data-annotation="{ann_id}">{anchor_escaped}</span><sup class="annotation-ref">[{ann_id}]</sup>'
        last_pos = pos

    result += html.escape(text[last_pos:])
    return result


def build_html(data):
    """Build complete HTML from review_data.json."""
    paragraphs = data.get("paragraphs", [])
    references = data.get("references", [])
    title = data.get("title", "Essay")
    total_pages = max(1, (sum(len(p.get("english", "").split()) for p in paragraphs)) // 350 + 1)

    # Collect all annotations
    all_annotations = []
    for para in paragraphs:
        for ann in para.get("annotations", []):
            all_annotations.append(ann)

    # Build pages (simple pagination: ~350 words/page)
    pages_html = []
    current_page_paras = []
    current_page_anns = []
    current_word_count = 0

    for para in paragraphs:
        en_text = para.get("english", "").strip()
        if not en_text:
            continue

        word_count = len(en_text.split())
        para_anns = para.get("annotations", [])

        if current_word_count + word_count > 350 and current_page_paras:
            pages_html.append((current_page_paras, current_page_anns))
            current_page_paras = []
            current_page_anns = []
            current_word_count = 0

        current_page_paras.append(para)
        current_page_anns.extend(para_anns)
        current_word_count += word_count

    # Last page
    if current_page_paras:
        pages_html.append((current_page_paras, current_page_anns))

    # Add references to last page
    total_pages = len(pages_html)

    # Build HTML
    html_parts = [
        "<!DOCTYPE html>",
        '<html lang="zh-CN">',
        "<head>",
        '<meta charset="UTF-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1.0">',
        f"<title>Essay范例精读 - {html.escape(title)}</title>",
        f"<style>{CSS}</style>",
        "</head>",
        "<body>",
    ]

    for page_idx, (paras, anns) in enumerate(pages_html):
        page_num = page_idx + 1
        is_first = page_idx == 0
        is_last = page_idx == total_pages - 1

        html_parts.append('<div class="page">')

        # Header
        html_parts.append('<header class="page-header">')
        html_parts.append(f'<span class="label">Essay范例精读</span>')
        html_parts.append(f'<span class="title">{html.escape(title)}</span>')
        html_parts.append(f'<span class="page-num">{page_num:02d} / {total_pages:02d}</span>')
        html_parts.append("</header>")

        # Body
        html_parts.append('<div class="page-body">')
        html_parts.append('<main class="essay-column">')

        # Metadata on first page
        if is_first:
            meta_lines = []
            if data.get("student"):
                meta_lines.append(f'<p class="meta-line"><span class="meta-label">Student:</span>{html.escape(data["student"])}</p>')
            if data.get("course"):
                meta_lines.append(f'<p class="meta-line"><span class="meta-label">Course:</span>{html.escape(data["course"])}</p>')
            if data.get("date"):
                meta_lines.append(f'<p class="meta-line"><span class="meta-label">Date:</span>{html.escape(data["date"])}</p>')
            if data.get("professor"):
                meta_lines.append(f'<p class="meta-line"><span class="meta-label">Professor:</span>{html.escape(data["professor"])}</p>')
            if meta_lines:
                html_parts.append('<div class="essay-meta">')
                html_parts.extend(meta_lines)
                html_parts.append("</div>")

            # Question
            question = data.get("question")
            if question:
                html_parts.append(f'<div class="essay-question">{html.escape(question)}</div>')

        # Paragraphs
        for para in paras:
            en_text = para.get("english", "").strip()
            cn_text = para.get("translation", "").strip()
            para_anns = para.get("annotations", [])

            html_parts.append('<div class="paragraph-unit">')

            # English with anchor markers
            en_html = insert_anchor_markers(en_text, para_anns)
            html_parts.append(f'<p class="essay-en">{en_html}</p>')

            # Chinese translation
            if cn_text:
                html_parts.append(f'<div class="translation-zh">{html.escape(cn_text)}</div>')

            html_parts.append("</div>")

        # References on last page
        if is_last and references:
            html_parts.append('<div class="references">')
            ref_title = "Works Cited" if data.get("references_title") == "Works Cited" else "References"
            html_parts.append(f"<h3>{ref_title}</h3>")
            for ref in references:
                ref_text = ref if isinstance(ref, str) else ref.get("text", "")
                html_parts.append(f"<p>{html.escape(ref_text)}</p>")
            html_parts.append("</div>")

        html_parts.append("</main>")  # essay-column

        # Right column: annotations
        html_parts.append('<aside class="annotation-column">')
        for ann in anns:
            ann_id = ann["id"]
            ann_en = html.escape(ann.get("comment_en", ""))
            ann_zh = html.escape(ann.get("comment_zh", ""))
            html_parts.append(f'<div class="annotation" data-anchor="{ann_id}">')
            html_parts.append(f'<div class="annotation-number">[{ann_id}]</div>')
            html_parts.append(f'<div class="annotation-en">{ann_en}</div>')
            if ann_zh:
                html_parts.append(f'<div class="annotation-zh">{ann_zh}</div>')
            html_parts.append("</div>")
        html_parts.append("</aside>")

        html_parts.append("</div>")  # page-body

        # Disclosure
        html_parts.append('<div class="disclosure">右栏含原始评语与补充写作解析。</div>')

        html_parts.append("</div>")  # page

    html_parts.extend(["</body>", "</html>"])
    return "\n".join(html_parts)


def main():
    parser = argparse.ArgumentParser(description="Build HTML preview of Essay范例精读")
    parser.add_argument("input", help="review_data.json path")
    parser.add_argument("--out", "-o", default="build/review.html", help="Output HTML path")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"ERROR: File not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    data = json.loads(input_path.read_text(encoding="utf-8"))
    html_content = build_html(data)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html_content, encoding="utf-8")

    print(f"OK: HTML saved to {out_path}")
    paragraphs = data.get("paragraphs", [])
    total_anns = sum(len(p.get("annotations", [])) for p in paragraphs)
    print(f"  Paragraphs: {len(paragraphs)}")
    print(f"  Annotations: {total_anns}")


if __name__ == "__main__":
    main()
