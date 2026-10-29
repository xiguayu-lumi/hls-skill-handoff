"""Validate an overlay video with ffprobe, ffmpeg and numpy."""
import argparse
import hashlib
import json
import math
import os
import subprocess
import sys
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path
VERSION, SIZE, THRESHOLD, DETAIL_LIMIT = "1.1", (160, 90), 1.0, 2000
def cli():
    p = argparse.ArgumentParser(description="Check format, full decode, hash and scene ROI motion.")
    p.add_argument("--video", type=Path, required=True, help="Rendered video.")
    p.add_argument("--config", type=Path, required=True, help="Contract JSON.")
    p.add_argument("--report", type=Path, required=True, help="Report JSON path.")
    p.add_argument("--skip-motion", action="store_true", help="Skip ROI motion and record it.")
    return p.parse_args()
def text(value):
    value = str(value or "").strip(); return value if len(value) <= DETAIL_LIMIT else value[:DETAIL_LIMIT] + "…"
def add(r, check, code, message, severity="error"):
    r["issues"].append({"check": check, "code": code, "severity": severity, "message": message})
def same(a, b):
    return os.path.normcase(os.path.abspath(os.fspath(a))) == os.path.normcase(os.path.abspath(os.fspath(b)))
def base(a):
    return {"schema_version": "1.0", "validator_version": VERSION, "checked_at": datetime.now(timezone.utc).isoformat(),
            "status": "ERROR", "exit_code": 2, "video": {"path": str(a.video)}, "config": {"path": str(a.config)},
            "hash": {"algorithm": "sha256", "value": None, "bytes": None, "status": "NOT_RUN"},
            "format": {"status": "NOT_RUN"}, "decode": {"status": "NOT_RUN"},
            "motion": {"status": "NOT_RUN", "skipped": a.skip_motion, "scenes": []}, "issues": []}
def num(v):
    try:
        return not isinstance(v, bool) and isinstance(v, (int, float)) and math.isfinite(float(v))
    except (OverflowError, TypeError, ValueError): return False
def integer(v):
    return num(v) and float(v).is_integer()
def call(cmd, text_mode=False):
    kwargs = {"stdout": subprocess.PIPE, "stderr": subprocess.PIPE, "check": False}
    if text_mode: kwargs.update(text=True, encoding="utf-8", errors="replace")
    try:
        return subprocess.run(cmd, **kwargs), None
    except FileNotFoundError: return None, "required executable was not found on PATH."
    except OSError as exc: return None, f"could not start command: {exc}"
def load(path):
    def reject(v):
        raise ValueError(f"non-standard number {v!r}")
    try:
        with path.open(encoding="utf-8") as f:
            value = json.load(f, parse_constant=reject)
    except FileNotFoundError:
        return None, [f"Config file does not exist: {path}"]
    except (OSError, json.JSONDecodeError, ValueError) as exc: return None, [f"Config could not be read as JSON: {exc}"]
    return (value, []) if isinstance(value, dict) else (None, ["Config root must be an object."])
