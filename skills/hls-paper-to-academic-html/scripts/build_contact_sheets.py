from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hls_academic.contact_sheet import build_contact_sheets


def main() -> int:
    parser = argparse.ArgumentParser(description="Build 2160x1440 two-slide contact sheets.")
    parser.add_argument("slides", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    for path in build_contact_sheets(args.slides, args.output):
        print(path.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
