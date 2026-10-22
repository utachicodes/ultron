from __future__ import annotations

from app import reports
from app.compliance import get_sector_pack


def test_sector_pack_aliases():
    assert get_sector_pack("sports") is not None
    assert get_sector_pack("football") is get_sector_pack("sports")
    assert get_sector_pack("banking") is None


def test_compliance_summary_sports_pack(client):
    res = client.get(
        "/compliance/summary",
        params={
            "total_findings": 7,
            "critical": 2,
            "high": 3,
            "medium": 1,
            "client_sector": "sports",
        },
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["sector_pack"]["label"].startswith("Sports")
    assert body["sector_pack"]["focus_areas"]
    assert any("matchday" in step.lower() for step in body["next_steps"])


def test_compliance_map_adds_sports_actions(client):
    res = client.post(
        "/compliance/map",
        json={
            "findings": [
                {
                    "title": "Exposed ticketing admin panel",
                    "severity": "critical",
                    "id": 1,
                    "target": "tickets.example.sn",
                },
                {
                    "title": "Academy portal missing MFA",
                    "severity": "high",
                    "id": 2,
                    "target": "academy.example.sn",
                },
            ],
            "client_sector": "sports",
        },
    )
    assert res.status_code == 200, res.text
    mappings = res.json()["mappings"]
    assert mappings
    assert all("sector_action" in m for m in mappings)
    actions = " ".join(m["sector_action"] for m in mappings).lower()
    assert "matchday revenue" in actions
    assert "safeguarding" in actions


def test_report_includes_sports_guidance():
    report = reports.generate_report(
        scan_id=1,
        scan_type="vulnerability",
        findings=[
            {
                "id": 1,
                "title": "Exposed ticketing admin panel",
                "description": "Public ticketing admin login.",
                "severity": "critical",
                "target": "tickets.dakarunitedfc.sn",
                "remediation": "Restrict to the club VPN.",
            }
        ],
        summary={"total_findings": 1},
        client_name="Dakar United FC",
        client_sector="sports",
    )

    assert report["sector_pack"]["label"].startswith("Sports")
    assert any("ticketing" in r.lower() for r in report["recommendations"])

    markdown = reports.report_to_markdown(report)
    assert "## Sector Guidance: Sports" in markdown
    assert "### Matchday and ticketing availability" in markdown
    assert "### Sector next steps" in markdown
