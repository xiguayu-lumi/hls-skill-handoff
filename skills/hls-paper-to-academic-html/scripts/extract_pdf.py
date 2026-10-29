from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hls_academic.pdf_pipeline import PDFPipelineError, extract_pdf


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Extract an academic PDF while preserving page markers."
    )
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--work-dir", type=Path, default=Path("work"))
    args = parser.parse_args()
    try:
        result = extract_pdf(args.pdf, args.work_dir)
    except PDFPipelineError as exc:
        parser.exit(2, f"extraction failed: {exc}\n")
    print(
        json.dumps(
            {
                "page_count": result.preflight.page_count,
                "text_page_count": result.preflight.text_page_count,
                "figure_candidates": len(result.figure_candidates),
                "table_candidates": len(result.table_candidates),
                "work_dir": str(args.work_dir.resolve()),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
