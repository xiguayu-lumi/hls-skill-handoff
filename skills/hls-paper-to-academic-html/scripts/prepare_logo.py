from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hls_academic.brand import prepare_logo


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Remove a near-white HLS Logo background without changing RGB."
    )
    parser.add_argument("source", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--white-threshold", type=int, default=248)
    parser.add_argument("--feather", type=int, default=20)
    args = parser.parse_args()
    result = prepare_logo(
        args.source,
        args.output,
        white_threshold=args.white_threshold,
        feather=args.feather,
    )
    print(json.dumps(result.__dict__, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
