"""Check a voice-led scene plan for missing or overlapping time spans."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


def check(path: Path) -> list[str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    scenes = data.get("scenes", [])
    duration = float(data["duration"])
    errors: list[str] = []
    if not math.isfinite(duration) or duration <= 0:
        errors.append("duration must be a positive finite number")
    if not scenes:
        errors.append("scenes must contain at least one scene")
        return errors

    previous_end = 0.0
    seen_ids: set[str] = set()
    for index, scene in enumerate(scenes, 1):
        scene_id = str(scene.get("id", index))
        if scene_id in seen_ids:
            errors.append(f"duplicate scene id: {scene_id}")
        seen_ids.add(scene_id)
        try:
            start, end = float(scene["start"]), float(scene["end"])
        except (KeyError, TypeError, ValueError):
            errors.append(f"{scene_id}: start/end must be numbers")
            continue
        if not math.isfinite(start) or not math.isfinite(end) or end <= start:
            errors.append(f"{scene_id}: invalid span {start}–{end}")
        delta = start - previous_end
        if abs(delta) > 0.001:
            kind = "gap" if delta > 0 else "overlap"
            errors.append(f"{scene_id}: {kind} of {abs(delta):.3f}s before start")
        previous_end = end
    if abs(previous_end - duration) > 0.001:
        errors.append(f"last scene ends at {previous_end:.3f}s; duration is {duration:.3f}s")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scene_plan", type=Path)
    args = parser.parse_args()
    errors = check(args.scene_plan)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    data = json.loads(args.scene_plan.read_text(encoding="utf-8"))
    print(f"OK: {len(data['scenes'])} scenes cover {data['duration']}s continuously")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
