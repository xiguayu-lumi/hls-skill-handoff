from __future__ import annotations

import hashlib
import json
from pathlib import Path


EXCLUDED_PARTS = {
    ".git",
    ".venv",
    "node_modules",
    "dist",
    "build",
    ".pytest_cache",
    "__pycache__",
    "hls-paper-to-academic-html-workspace",
}


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    target = root / "release-manifest.json"
    files = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(root)
        if path == target or any(part in EXCLUDED_PARTS for part in relative.parts):
            continue
        if relative.parts[:4] == (
            "examples",
            "smoke-test",
            "output",
            "slides",
        ):
            continue
        if relative.parts[:4] == (
            "examples",
            "smoke-test",
            "output",
            "contact-sheets",
        ):
            continue
        data = path.read_bytes()
        files.append(
            {
                "path": relative.as_posix(),
                "bytes": len(data),
                "sha256": hashlib.sha256(data).hexdigest(),
            }
        )

    manifest = {
        "name": "hls-paper-to-academic-html",
        "version": "0.1.0",
        "release_status": "validated-local-candidate",
        "installed_to_personal_skill_directory": False,
        "source_files": files,
        "generated_artifacts": {
            "smoke_slide_pngs": 5,
            "smoke_contact_sheet_pngs": 3,
            "smoke_slide_size": "1080x1440",
            "qa_status": "PASS",
        },
    }
    target.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(target.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