def validate(raw):
    errors = []
    w, h, fps, duration = (raw.get(k) for k in ("width", "height", "fps", "duration"))
    for ok, msg in ((integer(w) and int(w) > 0, "width must be a positive integer."),
                    (integer(h) and int(h) > 0, "height must be a positive integer."),
                    (num(fps) and float(fps) > 0, "fps must be a positive number."),
                    (num(duration) and float(duration) > 0, "duration must be a positive number.")):
        if not ok: errors.append(msg)
    scenes = raw.get("scenes")
    if not isinstance(scenes, list) or not scenes:
        errors.append("scenes must be a non-empty array."); scenes = []
    w, h = (int(w) if integer(w) else None), (int(h) if integer(h) else None)
    duration = float(duration) if num(duration) else None
    seen, out = set(), []
    for i, s in enumerate(scenes):
        label = f"scenes[{i}]"
        if not isinstance(s, dict):
            errors.append(f"{label} must be an object."); continue
        sid, start, end, roi = (s.get(k) for k in ("id", "start", "end", "motion_roi"))
        if not isinstance(sid, str) or not sid.strip():
            errors.append(f"{label}.id must be a non-empty string."); sid = f"scene-{i + 1}"
        elif sid in seen: errors.append(f"{label}.id duplicates {sid!r}.")
        seen.add(sid)
        if not num(start) or not num(end): errors.append(f"{label}.start and end must be finite numbers."); start, end = 0.0, 0.0
        else:
            start, end = float(start), float(end)
            if start < 0 or end <= start: errors.append(f"{label} must satisfy 0 <= start < end.")
            if duration is not None and end > duration: errors.append(f"{label}.end must be <= config duration.")
        good_roi = isinstance(roi, list) and len(roi) == 4 and all(integer(v) for v in roi)
        if not good_roi: errors.append(f"{label}.motion_roi must be four integer pixels."); roi = [0, 0, 0, 0]
        else:
            roi = [int(v) for v in roi]; x, y, rw, rh = roi
            if rw <= 0 or rh <= 0 or x < 0 or y < 0: errors.append(f"{label}.motion_roi must be inside the frame.")
            if w is not None and x + rw > w: errors.append(f"{label}.motion_roi exceeds width.")
            if h is not None and y + rh > h: errors.append(f"{label}.motion_roi exceeds height.")
        out.append({"id": sid, "start": start, "end": end, "motion_roi": roi})
    if errors: return None, errors
    return {"width": w, "height": h, "fps": float(fps), "duration": duration, "scenes": out}, []
def probe(path):
    cmd = ["ffprobe", "-hide_banner", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)]
    p, error = call(cmd, True)
    if error: return None, f"ffprobe: {error}"
    if p.returncode: return None, f"ffprobe failed ({p.returncode}): {text(p.stderr)}"
    try: data = json.loads(p.stdout)
    except json.JSONDecodeError as exc: return None, f"ffprobe returned invalid JSON: {exc}"
    streams = data.get("streams", []); videos = [s for s in streams if s.get("codec_type") == "video"]
    if not videos: return None, "Video has no video stream."
    v, fmt = videos[0], data.get("format") or {}; rate = v.get("avg_frame_rate") or v.get("r_frame_rate")
    try: real_fps = float(Fraction(str(rate))) if rate else None
    except (ValueError, ZeroDivisionError): real_fps = None
    try: real_duration = float(fmt.get("duration") or v.get("duration"))
    except (TypeError, ValueError): real_duration = None
    return {"width": v.get("width"), "height": v.get("height"), "fps": real_fps,
            "duration": real_duration, "avg_frame_rate": v.get("avg_frame_rate"),
            "r_frame_rate": v.get("r_frame_rate"), "format_name": fmt.get("format_name"),
            "audio_present": any(s.get("codec_type") == "audio" for s in streams)}, None
def format_check(actual, expected):
    checks = [
        (actual["width"] == expected["width"], "width_mismatch", f"Expected width {expected['width']}, got {actual['width']}."),
        (actual["height"] == expected["height"], "height_mismatch", f"Expected height {expected['height']}, got {actual['height']}."),
    ]
    fps_tol, dur_tol = max(.05, expected["fps"] * .005), max(.1, 2 / expected["fps"])
    checks += [
        (actual["fps"] is not None and abs(actual["fps"] - expected["fps"]) <= fps_tol, "fps_mismatch", f"Expected fps {expected['fps']:g}, got {actual['fps']}."),
        (actual["duration"] is not None and abs(actual["duration"] - expected["duration"]) <= dur_tol, "duration_mismatch", f"Expected duration {expected['duration']:g}s, got {actual['duration']}."),
        (actual["audio_present"], "audio_missing", "Video has no audio stream."),
    ]
    errors = [{"code": code, "message": message} for ok, code, message in checks if not ok]
    return {"status": "PASS" if not errors else "ERROR",
            "expected": {k: expected[k] for k in ("width", "height", "fps", "duration")},
            "actual": actual, "tolerances": {"fps": fps_tol, "duration": dur_tol}, "issues": errors}, errors
