#!/usr/bin/env python3
"""
Extract text, metadata, and annotations from an Essay PDF.

Outputs source.json with:
  - title, course, student, date, question
  - paragraphs[] (ordered, cleaned)
  - references[] (Works Cited / Reference List)
  - original_annotations[] (PDF comments with anchor text)

Usage:
  python extract_pdf.py input.pdf --out source.json [--dpi 150]

Works with PyMuPDF (pymupdf). Falls back to page.get_text() if no
text layer is found, and warns about OCR requirement.
"""

import argparse
import json
import re
import sys
from pathlib import Path

try:
    import pymupdf  # PyMuPDF 1.28+
except ImportError:
    try:
        import fitz as pymupdf  # legacy import name
    except ImportError:
        print("ERROR: PyMuPDF not installed. Run: pip install PyMuPDF", file=sys.stderr)
        sys.exit(1)


# --- Metadata heuristics ---

META_PATTERNS = {
    "student": [
        r"(?:Student|Author|Name)\s*[:\uff1a]?\s*(.+)",
        r"(?:By|by)\s+(.+)",  # "By John Smith"
    ],
    "course": [
        r"(?:Course|Class|Module)\s*[:\uff1a]?\s*(.+)",
        r"\b([A-Z]{2,4}\s?\d{2,4}[A-Z]?)\b",  # "ENG 101", "M02"
    ],
    "date": [
        r"(\d{1,2}\s+(?:January|February|March|April|May|June|July|"
        r"August|September|October|November|December)\s+\d{4})",
        r"((?:January|February|March|April|May|June|July|"
        r"August|September|October|November|December)\s+\d{1,2},?\s+\d{4})",
    ],
    "professor": [
        r"(?:Professor|Instructor|Teacher|Tutor)\s*[:\uff1a]?\s*(.+)",
    ],
}

COMMENT_PREFIX_RE = re.compile(
    r"^(?:Comment(?:ed)?\s*\[?\w*\]?\s*[:\uff1a]\s*|"
    r"\[?(?:w|W|A|a|Comment)\d*\]?\s*[:\uff1a]\s*)",
    re.IGNORECASE,
)


def extract_metadata(first_page_text, all_text):
    """Try to extract essay metadata from the first page or full text."""
    meta = {
        "title": None,
        "course": None,
        "student": None,
        "professor": None,
        "date": None,
        "question": None,
    }

    lines = [l.strip() for l in first_page_text.split("\n") if l.strip()]

    # Title: usually first non-empty line that isn't a name/course/date
    for line in lines[:8]:
        if not any(
            re.match(p, line, re.IGNORECASE)
            for patterns in META_PATTERNS.values()
            for p in patterns
        ):
            # Skip short header-like lines
            if len(line) > 5 and not line.isupper():
                meta["title"] = line
                break

    for key, patterns in META_PATTERNS.items():
        for pat in patterns:
            for line in lines[:15]:
                m = re.search(pat, line, re.IGNORECASE)
                if m:
                    val = m.group(1).strip().rstrip(".,")
                    if val and len(val) < 120:
                        meta[key] = val
                        break
            if meta[key]:
                break

    return meta


def detect_regions(page_rect, blocks):
    """
    Detect main text region vs annotation region based on x-coordinates.

    Returns (main_x_threshold, annotation_x_start).
    If text is single-column (no right-margin annotations), returns (page_rect.width, 0).
    """
    if not blocks:
        return page_rect.width * 0.85, page_rect.width * 0.85

    # Group blocks by x-position to detect column split
    x_starts = [b["bbox"][0] for b in blocks]
    if not x_starts:
        return page_rect.width * 0.85, page_rect.width * 0.85

    page_width = page_rect.width
    right_half_start = page_width * 0.55

    right_blocks = [b for b in blocks if b["bbox"][0] >= right_half_start]
    left_blocks = [b for b in blocks if b["bbox"][0] < right_half_start]

    # If <15% of blocks are on the right, treat as single-column
    if len(right_blocks) < len(blocks) * 0.15 or len(right_blocks) == 0:
        return page_width * 0.85, page_width * 0.85

    # Find the gap between left and right columns
    left_max_x = max(b["bbox"][2] for b in left_blocks) if left_blocks else right_half_start
    right_min_x = min(b["bbox"][0] for b in right_blocks)

    threshold = (left_max_x + right_min_x) / 2 if right_min_x > left_max_x else page_width * 0.65

    return threshold, right_min_x


