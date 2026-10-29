from __future__ import annotations

import re
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]


class SkillPackageTests(unittest.TestCase):
    def test_frontmatter_and_workflow_are_v1_5_2(self) -> None:
        source = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertRegex(source, r"(?m)^version: 1\.5\.2$")
        self.assertRegex(source, r"(?m)^description: Use when ")
        for step in range(1, 13):
            self.assertIn(f"第 {step} 步", source)
        self.assertIn("EDITOR_APPROVED", source)
        self.assertIn("127.0.0.1:8765", source)

    def test_manifest_matches_package_files(self) -> None:
        expected = {
            line.strip().replace("\\", "/")
            for line in (SKILL_ROOT / "manifest.txt").read_text(encoding="utf-8").splitlines()
            if line.strip()
        }
        actual = {
            path.relative_to(SKILL_ROOT).as_posix()
            for path in SKILL_ROOT.rglob("*")
            if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc"
        }
        self.assertEqual(expected, actual)

    def test_readme_documents_human_approval_gate(self) -> None:
        source = (SKILL_ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("确认并生成 PDF", source)
        self.assertIn("--approval-only", source)
        self.assertIn("--auto-approve-for-test", source)
        self.assertIsNone(re.search(r"React|Vue|Next\.js", source, re.I))

    def test_contact_sheet_resolves_pdfjs_through_node_module_paths(self) -> None:
        source = (SKILL_ROOT / "scripts" / "render_contact_sheet.js").read_text(encoding="utf-8")
        self.assertIn('require.resolve("pdfjs-dist/legacy/build/pdf.mjs")', source)
        self.assertIn("pathToFileURL", source)

    def test_toc_defaults_to_single_column_with_explicit_two_column_opt_in(self) -> None:
        css = (SKILL_ROOT / "templates" / "hls-handout.css").read_text(encoding="utf-8")
        self.assertIn(".toc {\n  column-count: 1;", css)
        self.assertIn(".toc.toc--two-column", css)


if __name__ == "__main__":
    unittest.main()
