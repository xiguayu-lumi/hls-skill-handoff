from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hls_academic.package_skill import package_skill


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(
        description="Package the HLS academic HTML Skill into a clean personal Skill directory."
    )
    parser.add_argument("target", type=Path)
    parser.add_argument("--source", type=Path, default=root)
    args = parser.parse_args()

    manifest = package_skill(args.source, args.target)
    print(args.target.resolve())
    print(f"Packaged files: {len(manifest['source_files'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
