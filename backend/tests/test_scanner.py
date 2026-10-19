from __future__ import annotations

from app import scanner


def test_http_extraction_does_not_double_scheme(monkeypatch):
    calls = []

    def fake_fetch(url, timeout=8.0):
        calls.append(url)
        return {"status_code": 200, "headers": {}, "title": "ok", "body_preview": "", "server": "nginx"}

    monkeypatch.setattr(scanner, "_http_fetch", fake_fetch)
    scanner.run_http_extraction("https://portal.bank.sn")

    assert calls
    assert all("https://https://" not in u for u in calls)
    assert all(":80" not in u and ":443" not in u for u in calls)
    assert calls[0] == "https://portal.bank.sn"


def test_http_extraction_keeps_explicit_port(monkeypatch):
    calls = []
    monkeypatch.setattr(
        scanner,
        "_http_fetch",
        lambda url, timeout=8.0: calls.append(url) or {"status_code": 200, "headers": {}},
    )
    scanner.run_http_extraction("http://example.com:9000")

    assert calls == ["http://example.com:9000"]


def test_http_extraction_bare_host_tries_http_then_https(monkeypatch):
    calls = []
    monkeypatch.setattr(
        scanner,
        "_http_fetch",
        lambda url, timeout=8.0: calls.append(url) or {"error": "refused"},
    )
    scanner.run_http_extraction("bank.sn")

    assert calls[:2] == ["http://bank.sn", "https://bank.sn"]
    # fallback ports are attempted only after the standard ones fail
    assert "http://bank.sn:8080" in calls


def test_web_scan_type_only_does_http(monkeypatch):
    called = {"nuclei": False, "nmap": False}

    monkeypatch.setattr(scanner, "run_nuclei", lambda t: called.__setitem__("nuclei", True) or [])
    monkeypatch.setattr(scanner, "run_nmap", lambda t: called.__setitem__("nmap", True) or [])
    monkeypatch.setattr(scanner, "run_http_extraction", lambda t: [{"title": "http", "severity": "info"}])

    results = scanner.run_scan("example.com", "web")
    assert results == [{"title": "http", "severity": "info"}]
    assert called == {"nuclei": False, "nmap": False}


def test_full_scan_type_runs_everything(monkeypatch):
    monkeypatch.setattr(scanner, "run_nuclei", lambda t: [{"title": "n", "severity": "high"}])
    monkeypatch.setattr(scanner, "run_nmap", lambda t: [{"title": "p", "severity": "info"}])
    monkeypatch.setattr(scanner, "run_http_extraction", lambda t: [{"title": "h", "severity": "info"}])

    titles = [r["title"] for r in scanner.run_scan("example.com", "full")]
    assert titles == ["n", "p", "h"]
