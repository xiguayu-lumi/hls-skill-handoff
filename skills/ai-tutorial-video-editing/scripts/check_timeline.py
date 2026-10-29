"""Validate 1x voice blocks and overlays; no media decoding or automatic edits."""
import argparse
import json
import math
from pathlib import Path


def validate(data):
    duration, fps = float(data['duration']), float(data['fps'])
    if not math.isfinite(duration) or not math.isfinite(fps) or duration <= 0 or fps <= 0:
        raise ValueError('duration and fps must be positive and finite')
    tol = 0.5 / fps + 1e-6
    voice = sorted(data['voice'], key=lambda b: b['start'])
    errors = []
    def bounds(b, label):
        s, e = float(b['start']), float(b['end'])
        if not all(map(math.isfinite, (s, e))) or s < 0 or e <= s or e > duration + tol:
            errors.append(f'{label}: invalid bounds')
        return s, e
    previous = 0.
    for i, b in enumerate(voice):
        s, e = bounds(b, f'voice[{i}]')
        if abs(s - previous) > tol:
            errors.append(f'voice[{i}]: gap or overlap at {s}')
        if not b.get('source') or not math.isfinite(float(b['source_in'])) or b['source_in'] < 0:
            errors.append(f'voice[{i}]: invalid source')
        previous = e
    if abs(previous - duration) > tol:
        errors.append('voice does not cover full duration')
    for i, b in enumerate(data.get('overlays', [])):
        s, e = bounds(b, f'overlay[{i}]')
        if b['track'] == 'pip':
            matches = [v for v in voice if s >= v['start'] - tol and e <= v['end'] + tol
                       and b.get('source') == v['source']
                       and abs(b.get('source_in', -1) - (v['source_in'] + s - v['start'])) <= tol]
            if not matches:
                errors.append(f'overlay[{i}]: PIP does not match voice source/time')
    return errors


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('timeline', type=Path)
    a = p.parse_args()
    try:
        errors = validate(json.loads(a.timeline.read_text(encoding='utf-8-sig')))
    except (KeyError, TypeError, ValueError) as exc:
        p.error(f'Invalid timeline schema: {exc}')
    if errors:
        print('\n'.join(errors))
        raise SystemExit(1)
    print('Timeline bounds, voice continuity and PIP mapping passed')


if __name__ == '__main__':
    main()