def decode(path):
    cmd = ["ffmpeg", "-hide_banner", "-nostdin", "-xerror", "-loglevel", "error", "-i", str(path),
           "-map", "0:v:0", "-map", "0:a:0?", "-f", "null", "-"]
    p, error = call(cmd, True)
    if error: return False, f"ffmpeg: {error}"
    return (True, None) if p.returncode == 0 else (False, f"Full audio/video decode failed ({p.returncode}): {text(p.stderr)}")
def hash_video(path):
    digest, size = hashlib.sha256(), 0
    with path.open("rb") as f:
        while chunk := f.read(1024 * 1024): digest.update(chunk); size += len(chunk)
    return digest.hexdigest(), size
def frame(path, timestamp, roi):
    x, y, w, h = roi
    vf = f"crop={w}:{h},scale={SIZE[0]}:{SIZE[1]},format=rgb24"
    cmd = ["ffmpeg", "-hide_banner", "-nostdin", "-xerror", "-loglevel", "error", "-i", str(path),
           "-ss", f"{timestamp:.6f}", "-vf", vf.replace(f"crop={w}:{h}", f"crop={w}:{h}:{x}:{y}"),
           "-frames:v", "1", "-f", "rawvideo", "-"]
    p, error = call(cmd)
    if error: return None, f"ffmpeg: {error}"
    expected = SIZE[0] * SIZE[1] * 3
    if p.returncode or len(p.stdout) != expected: return None, f"ROI sample at {timestamp:.3f}s failed: {text(p.stderr.decode(errors='replace'))}"
    return p.stdout, None
def motion(path, cfg, actual_duration, report):
    try: import numpy as np
    except ImportError:
        result = {"status": "ERROR", "skipped": False, "method": "not_run", "scenes": []}
        report["motion"] = result; add(report, "motion", "numpy_missing", "numpy is required; use --skip-motion.")
        return result
    result = {"status": "PASS", "skipped": False, "method": "mean_absolute_rgb_difference",
              "threshold": THRESHOLD, "sample_size": list(SIZE), "roi_coordinate_space": "final_video_pixels",
              "method_note": "Pixel-difference screening only; REVIEW requires human inspection and does not prove a frozen frame.", "scenes": []}
    low = False
    for s in cfg["scenes"]:
        offset = min(.35, (s["end"] - s["start"]) * .2); t1, t2 = s["start"] + offset, s["end"] - offset; strategy = "end_near"
        if actual_duration is not None: t1, t2 = min(t1, max(0., actual_duration - 1e-6)), min(t2, max(0., actual_duration - 1e-6))
        if t2 <= t1:
            t2 = min(s["end"] + 1.2, max(0., (actual_duration or s["end"] + 1.2) - 1e-6)); strategy = "end_plus_1_2_fallback"
        a, e1 = frame(path, t1, s["motion_roi"]); b, e2 = frame(path, t2, s["motion_roi"])
        item = {"id": s["id"], "start": s["start"], "end": s["end"], "motion_roi": s["motion_roi"],
                "samples": {"first_timestamp": t1, "second_timestamp": t2, "strategy": strategy}}
        if e1 or e2 or a is None or b is None:
            item.update({"status": "ERROR", "motion_detected": None, "error": e1 or e2}); result["status"] = "ERROR"
            add(report, "motion", "roi_sample_failed", f"Scene {s['id']}: {e1 or e2}")
        else:
            aa, bb = np.frombuffer(a, dtype=np.uint8).astype(np.int16), np.frombuffer(b, dtype=np.uint8).astype(np.int16)
            diff, detected = float(np.mean(np.abs(aa - bb))), False
            detected = diff > THRESHOLD; item.update({"mean_absolute_rgb_difference": diff, "motion_detected": detected, "status": "PASS" if detected else "REVIEW"})
            if not detected: low = True; item["review"] = "Low ROI difference; inspect manually. It does not prove a frozen background."
        result["scenes"].append(item)
    if result["status"] != "ERROR" and low:
        result["status"] = "REVIEW"; add(report, "motion", "low_motion", "At least one scene needs human review.", "review")
    return result
