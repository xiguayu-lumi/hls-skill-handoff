from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from PIL import Image
import yaml


ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples" / "example-study-abroad.yaml"
TEMPLATE = ROOT / "templates" / "cover-spec.yaml"
VALIDATE_SPEC = ROOT / "scripts" / "validate_spec.py"
VALIDATE_OUTPUT = ROOT / "scripts" / "validate_output.py"


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


class ValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.example = yaml.safe_load(EXAMPLE.read_text(encoding="utf-8"))

    def test_example_spec_passes(self) -> None:
        result = run(str(VALIDATE_SPEC), "--spec", str(EXAMPLE))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Spec validation passed", result.stdout)

    def test_orphan_chinese_headline_line_fails(self) -> None:
        broken = deepcopy(self.example)
        broken["content"]["chinese_headline_lines"] = ["别急着融入", "先", "找到节奏"]
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "broken.yaml"
            path.write_text(
                yaml.safe_dump(broken, allow_unicode=True, sort_keys=False),
                encoding="utf-8",
            )
            result = run(str(VALIDATE_SPEC), "--spec", str(path))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("one-character orphan line", result.stderr)

    def test_wrong_cover_size_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            wrong_cover = temp / "wrong.png"
            illustration = temp / "illustration.png"
            Image.new("RGB", (100, 100), "white").save(wrong_cover)
            Image.new("RGB", (1080, 520), "#82B7C5").save(illustration)
            result = run(
                str(VALIDATE_OUTPUT),
                "--spec",
                str(EXAMPLE),
                "--illustration",
                str(illustration),
                "--cover",
                str(wrong_cover),
            )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Cover size", result.stderr)

    def test_approved_typography_defaults_are_preserved(self) -> None:
        template = yaml.safe_load(TEMPLATE.read_text(encoding="utf-8"))
        layout = template["layout"]
        left_column_width = layout["right_rule_x"] - layout["left_margin"]
        self.assertGreaterEqual(template["font_sizes"]["chinese_headline"], 96)
        self.assertLessEqual(layout["summary_max_width"], int(left_column_width * 0.84))


if __name__ == "__main__":
    unittest.main()
