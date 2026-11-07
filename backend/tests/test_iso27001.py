from __future__ import annotations

"""Tests for the ISO 27001 readiness mapping (app/iso27001.py)."""

from app.iso27001 import CONTROL_CATEGORIES, get_iso27001_readiness, map_findings_to_iso27001


def test_map_findings_covers_every_control_category_always():
    controls = map_findings_to_iso27001([])
    assert {c["control"] for c in controls} == set(CONTROL_CATEGORIES.keys())


def test_non_assessable_categories_are_marked_not_assessed_not_passing():
    controls = map_findings_to_iso27001([])
    by_key = {c["control"]: c for c in controls}
    for key in ("supplier_relationships", "people_security", "physical_security"):
        assert by_key[key]["status"] == "not_assessed"
        assert by_key[key]["open_items"] == []


def test_classifies_findings_by_keyword():
    findings = [
        {"id": 1, "title": "Hardcoded API key found", "severity": "high"},
        {"id": 2, "title": "Outdated vulnerable dependency", "severity": "high"},
        {"id": 3, "title": "Debug mode enabled in production", "severity": "medium"},
        {"id": 4, "title": "Backup monitoring disabled", "severity": "medium"},
        {"id": 5, "title": "Open SSH port with weak TLS certificate", "severity": "medium"},
        {"id": 6, "title": "Security incident alert ignored", "severity": "high"},
    ]
    controls = map_findings_to_iso27001(findings)
    by_key = {c["control"]: c for c in controls}

    assert by_key["access_control"]["status"] == "gap"
    assert by_key["vulnerability_management"]["status"] == "gap"
    assert by_key["secure_development"]["status"] == "gap"
    assert by_key["logging_monitoring"]["status"] == "gap"
    assert by_key["network_security"]["status"] == "gap"
    assert by_key["incident_management"]["status"] == "gap"


def test_confirmed_authz_leak_counts_as_access_control_gap():
    authz_findings = [{"id": 9, "method": "GET", "path": "/accounts/{id}", "verdict": "confirmed_leak"}]
    controls = map_findings_to_iso27001([], authz_findings)
    access_control = next(c for c in controls if c["control"] == "access_control")
    assert access_control["status"] == "gap"
    assert access_control["open_items"][0]["severity"] == "critical"


def test_readiness_excludes_not_assessed_from_the_percentage():
    result = get_iso27001_readiness([])
    assert result["readiness_percent"] == 100
    assert result["not_assessed_count"] == 3
    assert result["gap_count"] == 0


def test_readiness_flags_critical_gaps():
    findings = [{"id": 1, "title": "Hardcoded secret in repo", "severity": "critical"}]
    result = get_iso27001_readiness(findings)
    assert result["critical_gap_count"] == 1
    assert result["readiness_percent"] < 100
    assert any("Identity and access management" in s for s in result["next_steps"])
    assert any("manual evidence" in s for s in result["next_steps"])
