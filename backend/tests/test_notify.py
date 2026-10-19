from __future__ import annotations

import hashlib
import hmac
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from app import notify
from app.config import settings


class _Capture(BaseHTTPRequestHandler):
    received = {}

    def do_POST(self):  # noqa: N802
        length = int(self.headers.get("Content-Length", 0))
        _Capture.received = {
            "body": self.rfile.read(length),
            "signature": self.headers.get("X-Ultorn-Signature"),
            "content_type": self.headers.get("Content-Type"),
        }
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"ok")

    def log_message(self, *args):
        pass


def test_dispatch_is_noop_without_webhook(monkeypatch):
    monkeypatch.setattr(settings, "alert_webhook_url", "")
    called = []
    monkeypatch.setattr(notify, "_post", lambda *a: called.append(a))
    notify.dispatch_alert({"id": 1})
    assert called == []


def test_post_signs_payload(monkeypatch):
    server = ThreadingHTTPServer(("127.0.0.1", 0), _Capture)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        url = f"http://127.0.0.1:{server.server_port}/hook"
        secret = "shared-secret"
        payload = json.dumps({"event": "alert.created"}).encode()

        notify._post(url, payload, secret)

        expected = "sha256=" + hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
        assert _Capture.received["body"] == payload
        assert _Capture.received["signature"] == expected
        assert _Capture.received["content_type"] == "application/json"
    finally:
        server.shutdown()
        server.server_close()


def test_post_swallows_delivery_errors():
    # Nothing listening: must not raise.
    notify._post("http://127.0.0.1:9/nope", b"{}", "")
