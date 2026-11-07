from __future__ import annotations

"""ISO/IEC 27001:2022 readiness mapping (Annex A controls).

Like `app.soc2`, this is a readiness *signal* built from Ultron's own
findings -- not a certification, audit, or Statement of Applicability. Only
an accredited certification body can issue an ISO 27001 certificate; this
module exists to show where the control gaps are before that engagement,
mirroring soc2compliance.com's positioning of SOC 2 vs. ISO 27001 as the two
frameworks clients most often ask about side by side.

Annex A (2022 revision) groups 93 controls into four themes. Only a subset
is derivable from automated scan findings -- physical controls and most
people controls require manual evidence, not a network/code scan, and are
reported as "not assessed by automated scanning" rather than silently
scored as passing.
"""

from typing import Any, Dict, List, Optional

ANNEX_A_THEMES: Dict[str, Dict[str, Any]] = {
    "organizational": {"label": "Organizational controls", "annex_range": "A.5.1-5.37"},
    "people": {"label": "People controls", "annex_range": "A.6.1-6.8"},
    "physical": {"label": "Physical controls", "annex_range": "A.7.1-7.14"},
    "technological": {"label": "Technological controls", "annex_range": "A.8.1-8.34"},
}

CONTROL_CATEGORIES: Dict[str, Dict[str, Any]] = {
    "access_control": {
        "label": "Identity and access management",
        "theme": "technological",
        "annex_controls": ["A.5.15", "A.5.16", "A.5.18", "A.8.2", "A.8.3", "A.8.5"],
        "description": "Access rights, authentication, and authorization checks (including IDOR/BOLA) over information and systems.",
        "assessable": True,
    },
    "vulnerability_management": {
        "label": "Vulnerability and patch management",
        "theme": "technological",
        "annex_controls": ["A.8.8"],
        "description": "Identification and remediation of technical vulnerabilities, including outdated or vulnerable dependencies.",
        "assessable": True,
    },
    "secure_development": {
        "label": "Secure development and change management",
        "theme": "technological",
        "annex_controls": ["A.8.25", "A.8.28", "A.8.29", "A.8.32"],
        "description": "Secure coding practices, code review, and controlled change/deployment -- dangerous calls, debug settings, and CI/CD misconfiguration reaching production.",
        "assessable": True,
    },
    "logging_monitoring": {
        "label": "Logging and monitoring",
        "theme": "technological",
        "annex_controls": ["A.8.15", "A.8.16"],
        "description": "Event logging and monitoring for anomalies, configuration drift, and backup/availability failures.",
        "assessable": True,
    },
    "network_security": {
        "label": "Network and communications security",
        "theme": "technological",
        "annex_controls": ["A.8.20", "A.8.21", "A.8.22", "A.8.24"],
        "description": "Network segmentation, secure configuration, and cryptography for data in transit.",
        "assessable": True,
    },
    "incident_management": {
        "label": "Incident management",
        "theme": "organizational",
        "annex_controls": ["A.5.24", "A.5.25", "A.5.26"],
        "description": "Planning, detection, and response to information security incidents.",
        "assessable": True,
    },
    "supplier_relationships": {
        "label": "Supplier and third-party security",
        "theme": "organizational",
        "annex_controls": ["A.5.19", "A.5.20", "A.5.21"],
        "description": "Security requirements and risk assessment for suppliers and dependencies. Not derivable from scan findings -- track vendor/dependency risk manually.",
        "assessable": False,
    },
    "people_security": {
        "label": "People security and awareness",
        "theme": "people",
        "annex_controls": ["A.6.1", "A.6.3"],
        "description": "Screening, security awareness training, and terms of employment. Not derivable from scan findings -- track manually.",
        "assessable": False,
    },
    "physical_security": {
        "label": "Physical and environmental security",
        "theme": "physical",
        "annex_controls": ["A.7.1", "A.7.2", "A.7.4"],
        "description": "Physical entry controls and protection of facilities and equipment. Out of scope for software/network scanning -- track manually.",
        "assessable": False,
    },
}

_SEVERITY_RANK = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}


