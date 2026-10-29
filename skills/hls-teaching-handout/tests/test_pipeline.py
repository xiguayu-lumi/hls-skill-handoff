from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

from prepare_preview import prepare  # noqa: E402
from preview_core import (  # noqa: E402
    ApprovalRequiredError,
    ProjectPaths,
    approve_document,
    rebuild_toc,
    sanitize_approved_html,
)
from qa_handout import inspect_html  # noqa: E402
from render_pdf import render_approved  # noqa: E402
from preview_server import build_pipeline_runner  # noqa: E402
from test_preview_core import SAMPLE_HTML  # noqa: E402


class PreparePreviewTests(unittest.TestCase):
    def test_prepare_copies_editor_assets_and_freezes_structure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source.html"
            source.write_text(SAMPLE_HTML, encoding="utf-8")
            paths = prepare(root / "project", source, SKILL_ROOT)
            self.assertTrue(paths.preview_index.is_file())
            self.assertTrue((paths.preview / "editor.css").is_file())
            self.assertTrue((paths.preview / "editor.js").is_file())
            locked = json.loads(paths.locked_structure_json.read_text(encoding="utf-8"))
            self.assertEqual(locked["toc_links"], ["#ch1", "#s1-1"])
            self.assertEqual(json.loads(paths.status_json.read_text(encoding="utf-8"))["state"], "editing")
            prepared = paths.editable_html.read_text(encoding="utf-8")
            self.assertIn('id="hls-controlled-editor-styles"', prepared)
            self.assertIn('[data-font-weight="bold"]', prepared)
            self.assertIn('[data-font-size="12"]', prepared)
            self.assertIn('[data-line-height="1.8"]', prepared)

    def test_prepare_embeds_fixed_cover_asset_for_standalone_preview(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source.html"
            source.write_text(
                SAMPLE_HTML.replace("url('cover.jpg')", 'url("../assets/hls-cover-template-clean.jpg")'),
                encoding="utf-8",
            )
            paths = prepare(root / "project", source, SKILL_ROOT)
            prepared = paths.editable_html.read_text(encoding="utf-8")
            self.assertIn("data:image/jpeg;base64,", prepared)
            self.assertNotIn("../assets/hls-cover-template-clean.jpg", prepared)


class RenderGateTests(unittest.TestCase):
    def test_render_refuses_unapproved_project(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = ProjectPaths(Path(tmp))
            paths.ensure_directories()
            paths.editable_html.write_text(SAMPLE_HTML, encoding="utf-8")
            with self.assertRaises(ApprovalRequiredError):
                render_approved(paths, [sys.executable, "-c", "raise SystemExit(0)"])

    def test_render_uses_approved_html_and_expands_command_tokens(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = ProjectPaths(Path(tmp))
            paths.ensure_directories()
            paths.editable_html.write_text(SAMPLE_HTML, encoding="utf-8")
            approve_document(paths, SAMPLE_HTML.replace("修改后的正文", "PDF 使用确认内容"))
            command = [
                sys.executable,
                "-c",
                (
                    "from pathlib import Path; import sys; "
                    "text=Path(sys.argv[1]).read_text(encoding='utf-8'); "
                    "assert 'PDF 使用确认内容' in text; Path(sys.argv[2]).write_bytes(b'%PDF-test')"
                ),
                "{input}",
                "{output}",
            ]
            pdf = render_approved(paths, command, two_pass_toc=False)
            self.assertEqual(pdf, paths.dist / "teaching-handout.pdf")
            self.assertEqual(pdf.read_bytes(), b"%PDF-test")
            self.assertIn("PDF 使用确认内容", (paths.dist / "teaching-handout.html").read_text(encoding="utf-8"))

    def test_server_pipeline_runner_returns_pdf_and_qa_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = ProjectPaths(Path(tmp))
            paths.ensure_directories()
            paths.editable_html.write_text(SAMPLE_HTML, encoding="utf-8")
            approve_document(paths, SAMPLE_HTML)
            command = [
                sys.executable,
                "-c",
                "from pathlib import Path; import sys; Path(sys.argv[2]).write_bytes(b'%PDF-test')",
                "{input}",
                "{output}",
            ]

            def fake_qa(project: Path) -> Path:
                report = project / "qa" / "qa-report.md"
                report.write_text("PASS", encoding="utf-8")
                return report

            runner = build_pipeline_runner(command, two_pass_toc=False, qa_runner=fake_qa)
            result = runner(paths)
            self.assertEqual(result["pdf"], "dist/teaching-handout.pdf")
            self.assertEqual(result["qa"], "qa/qa-report.md")

    def test_successful_standard_project_pipeline_archives_final_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            content_project = Path(tmp) / "内容项目" / "2026-08-04_测试讲义"
            preview_root = content_project / "03_制作工程" / "preview-project"
            paths = ProjectPaths(preview_root)
            paths.ensure_directories()
            paths.editable_html.write_text(SAMPLE_HTML, encoding="utf-8")
            approve_document(paths, SAMPLE_HTML)
            command = [
                sys.executable,
                "-c",
                "from pathlib import Path; import sys; Path(sys.argv[2]).write_bytes(b'%PDF-test')",
                "{input}",
                "{output}",
            ]

            def fake_qa(project: Path) -> Path:
                report = project / "qa" / "qa-report.md"
                report.write_text("PASS", encoding="utf-8")
                (project / "qa" / "qa-summary.json").write_text('{"overall":"PASS"}', encoding="utf-8")
                return report

            result = build_pipeline_runner(command, two_pass_toc=False, qa_runner=fake_qa)(paths)
            delivery = content_project / "05_最终交付" / "教学讲义"
            self.assertEqual(result["pdf"], "05_最终交付/教学讲义/teaching-handout.pdf")
            self.assertEqual(result["qa"], "05_最终交付/教学讲义/qa-report.md")
            self.assertEqual((delivery / "teaching-handout.pdf").read_bytes(), b"%PDF-test")
            self.assertTrue((delivery / "teaching-handout.html").is_file())
            self.assertTrue((delivery / "qa-report.md").is_file())
            self.assertTrue((delivery / "qa-summary.json").is_file())


class HtmlQaTests(unittest.TestCase):
    def test_clean_approved_html_passes_structural_qa(self) -> None:
        clean = sanitize_approved_html(rebuild_toc(SAMPLE_HTML))
        clean = clean.replace(
            "</p>", '</p><div class="manual-page-break" data-manual-page-break="true"></div>', 1
        )
        checks = inspect_html(clean)
        self.assertTrue(all(checks.values()), checks)

    def test_editor_residue_fails_qa(self) -> None:
        checks = inspect_html(SAMPLE_HTML)
        self.assertFalse(checks["no_editor_residue"])

    def test_manual_page_break_css_selector_is_not_counted_as_an_element(self) -> None:
        source = sanitize_approved_html(rebuild_toc(SAMPLE_HTML))
        source = source.replace(
            "</head>",
            '<style>.manual-page-break[data-manual-page-break="true"] { break-before: page; }</style></head>',
        ).replace(
            "</p>",
            '</p><div class="manual-page-break" data-manual-page-break="true"></div>',
            1,
        )
        checks = inspect_html(source)
        self.assertTrue(checks["manual_page_breaks_semantic"], checks)

    def test_user_facing_output_rejects_banned_source_wording(self) -> None:
        clean = sanitize_approved_html(rebuild_toc(SAMPLE_HTML))
        self.assertTrue(inspect_html(clean)["no_banned_source_wording"])
        self.assertFalse(inspect_html(clean.replace("修改后的正文", "原资料中的示例"))["no_banned_source_wording"])


if __name__ == "__main__":
    unittest.main()
