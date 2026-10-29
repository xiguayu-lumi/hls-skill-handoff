from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hls_academic.render import render_deck


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description="Render deterministic offline HLS deck HTML.")
    parser.add_argument("deck", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--template", type=Path, default=root / "templates" / "deck.html.j2")
    args = parser.parse_args()
    output = render_deck(args.deck, args.output, template_path=args.template)
    print(output.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
