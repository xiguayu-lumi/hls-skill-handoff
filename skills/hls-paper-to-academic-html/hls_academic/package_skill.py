from __future__ import annotations

import hashlib
import json
import re
import shutil
from pathlib import Path


RUNTIME_FILES = {
    "SKILL.md",
    "CODEX.md",
    "DESIGN.md",
    "README.md",
    "pyproject.toml",
    "package.json",
    "package-lock.json",
}

RUNTIME_DIRECTORIES = {
    "assets",
    "hls_academic",
    "references",
    "schemas",
    "scripts",
    "templates",
}

EXCLUDED_PARTS = {
    "__pycache__",
    ".pytest_cache",
}


def _is_runtime_file(relative: Path) -> bool:
    if relative.as_posix() in RUNTIME_FILES:
        return True
    if not relative.parts or relative.parts[0] not in RUNTIME_DIRECTORIES:
        return False
    return not any(part in EXCLUDED_PARTS for part in relative.parts) and relative.suffix != ".pyc"


def _package_version(source_root: Path) -> str:
    pyproject = source_root / "pyproject.toml"
    if not pyproject.is_file():
        return "0.0.0"
    match = re.search(
        r'^version\s*=\s*"([^"]+)"',
        pyproject.read_text(encoding="utf-8"),
        flags=re.MULTILINE,
    )
    return match.group(1) if match else "0.0.0"


def package_skill(source_root: Path, target_root: Path) -> dict:
    source = source_root.resolve()
    target = target_root.resolve()

    if target.exists():
        raise FileExistsError(f"Package target already exists: {target}")
    if not (source / "SKILL.md").is_file():
        raise FileNotFoundError(f"SKILL.md is missing from source: {source}")

    target.mkdir(parents=True)
    packaged: list[dict[str, object]] = []
    for source_path in sorted(source.rglob("*")):
        if not source_path.is_file():
            continue
        relative = source_path.relative_to(source)
        if not _is_runtime_file(relative):
            continue
        target_path = target / relative
        target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, target_path)
        data = target_path.read_bytes()
        packaged.append(
            {
                "path": relative.as_posix(),
                "bytes": len(data),
                "sha256": hashlib.sha256(data).hexdigest(),
            }
        )
    packaged.sort(key=lambda item: str(item["path"]))

    manifest = {
        "name": "hls-paper-to-academic-html",
        "version": _package_version(source),
        "release_status": "installed-personal-skill",
        "installed_to_personal_skill_directory": True,
        "source_files": packaged,
    }
    (target / "release-manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest
