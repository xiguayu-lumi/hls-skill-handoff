from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hls_academic.qa import (
    build_contact_sheet_index,
    build_language_report,
    build_visual_report,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build language and visual QA reports.")
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--deck", type=Path, required=True)
    parser.add_argument("--dom-report", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--inspected", nargs="+", default=["S01", "S07", "S12", "S14"])
    args = parser.parse_args()

    build_language_report(
        args.evidence,
        args.deck,
        args.output_dir / "qa-language-report.md",
    )
    build_visual_report(
        args.dom_report,
        args.manifest,
        args.output_dir,
        args.output_dir / "qa-visual-report.md",
        inspected_slides=args.inspected,
    )
    build_contact_sheet_index(
        args.output_dir / "contact-sheets",
        args.output_dir / "xhs-contact-sheet.html",
        title="HLS 论文拆解 · 小红书竖版接触表",
    )
    print(args.output_dir.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
