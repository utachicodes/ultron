from __future__ import annotations

"""Compliance readiness mapping to Senegal's 2026 Cybersecurity Law.

Maps findings to regulatory obligations under the new law establishing
the National Cybersecurity Authority, National CERT, mandatory incident
reporting, and local hosting requirements.
"""

from typing import List, Dict, Any


# Senegal Cyber Law 2026 - Article mappings
LAW_ARTICLES = {
    "incident_reporting": {
        "article": "Article 14 - Mandatory Incident Reporting",
        "description": "Security incidents must be reported to the National CERT within 72 hours.",
        "severity_threshold": ["critical", "high"],
    },
    "vulnerability_reporting": {
        "article": "Article 16 - Vulnerability Disclosure",
        "description": "Discovered vulnerabilities in critical infrastructure must be disclosed to the National Cybersecurity Authority.",
        "severity_threshold": ["critical", "high", "medium"],
    },
    "local_hosting": {
        "article": "Article 22 - Local Hosting of Public-Sector Data",
        "description": "Public-sector data must be hosted within Senegal or accredited sovereign infrastructure.",
        "severity_threshold": ["critical"],
    },
    "security_audit": {
        "article": "Article 10 - Regular Security Audits",
        "description": "Critical infrastructure operators must undergo annual security audits by accredited providers.",
        "severity_threshold": ["info"],
    },
    "ai_governance": {
        "article": "Article 30 - AI Governance Standards",
        "description": "AI systems in high-risk sectors require documented governance and human oversight.",
        "severity_threshold": ["medium"],
    },
}


def map_findings_to_compliance(
    findings: List[Dict[str, Any]],
    client_sector: str | None = None,
) -> List[Dict[str, Any]]:
    """Map scan findings to Senegal cyber law obligations."""
    mappings: List[Dict[str, Any]] = []

    for finding in findings:
        severity = finding.get("severity", "info").lower()

        # Incident reporting - critical/high findings
        if severity in LAW_ARTICLES["incident_reporting"]["severity_threshold"]:
            mappings.append({
                "finding_id": finding.get("id"),
                "finding_title": finding.get("title"),
                "severity": severity,
                "law_article": LAW_ARTICLES["incident_reporting"]["article"],
                "obligation": LAW_ARTICLES["incident_reporting"]["description"],
                "action_required": "Report to National CERT within 72 hours if this constitutes a security incident.",
                "priority": "immediate" if severity == "critical" else "urgent",
            })

        # Vulnerability reporting
        if severity in LAW_ARTICLES["vulnerability_reporting"]["severity_threshold"]:
            mappings.append({
                "finding_id": finding.get("id"),
                "finding_title": finding.get("title"),
                "severity": severity,
                "law_article": LAW_ARTICLES["vulnerability_reporting"]["article"],
                "obligation": LAW_ARTICLES["vulnerability_reporting"]["description"],
                "action_required": "Consider disclosure to National Cybersecurity Authority for critical infrastructure.",
                "priority": "high",
            })

        # AI governance findings
        if "ai" in finding.get("title", "").lower() or "algorithm" in finding.get("title", "").lower():
            if severity in LAW_ARTICLES["ai_governance"]["severity_threshold"]:
                mappings.append({
                    "finding_id": finding.get("id"),
                    "finding_title": finding.get("title"),
                    "severity": severity,
                    "law_article": LAW_ARTICLES["ai_governance"]["article"],
                    "obligation": LAW_ARTICLES["ai_governance"]["description"],
                    "action_required": "Document AI governance and ensure human oversight.",
                    "priority": "medium",
                })

    # Deduplicate by law article
    seen = set()
    unique_mappings = []
    for m in mappings:
        key = m["law_article"]
        if key not in seen:
            seen.add(key)
            unique_mappings.append(m)

    return unique_mappings


def get_compliance_summary(
    total_findings: int,
    critical: int,
    high: int,
    medium: int,
    client_sector: str | None = None,
) -> Dict[str, Any]:
    """Generate a compliance readiness summary."""
    return {
        "framework": "Senegal Cybersecurity Law 2026",
        "client_sector": client_sector or "not_specified",
        "total_findings": total_findings,
        "critical": critical,
        "high": high,
        "medium": medium,
        "reporting_required": critical > 0 or high > 0,
        "cert_notification_window_hours": 72,
        "accreditation_recommended": critical > 0 or high > 0 or medium > 0,
        "next_steps": [
            "Review critical and high findings with legal counsel",
            "File incident report with National CERT if applicable",
            "Schedule remediation within 30 days for critical findings",
            "Consider accreditation with National Cybersecurity Authority",
        ],
    }
