from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

from preview_core import (  # noqa: E402
    ApprovalRequiredError,
    LockedStructureError,
    ProjectPaths,
    approve_document,
    rebuild_toc,
    require_approval,
    sanitize_approved_html,
    snapshot_locked_structure,
)


SAMPLE_HTML = """<!doctype html>
<html><head><meta charset="utf-8"><style>
.cover{background-image:url('cover.jpg')}.manual-page-break{break-before:page}
</style></head><body>
<div id="hls-editor-toolbar" data-editor-ui="true">toolbar</div>
<section class="cover" data-locked-region="cover-background">
  <div class="cover-kicker" contenteditable="true">学术学习资料</div>
  <h1 class="cover-title" contenteditable="true">旧封面标题</h1>
</section>
<section class="contents-page" data-editor-locked="true"><nav class="toc">
  <a href="#ch1"><span class="toc-label">第一章　旧章标题</span></a>
  <a href="#s1-1"><span class="toc-label">1.1　旧节标题</span></a>
</nav></section>
<main>
  <section class="chapter"><h1 id="ch1" class="chapter-title" data-bookmark-level="1" contenteditable="true">第一章　新章标题</h1>
  <h2 id="s1-1" data-bookmark-level="2" contenteditable="true" onclick="evil()">1.1　新节标题</h2>
  <p contenteditable="true" data-font-size="11.5" data-line-height="1.75" style="color:red" data-editor-selected="true">修改后的正文</p>
  <table class="academic-table"><thead><tr><th contenteditable="true">列一</th><th contenteditable="true">列二</th></tr></thead>
  <tbody><tr><td contenteditable="true">甲</td><td contenteditable="true">乙</td></tr></tbody></table>
  </section>
</main><script data-editor-script="true">alert(1)</script></body></html>"""


class ProjectPathsTests(unittest.TestCase):
    def test_resolve_rejects_paths_outside_project(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = ProjectPaths(Path(tmp) / "project")
            paths.ensure_directories()
            with self.assertRaises(ValueError):
                paths.resolve_inside("..", "escape.txt")

    def test_unapproved_project_cannot_render(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = ProjectPaths(Path(tmp))
            paths.ensure_directories()
            with self.assertRaises(ApprovalRequiredError):
                require_approval(paths)
            self.assertFalse(paths.approval_marker.exists())


class HtmlSafetyTests(unittest.TestCase):
    def test_sanitizer_removes_editor_residue_but_preserves_locked_structure(self) -> None:
        before = snapshot_locked_structure(SAMPLE_HTML)
        clean = sanitize_approved_html(SAMPLE_HTML)
        after = snapshot_locked_structure(clean)

        self.assertEqual(before, after)
        self.assertNotIn("contenteditable", clean)
        self.assertNotIn("hls-editor-toolbar", clean)
        self.assertNotIn("data-editor-selected", clean)
        self.assertNotIn("onclick", clean)
        self.assertNotIn("<script", clean)
        self.assertNotIn("color:red", clean)
        self.assertIn('id="ch1"', clean)
        self.assertIn('data-bookmark-level="1"', clean)
        self.assertIn('data-font-size="11.5"', clean)
        self.assertIn('data-line-height="1.75"', clean)
        self.assertIn("<thead>", clean)

    def test_toc_labels_are_rebuilt_from_heading_text_without_changing_links(self) -> None:
        rebuilt = rebuild_toc(SAMPLE_HTML)
        self.assertIn('href="#ch1"', rebuilt)
        self.assertIn('href="#s1-1"', rebuilt)
        self.assertIn("第一章　新章标题", rebuilt)
        self.assertIn("1.1　新节标题", rebuilt)
        self.assertNotIn("第一章　旧章标题", rebuilt)

    def test_approval_rejects_deleted_table_structure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = ProjectPaths(Path(tmp))
            paths.ensure_directories()
            paths.editable_html.write_text(SAMPLE_HTML, encoding="utf-8")
            damaged = SAMPLE_HTML.replace("<thead>", "").replace("</thead>", "")
            with self.assertRaises(LockedStructureError):
                approve_document(paths, damaged)
            self.assertFalse(paths.approval_marker.exists())

    def test_approval_writes_clean_html_and_marker(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = ProjectPaths(Path(tmp))
            paths.ensure_directories()
            paths.editable_html.write_text(SAMPLE_HTML, encoding="utf-8")
            approved = approve_document(paths, SAMPLE_HTML)
            self.assertEqual(approved, paths.approved_html)
            self.assertTrue(paths.approval_marker.is_file())
            self.assertNotIn("contenteditable", approved.read_text(encoding="utf-8"))
            require_approval(paths)


if __name__ == "__main__":
    unittest.main()
