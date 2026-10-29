from __future__ import annotations

import hashlib
import html
import json
import re
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable


ALLOWED_FONT_SIZES = {
    "9.5", "10", "10.5", "11", "11.5", "12", "13", "14", "16", "18", "20", "24", "28"
}
ALLOWED_LINE_HEIGHTS = {"1.4", "1.5", "1.6", "1.65", "1.7", "1.75", "1.8", "2"}
ALLOWED_ALIGNMENTS = {"left", "center", "justify"}


class ApprovalRequiredError(RuntimeError):
    pass


class LockedStructureError(RuntimeError):
    pass


@dataclass(frozen=True)
class ProjectPaths:
    root: Path

    def __post_init__(self) -> None:
        object.__setattr__(self, "root", self.root.expanduser().resolve())

    @property
    def work(self) -> Path:
        return self.root / "work"

    @property
    def preview(self) -> Path:
        return self.root / "preview"

    @property
    def dist(self) -> Path:
        return self.root / "dist"

    @property
    def qa(self) -> Path:
        return self.root / "qa"

    @property
    def editable_html(self) -> Path:
        return self.work / "editable-handout.html"

    @property
    def approved_html(self) -> Path:
        return self.work / "approved-handout.html"

    @property
    def approval_marker(self) -> Path:
        return self.work / "EDITOR_APPROVED"

    @property
    def status_json(self) -> Path:
        return self.work / "preview-status.json"

    @property
    def locked_structure_json(self) -> Path:
        return self.work / "locked-structure.json"

    @property
    def preview_index(self) -> Path:
        return self.preview / "index.html"

    def ensure_directories(self) -> None:
        for path in (self.root, self.work, self.preview, self.dist, self.qa):
            path.mkdir(parents=True, exist_ok=True)

    def resolve_inside(self, *parts: str) -> Path:
        candidate = self.root.joinpath(*parts).resolve()
        if candidate != self.root and self.root not in candidate.parents:
            raise ValueError(f"Path escapes project root: {candidate}")
        return candidate


class _StructureParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.heading_ids: list[tuple[str, str, str]] = []
        self.toc_links: list[str] = []
        self.table_shapes: list[dict[str, object]] = []
        self.cover_regions = 0
        self._in_toc = 0
        self._in_table = False
        self._in_thead = False
        self._row_cells: list[int] = []
        self._current_cells = 0
        self._thead_count = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        classes = set((values.get("class") or "").split())
        if "contents-page" in classes or "toc" in classes:
            self._in_toc += 1
        if "cover" in classes or values.get("data-locked-region") == "cover-background":
            self.cover_regions += 1
        if tag in {"h1", "h2", "h3"} and values.get("id"):
            self.heading_ids.append((tag, values["id"] or "", values.get("data-bookmark-level") or ""))
        if tag == "a" and self._in_toc and (values.get("href") or "").startswith("#"):
            self.toc_links.append(values["href"] or "")
        if tag == "table":
            self._in_table = True
            self._row_cells = []
            self._thead_count = 0
        elif self._in_table and tag == "thead":
            self._in_thead = True
            self._thead_count += 1
        elif self._in_table and tag == "tr":
            self._current_cells = 0
        elif self._in_table and tag in {"th", "td"}:
            self._current_cells += 1

    def handle_endtag(self, tag: str) -> None:
        if tag == "tr" and self._in_table:
            self._row_cells.append(self._current_cells)
        elif tag == "thead" and self._in_table:
            self._in_thead = False
        elif tag == "table" and self._in_table:
            self.table_shapes.append({"thead": self._thead_count, "rows": tuple(self._row_cells)})
            self._in_table = False
        if tag in {"section", "nav"} and self._in_toc:
            self._in_toc -= 1


def snapshot_locked_structure(source: str) -> dict[str, object]:
    parser = _StructureParser()
    parser.feed(source)
    return {
        "heading_ids": tuple(parser.heading_ids),
        "toc_links": tuple(parser.toc_links),
        "table_shapes": tuple((item["thead"], item["rows"]) for item in parser.table_shapes),
        "cover_regions": parser.cover_regions,
    }


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self.parts.append(data)

    def text(self) -> str:
        return "".join(self.parts).strip()


def _plain_text(fragment: str) -> str:
    parser = _TextExtractor()
    parser.feed(fragment)
    return parser.text()


def rebuild_toc(source: str) -> str:
    headings: dict[str, str] = {}
    heading_pattern = re.compile(
        r'<h[1-3]\b(?=[^>]*\bid="([^"]+)")[^>]*>(.*?)</h[1-3]>',
        flags=re.IGNORECASE | re.DOTALL,
    )
    for anchor, inner in heading_pattern.findall(source):
        headings[anchor] = _plain_text(inner)

    link_pattern = re.compile(
        r'(<a\b[^>]*\bhref="#([^"]+)"[^>]*>.*?<span\b[^>]*class="[^"]*\btoc-label\b[^"]*"[^>]*>)(.*?)(</span>)',
        flags=re.IGNORECASE | re.DOTALL,
    )

    def replace(match: re.Match[str]) -> str:
        label = headings.get(match.group(2))
        if label is None:
            return match.group(0)
        return f"{match.group(1)}{html.escape(label)}{match.group(4)}"

    return link_pattern.sub(replace, source)


