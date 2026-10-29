from __future__ import annotations

import argparse
import re
from pathlib import Path


REQUIRED_REFERENCES = [
    "references/paper-analysis-framework.md",
    "references/narrative-templates.md",
    "references/evidence-and-language-rules.md",
    "references/page-components.md",
    "references/visual-system.md",
]


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate HLS Skill metadata and hard gates.")
    parser.add_argument("root", type=Path, nargs="?", default=Path("."))
    args = parser.parse_args()
    root = args.root.resolve()
    skill_path = root / "SKILL.md"
    errors: list[str] = []
    if not skill_path.is_file():
        errors.append("SKILL.md is missing")
    else:
        text = skill_path.read_text(encoding="utf-8")
        match = re.match(r"^---\n(.*?)\n---\n", text, flags=re.DOTALL)
        if not match:
            errors.append("frontmatter is missing or malformed")
        else:
            frontmatter = match.group(1)
            if len(frontmatter) > 1024:
                errors.append("frontmatter exceeds 1024 characters")
            if not re.search(r"^name: [a-z0-9-]+$", frontmatter, flags=re.MULTILINE):
                errors.append("name must contain only lowercase letters, numbers, and hyphens")
            if not re.search(r"^description: Use when", frontmatter, flags=re.MULTILINE):
                errors.append("description must start with 'Use when'")
        required = ["完整阅读", "evidence-map.json", "deck-plan.json", "render_html.py", "screenshot.mjs", "不得宣布完成"]
        for token in required:
            if token not in text:
                errors.append(f"required hard gate is missing: {token}")
        indexes = [text.find(token) for token in ["evidence-map.json", "deck-plan.json", "render_html.py", "screenshot.mjs"]]
        if any(index < 0 for index in indexes) or indexes != sorted(indexes):
            errors.append("required workflow order is invalid")
        for token in ["TBD", "TODO", "implement later", "待定", "稍后补"]:
            if token.lower() in text.lower():
                errors.append(f"placeholder is forbidden: {token}")
    for relative in REQUIRED_REFERENCES:
        if not (root / relative).is_file():
            errors.append(f"required reference is missing: {relative}")
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("Skill validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
