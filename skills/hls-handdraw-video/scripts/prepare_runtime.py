"""Prepare a version-checked local handdraw runtime after explicit production choice."""
import argparse
import hashlib
import json
import shutil
from pathlib import Path

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def prepare(source, job, confirmation):
    source, job, confirmation = map(lambda x: Path(x).resolve(), (source, job, confirmation))
    record = json.loads(confirmation.read_text(encoding="utf-8-sig"))
    if record.get("status") != "confirmed" or record.get("scope") != "production" or record.get("paused") is not False:
        raise ValueError("Explicit style confirmation and active production scope required")
    for key in ("topic", "style_id", "user_quote", "evidence"):
        if not isinstance(record.get(key), str) or not record[key].strip():
            raise ValueError(f"Missing genuine confirmation field: {key}")
    patch = Path(__file__).resolve().parents[1] / "patches"
    manifest = json.loads((patch / "manifest.json").read_text(encoding="utf-8"))
    for name, hashes in manifest.items():
        if digest(source / "scripts" / name) != hashes["source_sha256"]:
            raise ValueError(f"Dependency version changed: {name}; review before adapting")
        if digest(patch / name) != hashes["patched_sha256"]:
            raise ValueError(f"Bundled patch integrity failed: {name}")
    anchor = "    if arguments.command == 'doctor':"
    entry_source = (source / 'scripts/handdraw_video.py').read_text(encoding='utf-8')
    if entry_source.count(anchor) != 1:
        raise ValueError('Runtime entry changed; review material gate integration before production')
    target = job / "runtime"
    if target.exists():
        raise ValueError("Runtime already exists; inspect its receipt instead of overwriting")
    job.mkdir(parents=True, exist_ok=True)
    for folder in ("scripts", "assets", "dependencies"):
        if not (source / folder).is_dir():
            raise ValueError(f"Missing dependency folder: {folder}")
    for folder in ("scripts", "assets", "dependencies"):
        shutil.copytree(source / folder, target / folder, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    for name in manifest:
        shutil.copy2(patch / name, target / "scripts" / name)
    gate = Path(__file__).with_name('material_gate.py')
    shutil.copy2(gate, target / 'scripts/material_gate.py')
    entry = target / 'scripts/handdraw_video.py'
    original = entry.read_text(encoding='utf-8')
    guard = "    if arguments.command in ('build', 'render', 'verify', 'finalize'):\n        from material_gate import check_job\n        check_job(arguments.job)\n"
    entry.write_text(original.replace(anchor, guard + anchor, 1), encoding='utf-8')
    receipt = {"upstream_version": (source / "VERSION").read_text(encoding="utf-8").strip(), "confirmation_sha256": digest(confirmation), "topic": record["topic"], "style_id": record["style_id"], "patches": manifest,
               "material_gate_sha256": digest(gate), "guarded_entry_sha256": digest(entry)}
    (job / "runtime-receipt.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding="utf-8")
    return target

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True)
    parser.add_argument("--job", required=True)
    parser.add_argument("--confirmation", required=True)
    args = parser.parse_args()
    print(prepare(args.source, args.job, args.confirmation))
