from __future__ import annotations

import argparse
import html
import json
import re
import shutil
import subprocess
from html.parser import HTMLParser
from pathlib import Path

from preview_core import ProjectPaths, require_approval


class _Text(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self.parts.append(data)


def _plain(fragment: str) -> str:
    parser = _Text()
    parser.feed(fragment)
    return "".join(parser.parts).strip()


def _expanded(command: list[str], source: Path, output: Path) -> list[str]:
    return [token.replace("{input}", str(source)).replace("{output}", str(output)) for token in command]


def _run_renderer(command: list[str], source: Path, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(_expanded(command, source, output), check=False)
    if result.returncode:
        raise RuntimeError(f"PDF renderer exited with code {result.returncode}")
    if not output.is_file() or output.stat().st_size == 0:
        raise RuntimeError(f"PDF renderer did not create output: {output}")


def update_toc_pages_from_pdf(source: str, pdf_path: Path) -> str:
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise RuntimeError("pypdf is required for two-pass TOC page regeneration") from exc

    reader = PdfReader(str(pdf_path))
    page_text = [(page.extract_text() or "").replace(" ", "") for page in reader.pages]
    headings: dict[str, str] = {}
    for anchor, inner in re.findall(
        r'<h[1-3]\b(?=[^>]*\bid="([^"]+)")[^>]*>(.*?)</h[1-3]>', source, re.I | re.S
    ):
        headings[anchor] = _plain(inner)
    pages: dict[str, int] = {}
    for anchor, title in headings.items():
        needle = title.replace(" ", "")
        matches = [index + 1 for index, text in enumerate(page_text) if needle and needle in text]
        if matches:
            pages[anchor] = matches[-1]

    link_pattern = re.compile(
        r'(<a\b[^>]*\bhref="#([^"]+)"[^>]*>.*?<span\b[^>]*class="[^"]*\btoc-page\b[^"]*"[^>]*>)(.*?)(</span>)',
        re.I | re.S,
    )

    def replace(match: re.Match[str]) -> str:
        page = pages.get(match.group(2))
        if page is None:
            raise RuntimeError(f"Could not derive TOC page for #{match.group(2)}")
        return f"{match.group(1)}{html.escape(str(page))}{match.group(4)}"

    updated, count = link_pattern.subn(replace, source)
    expected = len(re.findall(r'<a\b[^>]*\bhref="#[^"]+"', source, re.I))
    if expected and count != expected:
        raise RuntimeError(f"Updated {count} TOC page fields, expected {expected}")
    return updated


def render_approved(
    paths: ProjectPaths,
    renderer_command: list[str],
    *,
    two_pass_toc: bool = True,
    auto_approve_for_test: bool = False,
) -> Path:
    approved = require_approval(paths, auto_approve_for_test=auto_approve_for_test)
    final_html = paths.dist / "teaching-handout.html"
    final_pdf = paths.dist / "teaching-handout.pdf"
    shutil.copy2(approved, final_html)
    if two_pass_toc:
        first_pdf = paths.work / "preview-pagination-pass.pdf"
        _run_renderer(renderer_command, final_html, first_pdf)
        updated = update_toc_pages_from_pdf(final_html.read_text(encoding="utf-8"), first_pdf)
        final_html.write_text(updated, encoding="utf-8")
    _run_renderer(renderer_command, final_html, final_pdf)
    return final_pdf


def main() -> None:
    parser = argparse.ArgumentParser(description="Render an approved HLS handout")
    parser.add_argument("--project", required=True)
    parser.add_argument("--renderer-command-json")
    parser.add_argument("--single-pass", action="store_true")
    parser.add_argument("--auto-approve-for-test", action="store_true")
    args = parser.parse_args()
    if args.renderer_command_json:
        command = json.loads(args.renderer_command_json)
        if not isinstance(command, list) or not all(isinstance(item, str) for item in command):
            raise SystemExit("--renderer-command-json must be a JSON string array")
    else:
        command = ["node", str(Path(__file__).with_name("render_pdf.js")), "{input}", "{output}"]
    pdf = render_approved(
        ProjectPaths(Path(args.project)),
        command,
        two_pass_toc=not args.single_pass,
        auto_approve_for_test=args.auto_approve_for_test,
    )
    print(pdf)


if __name__ == "__main__":
    main()
