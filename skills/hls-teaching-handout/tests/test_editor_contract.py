from __future__ import annotations

import re
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
INDEX = SKILL_ROOT / "templates" / "preview-index.html"
SCRIPT = SKILL_ROOT / "templates" / "preview-editor.js"


class EditorContractTests(unittest.TestCase):
    def test_toolbar_contains_only_required_controls(self) -> None:
        html = INDEX.read_text(encoding="utf-8")
        controls = re.findall(r'data-tool="([^"]+)"', html)
        self.assertEqual(
            controls,
            [
                "undo", "redo", "block-type", "font-size", "bold",
                "align-left", "align-center", "align-justify", "line-height",
                "page-break", "reset", "approve",
            ],
        )
        for forbidden in ("import", "export", "save-as", "template", "login", "comment"):
            self.assertNotIn(forbidden, html.lower())

    def test_script_uses_controlled_fonts_and_locks_structure(self) -> None:
        script = SCRIPT.read_text(encoding="utf-8")
        for size in ("9.5", "10", "10.5", "11", "11.5", "12", "13", "14", "16", "18", "20", "24", "28"):
            self.assertIn(f'"{size}"', script)
        self.assertIn("MIN_BODY_FONT_SIZE", script)
        self.assertIn(".contents-page", script)
        self.assertIn("thead", script)
        self.assertIn("data-manual-page-break", script)
        self.assertIn("beforeinput", script)
        self.assertIn("paste", script)

    def test_table_cells_bypass_locked_table_ancestor(self) -> None:
        script = SCRIPT.read_text(encoding="utf-8")
        self.assertIn('if (element.closest("th, td")) return false;', script)

    def test_captions_and_source_notes_are_editable_without_unlocking_toc(self) -> None:
        script = SCRIPT.read_text(encoding="utf-8")
        self.assertIn('"figcaption"', script)
        self.assertIn('".document-note"', script)
        self.assertIn('if (element.closest(".document-note")) return false;', script)
        self.assertIn('if (element.closest(".contents-page")) return true;', script)

    def test_unified_history_records_text_and_format_changes(self) -> None:
        script = SCRIPT.read_text(encoding="utf-8")
        self.assertIn("function recordHistory()", script)
        self.assertIn("function undoEdit()", script)
        self.assertIn("function redoEdit()", script)
        self.assertIn('event.inputType !== "historyUndo"', script)
        self.assertIn('tool === "undo"', script)
        self.assertIn("recordHistory();", script)

    def test_toolbar_preserves_iframe_selection_for_formatting(self) -> None:
        script = SCRIPT.read_text(encoding="utf-8")
        self.assertIn('addEventListener("selectionchange"', script)
        self.assertIn("function restoreSelection()", script)
        self.assertIn('toolbar.addEventListener("mousedown"', script)

    def test_bold_falls_back_to_current_block_without_text_selection(self) -> None:
        script = SCRIPT.read_text(encoding="utf-8")
        self.assertIn('tool === "bold"', script)
        self.assertIn("block.dataset.fontWeight", script)


if __name__ == "__main__":
    unittest.main()
