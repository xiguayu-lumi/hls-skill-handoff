from __future__ import annotations

import argparse
import json
import shutil
import threading
from collections.abc import Callable
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from preview_core import (
    LockedStructureError,
    ProjectPaths,
    approve_document,
    snapshot_locked_structure,
)


PipelineRunner = Callable[[ProjectPaths], dict[str, Any] | None]


def _standard_delivery_dir(paths: ProjectPaths) -> tuple[Path, Path] | None:
    if paths.root.name != "preview-project" or paths.root.parent.name != "03_制作工程":
        return None
    content_project = paths.root.parent.parent
    return content_project, content_project / "05_最终交付" / "教学讲义"


def _delivery_stem(delivery: Path, pdf: Path) -> str:
    stem = "teaching-handout"
    candidate = delivery / f"{stem}.pdf"
    if not candidate.exists() or candidate.read_bytes() == pdf.read_bytes():
        return stem
    version = 2
    while (delivery / f"{stem}_v{version}.pdf").exists():
        version += 1
    return f"{stem}_v{version}"


def archive_successful_outputs(paths: ProjectPaths, pdf: Path, qa: Path) -> dict[str, str] | None:
    standard = _standard_delivery_dir(paths)
    if standard is None:
        return None
    content_project, delivery = standard
    delivery.mkdir(parents=True, exist_ok=True)
    stem = _delivery_stem(delivery, pdf)
    archived_pdf = delivery / f"{stem}.pdf"
    archived_html = delivery / f"{stem}.html"
    archived_qa = delivery / ("qa-report.md" if stem == "teaching-handout" else f"{stem}-qa-report.md")
    archived_summary = delivery / ("qa-summary.json" if stem == "teaching-handout" else f"{stem}-qa-summary.json")
    shutil.copy2(pdf, archived_pdf)
    shutil.copy2(paths.dist / "teaching-handout.html", archived_html)
    shutil.copy2(qa, archived_qa)
    summary = paths.qa / "qa-summary.json"
    if summary.is_file():
        shutil.copy2(summary, archived_summary)
    return {
        "pdf": archived_pdf.relative_to(content_project).as_posix(),
        "qa": archived_qa.relative_to(content_project).as_posix(),
    }


def build_pipeline_runner(
    renderer_command: list[str],
    *,
    two_pass_toc: bool = True,
    qa_runner: Callable[[Path], Path] | None = None,
) -> PipelineRunner:
    from qa_handout import run_qa
    from render_pdf import render_approved

    qa_action = qa_runner or run_qa

    def runner(paths: ProjectPaths) -> dict[str, Any]:
        pdf = render_approved(paths, renderer_command, two_pass_toc=two_pass_toc)
        qa = qa_action(paths.root)
        archived = archive_successful_outputs(paths, pdf, qa)
        if archived is not None:
            return archived
        return {
            "pdf": pdf.relative_to(paths.root).as_posix(),
            "qa": qa.relative_to(paths.root).as_posix(),
        }

    return runner


def _atomic_text(path: Path, content: str) -> None:
    temporary = path.with_suffix(path.suffix + ".next")
    temporary.write_text(content, encoding="utf-8")
    temporary.replace(path)


def _read_status(paths: ProjectPaths) -> dict[str, Any]:
    if not paths.status_json.is_file():
        return {"state": "editing", "pdf": None, "qa": None, "error": None}
    return json.loads(paths.status_json.read_text(encoding="utf-8"))


def _write_status(paths: ProjectPaths, **updates: Any) -> dict[str, Any]:
    status = _read_status(paths)
    status.update(updates)
    _atomic_text(paths.status_json, json.dumps(status, ensure_ascii=False, indent=2) + "\n")
    return status


def _initialize_locked_structure(paths: ProjectPaths) -> None:
    if paths.locked_structure_json.exists():
        return
    snapshot = snapshot_locked_structure(paths.editable_html.read_text(encoding="utf-8"))
    _atomic_text(
        paths.locked_structure_json,
        json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n",
    )


