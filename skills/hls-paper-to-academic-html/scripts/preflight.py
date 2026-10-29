from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hls_academic.pdf_pipeline import PDFPipelineError, preflight_pdf


def main() -> int:
    parser = argparse.ArgumentParser(description="Preflight an academic PDF.")
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--work-dir", type=Path, default=Path("work"))
    args = parser.parse_args()
    try:
        result = preflight_pdf(args.pdf)
    except PDFPipelineError as exc:
        parser.exit(2, f"preflight failed: {exc}\n")
    args.work_dir.mkdir(parents=True, exist_ok=True)
    output = args.work_dir / "preflight.json"
    text = json.dumps(result.to_dict(), ensure_ascii=False, indent=2) + "\n"
    output.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
