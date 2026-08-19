import json
import os
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import ClassVar
from unittest import mock

from scripts import webhook


class Sink(BaseHTTPRequestHandler):
    calls: ClassVar[list] = []
    status = 200

    def do_POST(self):
        length = int(self.headers.get("content-length", "0"))
        Sink.calls.append(
            (self.path, self.headers.get("authorization"), self.rfile.read(length))
        )
        self.send_response(Sink.status)
        self.end_headers()

    def log_message(self, *args):
        return


class WebhookTest(unittest.TestCase):
    def setUp(self):
        Sink.calls, Sink.status = [], 200
        self.server = HTTPServer(("127.0.0.1", 0), Sink)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.base = f"http://127.0.0.1:{self.server.server_address[1]}/api/ingest"

    def tearDown(self):
        self.server.shutdown()

    def test_event_and_sarif(self):
        with mock.patch.dict(
            os.environ,
            {"EVIDENCE_WEBHOOK_URL": self.base + "/", "EVIDENCE_WEBHOOK_TOKEN": "tok"},
        ):
            self.assertEqual(
                webhook.main(
                    [
                        "event",
                        "--type",
                        "image.pushed",
                        "--payload",
                        '{"image":"x","digest":"sha256:1"}',
                    ]
                ),
                0,
            )
            self.assertEqual(
                webhook.main(["sarif", "--file", "tests/samples/semgrep.json"]), 0
            )
        self.assertEqual(Sink.calls[0][0], "/api/ingest/event")
        self.assertEqual(Sink.calls[0][1], "Bearer tok")
        self.assertEqual(
            json.loads(Sink.calls[0][2]),
            {"type": "image.pushed", "payload": {"image": "x", "digest": "sha256:1"}},
        )
        self.assertEqual(Sink.calls[1][0], "/api/ingest/sarif")

    def test_client_error_is_not_retried_and_never_fails(self):
        Sink.status = 400
        with mock.patch.dict(
            os.environ,
            {"EVIDENCE_WEBHOOK_URL": self.base, "EVIDENCE_WEBHOOK_TOKEN": "tok"},
        ):
            self.assertEqual(
                webhook.main(
                    ["event", "--type", "pipeline.completed", "--payload", "{}"]
                ),
                0,
            )
        self.assertEqual(len(Sink.calls), 1)

    def test_disabled_without_url(self):
        with mock.patch.dict(os.environ, {"EVIDENCE_WEBHOOK_URL": ""}):
            self.assertEqual(
                webhook.main(["event", "--type", "x", "--payload", "{}"]), 0
            )
        self.assertEqual(Sink.calls, [])


if __name__ == "__main__":
    unittest.main()
