from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import shutil
from pathlib import Path

from preview_core import ALLOWED_FONT_SIZES, ALLOWED_LINE_HEIGHTS, ProjectPaths, snapshot_locked_structure


def _controlled_editor_styles() -> str:
    rules = [
        f'[data-font-size="{value}"] {{ font-size: {value}pt !important; }}'
        for value in sorted(ALLOWED_FONT_SIZES, key=float)
    ]
    rules.extend(
        f'[data-line-height="{value}"] {{ line-height: {value} !important; }}'
        for value in sorted(ALLOWED_LINE_HEIGHTS, key=float)
    )
    rules.extend(
        [
            '[data-text-align="left"] { text-align: left !important; }',
            '[data-text-align="center"] { text-align: center !important; }',
            '[data-text-align="justify"] { text-align: justify !important; }',
            '[data-font-weight="bold"] { font-weight: 700 !important; }',
        ]
    )
    return '<style id="hls-controlled-editor-styles">\n' + "\n".join(rules) + "\n</style>"


def _inject_controlled_styles(source: str) -> str:
    if 'id="hls-controlled-editor-styles"' in source:
        return source
    styles = _controlled_editor_styles()
    if "</head>" in source.lower():
        index = source.lower().rfind("</head>")
        return source[:index] + styles + "\n" + source[index:]
    return styles + "\n" + source


def prepare(project: Path, html_path: Path, skill_root: Path | None = None) -> ProjectPaths:
    skill = (skill_root or Path(__file__).resolve().parents[1]).resolve()
    source = html_path.expanduser().resolve()
    if not source.is_file():
        raise FileNotFoundError(source)
    paths = ProjectPaths(project)
    paths.ensure_directories()
    content = source.read_text(encoding="utf-8")
    content = _inject_controlled_styles(content)
    cover = skill / "assets" / "hls-cover-template-clean.jpg"
    if cover.is_file() and "../assets/hls-cover-template-clean.jpg" in content:
        mime = mimetypes.guess_type(cover.name)[0] or "image/jpeg"
        data_uri = f"data:{mime};base64,{base64.b64encode(cover.read_bytes()).decode('ascii')}"
        content = content.replace("../assets/hls-cover-template-clean.jpg", data_uri)
    paths.editable_html.write_text(content, encoding="utf-8")
    paths.locked_structure_json.write_text(
        json.dumps(snapshot_locked_structure(content), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    resources = {
        skill / "templates" / "preview-index.html": paths.preview_index,
        skill / "templates" / "preview-editor.css": paths.preview / "editor.css",
        skill / "templates" / "preview-editor.js": paths.preview / "editor.js",
    }
    for source_path, target in resources.items():
        if not source_path.is_file():
            raise FileNotFoundError(source_path)
        shutil.copy2(source_path, target)
    paths.status_json.write_text(
        json.dumps({"state": "editing", "pdf": None, "qa": None, "error": None}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return paths


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare an HLS handout preview project")
    parser.add_argument("--project", required=True)
    parser.add_argument("--html", required=True)
    args = parser.parse_args()
    paths = prepare(Path(args.project), Path(args.html))
    print(f"Preview project prepared: {paths.root}")


if __name__ == "__main__":
    main()
