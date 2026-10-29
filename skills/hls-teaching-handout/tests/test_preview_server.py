from __future__ import annotations

import json
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen


SKILL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

from preview_core import ProjectPaths  # noqa: E402
from preview_server import create_server  # noqa: E402
from test_preview_core import SAMPLE_HTML  # noqa: E402


class PreviewServerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.paths = ProjectPaths(Path(self.temp.name))
        self.paths.ensure_directories()
        self.paths.editable_html.write_text(SAMPLE_HTML, encoding="utf-8")
        self.paths.preview_index.write_text("<html>editor</html>", encoding="utf-8")
        self.server = create_server(self.paths, host="127.0.0.1", port=0)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = f"http://127.0.0.1:{self.server.server_address[1]}"

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        self.temp.cleanup()

    def get(self, path: str) -> tuple[int, str]:
        with urlopen(self.base + path, timeout=3) as response:
            return response.status, response.read().decode("utf-8")

    def post(self, path: str, payload: dict) -> tuple[int, dict]:
        request = Request(
            self.base + path,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(request, timeout=3) as response:
            return response.status, json.loads(response.read().decode("utf-8"))

    def test_document_and_status_endpoints(self) -> None:
        status, body = self.get("/document")
        self.assertEqual(status, 200)
        self.assertIn("旧封面标题", body)
        status, body = self.get("/status")
        self.assertEqual(json.loads(body)["state"], "editing")

    def test_save_does_not_approve(self) -> None:
        changed = SAMPLE_HTML.replace("修改后的正文", "只保存未批准")
        status, payload = self.post("/save", {"html": changed})
        self.assertEqual(status, 200)
        self.assertEqual(payload["state"], "editing")
        self.assertIn("只保存未批准", self.paths.editable_html.read_text(encoding="utf-8"))
        self.assertFalse(self.paths.approval_marker.exists())

    def test_approve_creates_clean_document_and_marker(self) -> None:
        changed = SAMPLE_HTML.replace("旧封面标题", "确认后的封面")
        status, payload = self.post("/approve", {"html": changed})
        self.assertEqual(status, 200)
        self.assertEqual(payload["state"], "approved")
        self.assertTrue(self.paths.approval_marker.exists())
        clean = self.paths.approved_html.read_text(encoding="utf-8")
        self.assertIn("确认后的封面", clean)
        self.assertNotIn("contenteditable", clean)

    def test_save_cannot_redefine_locked_structure(self) -> None:
        damaged = SAMPLE_HTML.replace("<thead>", "").replace("</thead>", "")
        self.post("/save", {"html": damaged})
        request = Request(
            self.base + "/approve",
            data=json.dumps({"html": damaged}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with self.assertRaises(HTTPError) as caught:
            urlopen(request, timeout=3)
        self.assertEqual(caught.exception.code, 409)
        self.assertFalse(self.paths.approval_marker.exists())

    def test_unknown_endpoint_is_404(self) -> None:
        with self.assertRaises(HTTPError) as caught:
            self.get("/unknown")
        self.assertEqual(caught.exception.code, 404)


class PipelineServerTests(unittest.TestCase):
    def run_pipeline_case(self, runner):
        with tempfile.TemporaryDirectory() as tmp:
            paths = ProjectPaths(Path(tmp))
            paths.ensure_directories()
            paths.editable_html.write_text(SAMPLE_HTML, encoding="utf-8")
            paths.preview_index.write_text("<html>editor</html>", encoding="utf-8")
            server = create_server(paths, host="127.0.0.1", port=0, pipeline_runner=runner)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            base = f"http://127.0.0.1:{server.server_address[1]}"
            try:
                request = Request(
                    base + "/approve",
                    data=json.dumps({"html": SAMPLE_HTML}).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with urlopen(request, timeout=3) as response:
                    self.assertIn(response.status, {200, 202})
                deadline = time.time() + 3
                status = {}
                while time.time() < deadline:
                    with urlopen(base + "/status", timeout=3) as response:
                        status = json.loads(response.read().decode("utf-8"))
                    if status.get("state") in {"complete", "failed"}:
                        break
                    time.sleep(0.03)
                return status
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=2)

    def test_pipeline_success_reaches_complete(self) -> None:
        status = self.run_pipeline_case(lambda paths: {"pdf": "dist/teaching-handout.pdf", "qa": "qa/qa-report.md"})
        self.assertEqual(status["state"], "complete", status)
        self.assertEqual(status["pdf"], "dist/teaching-handout.pdf")

    def test_pipeline_failure_reaches_failed(self) -> None:
        def fail(_paths):
            raise RuntimeError("qa failed")

        status = self.run_pipeline_case(fail)
        self.assertEqual(status["state"], "failed")
        self.assertIn("qa failed", status["error"])


if __name__ == "__main__":
    unittest.main()