def clean_comment_text(text):
    """Remove software prefixes like 'Comment [w3]:' from annotation text."""
    return COMMENT_PREFIX_RE.sub("", text).strip()


def extract_annotations(doc):
    """
    Extract PDF annotations (comments, highlights, etc.) from all pages.

    Returns list of annotation dicts with:
      id, source="original", source_page, anchor_text, comment_en,
      comment_zh (empty, to be filled), anchor_confidence
    """
    annotations = []
    ann_id_counter = 0

    for page_num in range(len(doc)):
        page = doc[page_num]

        # Method 1: Extract PDF annotation objects (proper comments)
        for annot in page.annots() or []:
            info = annot.info
            annot_type = annot.type  # tuple (type_id, type_name)

            comment_text = ""
            if info.get("content"):
                comment_text = clean_comment_text(info["content"])

            if not comment_text:
                continue

            # Get the anchored text (text within the annotation's rectangle)
            rect = annot.rect
            anchor_text = ""

            # Try to get text within the annotation rectangle
            try:
                anchor_text = page.get_textbox(rect, sort=True).strip()
            except Exception:
                pass

            # If no direct anchor text, try nearby text
            if not anchor_text:
                # Expand the rect slightly to catch adjacent text
                expanded = pymupdf.Rect(
                    rect.x0 - 5, rect.y0 - 5,
                    min(rect.x1 + 50, page.rect.width - 5), rect.y1 + 5
                )
                try:
                    anchor_text = page.get_textbox(expanded, sort=True).strip()
                except Exception:
                    pass

            ann_id_counter += 1
            annotations.append({
                "id": f"o{ann_id_counter}",
                "source": "original",
                "source_page": page_num + 1,
                "anchor_text": anchor_text[:500] if anchor_text else "",
                "comment_en": comment_text,
                "comment_zh": "",  # To be filled by translation step
                "anchor_confidence": 0.90 if anchor_text else 0.40,
                "annot_type": annot_type[1] if annot_type else "Comment",
                "rect": [rect.x0, rect.y0, rect.x1, rect.y1],
            })

    # Method 2: Look for inline comment text (Word-style comments baked into text)
    # These appear as "Comment [w3]: ..." in the text flow
    full_text_parts = []
    for page_num in range(len(doc)):
        page = doc[page_num]
        blocks = page.get_text("dict", sort=True)["blocks"]

        threshold, ann_x_start = detect_regions(page.rect, blocks)

        for block in blocks:
            if block["type"] != 0:  # text block
                continue

            block_x = block["bbox"][0]
            # If block is in the annotation region (right side)
            if block_x >= threshold:
                for line in block.get("lines", []):
                    line_text = ""
                    for span in line.get("spans", []):
                        line_text += span.get("text", "")
                    line_text = line_text.strip()
                    if not line_text:
                        continue

                    # Check if this line looks like a comment
                    if COMMENT_PREFIX_RE.match(line_text):
                        comment_text = clean_comment_text(line_text)
                        if comment_text and len(comment_text) > 3:
                            ann_id_counter += 1
                            annotations.append({
                                "id": f"o{ann_id_counter}",
                                "source": "original",
                                "source_page": page_num + 1,
                                "anchor_text": "",  # Will need semantic matching
                                "comment_en": comment_text,
                                "comment_zh": "",
                                "anchor_confidence": 0.30,
                                "annot_type": "InlineComment",
                                "rect": None,
                            })

    return annotations


