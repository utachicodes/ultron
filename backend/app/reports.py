from __future__ import annotations

"""Report generation for scan findings.

Generates plain-language reports mapped to business impact and
Senegal cyber law obligations.
"""

import json
from typing import List, Dict, Any
from app.compliance import map_findings_to_compliance, get_compliance_summary


def generate_report(
    scan_id: int,
    scan_type: str,
    findings: List[Dict[str, Any]],
    summary: Dict[str, Any],
    client_name: str,
    client_sector: str | None = None,
) -> Dict[str, Any]:
    """Generate a comprehensive plain-language report."""
    critical = [f for f in findings if f.get("severity") == "critical"]
    high = [f for f in findings if f.get("severity") == "high"]
    medium = [f for f in findings if f.get("severity") == "medium"]
    low = [f for f in findings if f.get("severity") == "low"]

    compliance_mappings = map_findings_to_compliance(findings, client_sector)
    compliance_summary = get_compliance_summary(
        len(findings), len(critical), len(high), len(medium), client_sector
    )

    # Executive summary
    if critical:
        overall = "CRITICAL"
        exec_summary = f"This assessment identified {len(critical)} critical finding(s) requiring immediate attention."
    elif high:
        overall = "HIGH"
        exec_summary = f"This assessment identified {len(high)} high-severity finding(s) that should be prioritized for remediation."
    elif medium:
        overall = "MEDIUM"
        exec_summary = f"This assessment identified {len(medium)} medium-severity finding(s) that should be addressed."
    elif findings:
        overall = "LOW"
        exec_summary = f"This assessment identified {len(findings)} low-severity finding(s). Overall security posture is acceptable."
    else:
        overall = "CLEAN"
        exec_summary = "No significant findings were identified during this assessment."

    # Plain-language explanation
    plain_language = []
    if critical:
        plain_language.append(
            f"CRITICAL: {len(critical)} issue(s) were found that could allow attackers to compromise systems or steal data. These need immediate attention."
        )
    if high:
        plain_language.append(
            f"HIGH: {len(high)} issue(s) were found that significantly weaken security. These should be fixed within days."
        )
    if medium:
        plain_language.append(
            f"MEDIUM: {len(medium)} issue(s) were found that should be addressed in the coming weeks."
        )
    if low:
        plain_language.append(
            f"LOW: {len(low)} minor issue(s) were found. These are low priority but should be noted."
        )

    report = {
        "scan_id": scan_id,
        "scan_type": scan_type,
        "client_name": client_name,
        "client_sector": client_sector,
        "overall_rating": overall,
        "executive_summary": exec_summary,
        "plain_language": plain_language,
        "summary": summary,
        "findings_count": {
            "total": len(findings),
            "critical": len(critical),
            "high": len(high),
            "medium": len(medium),
            "low": len(low),
        },
        "compliance": compliance_summary,
        "compliance_mappings": compliance_mappings,
        "recommendations": _generate_recommendations(findings),
        "generated_at": None,
    }

    return report


def _generate_recommendations(findings: List[Dict[str, Any]]) -> List[str]:
    recommendations = []

    severities = [f.get("severity", "info") for f in findings]
    if "critical" in severities:
        recommendations.append("Address all critical findings immediately — these pose active risk to systems and data.")
    if "high" in severities:
        recommendations.append("Prioritize high-severity findings for remediation within 7 days.")
    if any("open_port" in (f.get("title", "")).lower() for f in findings):
        recommendations.append("Close unnecessary open ports and restrict access to essential services only.")
    if any("http" in (f.get("title", "")).lower() for f in findings):
        recommendations.append("Review HTTP service configurations and ensure headers follow security best practices.")
    if any("secret" in (f.get("title", "")).lower() or "key" in (f.get("title", "")).lower() for f in findings):
        recommendations.append("Rotate any exposed credentials and remove secrets from source code and configurations.")

    if not recommendations:
        recommendations.append("Maintain current security posture and continue regular monitoring.")

    return recommendations


def report_to_markdown(report: Dict[str, Any]) -> str:
    """Convert a report dict to Markdown format."""
    lines = []
    lines.append(f"# Security Assessment Report")
    lines.append(f"**Client:** {report['client_name']}")
    lines.append(f"**Scan Type:** {report['scan_type']}")
    lines.append(f"**Overall Rating:** {report['overall_rating']}")
    lines.append(f"**Scan ID:** {report['scan_id']}")
    lines.append("")

    lines.append("## Executive Summary")
    lines.append(report["executive_summary"])
    lines.append("")

    lines.append("## Plain-Language Summary")
    for p in report["plain_language"]:
        lines.append(f"- {p}")
    lines.append("")

    lines.append("## Findings Summary")
    lines.append(f"- Total: {report['findings_count']['total']}")
    lines.append(f"- Critical: {report['findings_count']['critical']}")
    lines.append(f"- High: {report['findings_count']['high']}")
    lines.append(f"- Medium: {report['findings_count']['medium']}")
    lines.append(f"- Low: {report['findings_count']['low']}")
    lines.append("")

    lines.append("## Recommendations")
    for r in report["recommendations"]:
        lines.append(f"- {r}")
    lines.append("")

    lines.append("## Compliance (Senegal Cyber Law 2026)")
    lines.append(f"- Framework: {report['compliance']['framework']}")
    lines.append(f"- CERT Notification Required: {report['compliance']['reporting_required']}")
    lines.append(f"- Notification Window: {report['compliance']['cert_notification_window_hours']} hours")
    lines.append(f"- Accreditation Recommended: {report['compliance']['accreditation_recommended']}")
    lines.append("")

    lines.append("## Compliance Mappings")
    for m in report["compliance_mappings"]:
        lines.append(f"- **{m['law_article']}**: {m['obligation']}")
        lines.append(f"  - Action: {m['action_required']}")
        lines.append(f"  - Priority: {m['priority']}")
    lines.append("")

    return "\n".join(lines)
