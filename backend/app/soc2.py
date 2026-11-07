from __future__ import annotations

"""SOC 2 readiness mapping (AICPA Trust Services Criteria).

This is a readiness *signal* built from Ultron's own findings -- it is not a
SOC 2 audit, attestation, or report. Only a licensed CPA firm can issue a
SOC 2 report; this module exists to show a client where its control gaps
are before that engagement starts, the same role the Bill No. 25/2026
mapping in `app.compliance` plays for local law.
"""

from typing import Any, Dict, List, Optional

TRUST_SERVICES_CRITERIA: Dict[str, Dict[str, Any]] = {
    "security": {
        "label": "Security",
        "required": True,
        "description": "Protection against unauthorized access, disclosure, or damage. The only criterion every SOC 2 report must include.",
    },
    "availability": {
        "label": "Availability",
        "required": False,
        "description": "Systems are available for operation and use as committed or agreed.",
    },
    "processing_integrity": {
        "label": "Processing Integrity",
        "required": False,
        "description": "System processing is complete, valid, accurate, timely, and authorized.",
    },
    "confidentiality": {
        "label": "Confidentiality",
        "required": False,
        "description": "Information designated as confidential is protected as committed or agreed.",
    },
    "privacy": {
        "label": "Privacy",
        "required": False,
        "description": "Personal information is collected, used, retained, disclosed, and disposed of in conformity with commitments.",
    },
}

CONTROL_CATEGORIES: Dict[str, Dict[str, Any]] = {
    "logical_access": {
        "label": "Logical Access Controls",
        "trust_services_criteria": ["security", "confidentiality"],
        "description": "MFA, least privilege, access reviews, deprovisioning, and authorization checks (including IDOR/BOLA).",
        "assessable": True,
    },
    "system_operations": {
        "label": "System Operations",
        "trust_services_criteria": ["security", "availability"],
        "description": "Monitoring, capacity management, backups, and detection of anomalies or configuration drift.",
        "assessable": True,
    },
    "change_management": {
        "label": "Change Management",
        "trust_services_criteria": ["security", "processing_integrity"],
        "description": "Code review, change approval, and deployment controls, including CI/CD and debug settings reaching production.",
        "assessable": True,
    },
    "risk_management": {
        "label": "Risk Management",
        "trust_services_criteria": ["security"],
        "description": "Vulnerability management, patching, and vendor/dependency risk.",
        "assessable": True,
    },
    "incident_response": {
        "label": "Incident Response",
        "trust_services_criteria": ["security", "availability"],
        "description": "Incident detection, a documented response plan, and post-incident review.",
        "assessable": True,
    },
    "hr_security": {
        "label": "HR Security",
        "trust_services_criteria": ["security"],
        "description": "Background checks, security awareness training, and onboarding/offboarding access control. Not derivable from scan findings -- tracked manually.",
        "assessable": False,
    },
}

_SEVERITY_RANK = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}


def _map_finding_to_control(finding: Dict[str, Any]) -> Optional[str]:
    """Heuristic, keyword-based mapping: the scanner reports generic
    titles/descriptions, so the control category is inferred from them
    rather than from a dedicated SOC 2 scanner."""
    text = " ".join(
        str(finding.get(field, "")) for field in ("title", "description", "target", "issue_type")
    ).lower()

    if any(w in text for w in ("credential", "password", "secret", "token", "api key", "login", "mfa", "access control", "authoriz", "idor", "bola")):
        return "logical_access"
    if any(w in text for w in ("backup", "monitor", "uptime", "availability", "capacity", "config drift", "configuration drift")):
        return "system_operations"
    if any(w in text for w in ("debug mode", "eval(", "exec(", "deploy", "pipeline", "ci/cd", "cors")):
        return "change_management"
    if any(w in text for w in ("outdated", "vulnerable", "cve", "patch", "dependency")):
        return "risk_management"
    if any(w in text for w in ("incident", "alert", "breach")):
        return "incident_response"
    return None


def map_findings_to_soc2(
    findings: List[Dict[str, Any]],
    authz_findings: Optional[List[Dict[str, Any]]] = None,
) -> List[Dict[str, Any]]:
    """Group findings (and confirmed authorization-hunt leaks) by SOC 2
    control category. Returns one entry per control category, always --
    categories with no matching findings are reported as "no gaps found",
    not omitted, so the readiness view is complete rather than partial."""
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
            hits["logical_access"].append(
                {
                    "finding_id": af.get("id"),
                    "title": f"Broken object-level authorization: {af.get('method')} {af.get('path')}",
                    "severity": "critical",
                }
            )

    controls = []
    for key, meta in CONTROL_CATEGORIES.items():
        if not meta["assessable"]:
            status, open_items = "not_assessed", []
        else:
            open_items = sorted(hits[key], key=lambda h: _SEVERITY_RANK.get(h["severity"], 5))
            status = "gap" if open_items else "no_gaps_found"

        controls.append(
            {
                "control": key,
                "label": meta["label"],
                "trust_services_criteria": meta["trust_services_criteria"],
                "description": meta["description"],
                "status": status,
                "open_items": open_items,
            }
        )
    return controls


def get_soc2_readiness(
    findings: List[Dict[str, Any]],
    authz_findings: Optional[List[Dict[str, Any]]] = None,
    report_type: str = "type2",
) -> Dict[str, Any]:
    """Build a SOC 2 readiness summary from Ultron's own findings.

    `report_type` is advisory only (`type1` or `type2`); it does not change
    the mapping, only the explanatory next step about observation windows.
    """
    controls = map_findings_to_soc2(findings, authz_findings)
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
            + " before scheduling an auditor walkthrough."
        )
    next_steps.append(
        "HR Security (background checks, security training, onboarding/offboarding) isn't "
        "derivable from scan findings -- track it manually alongside these results."
    )
    if report_type == "type1":
        next_steps.append(
            "A Type I report attests controls at a single point in time -- it can be pursued "
            "once the gaps above are closed."
        )
    else:
        next_steps.append(
            "A Type II report attests operating effectiveness over a 3-12 month observation "
            "window; most customers ask for Type II, and it should start only after the gaps "
            "above are closed."
        )
    next_steps.append(
        "Typical first-time path to a SOC 2 Type II report is 7-14 months once Security-"
        "category gaps are closed; engage a licensed CPA firm for the actual audit."
    )

    return {
        "framework": "SOC 2 (AICPA Trust Services Criteria) -- readiness mapping, not an attestation",
        "disclaimer": (
            "This is an automated readiness signal built from Ultron's own findings, not a "
            "SOC 2 audit or attestation. A SOC 2 report can only be issued by a licensed CPA firm."
        ),
        "trust_services_criteria": TRUST_SERVICES_CRITERIA,
        "report_type_recommended": report_type,
        "readiness_percent": readiness_percent,
        "controls": controls,
        "gap_count": len(gaps),
        "critical_gap_count": len(critical_gaps),
        "not_assessed_count": len(not_assessed),
        "next_steps": next_steps,
    }
