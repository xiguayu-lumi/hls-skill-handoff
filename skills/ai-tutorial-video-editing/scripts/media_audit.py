"""Read-only media inventory; requires ffprobe on PATH."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('inputs', nargs='+', type=Path)
    p.add_argument('--output', required=True, type=Path)
    a = p.parse_args()
    if a.output.resolve() in [x.resolve() for x in a.inputs]:
        p.error('Output must not overwrite an input')
    records = []
    for path in a.inputs:
        h = hashlib.sha256()
        with path.open('rb') as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b''):
                h.update(chunk)
        result = subprocess.run(['ffprobe', '-v', 'error', '-show_format',
            '-show_streams', '-of', 'json', str(path)], check=True,
            capture_output=True, encoding='utf-8')
        records.append({'path': str(path.resolve()), 'sha256': h.hexdigest(),
                        'probe': json.loads(result.stdout)})
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'Wrote {len(records)} records')


if __name__ == '__main__':
    main()
