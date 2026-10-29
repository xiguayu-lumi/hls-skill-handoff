"""Copy the editable starter into a new empty production directory."""
import argparse
import shutil
from pathlib import Path

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output', type=Path, required=True)
    a = ap.parse_args()
    source = Path(__file__).resolve().parents[1] / 'assets/starter'
    if a.output.exists() and any(a.output.iterdir()):
        ap.error('Output must be absent or empty; existing files are never overwritten')
    a.output.mkdir(parents=True, exist_ok=True)
    for f in source.iterdir():
        shutil.copy2(f, a.output / f.name)
    print(a.output.resolve() / 'config.json')

if __name__ == '__main__':
    main()
