from __future__ import annotations

"""End-to-end tests for app/browser_crawl.py against a real (tiny, local)
HTTP server and a real headless Chromium -- not mocked. Skips gracefully if
Playwright or its Chromium binary isn't installed in this environment.
"""

import http.server
import threading
from urllib.parse import parse_qs

import pytest

from app import browser_crawl

pytestmark = pytest.mark.skipif(
    not browser_crawl.is_available(), reason="playwright is not installed in this environment"
)

LOGIN_PAGE = """
<html><body>
<form method="post" action="/login">
  <input name="username" id="username">
  <input name="password" id="password" type="password">
  <button type="submit" id="submit">Log in</button>
</form>
</body></html>
"""

# Each username "owns" a different invoice id, simulating two real accounts.
OWNED_INVOICE = {"alice": "1024", "bob": "2048"}


def _dashboard_html(username: str) -> str:
    invoice_id = OWNED_INVOICE.get(username, "0")
    return f"""
    <html><body>
      <h1>Welcome {username}</h1>
      <a href="/invoices/{invoice_id}">My invoice</a>
      <a href="/profile">My profile</a>
    </body></html>
    """


class _Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass  # keep test output quiet

    def _send_html(self, body: str, cookie: str = None, status: int = 200):
        self.send_response(status)
        self.send_header("Content-Type", "text/html")
        if cookie:
            self.send_header("Set-Cookie", cookie)
        self.end_headers()
        self.wfile.write(body.encode())

    def do_GET(self):
        cookie_header = self.headers.get("Cookie", "")
        username = None
        for part in cookie_header.split(";"):
            if "=" in part and part.strip().startswith("session"):
                username = part.strip().split("=", 1)[1]

        if self.path == "/login":
            self._send_html(LOGIN_PAGE)
        elif self.path == "/dashboard" and username:
            self._send_html(_dashboard_html(username))
        elif self.path.startswith("/invoices/"):
            self._send_html(f"<html><body>Invoice {self.path.rsplit('/', 1)[-1]}</body></html>")
        elif self.path == "/profile":
            self._send_html("<html><body>Profile page</body></html>")
        else:
            self._send_html("<html><body>Not found</body></html>", status=404)

    def do_POST(self):
        if self.path == "/login":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length).decode()
            fields = parse_qs(body)
            username = fields.get("username", [""])[0]
            self.send_response(302)
            self.send_header("Set-Cookie", f"session={username}")
            self.send_header("Location", "/dashboard")
            self.end_headers()
        else:
            self._send_html("", status=404)


@pytest.fixture
def test_server():
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{port}"
    server.shutdown()
    thread.join(timeout=5)


def test_login_and_crawl_finds_role_owned_invoice(test_server):
    result = browser_crawl.login_and_crawl(
        start_url=f"{test_server}/dashboard",
        role_name="alice",
        login={
            "url": f"{test_server}/login",
            "username_selector": "#username",
            "username": "alice",
            "password_selector": "#password",
            "password": "whatever",
            "submit_selector": "#submit",
        },
        max_pages=5,
    )

    assert result["role"] == "alice"
    assert "session=alice" in result["cookie_header"]
    assert any(u.endswith("/invoices/1024") for u in result["visited_urls"])

    probes = browser_crawl.build_probes_from_crawl(result)
    assert any(p["path"] == "/invoices/{id}" and p["owner_value"] == "1024" for p in probes)
    assert all(p["owner_role"] == "alice" for p in probes)


def test_crawl_roles_and_build_authz_config_combines_two_roles(test_server):
    config = browser_crawl.crawl_roles_and_build_authz_config(
        base_url=test_server,
        role_configs=[
            {
                "role_name": "alice",
                "start_url": f"{test_server}/dashboard",
                "login": {
                    "url": f"{test_server}/login",
                    "username_selector": "#username",
                    "username": "alice",
                    "password_selector": "#password",
                    "password": "x",
                    "submit_selector": "#submit",
                },
            },
            {
                "role_name": "bob",
                "start_url": f"{test_server}/dashboard",
                "login": {
                    "url": f"{test_server}/login",
                    "username_selector": "#username",
                    "username": "bob",
                    "password_selector": "#password",
                    "password": "x",
                    "submit_selector": "#submit",
                },
            },
        ],
        max_pages=5,
    )

    assert config["base_url"] == test_server
    role_names = {r["name"] for r in config["roles"]}
    assert role_names == {"alice", "bob"}

    # One probe per distinct (method, path) template, deduped across roles,
    # owned by whichever role's crawl it came from.
    invoice_probes = [p for p in config["probes"] if p["path"] == "/invoices/{id}"]
    assert len(invoice_probes) == 1
    assert invoice_probes[0]["owner_value"] in ("1024", "2048")


def test_login_and_crawl_without_login_crawls_public_pages(test_server):
    result = browser_crawl.login_and_crawl(
        start_url=f"{test_server}/profile", role_name="guest", login=None, max_pages=3
    )
    assert result["role"] == "guest"
    assert any(u.endswith("/profile") for u in result["visited_urls"])


def test_raises_actionable_error_without_playwright(monkeypatch):
    import builtins

    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "playwright.sync_api":
            raise ImportError("no playwright")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    with pytest.raises(RuntimeError, match="playwright install chromium"):
        browser_crawl.login_and_crawl("http://example.test", "role", login=None)


def test_crawl_and_suggest_authz_config_endpoint(client, test_server):
    res = client.post(
        "/authz-hunts/crawl-and-suggest",
        json={
            "base_url": test_server,
            "max_pages": 5,
            "roles": [
                {
                    "role_name": "alice",
                    "start_url": f"{test_server}/dashboard",
                    "login": {
                        "url": f"{test_server}/login",
                        "username_selector": "#username",
                        "username": "alice",
                        "password_selector": "#password",
                        "password": "x",
                        "submit_selector": "#submit",
                    },
                },
                {
                    "role_name": "bob",
                    "start_url": f"{test_server}/dashboard",
                    "login": {
                        "url": f"{test_server}/login",
                        "username_selector": "#username",
                        "username": "bob",
                        "password_selector": "#password",
                        "password": "x",
                        "submit_selector": "#submit",
                    },
                },
            ],
        },
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert {r["name"] for r in body["roles"]} == {"alice", "bob"}
    assert any(p["path"] == "/invoices/{id}" for p in body["probes"])


def test_crawl_and_suggest_requires_two_roles(client, test_server):
    res = client.post(
        "/authz-hunts/crawl-and-suggest",
        json={
            "base_url": test_server,
            "roles": [{"role_name": "solo", "start_url": f"{test_server}/dashboard"}],
        },
    )
    assert res.status_code == 400