def _map_finding_to_control(finding: Dict[str, Any]) -> Optional[str]:
    text = " ".join(
        str(finding.get(field, "")) for field in ("title", "description", "target", "issue_type")
    ).lower()

    if any(w in text for w in ("credential", "password", "secret", "token", "api key", "login", "mfa", "access control", "authoriz", "idor", "bola")):
        return "access_control"
    if any(w in text for w in ("outdated", "vulnerable", "cve", "patch", "dependency")):
        return "vulnerability_management"
    if any(w in text for w in ("debug mode", "eval(", "exec(", "deploy", "pipeline", "ci/cd", "cors")):
        return "secure_development"
    if any(w in text for w in ("backup", "monitor", "uptime", "availability", "config drift", "configuration drift")):
        return "logging_monitoring"
    if any(w in text for w in ("open port", "network", "ssl", "tls", "certificate", "firewall")):
        return "network_security"
    if any(w in text for w in ("incident", "alert", "breach")):
        return "incident_management"
    return None


def map_findings_to_iso27001(
    findings: List[Dict[str, Any]],
    authz_findings: Optional[List[Dict[str, Any]]] = None,
) -> List[Dict[str, Any]]:
    """Group findings (and confirmed authorization-hunt leaks) by Annex A
    control category. Every category is always reported, including the
    manual-only ones, so the readiness view states plainly what automated
    scanning can and cannot speak to."""
    hits: Dict[str, List[Dict[str, Any]]] = {k: [] for k in CONTROL_CATEGORIES}

    for finding in findings:
        category = _map_finding_to_control(finding)
        if category:
            hits[category].append(
                {
                    "finding_id": finding.get("id"),
                    "title": finding.get("title"),
                    "severity": (finding.get("severity") or "info").lower(),
                }
            )

    for af in authz_findings or []:
        if af.get("verdict") == "confirmed_leak":
            hits["access_control"].append(
                {
                    "finding_id": af.get("id"),
                    "title": f"Broken object-level authorization: {af.get('method')} {af.get('path')}",
                    "severity": "critical",
                }
            )

    controls = []
    for key, meta in CONTROL_CATEGORIES.items():
        if not meta["assessable"]:
            status = "not_assessed"
            open_items: List[Dict[str, Any]] = []
        else:
            open_items = sorted(hits[key], key=lambda h: _SEVERITY_RANK.get(h["severity"], 5))
            status = "gap" if open_items else "no_gaps_found"

        controls.append(
            {
                "control": key,
                "label": meta["label"],
                "theme": meta["theme"],
                "annex_controls": meta["annex_controls"],
                "description": meta["description"],
                "status": status,
                "open_items": open_items,
            }
        )
    return controls


def get_iso27001_readiness(
    findings: List[Dict[str, Any]],
    authz_findings: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    controls = map_findings_to_iso27001(findings, authz_findings)
    assessable = [c for c in controls if c["status"] != "not_assessed"]
    gaps = [c for c in assessable if c["status"] == "gap"]
    critical_gaps = [
        c for c in gaps if any(i["severity"] in ("critical", "high") for i in c["open_items"])
    ]
    not_assessed = [c for c in controls if c["status"] == "not_assessed"]

    readiness_percent = (
        round(100 * (len(assessable) - len(gaps)) / len(assessable)) if assessable else 100
    )

    next_steps: List[str] = []
    if critical_gaps:
        next_steps.append(
            "Remediate critical/high findings in: "
            + ", ".join(c["label"] for c in critical_gaps)
            + " before a Stage 1 certification audit."
        )
    next_steps.append(
        "Automated scanning cannot assess "
        + ", ".join(c["label"] for c in not_assessed)
        + " -- these need manual evidence (policies, screening records, physical access logs) "
        "for the Statement of Applicability."
    )
    next_steps.append(
        "A Stage 1 audit reviews documentation and scope (including the Statement of "
        "Applicability); Stage 2 reviews operating effectiveness. Engage an accredited "
        "certification body once the gaps above are closed."
    )

    return {
        "framework": "ISO/IEC 27001:2022 (Annex A) -- readiness mapping, not a certification",
        "disclaimer": (
            "This is an automated readiness signal built from Ultron's own findings, not an "
            "ISO 27001 audit, certification, or Statement of Applicability. Only an accredited "
            "certification body can issue an ISO 27001 certificate."
        ),
        "annex_a_themes": ANNEX_A_THEMES,
        "readiness_percent": readiness_percent,
        "controls": controls,
        "gap_count": len(gaps),
        "critical_gap_count": len(critical_gaps),
        "not_assessed_count": len(not_assessed),
        "next_steps": next_steps,
    }