def create_server(
    paths: ProjectPaths,
    *,
    host: str = "127.0.0.1",
    port: int = 8765,
    pipeline_runner: PipelineRunner | None = None,
) -> ThreadingHTTPServer:
    paths.ensure_directories()
    if not paths.editable_html.is_file():
        raise FileNotFoundError(paths.editable_html)
    _initialize_locked_structure(paths)
    if not paths.status_json.exists():
        _write_status(paths, state="editing", pdf=None, qa=None, error=None)
    status_lock = threading.RLock()

    def read_status() -> dict[str, Any]:
        with status_lock:
            return _read_status(paths)

    def write_status(**updates: Any) -> dict[str, Any]:
        with status_lock:
            return _write_status(paths, **updates)

    class Handler(BaseHTTPRequestHandler):
        server_version = "HLSPreview/1.5"

        def log_message(self, format: str, *args: object) -> None:
            return

        def _send_bytes(self, payload: bytes, content_type: str, status: int = 200) -> None:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(payload)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(payload)

        def _json(self, payload: dict[str, Any], status: int = 200) -> None:
            self._send_bytes(
                json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                "application/json; charset=utf-8",
                status,
            )

        def _file(self, path: Path, content_type: str) -> None:
            if not path.is_file():
                self._json({"error": f"Not found: {path.name}"}, HTTPStatus.NOT_FOUND)
                return
            self._send_bytes(path.read_bytes(), content_type)

        def do_GET(self) -> None:  # noqa: N802
            route = self.path.split("?", 1)[0]
            if route == "/":
                self._file(paths.preview_index, "text/html; charset=utf-8")
            elif route == "/document":
                self._file(paths.editable_html, "text/html; charset=utf-8")
            elif route == "/editor.css":
                self._file(paths.preview / "editor.css", "text/css; charset=utf-8")
            elif route == "/editor.js":
                self._file(paths.preview / "editor.js", "text/javascript; charset=utf-8")
            elif route == "/status":
                self._json(read_status())
            else:
                self._json({"error": "Not found"}, HTTPStatus.NOT_FOUND)

        def _payload(self) -> dict[str, Any]:
            content_type = self.headers.get("Content-Type", "")
            if "application/json" not in content_type:
                raise ValueError("Content-Type must be application/json")
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0 or length > 20 * 1024 * 1024:
                raise ValueError("Invalid request size")
            value = json.loads(self.rfile.read(length).decode("utf-8"))
            if not isinstance(value, dict) or not isinstance(value.get("html"), str):
                raise ValueError("JSON body must contain an html string")
            return value

        def do_POST(self) -> None:  # noqa: N802
            route = self.path.split("?", 1)[0]
            if route not in {"/save", "/approve"}:
                self._json({"error": "Not found"}, HTTPStatus.NOT_FOUND)
                return
            try:
                payload = self._payload()
                edited_html = payload["html"]
                if route == "/save":
                    _atomic_text(paths.editable_html, edited_html)
                    self._json(write_status(state="editing", error=None))
                    return

                approve_document(paths, edited_html)
                approved = write_status(state="approved", error=None)
                if pipeline_runner is None:
                    self._json(approved)
                    return

                def run_pipeline() -> None:
                    try:
                        write_status(state="rendering", error=None)
                        result = pipeline_runner(paths) or {}
                        write_status(state="complete", error=None, **result)
                    except Exception as exc:
                        write_status(state="failed", error=str(exc))

                threading.Thread(target=run_pipeline, daemon=True).start()
                self._json(read_status(), HTTPStatus.ACCEPTED)
            except LockedStructureError as exc:
                self._json({"state": "editing", "error": str(exc)}, HTTPStatus.CONFLICT)
            except (ValueError, json.JSONDecodeError, UnicodeDecodeError) as exc:
                self._json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
            except Exception as exc:
                self._json({"error": str(exc)}, HTTPStatus.INTERNAL_SERVER_ERROR)

    return ThreadingHTTPServer((host, port), Handler)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the local HLS handout preview editor")
    parser.add_argument("--project", required=True)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--renderer-command-json")
    parser.add_argument("--single-pass", action="store_true")
    parser.add_argument("--approval-only", action="store_true")
    args = parser.parse_args()
    if args.host != "127.0.0.1":
        raise SystemExit("The preview editor may only bind to 127.0.0.1")
    paths = ProjectPaths(Path(args.project))
    if args.renderer_command_json:
        renderer_command = json.loads(args.renderer_command_json)
        if not isinstance(renderer_command, list) or not all(isinstance(item, str) for item in renderer_command):
            raise SystemExit("--renderer-command-json must be a JSON string array")
    else:
        renderer_command = ["node", str(Path(__file__).with_name("render_pdf.js")), "{input}", "{output}"]
    pipeline = None if args.approval_only else build_pipeline_runner(
        renderer_command,
        two_pass_toc=not args.single_pass,
    )
    server = create_server(paths, host=args.host, port=args.port, pipeline_runner=pipeline)
    print("HLS 讲义预览编辑器已启动：")
    print(f"http://{args.host}:{server.server_address[1]}")
    print("\n请在浏览器中完成修改，然后点击“确认并生成 PDF”。")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
