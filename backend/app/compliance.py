from __future__ import annotations

"""Compliance readiness mapping to Senegal's 2026 Cybersecurity Law.

Maps findings to regulatory obligations under the new law establishing
the National Cybersecurity Authority, National CERT, mandatory incident
reporting, and local hosting requirements.
"""

from typing import List, Dict, Any


# Sector-specific operational guidance. These are deliberately separate from
# LAW_ARTICLES below: the law mappings are legal obligations, while a sector
# pack is the practical checklist an operator should walk through for that
# kind of client. Kept as data so the console, reports, and API all read the
# same source instead of drifting.
SECTOR_PACKS: Dict[str, Dict[str, Any]] = {
    "sports": {
        "label": "Sports (clubs, federations, academies)",
        "summary": (
            "Sports organizations concentrate athlete, minor, medical, and fan-payment "
            "data across ticketing, membership, streaming, and academy systems. Matchday "
            "availability and athlete privacy are the two failure modes that matter most."
        ),
        "focus_areas": [
            {
                "area": "Matchday and ticketing availability",
                "why": "Ticketing, streaming, and results endpoints are revenue- and reputation-critical on matchday.",
                "checks": [
                    "Monitor ticketing, streaming, and results endpoints from T-24h to T+6h.",
                    "Confirm payment webhooks and mobile-money callbacks have failover and alerting.",
                    "Keep a tested offline or manual ticketing fallback for connectivity loss.",
                ],
            },
            {
                "area": "Athlete and minor safeguarding data",
                "why": "Academies and federations hold passports, medical notes, and records for minors.",
                "checks": [
                    "Inventory every system that holds athlete, guardian, or academy records.",
                    "Restrict and log access; require named approval for exports.",
                    "Redact athlete names, dates of birth, passport numbers, and medical terms before AI use.",
                ],
            },
            {
                "area": "Fan, membership, and payment data",
                "why": "Fan accounts, memberships, and mobile-money payments create dense PII and fraud value.",
                "checks": [
                    "Require MFA on admin and back-office accounts.",
                    "Scan public properties for leaked API keys and tokens.",
                    "Review third-party scripts on club and ticketing sites.",
                ],
            },
            {
                "area": "Federation governance and evidence",
                "why": "Club licensing, sponsor due diligence, and donor audits ask for evidence, not assurances.",
                "checks": [
                    "Keep an immutable record of scans, reviews, and remediations.",
                    "Attach screenshots and scanner output to high-severity findings.",
                    "Produce a plain-language report for the board and sponsors each cycle.",
                ],
            },
            {
                "area": "AI in scouting, selection, and fan engagement",
                "why": "AI tools increasingly touch athlete evaluation and fan data, which triggers human-oversight obligations.",
                "checks": [
                    "Document where AI is used and who reviews its output.",
                    "Keep sensitive prompts on-premises or sanitize them before they leave.",
                    "Retain an audit log of AI queries without storing raw athlete data.",
                ],
            },
        ],
        "next_steps": [
            "Inventory club, ticketing, academy, streaming, and payment endpoints before the next matchday.",
            "Enable matchday monitoring for ticketing, streaming, and results endpoints.",
            "Redact athlete and minor data before any AI-assisted report or communication.",
            "Store the scan report with the club-licensing or sponsor due-diligence file.",
        ],
    },
}

SECTOR_ALIASES = {
    "sport": "sports",
    "football": "sports",
    "club": "sports",
    "federation": "sports",
    "academy": "sports",
}


def get_sector_pack(sector: str | None) -> Dict[str, Any] | None:
    """Return the operational guidance pack for a client sector, if one exists."""
    if not sector:
        return None
    key = sector.strip().lower()
    key = SECTOR_ALIASES.get(key, key)
    return SECTOR_PACKS.get(key)


def _sports_sector_action(finding: Dict[str, Any]) -> str:
    """Map a finding to the sports-specific action an operator should take.

    Keyword-based on purpose: the scanner reports generic titles, so the
    sector context has to be derived from the asset and finding text rather
    than from a dedicated sports scanner.
    """
    text = " ".join(
        str(finding.get(field, "")) for field in ("title", "description", "target")
    ).lower()

    if any(word in text for word in ("ticket", "payment", "mobile money", "pos", "gateway")):
        return (
            "Matchday revenue risk: verify payment failover, rotate any exposed payment "
            "credentials, and keep a manual ticketing fallback ready."
        )
    if any(word in text for word in ("athlete", "academy", "medical", "roster", "guardian", "minor")):
        return (
            "Athlete safeguarding risk: restrict access, involve the designated safeguarding "
            "lead, and document how the record was handled."
        )
    if any(word in text for word in ("fan", "member", "account", "login", "password")):
        return (
            "Fan and membership data risk: force credential resets where exposure is likely, "
            "notify affected users, and review third-party scripts."
        )
    if any(word in text for word in ("stream", "broadcast", "result", "score", "match")):
        return (
            "Matchday availability risk: add a monitor, prepare a fallback, and confirm the "
            "incident owner before kickoff."
        )
    return (
        "Record this finding in the club's licensing, sponsor, or donor evidence file and "
        "assign a named owner for remediation."
    )


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
    """Map scan findings to Senegal cyber law obligations.

    For sectors with a pack (currently sports), each mapping also carries a
    ``sector_action`` written in that sector's operational language.
    """
    mappings: List[Dict[str, Any]] = []
    sector_pack = get_sector_pack(client_sector)

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

    # Attach sector-specific operational context. Look findings up by id
    # first, then title, because the API accepts caller-supplied findings
    # that may not carry an id.
    if sector_pack is SECTOR_PACKS.get("sports"):
        by_id = {f.get("id"): f for f in findings if f.get("id") is not None}
        by_title = {f.get("title"): f for f in findings if f.get("title")}
        for mapping in mappings:
            finding = (
                by_id.get(mapping.get("finding_id"))
                or by_title.get(mapping.get("finding_title"))
                or {}
            )
            mapping["sector_action"] = _sports_sector_action(finding)

    # Deduplicate by law article (and sector action, when present, so a sports
    # client keeps one actionable line per distinct operational risk).
    seen = set()
    unique_mappings = []
    for m in mappings:
        key = (m["law_article"], m.get("sector_action"))
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
    sector_pack = get_sector_pack(client_sector)
    next_steps = [
        "Review critical and high findings with legal counsel",
        "File incident report with National CERT if applicable",
        "Schedule remediation within 30 days for critical findings",
        "Consider accreditation with National Cybersecurity Authority",
    ]
    if sector_pack:
        # Sector-specific actions come first: they are the concrete things an
        # operator can do this week, before the legal/procurement steps.
        next_steps = sector_pack["next_steps"] + next_steps

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
        "sector_pack": sector_pack,
        "next_steps": next_steps,
    }
