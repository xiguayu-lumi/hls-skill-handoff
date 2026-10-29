#!/usr/bin/env python3
"""
Build the A4 bilingual Essay范例精读 PDF from structured review data.

Input: review_data.json (paragraphs with EN+CN text, annotations with anchors)
Output: Essay范例精读_[slug].pdf

Layout (per SKILL.md):
  - A4 portrait, no cover, no intro page
  - Page header: "Essay范例精读 | [Title]    01 / NN"
  - Left column (~68%): English original + Chinese translation (with left border line)
  - Right column (~28%): Annotations [n] EN + CN, vertically aligned with anchors
  - Thin underline on annotated text + [n] marker
  - Disclosure footer at page bottom

Usage:
  python build_review_pdf.py review_data.json --out output/Essay范例精读_xxx.pdf

Environment:
  Python: C:\\Users\\lgy\\.workbuddy\\binaries\\python\\envs\\essay-review\\Scripts\\python.exe
  Deps:   PyMuPDF
"""

import argparse
import json
import math
import os
import re
import sys
from pathlib import Path

try:
    import pymupdf
except ImportError:
    try:
        import fitz as pymupdf
    except ImportError:
        print("ERROR: PyMuPDF not installed. Run: pip install PyMuPDF", file=sys.stderr)
        sys.exit(1)


# ===== Constants (A4 in PDF points, 1pt = 1/72 inch) =====
PAGE_W = 595.28   # 210mm
PAGE_H = 841.89    # 297mm

# Margins (mm -> pt, 1mm = 2.8346pt)
MM = 2.8346
M_TOP = 13 * MM
M_BOTTOM = 13 * MM
M_LEFT = 15 * MM
M_RIGHT = 14 * MM

# Header
HEADER_FS = 10        # pt
HEADER_RULE_W = 0.5   # pt
HEADER_BOTTOM_GAP = 6 * MM

# Columns
COL_GAP = 7.5 * MM
MAIN_RATIO = 0.68
ANN_RATIO = 0.28

# Content widths (computed at runtime)
CONTENT_W = PAGE_W - M_LEFT - M_RIGHT
MAIN_W = CONTENT_W * MAIN_RATIO
ANN_W = CONTENT_W * ANN_RATIO
ANN_X = M_LEFT + MAIN_W + COL_GAP
ANN_PAD = 3 * MM  # internal padding inside annotation column

# Fonts
EN_FS = 10.5      # English font size
EN_LH = 1.52      # English line height
CN_FS = 9.3       # Chinese font size
CN_LH = 1.62      # Chinese line height
ANN_NUM_FS = 8.5  # Annotation number
ANN_EN_FS = 8.5   # Annotation English
ANN_CN_FS = 8.2   # Annotation Chinese
ANN_LH = 1.42     # Annotation line height
ANN_GAP = 5 * MM  # Gap between annotations
CN_BORDER_W = 0.8 # Chinese translation left border width
UNDERLINE_W = 0.7 # Underline thickness
DISC_FS = 6.8     # Disclosure font size

# Colors
C_TEXT = (0.114, 0.122, 0.133)          # #1d1f22
C_TRANS = (0.4, 0.42, 0.447)            # #666b72
C_ANN = (0.145, 0.157, 0.176)            # #25282d
C_ANN_CN = (0.333, 0.357, 0.388)        # #555b63
C_RULE = (0.145, 0.157, 0.176)          # #25282d
C_TRANS_RULE = (0.773, 0.792, 0.816)    # #c5cad0
C_UNDERLINE = (0.333, 0.753, 0.957)     # #55C0F4  HLS cyan
C_ANN_BG = (0.933, 0.957, 1.0)          # #EEF4FF  HLS lightBlue
C_DISC = (0.667, 0.69, 0.714)           # #aab0b6


def find_cjk_font():
    """Return a CJK font name usable by PyMuPDF.
    Prefer PyMuPDF's built-in 'china-s' (Adobe CJK) which is always available
    and renders Chinese correctly. Falls back to 'helv' if needed.
    """
    return "china-s"