def extract_paragraphs(doc):
    """
    Extract essay body paragraphs from the PDF.

    Uses coordinate-based region detection to separate main text from
    annotation column, then reconstructs logical paragraph flow.
    """
    paragraphs = []
    references = []
    in_references = False

    for page_num in range(len(doc)):
        page = doc[page_num]
        blocks_data = page.get_text("dict", sort=True)
        blocks = blocks_data.get("blocks", [])

        threshold, ann_x_start = detect_regions(page.rect, blocks)

        # Also detect and skip headers/footers (very short lines at top/bottom)
        page_height = page.rect.height
        header_y_max = page_height * 0.05  # top 5%
        footer_y_min = page_height * 0.95  # bottom 5%

        for block in blocks:
            if block["type"] != 0:
                continue

            bbox = block["bbox"]
            block_x = bbox[0]
            block_y = bbox[1]

            # Skip annotation region
            if block_x >= threshold:
                continue

            # Skip headers/footers
            if block_y < header_y_max or block_y > footer_y_min:
                continue

            # Extract text from this block
            block_text = ""
            for line in block.get("lines", []):
                line_text = ""
                for span in line.get("spans", []):
                    line_text += span.get("text", "")
                if line_text.strip():
                    block_text += line_text.strip() + " "
                else:
                    block_text += "\n"

            block_text = block_text.strip()
            if not block_text or len(block_text) < 10:
                continue

            # Detect References / Works Cited section
            if re.match(
                r"^(?:Works\s*Cited|References?|Bibliography|Reference\s*List)\b",
                block_text,
                re.IGNORECASE,
            ):
                in_references = True

            if in_references:
                references.append({
                    "text": block_text,
                    "page": page_num + 1,
                })
            else:
                paragraphs.append({
                    "text": block_text,
                    "page": page_num + 1,
                    "bbox": [bbox[0], bbox[1], bbox[2], bbox[3]],
                })

    return paragraphs, references


def detect_annotation_mode(annotations, paragraphs):
    """Determine if the essay is Mode A (well-annotated), B (sparse), or C (none)."""
    if not annotations:
        return "C"

    # Count total words in paragraphs
    total_words = sum(len(p["text"].split()) for p in paragraphs)
    if total_words == 0:
        return "C"

    # Annotations per 150-250 words
    ratio = len(annotations) / (total_words / 200)  # annotations per 200 words

    if ratio >= 1.0:
        return "A"
    elif ratio >= 0.3:
        return "B"
    else:
        return "B" if annotations else "C"


def main():
    parser = argparse.ArgumentParser(
        description="Extract text and annotations from an Essay PDF"
    )
    parser.add_argument("input", help="Input PDF file path")
    parser.add_argument("--out", "-o", default="source.json", help="Output JSON path")
    parser.add_argument("--dpi", type=int, default=150, help="DPI for image rendering if needed")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"ERROR: File not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    # Handle non-PDF inputs
    if input_path.suffix.lower() not in (".pdf",):
        print(f"INFO: Non-PDF input ({input_path.suffix}). Reading as text.")
        text = input_path.read_text(encoding="utf-8", errors="replace")
        # Simple paragraph split for text files
        paras = [p.strip() for p in text.split("\n\n") if p.strip()]
        paragraphs = [{"text": p, "page": 1, "bbox": None} for p in paras]
        meta = extract_metadata(text, text)
        result = {
            **meta,
            "paragraphs": paragraphs,
            "references": [],
            "original_annotations": [],
            "annotation_mode": "C",
            "source_file": str(input_path),
            "source_type": input_path.suffix.lstrip("."),
        }
        Path(args.out).write_text(
            json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"OK: Extracted {len(paragraphs)} paragraphs -> {args.out}")
        return

    # Open PDF
    doc = pymupdf.open(str(input_path))

    # Check if it has a text layer
    first_page_text = doc[0].get_text()
    if len(first_page_text.strip()) < 50:
        print(
            "WARNING: This PDF appears to have no text layer (possibly scanned). "
            "OCR is required. PyMuPDF does not do OCR. "
            "Please run OCR (e.g., Tesseract) first and provide the text-based PDF.",
            file=sys.stderr,
        )

    # Extract metadata from first page
    first_page_full_text = ""
    for page_num in range(min(3, len(doc))):
        first_page_full_text += doc[page_num].get_text() + "\n"

    meta = extract_metadata(doc[0].get_text(), first_page_full_text)

    # Extract paragraphs and references
    paragraphs, references = extract_paragraphs(doc)

    # Extract annotations
    annotations = extract_annotations(doc)

    # Detect annotation mode
    mode = detect_annotation_mode(annotations, paragraphs)

    result = {
        **meta,
        "paragraphs": paragraphs,
        "references": references,
        "original_annotations": annotations,
        "annotation_mode": mode,
        "source_file": str(input_path),
        "source_type": "pdf",
        "page_count": len(doc),
    }

    Path(args.out).write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"OK: Extracted from {input_path.name}")
    print(f"  Title:     {meta.get('title', '(unknown)')}")
    print(f"  Student:   {meta.get('student', '(unknown)')}")
    print(f"  Paragraphs: {len(paragraphs)}")
    print(f"  References: {len(references)}")
    print(f"  Annotations: {len(annotations)} (Mode {mode})")


if __name__ == "__main__":
    main()
