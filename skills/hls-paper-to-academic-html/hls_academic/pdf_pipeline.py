from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import pymupdf


class PDFPipelineError(RuntimeError):
    """Base error for deterministic PDF processing failures."""


class MissingPDFError(PDFPipelineError):
    pass


class EncryptedPDFError(PDFPipelineError):
    pass


class NoTextLayerError(PDFPipelineError):
    pass


class CorruptPDFError(PDFPipelineError):
    pass


@dataclass(frozen=True)
class PreflightResult:
    source_path: str
    file_name: str
    file_size: int
    sha256: str
    page_count: int
    text_page_count: int
    encrypted: bool
    language: str
    warnings: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ExtractionResult:
    preflight: PreflightResult
    metadata: dict[str, Any]
    figure_candidates: list[dict[str, Any]]
    table_candidates: list[dict[str, Any]]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _open_pdf(path: Path) -> pymupdf.Document:
    try:
        document = pymupdf.open(path)
    except Exception as exc:
        raise CorruptPDFError(f"PDF cannot be opened: {path}") from exc
    if document.needs_pass:
        document.close()
        raise EncryptedPDFError(f"PDF is encrypted: {path}")
    return document


def _guess_language(text: str) -> str:
    sample = text[:20_000]
    cjk = len(re.findall(r"[\u3400-\u9fff]", sample))
    latin = len(re.findall(r"[A-Za-z]", sample))
    if cjk > latin * 0.2:
        return "zh-CN"
    return "en" if latin else "unknown"


def preflight_pdf(pdf_path: Path | str) -> PreflightResult:
    path = Path(pdf_path)
    if not path.is_file():
        raise MissingPDFError(f"PDF not found: {path}")
    if path.suffix.lower() != ".pdf":
        raise MissingPDFError(f"Input is not a PDF: {path}")

    document = _open_pdf(path)
    try:
        page_texts = [page.get_text("text") or "" for page in document]
        text_page_count = sum(bool(text.strip()) for text in page_texts)
        if text_page_count == 0:
            raise NoTextLayerError(f"PDF has no usable text layer: {path}")
        warnings: list[str] = []
        if text_page_count < document.page_count:
            warnings.append(
                f"{document.page_count - text_page_count} page(s) have no extractable text"
            )
        return PreflightResult(
            source_path=str(path.resolve()),
            file_name=path.name,
            file_size=path.stat().st_size,
            sha256=_sha256(path),
            page_count=document.page_count,
            text_page_count=text_page_count,
            encrypted=False,
            language=_guess_language("\n".join(page_texts)),
            warnings=warnings,
        )
    finally:
        document.close()


def _first_match(pattern: str, text: str) -> str | None:
    match = re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE)
    return match.group(1).strip() if match else None


def _metadata(document: pymupdf.Document, texts: list[str]) -> dict[str, Any]:
    raw = document.metadata or {}
    joined_head = "\n".join(texts[:2])
    subject = raw.get("subject") or ""
    doi = _first_match(r"(?:doi:\s*|https?://doi\.org/)(10\.\d{4,9}/[-._;()/:A-Z0-9]+)", subject)
    if doi is None:
        doi = _first_match(r"(?:doi:\s*|https?://doi\.org/)(10\.\d{4,9}/[-._;()/:A-Z0-9]+)", joined_head)
    if doi:
        doi = doi.rstrip(".,;)")

    title = (raw.get("title") or "").strip() or None
    author = (raw.get("author") or "").strip() or None
    journal = None
    if subject and "," in subject:
        journal = subject.split(",", 1)[0].strip() or None
    creation_date = raw.get("creationDate") or ""
    year = _first_match(r"(?:D:)?((?:19|20)\d{2})", creation_date)
    if year is None:
        year = _first_match(r"\b((?:19|20)\d{2})\b", joined_head)

    return {
        "title": title,
        "authors": [author] if author else [],
        "year": int(year) if year else None,
        "journal": journal,
        "doi": doi,
        "page_count": document.page_count,
        "language": _guess_language("\n".join(texts)),
        "source_file": Path(document.name).name,
    }


def _find_candidates(texts: list[str], kind: str) -> list[dict[str, Any]]:
    if kind == "figure":
        pattern = re.compile(r"^\s*(Fig(?:ure)?\.?\s+\d+[A-Za-z]?[^\n]*)", re.IGNORECASE)
    else:
        pattern = re.compile(r"^\s*(Table\s+\d+[A-Za-z]?[^\n]*)", re.IGNORECASE)
    found: list[dict[str, Any]] = []
    seen: set[tuple[int, str]] = set()
    for page_number, text in enumerate(texts, start=1):
        for line in text.splitlines():
            match = pattern.match(line)
            if not match:
                continue
            caption = re.sub(r"\s+", " ", match.group(1)).strip()
            key = (page_number, caption)
            if key not in seen:
                found.append({"page": page_number, "caption": caption})
                seen.add(key)
    return found


def _references(texts: list[str]) -> list[dict[str, Any]]:
    references: list[dict[str, Any]] = []
    in_references = False
    for page_number, text in enumerate(texts, start=1):
        for line in text.splitlines():
            stripped = line.strip()
            if re.fullmatch(r"References", stripped, flags=re.IGNORECASE):
                in_references = True
                continue
            if in_references and re.match(r"^\d+[\.\s]", stripped):
                references.append({"page": page_number, "text": stripped})
    return references


def extract_pdf(pdf_path: Path | str, work_dir: Path | str) -> ExtractionResult:
    path = Path(pdf_path)
    preflight = preflight_pdf(path)
    destination = Path(work_dir)
    destination.mkdir(parents=True, exist_ok=True)

    document = _open_pdf(path)
    try:
        texts = [page.get_text("text") or "" for page in document]
        metadata = _metadata(document, texts)
    finally:
        document.close()

    paper_chunks = [
        f"<!-- page: {index} -->\n\n{text.strip()}\n"
        for index, text in enumerate(texts, start=1)
    ]
    figure_candidates = _find_candidates(texts, "figure")
    table_candidates = _find_candidates(texts, "table")

    (destination / "paper.md").write_text(
        "\n".join(paper_chunks),
        encoding="utf-8",
    )
    (destination / "preflight.json").write_text(
        json.dumps(preflight.to_dict(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (destination / "metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (destination / "references.json").write_text(
        json.dumps(_references(texts), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (destination / "figures.json").write_text(
        json.dumps(figure_candidates, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (destination / "tables.json").write_text(
        json.dumps(table_candidates, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    return ExtractionResult(
        preflight=preflight,
        metadata=metadata,
        figure_candidates=figure_candidates,
        table_candidates=table_candidates,
    )
