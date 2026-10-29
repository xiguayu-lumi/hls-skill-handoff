from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hls_academic.source_assets import render_source_assets


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Render exact PDF text crops and extract embedded paper figures."
    )
    parser.add_argument("pdf", type=Path)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--scale", type=float, default=3.0)
    args = parser.parse_args()
    data = json.loads(args.manifest.read_text(encoding="utf-8"))
    outputs = render_source_assets(
        args.pdf,
        data,
        args.output_dir,
        scale=args.scale,
    )
    print(
        json.dumps(
            {
                "asset_count": len(outputs),
                "files": [
                    path.relative_to(args.output_dir).as_posix() for path in outputs
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