def finish(r):
    status = "ERROR" if any(i["severity"] == "error" for i in r["issues"]) else ("REVIEW" if r["motion"].get("status") == "REVIEW" else "PASS")
    r["status"], r["exit_code"] = status, 0 if status == "PASS" else 2
    return r["exit_code"]
def run(a, r):
    if same(a.report, a.video) or same(a.report, a.config):
        add(r, "paths", "report_overwrites_input", "Report path must differ from video and config."); return finish(r)
    raw, errors = load(a.config)
    if errors:
        r["config"].update({"status": "ERROR", "errors": errors}); [add(r, "config", "invalid_config", e) for e in errors]; return finish(r)
    cfg, errors = validate(raw)
    if errors:
        r["config"].update({"status": "ERROR", "errors": errors}); [add(r, "config", "invalid_config", e) for e in errors]; return finish(r)
    r["config"].update({"status": "PASS", "normalized": cfg})
    if not a.video.is_file(): add(r, "video", "video_missing", f"Video file does not exist: {a.video}"); return finish(r)
    try:
        digest, size = hash_video(a.video); r["hash"].update({"status": "PASS", "value": digest, "bytes": size})
    except OSError as exc: add(r, "hash", "hash_failed", str(exc))
    actual, error = probe(a.video)
    if error or actual is None:
        r["format"] = {"status": "ERROR", "error": error}; add(r, "format", "ffprobe_failed", error or "ffprobe failed.")
    else:
        checked, errors = format_check(actual, cfg); r["format"] = checked
        for e in errors: add(r, "format", e["code"], e["message"])
    ok, error = decode(a.video)
    r["decode"] = {"status": "PASS" if ok else "ERROR", "full_audio_video": True, "audio_present": actual.get("audio_present") if actual else None}
    if error: r["decode"]["error"] = error; add(r, "decode", "full_decode_failed", error)
    if a.skip_motion:
        r["motion"] = {"status": "SKIPPED", "skipped": True, "method": "not_run", "roi_coordinate_space": "final_video_pixels", "scenes": [], "method_note": "Skipped by --skip-motion; no frozen-frame judgment was made."}
    elif actual is not None: r["motion"] = motion(a.video, cfg, actual.get("duration"), r)
    else: r["motion"] = {"status": "ERROR", "skipped": False, "method": "not_run", "scenes": []}; add(r, "motion", "probe_required", "Motion check requires ffprobe data.")
    return finish(r)
def main():
    a, r = cli(), None
    r = base(a)
    try: code = run(a, r)
    except Exception as exc: add(r, "validator", "unexpected_error", f"{type(exc).__name__}: {exc}"); code = finish(r)
    if same(a.report, a.video) or same(a.report, a.config):
        print("ERROR: report path equals an input; no file was written.", file=sys.stderr); return 2
    try:
        a.report.parent.mkdir(parents=True, exist_ok=True)
        with a.report.open("w", encoding="utf-8", newline="\n") as f: json.dump(r, f, ensure_ascii=False, indent=2, allow_nan=False); f.write("\n")
    except (OSError, ValueError) as exc:
        print(f"ERROR: could not write report: {exc}", file=sys.stderr); return 2
    print(f"{r['status']}: report written to {a.report}", file=sys.stderr if code else sys.stdout)
    return code
if __name__ == "__main__": raise SystemExit(main())
