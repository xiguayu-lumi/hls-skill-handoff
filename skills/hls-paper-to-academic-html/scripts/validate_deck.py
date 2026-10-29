from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from pydantic import ValidationError

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hls_academic.evidence import (
    validate_deck_assets,
    validate_deck_evidence,
    validate_deck_structure,
)
from hls_academic.models import Deck


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate deck JSON and evidence references.")
    parser.add_argument("deck", type=Path)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--output-root", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    deck_data = json.loads(args.deck.read_text(encoding="utf-8"))
    evidence_data = json.loads(args.evidence.read_text(encoding="utf-8"))
    messages: list[str] = []
    try:
        Deck.model_validate(deck_data)
    except ValidationError as exc:
        messages.extend(error["msg"] for error in exc.errors())
    messages.extend(issue.message for issue in validate_deck_evidence(deck_data, evidence_data))
    messages.extend(issue.message for issue in validate_deck_structure(deck_data))
    output_root = args.output_root or args.deck.parent
    messages.extend(issue.message for issue in validate_deck_assets(deck_data, output_root))
    report = "\n".join(
        [
            "# QA Deck Report",
            "",
            f"- Slides: {len(deck_data.get('slides', []))}",
            f"- Errors: {len(messages)}",
            f"- Status: {'PASS' if not messages else 'FAIL'}",
            "",
            *(f"- {message}" for message in messages),
        ]
    ) + "\n"
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(report, encoding="utf-8")
    print(report, end="")
    return 1 if messages else 0


if __name__ == "__main__":
    raise SystemExit(main())
