from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def run(*parts: str) -> None:
    subprocess.run(parts, check=True)


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    smoke = root / "examples" / "smoke-test"
    work = smoke / "work"
    output = smoke / "output"
    python = sys.executable

    run(
        python,
        str(root / "scripts" / "validate_evidence.py"),
        str(work / "evidence-map.json"),
        "--paper",
        str(work / "paper.md"),
        "--report",
        str(output / "qa-evidence-report.md"),
    )
    run(
        python,
        str(root / "scripts" / "validate_deck.py"),
        str(output / "deck.json"),
        "--evidence",
        str(work / "evidence-map.json"),
        "--output-root",
        str(output),
        "--report",
        str(output / "qa-deck-report.md"),
    )
    run(
        python,
        str(root / "scripts" / "render_html.py"),
        str(output / "deck.json"),
        "--output",
        str(output / "index.html"),
    )
    run(
        "node",
        str(root / "scripts" / "visual-dom-check.mjs"),
        str(output / "index.html"),
        "--report",
        str(output / "qa-dom-report.json"),
    )
    run(
        "node",
        str(root / "scripts" / "screenshot.mjs"),
        str(output / "index.html"),
        str(output),
    )
    run(
        python,
        str(root / "scripts" / "build_contact_sheets.py"),
        str(output / "slides"),
        "--output",
        str(output / "contact-sheets"),
    )
    run(
        python,
        str(root / "scripts" / "build_qa_reports.py"),
        "--evidence",
        str(work / "evidence-map.json"),
        "--deck",
        str(output / "deck.json"),
        "--dom-report",
        str(output / "qa-dom-report.json"),
        "--manifest",
        str(output / "render-manifest.json"),
        "--output-dir",
        str(output),
        "--inspected",
        "S01",
        "S02",
        "S03",
        "S04",
        "S05",
    )
    run(
        python,
        "-m",
        "pytest",
        str(root / "tests" / "test_smoke_outputs.py"),
        "-q",
    )
    print(f"Smoke test passed: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
