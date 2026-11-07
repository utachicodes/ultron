from __future__ import annotations

"""Tests for the SOC 2 readiness mapping (app/soc2.py)."""

from app.soc2 import CONTROL_CATEGORIES, get_soc2_readiness, map_findings_to_soc2


def test_map_findings_to_soc2_covers_every_control_category_always():
    controls = map_findings_to_soc2([])
    assert {c["control"] for c in controls} == set(CONTROL_CATEGORIES.keys())
    assert all(c["open_items"] == [] for c in controls)
    by_key = {c["control"]: c for c in controls}
    # HR Security isn't derivable from scan findings -- it must say so
    # honestly rather than default to a passing "no_gaps_found".
    assert by_key["hr_security"]["status"] == "not_assessed"
    assert all(
        c["status"] == "no_gaps_found" for key, c in by_key.items() if key != "hr_security"
    )


def test_map_findings_to_soc2_classifies_by_keyword():
    findings = [
        {"id": 1, "title": "Hardcoded API key found", "severity": "high"},
        {"id": 2, "title": "Backup monitoring disabled", "severity": "medium"},
        {"id": 3, "title": "Debug mode enabled in production", "severity": "medium"},
        {"id": 4, "title": "Outdated vulnerable dependency", "severity": "high"},
        {"id": 5, "title": "Unrelated informational banner", "severity": "info"},
    ]
    controls = map_findings_to_soc2(findings)
    by_key = {c["control"]: c for c in controls}

    assert by_key["logical_access"]["status"] == "gap"
    assert by_key["logical_access"]["open_items"][0]["finding_id"] == 1

    assert by_key["system_operations"]["status"] == "gap"
    assert by_key["change_management"]["status"] == "gap"
    assert by_key["risk_management"]["status"] == "gap"

    # An unmapped finding doesn't get force-fit into a category.
    assert by_key["incident_response"]["status"] == "no_gaps_found"
    assert by_key["hr_security"]["status"] == "not_assessed"


def test_map_findings_to_soc2_includes_confirmed_authz_leaks_as_logical_access_gaps():
    authz_findings = [
        {"id": 7, "method": "GET", "path": "/invoices/{id}", "verdict": "confirmed_leak"},
        {"id": 8, "method": "GET", "path": "/profile/{id}", "verdict": "no_leak"},
    ]
    controls = map_findings_to_soc2([], authz_findings)
    logical_access = next(c for c in controls if c["control"] == "logical_access")
    assert logical_access["status"] == "gap"
    assert len(logical_access["open_items"]) == 1
    assert logical_access["open_items"][0]["severity"] == "critical"
    assert "/invoices/{id}" in logical_access["open_items"][0]["title"]


def test_get_soc2_readiness_full_score_with_no_findings():
    result = get_soc2_readiness([])
    assert result["readiness_percent"] == 100
    assert result["gap_count"] == 0
    assert result["critical_gap_count"] == 0
    assert "not an attestation" in result["framework"]


def test_get_soc2_readiness_flags_critical_gaps_and_scores_below_100():
    findings = [{"id": 1, "title": "Hardcoded secret in repo", "severity": "critical"}]
    result = get_soc2_readiness(findings)
    assert result["gap_count"] >= 1
    assert result["critical_gap_count"] == 1
    assert result["readiness_percent"] < 100
    assert any("Logical Access" in s for s in result["next_steps"])


def test_get_soc2_readiness_report_type_changes_next_steps_language():
    type1 = get_soc2_readiness([], report_type="type1")
    type2 = get_soc2_readiness([], report_type="type2")
    assert any("point in time" in s for s in type1["next_steps"])
    assert any("observation" in s for s in type2["next_steps"])