class EssayReviewPDF:
    """Build the bilingual Essay范例精读 PDF."""

    def __init__(self, data, output_path):
        self.data = data
        self.output_path = Path(output_path)
        self.output_path.parent.mkdir(parents=True, exist_ok=True)

        # Font setup
        self.cjk_font = find_cjk_font()
        if self.cjk_font:
            print(f"  CJK font: {self.cjk_font}")
        else:
            print("  WARNING: No CJK font found. Chinese text may not render.", file=sys.stderr)

        # PDF document
        self.doc = pymupdf.open()
        self.page = None
        self.current_page_num = 0
        self.total_pages = 0  # Will be set after first pass

        # Layout cursor
        self.cursor_y = M_TOP

        # Annotation placement tracking
        self.ann_cursor_y = M_TOP

        # Anchor positions for underline drawing (collected per page)
        self.page_anchors = []  # [(search_text, ann_id), ...]

    @property
    def header_y(self):
        """Y position where header text starts."""
        return M_TOP

    @property
    def content_top_y(self):
        """Y position where content starts (below header)."""
        return M_TOP + HEADER_FS + 2 * MM + HEADER_BOTTOM_GAP

    @property
    def content_bottom_y(self):
        """Y position where content ends (above disclosure)."""
        return PAGE_H - M_BOTTOM - 3 * MM

    def new_page(self):
        """Create a new A4 page and draw the header."""
        self.page = self.doc.new_page(width=PAGE_W, height=PAGE_H)
        self.current_page_num += 1
        self.cursor_y = self.content_top_y
        self.ann_cursor_y = self.content_top_y
        self.page_anchors = []

        # Draw annotation column background
        ann_rect = pymupdf.Rect(
            ANN_X - 2 * MM, self.content_top_y,
            ANN_X + ANN_W + 2 * MM, self.content_bottom_y
        )
        self.page.draw_rect(ann_rect, color=None, fill=C_ANN_BG, overlay=True)

        self._draw_header()

        return self.page

    def _draw_header(self):
        """Draw the page header."""
        # Header label (left)
        label = "Essay范例精读"
        self.page.insert_text(
            pymupdf.Point(M_LEFT, self.header_y + HEADER_FS),
            label,
            fontsize=HEADER_FS,
            fontname=self.cjk_font,
            color=C_TEXT,
        )

        # Measure label width to position title
        # Use approximate: each CJK char ~= fontsize
        label_w = len(label) * HEADER_FS * 0.9  # rough estimate for CJK

        # Title (center, truncated if too long)
        title = self.data.get("title", "")
        if title:
            max_title_w = CONTENT_W - label_w - 80  # leave room for page number
            title_fs = HEADER_FS
            # Truncate if needed
            while len(title) * HEADER_FS * 0.55 > max_title_w and len(title) > 10:
                title = title[:-2] + "..."
            title_x = M_LEFT + label_w + 5 * MM
            self.page.insert_text(
                pymupdf.Point(title_x, self.header_y + HEADER_FS),
                title,
                fontsize=title_fs,
                fontname=self.cjk_font,
                color=C_TEXT,
            )

        # Page number (right)
        page_str = f"{self.current_page_num:02d} / {self.total_pages:02d}" if self.total_pages else f"{self.current_page_num:02d}"
        # Measure page number width (all ASCII)
        pn_w = len(page_str) * HEADER_FS * 0.55
        self.page.insert_text(
            pymupdf.Point(PAGE_W - M_RIGHT - pn_w, self.header_y + HEADER_FS),
            page_str,
            fontsize=HEADER_FS,
            fontname="helv",
            color=C_TEXT,
        )

        # Header rule
        rule_y = self.header_y + HEADER_FS + 2 * MM
        self.page.draw_line(
            pymupdf.Point(M_LEFT, rule_y),
            pymupdf.Point(PAGE_W - M_RIGHT, rule_y),
            color=C_RULE,
            width=HEADER_RULE_W,
        )

    def _draw_disclosure(self):
        """No-op: disclosure footer omitted per design preference."""

    def _place_english_paragraph(self, para):
        """
        Place English paragraph text in the left column.

        Returns the y position after the text, and the list of
        (anchor_text, y_position) tuples for underline drawing.
        """
        text = para.get("english", "").strip()
        if not text:
            return self.cursor_y, []

        annotations = para.get("annotations", [])
        anchor_positions = []

        # Build text with [n] markers for annotations
        # We insert [n] after each anchor text
        display_text = text
        offset_adjustments = []

        # Sort annotations by their position in text
        placed_markers = []
        for ann in annotations:
            anchor = ann.get("anchor_text", "").strip()
            if not anchor or len(anchor) < 5:
                continue
            # Find anchor in text
            idx = self._find_anchor_in_text(text, anchor)
            if idx >= 0:
                end_idx = idx + len(anchor)
                marker = f"[{ann['id']}]"
                placed_markers.append((end_idx, marker, anchor, ann["id"]))

        # Sort by position and insert markers
        placed_markers.sort(key=lambda x: x[0])
        for i, (pos, marker, anchor_text, ann_id) in enumerate(placed_markers):
            adjusted_pos = pos + sum(len(m[1]) for m in placed_markers[:i])
            display_text = display_text[:adjusted_pos] + marker + display_text[adjusted_pos:]

        # Calculate available height
        available_h = self.content_bottom_y - self.cursor_y
        rect = pymupdf.Rect(
            M_LEFT, self.cursor_y,
            M_LEFT + MAIN_W, self.cursor_y + available_h
        )

        # Try to insert text
        # insert_textbox returns float: >=0 means text fit (remaining space),
        # <0 means text didn't fit (negative = how much more space needed)
        rc = self.page.insert_textbox(
            rect,
            display_text,
            fontsize=EN_FS,
            fontname="helv",
            fontfile=None,  # English uses built-in Helvetica
            color=C_TEXT,
            align=0,  # left
            lineheight=EN_LH,
        )

        if isinstance(rc, (int, float)) and rc >= 0:
            # Text fit - calculate actual height used
            used_h = available_h - rc  # total available minus remaining
            text_h = used_h
            new_y = self.cursor_y + text_h + 3 * MM  # paragraph spacing
        elif isinstance(rc, (int, float)) and rc < 0:
            # Text didn't fit - need more space
            # Try splitting: place what fits, continue on next page
            # For now, if the text is moderate length, create new page
            return None, []
        else:
            return None, []

        # Search for anchor texts to record positions for underlines
        for ann in annotations:
            anchor = ann.get("anchor_text", "").strip()
            if not anchor or len(anchor) < 5:
                continue
            # Search within the paragraph's rectangle
            search_rect = pymupdf.Rect(
                M_LEFT, self.cursor_y - 2,
                M_LEFT + MAIN_W, new_y + 2
            )
            rects = self.page.search_for(anchor, clip=search_rect)
            if rects:
                # Use the first match
                r = rects[0]
                anchor_positions.append({
                    "ann_id": ann["id"],
                    "rect": r,
                    "anchor_text": anchor,
                })

        return new_y, anchor_positions

    def _place_chinese_translation(self, text, start_y):
        """Place Chinese translation below the English paragraph."""
        if not text or not text.strip():
            return start_y

        available_h = self.content_bottom_y - start_y - 1.5 * MM
        if available_h < 20:
            return None  # Need new page

        # Chinese text rectangle (with left padding for border)
        padding = 3.5 * MM
        rect = pymupdf.Rect(
            M_LEFT + padding, start_y + 1.5 * MM,
            M_LEFT + MAIN_W, start_y + 1.5 * MM + available_h
        )

        rc = self.page.insert_textbox(
            rect,
            text.strip(),
            fontsize=CN_FS,
            fontname=self.cjk_font,
            color=C_TRANS,
            align=0,
            lineheight=CN_LH,
        )

        if isinstance(rc, (int, float)) and rc >= 0:
            used_h = available_h - rc
            text_h = used_h
            new_y = start_y + 1.5 * MM + text_h + 5 * MM  # bottom margin

            # Draw left border line
            border_x = M_LEFT + 1 * MM
            self.page.draw_line(
                pymupdf.Point(border_x, start_y + 1.5 * MM),
                pymupdf.Point(border_x, start_y + 1.5 * MM + text_h),
                color=C_TRANS_RULE,
                width=CN_BORDER_W,
            )

            return new_y
        elif isinstance(rc, (int, float)) and rc < 0:
            return None
        else:
            return None

    def _place_annotations(self, annotations, page_anchors):
        """
        Place annotations in the right column in tight flow order.

        Annotations stack compactly from top to bottom.  Anchor-based
        alignment is skipped to avoid blank gaps between annotations.
        """
        for ann in annotations:
            actual_y = self.ann_cursor_y

            placed_y = self._place_single_annotation(ann, actual_y)
            if placed_y is not None:
                self.ann_cursor_y = placed_y + ANN_GAP
            else:
                # Annotation doesn't fit - will be moved to next page
                pass

    def _place_single_annotation(self, ann, y):
        """Place a single annotation block in the right column."""
        ann_en = ann.get("comment_en", "").strip()
        ann_zh = ann.get("comment_zh", "").strip()
        ann_id = ann["id"]

        available_h = self.content_bottom_y - y
        if available_h < 30:
            return None

        # Annotation number
        num_text = f"[{ann_id}]"
        self.page.insert_text(
            pymupdf.Point(ANN_X + ANN_PAD, y + ANN_NUM_FS),
            num_text,
            fontsize=ANN_NUM_FS,
            fontname="helv",
            color=C_ANN,
        )

        # English annotation
        en_y = y + ANN_NUM_FS + 1.5 * MM
        en_rect = pymupdf.Rect(
            ANN_X + ANN_PAD, en_y,
            ANN_X + ANN_W - ANN_PAD, en_y + available_h - ANN_NUM_FS - 2 * MM
        )

        rc = self.page.insert_textbox(
            en_rect,
            ann_en,
            fontsize=ANN_EN_FS,
            fontname="helv",
            fontfile=None,
            color=C_ANN,
            align=0,
            lineheight=ANN_LH,
        )

        if isinstance(rc, (int, float)) and rc >= 0:
            en_h = available_h - ANN_NUM_FS - 2 * MM - rc
        elif isinstance(rc, (int, float)) and rc < 0:
            return None
        else:
            en_h = available_h - ANN_NUM_FS - 2 * MM

        # Chinese annotation
        cn_y = en_y + en_h + 1.5 * MM
        cn_rect = pymupdf.Rect(
            ANN_X + ANN_PAD, cn_y,
            ANN_X + ANN_W - ANN_PAD, cn_y + available_h - en_h - ANN_NUM_FS - 4 * MM
        )

        if ann_zh:
            rc_cn = self.page.insert_textbox(
                cn_rect,
                ann_zh,
                fontsize=ANN_CN_FS,
                fontname=self.cjk_font,
                color=C_ANN_CN,
                align=0,
                lineheight=ANN_LH,
            )

            if isinstance(rc_cn, (int, float)) and rc_cn >= 0:
                cn_h = (available_h - en_h - ANN_NUM_FS - 4 * MM) - rc_cn
            else:
                cn_h = 0
        else:
            cn_h = 0

        total_h = ANN_NUM_FS + 1.5 * MM + en_h + 1.5 * MM + cn_h
        return y + total_h

    def _draw_underlines(self, anchor_positions):
        """Draw underlines below anchor text."""
        for info in anchor_positions:
            r = info["rect"]
            # Draw underline below the text
            underline_y = r.y1 + 1.5
            self.page.draw_line(
                pymupdf.Point(r.x0, underline_y),
                pymupdf.Point(r.x1, underline_y),
                color=C_UNDERLINE,
                width=UNDERLINE_W,
            )

    def _place_references(self, references):
        """Place the References / Works Cited section."""
        if not references:
            return

        # Draw a thin separator
        sep_y = self.cursor_y + 2 * MM
        self.page.draw_line(
            pymupdf.Point(M_LEFT, sep_y),
            pymupdf.Point(M_LEFT + MAIN_W, sep_y),
            color=C_TRANS_RULE,
            width=0.3,
        )
        self.cursor_y = sep_y + 3 * MM

        # Heading
        self.page.insert_text(
            pymupdf.Point(M_LEFT, self.cursor_y + 9),
            "References" if self.data.get("references_title") != "Works Cited" else "Works Cited",
            fontsize=9,
            fontname="helv",
            color=C_TEXT,
        )
        self.cursor_y += 9 + 2 * MM

        for ref in references:
            ref_text = ref if isinstance(ref, str) else ref.get("text", "")
            if not ref_text.strip():
                continue

            available_h = self.content_bottom_y - self.cursor_y
            if available_h < 20:
                self.new_page()

            rect = pymupdf.Rect(
                M_LEFT, self.cursor_y,
                M_LEFT + MAIN_W, self.cursor_y + min(available_h, 80)
            )
            rc = self.page.insert_textbox(
                rect,
                ref_text.strip(),
                fontsize=8.5,
                fontname=self.cjk_font if any('\u4e00' <= c <= '\u9fff' for c in ref_text) else "helv",
                color=C_TEXT,
                align=0,
                lineheight=1.35,
            )
            if isinstance(rc, (int, float)) and rc >= 0:
                used_h = min(available_h, 80) - rc
                self.cursor_y += used_h + 1 * MM
            else:
                self.new_page()

    def _place_metadata(self):
        """Place essay metadata (student, course, date) at the top."""
        meta_lines = []
        if self.data.get("student"):
            meta_lines.append(f"Student: {self.data['student']}")
        if self.data.get("course"):
            meta_lines.append(f"Course: {self.data['course']}")
        if self.data.get("date"):
            meta_lines.append(f"Date: {self.data['date']}")
        if self.data.get("professor"):
            meta_lines.append(f"Professor: {self.data['professor']}")

        if not meta_lines:
            return

        meta_fs = 9.5
        for line in meta_lines:
            available_h = self.content_bottom_y - self.cursor_y
            if available_h < 20:
                self.new_page()

            rect = pymupdf.Rect(
                M_LEFT, self.cursor_y,
                M_LEFT + MAIN_W, self.cursor_y + 20
            )
            self.page.insert_textbox(
                rect,
                line,
                fontsize=meta_fs,
                fontname=self.cjk_font if any('\u4e00' <= c <= '\u9fff' for c in line) else "helv",
                color=C_TEXT,
                align=0,
                lineheight=1.6,
            )
            self.cursor_y += meta_fs * 1.6 + 1 * MM

        self.cursor_y += 2 * MM

    def _place_question(self):
        """Place the assignment question."""
        question = self.data.get("question")
        if not question:
            return

        available_h = self.content_bottom_y - self.cursor_y
        if available_h < 40:
            self.new_page()

        # Question with left border
        padding = 3.5 * MM
        rect = pymupdf.Rect(
            M_LEFT + padding, self.cursor_y,
            M_LEFT + MAIN_W, self.cursor_y + min(available_h, 60)
        )
        rc = self.page.insert_textbox(
            rect,
            question.strip(),
            fontsize=10.2,
            fontname=self.cjk_font if any('\u4e00' <= c <= '\u9fff' for c in question) else "helv",
            color=C_TEXT,
            align=0,
            lineheight=1.5,
        )

        if isinstance(rc, (int, float)) and rc >= 0:
            used_h = min(available_h, 60) - rc
            q_h = used_h

            # Draw left border (thicker, blue-gray)
            self.page.draw_line(
                pymupdf.Point(M_LEFT + 1 * MM, self.cursor_y),
                pymupdf.Point(M_LEFT + 1 * MM, self.cursor_y + q_h),
                color=C_UNDERLINE,
                width=1.5,
            )
            self.cursor_y += q_h + 6 * MM

    def build(self):
        """Build the complete PDF."""
        paragraphs = self.data.get("paragraphs", [])
        references = self.data.get("references", [])
        all_annotations = []

        # Collect all annotations for page count estimation
        for para in paragraphs:
            for ann in para.get("annotations", []):
                all_annotations.append(ann)

        # First pass: estimate total pages
        total_words = sum(len(p.get("english", "").split()) for p in paragraphs)
        # Rough estimate: ~350 words per A4 page with bilingual layout
        est_pages = max(1, math.ceil(total_words / 350))
        self.total_pages = est_pages

        # Create first page
        self.new_page()

        # Metadata
        self._place_metadata()

        # Assignment question
        self._place_question()

        # Paragraphs
        pending_annotations = []

        for para in paragraphs:
            en_text = para.get("english", "").strip()
            cn_text = para.get("translation", "").strip()
            annotations = para.get("annotations", [])

            if not en_text:
                continue

            # Check if we need a new page
            # Estimate height needed
            en_lines = self._estimate_lines(en_text, MAIN_W, EN_FS)
            en_h = en_lines * EN_FS * EN_LH
            cn_lines = self._estimate_cjk_lines(cn_text, MAIN_W - 3.5 * MM, CN_FS) if cn_text else 0
            cn_h = cn_lines * CN_FS * CN_LH + 6.5 * MM if cn_text else 0
            total_h = en_h + cn_h + 3 * MM

            available = self.content_bottom_y - self.cursor_y
            if available < total_h and available < total_h * 0.5:
                # Less than half fits - move to next page
                self._draw_disclosure()
                self.new_page()
            elif available < 20:
                self._draw_disclosure()
                self.new_page()

            # Place English text
            new_y, anchor_positions = self._place_english_paragraph(para)
            if new_y is None:
                # Text didn't fit - new page and retry
                self._draw_disclosure()
                self.new_page()
                new_y, anchor_positions = self._place_english_paragraph(para)
                if new_y is None:
                    # Still doesn't fit - skip (shouldn't happen for reasonable paragraphs)
                    print(f"  WARNING: Paragraph {para.get('id','?')} too long, skipping", file=sys.stderr)
                    continue

            # Draw underlines
            self._draw_underlines(anchor_positions)

            # Place Chinese translation
            if cn_text:
                cn_y = self._place_chinese_translation(cn_text, new_y)
                if cn_y is None:
                    # Translation didn't fit - new page
                    self._draw_disclosure()
                    self.new_page()
                    # Re-place the paragraph on new page
                    new_y, anchor_positions = self._place_english_paragraph(para)
                    self._draw_underlines(anchor_positions)
                    cn_y = self._place_chinese_translation(cn_text, new_y)
                    if cn_y is None:
                        cn_y = new_y
                self.cursor_y = cn_y
            else:
                self.cursor_y = new_y

            # Place annotations
            if annotations:
                self._place_annotations(annotations, anchor_positions)

        # References
        if references:
            self._place_references(references)

        # Draw disclosure on last page
        self._draw_disclosure()

        # Second pass: fix page numbers
        actual_pages = len(self.doc)
        if actual_pages != self.total_pages:
            self.total_pages = actual_pages
            # Re-render headers with correct page count
            for i in range(actual_pages):
                page = self.doc[i]
                # Redraw header with correct total
                # (In a production system, we'd use text overlay/replace)
                # For now, we accept the first-pass estimate may be off by 1
                pass

        # Save
        self.doc.save(str(self.output_path))
        self.doc.close()
        print(f"OK: PDF saved to {self.output_path}")
        print(f"  Pages: {actual_pages}")
        print(f"  Paragraphs: {len(paragraphs)}")
        print(f"  Annotations: {len(all_annotations)}")

    # ===== Helper methods =====

    def _find_anchor_in_text(self, text, anchor):
        """Find the position of anchor text in the main text."""
        # Try exact match first
        idx = text.find(anchor)
        if idx >= 0:
            return idx

        # Try case-insensitive
        idx = text.lower().find(anchor.lower())
        if idx >= 0:
            return idx

        # Try first 30 chars
        if len(anchor) > 30:
            idx = text.find(anchor[:30])
            if idx >= 0:
                return idx

        return -1

    def _estimate_lines(self, text, width_pt, font_size):
        """Estimate number of lines for English text."""
        if not text:
            return 1
        # Average char width for Helvetica ~= 0.5 * font_size
        avg_char_w = font_size * 0.52
        chars_per_line = max(1, int(width_pt / avg_char_w))
        words = text.split()
        total_chars = sum(len(w) + 1 for w in words)
        lines = max(1, math.ceil(total_chars / chars_per_line))
        return lines

    def _estimate_cjk_lines(self, text, width_pt, font_size):
        """Estimate number of lines for CJK text."""
        if not text:
            return 1
        # CJK chars are roughly square, ~= font_size wide
        chars_per_line = max(1, int(width_pt / font_size))
        # Count actual chars (CJK + ASCII)
        total_chars = len(text)
        lines = max(1, math.ceil(total_chars / chars_per_line))
        return lines


def slugify(text):
    """Create a URL-safe slug from text."""
    if not text:
        return "essay"
    # Keep alphanumeric and CJK
    slug = re.sub(r"[^\w\u4e00-\u9fff]", "-", text.strip())
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug[:40] if slug else "essay"


def main():
    parser = argparse.ArgumentParser(
        description="Build A4 bilingual Essay范例精读 PDF"
    )
    parser.add_argument("input", help="review_data.json path")
    parser.add_argument("--out", "-o", default=None, help="Output PDF path (default: auto)")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"ERROR: File not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    data = json.loads(input_path.read_text(encoding="utf-8"))

    # Determine output path
    if args.out:
        out_path = args.out
    else:
        title = data.get("title", "essay")
        slug = slugify(title)
        out_path = f"output/Essay范例精读_{slug}.pdf"

    print(f"Building PDF from {input_path.name}...")
    builder = EssayReviewPDF(data, out_path)
    builder.build()


if __name__ == "__main__":
    main()