class _Sanitizer(HTMLParser):
    VOID_TAGS = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=False)
        self.output: list[str] = []
        self._skip_depth = 0

    @staticmethod
    def _is_editor_node(tag: str, attrs: dict[str, str | None]) -> bool:
        return (
            tag == "script"
            or attrs.get("id") == "hls-editor-toolbar"
            or attrs.get("data-editor-ui") == "true"
        )

    @staticmethod
    def _clean_attrs(attrs: Iterable[tuple[str, str | None]]) -> list[tuple[str, str | None]]:
        cleaned: list[tuple[str, str | None]] = []
        for name, value in attrs:
            lower = name.lower()
            if lower in {"contenteditable", "spellcheck", "style"} or lower.startswith("on"):
                continue
            if lower.startswith("data-editor-"):
                continue
            if lower == "data-font-size" and value not in ALLOWED_FONT_SIZES:
                continue
            if lower == "data-line-height" and value not in ALLOWED_LINE_HEIGHTS:
                continue
            if lower == "data-text-align" and value not in ALLOWED_ALIGNMENTS:
                continue
            cleaned.append((name, value))
        return cleaned

    @staticmethod
    def _render_start(tag: str, attrs: Iterable[tuple[str, str | None]], closed: bool = False) -> str:
        rendered = [f"<{tag}"]
        for name, value in attrs:
            rendered.append(f" {name}")
            if value is not None:
                rendered.append(f'="{html.escape(value, quote=True)}"')
        rendered.append("/>" if closed else ">")
        return "".join(rendered)

    def handle_decl(self, decl: str) -> None:
        if not self._skip_depth:
            self.output.append(f"<!{decl}>")

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if self._skip_depth:
            self._skip_depth += 1
            return
        if self._is_editor_node(tag, values):
            self._skip_depth = 1
            return
        self.output.append(self._render_start(tag, self._clean_attrs(attrs)))

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if not self._skip_depth:
            self.output.append(self._render_start(tag, self._clean_attrs(attrs), closed=True))

    def handle_endtag(self, tag: str) -> None:
        if self._skip_depth:
            self._skip_depth -= 1
            return
        if tag not in self.VOID_TAGS:
            self.output.append(f"</{tag}>")

    def handle_data(self, data: str) -> None:
        if not self._skip_depth:
            self.output.append(data)

    def handle_entityref(self, name: str) -> None:
        if not self._skip_depth:
            self.output.append(f"&{name};")

    def handle_charref(self, name: str) -> None:
        if not self._skip_depth:
            self.output.append(f"&#{name};")

    def handle_comment(self, data: str) -> None:
        if not self._skip_depth and "editor" not in data.lower():
            self.output.append(f"<!--{data}-->")


def sanitize_approved_html(source: str) -> str:
    parser = _Sanitizer()
    parser.feed(source)
    return "".join(parser.output)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_atomic(path: Path, content: str) -> None:
    temporary = path.with_suffix(path.suffix + ".next")
    temporary.write_text(content, encoding="utf-8")
    temporary.replace(path)


def approve_document(paths: ProjectPaths, edited_html: str) -> Path:
    if not paths.editable_html.is_file():
        raise FileNotFoundError(paths.editable_html)
    if paths.locked_structure_json.is_file():
        baseline = json.loads(paths.locked_structure_json.read_text(encoding="utf-8"))
    else:
        baseline = snapshot_locked_structure(paths.editable_html.read_text(encoding="utf-8"))
    candidate = snapshot_locked_structure(edited_html)
    candidate_json = json.loads(json.dumps(candidate, ensure_ascii=False))
    if baseline != candidate_json and baseline != candidate:
        raise LockedStructureError(f"Locked document structure changed: before={baseline}, after={candidate}")
    rebuilt = rebuild_toc(edited_html)
    clean = sanitize_approved_html(rebuilt)
    clean_snapshot = snapshot_locked_structure(clean)
    clean_json = json.loads(json.dumps(clean_snapshot, ensure_ascii=False))
    if baseline != clean_snapshot and baseline != clean_json:
        raise LockedStructureError("Sanitization changed locked document structure")
    _write_atomic(paths.approved_html, clean)
    marker = {
        "approved_html": paths.approved_html.name,
        "sha256": _sha256(paths.approved_html),
    }
    _write_atomic(paths.approval_marker, json.dumps(marker, ensure_ascii=False, indent=2) + "\n")
    return paths.approved_html


def require_approval(paths: ProjectPaths, *, auto_approve_for_test: bool = False) -> Path:
    if auto_approve_for_test and not paths.approval_marker.exists():
        approve_document(paths, paths.editable_html.read_text(encoding="utf-8"))
    if not paths.approval_marker.is_file() or not paths.approved_html.is_file():
        raise ApprovalRequiredError("work/EDITOR_APPROVED is required before PDF generation")
    try:
        marker = json.loads(paths.approval_marker.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        raise ApprovalRequiredError("Invalid approval marker") from exc
    if marker.get("sha256") != _sha256(paths.approved_html):
        raise ApprovalRequiredError("Approved HTML does not match approval marker")
    return paths.approved_html
