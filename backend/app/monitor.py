from __future__ import annotations

"""Continuous AI-agent monitoring engine.

Watches client environments for:
- Anomalous access patterns
- Configuration drift from baseline
- Leaked credentials on open/dark web
- Policy-violating deployments
"""

import json
import socket
import ssl
import urllib.request
import re
from typing import List, Dict, Any


def _http_fetch(target: str, timeout: float = 8.0) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "status_code": None,
        "headers": {},
        "server": None,
        "title": None,
        "body_preview": "",
    }

    if not target.startswith(("http://", "https://")):
        url = "http://" + target
    else:
        url = target

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Ultorn-Monitor/1.0"})
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            result["status_code"] = resp.getcode()
            result["headers"] = dict(resp.headers)
            result["server"] = resp.headers.get("Server")
            body = resp.read(65536).decode("utf-8", errors="replace")
            result["body_preview"] = body
            m = re.search(r"<title>(.*?)</title>", body, re.IGNORECASE | re.DOTALL)
            if m:
                result["title"] = m.group(1).strip()
    except Exception as e:
        result["error"] = str(e)

    return result


def check_target(target: str, monitor_type: str, baseline: Dict[str, Any] | None = None) -> List[Dict[str, Any]]:
    """Run a monitoring check against a target. Returns alerts if anomalies detected."""
    alerts: List[Dict[str, Any]] = []

    if monitor_type == "access_anomaly":
        result = _http_fetch(target)
        if "error" in result:
            alerts.append({
                "title": f"Target unreachable: {target}",
                "description": f"Monitor could not reach {target}: {result['error']}",
                "severity": "high",
                "evidence": {"target": target, "error": result["error"]},
            })
        else:
            status = result.get("status_code")
            if status and status >= 500:
                alerts.append({
                    "title": f"Server error on {target}",
                    "description": f"Target returned HTTP {status}",
                    "severity": "high",
                    "evidence": {"target": target, "status_code": status},
                })

    elif monitor_type == "config_drift":
        result = _http_fetch(target)
        if "error" in result:
            alerts.append({
                "title": f"Config check failed: {target}",
                "description": f"Could not fetch config from {target}: {result['error']}",
                "severity": "medium",
                "evidence": {"target": target, "error": result["error"]},
            })
        else:
            server = result.get("server", "")
            baseline_server = (baseline or {}).get("server", "")
            if baseline_server and server and server != baseline_server:
                alerts.append({
                    "title": f"Configuration drift on {target}",
                    "description": f"Server header changed from '{baseline_server}' to '{server}'",
                    "severity": "medium",
                    "evidence": {
                        "target": target,
                        "baseline_server": baseline_server,
                        "current_server": server,
                    },
                })

    elif monitor_type == "leaked_cred":
        result = _http_fetch(target)
        if "error" in result:
            alerts.append({
                "title": f"Credential scan failed: {target}",
                "description": f"Could not scan {target} for leaked credentials: {result['error']}",
                "severity": "low",
                "evidence": {"target": target, "error": result["error"]},
            })
        else:
            body = result.get("body_preview", "") or ""
            headers_str = json.dumps(result.get("headers", {}))
            combined = body + headers_str

            key_patterns = [
                (re.compile(r'(?i)(api[_-]?key|secret|password)\s*[:=]\s*[\'"][^\'"]{8,}[\'"]'), "exposed_api_key"),
                (re.compile(r'\b(sk|pk|wh|ghp|gho)-[A-Za-z0-9]{12,}\b'), "exposed_secret_key"),
            ]

            for pattern, issue_type in key_patterns:
                if pattern.search(combined):
                    alerts.append({
                        "title": f"Potential leaked credential on {target}",
                        "description": f"Detected possible {issue_type.replace('_', ' ')} in exposed content",
                        "severity": "critical",
                        "evidence": {"target": target, "issue_type": issue_type},
                    })
                    break

    elif monitor_type == "policy_violation":
        result = _http_fetch(target)
        if "error" in result:
            alerts.append({
                "title": f"Policy check failed: {target}",
                "description": f"Could not verify policy on {target}: {result['error']}",
                "severity": "medium",
                "evidence": {"target": target, "error": result["error"]},
            })
        else:
            server = result.get("server", "") or ""
            if "Apache/2.2" in server:
                alerts.append({
                    "title": f"Outdated server software on {target}",
                    "description": f"Server running Apache 2.2 ({server}), which is EOL",
                    "severity": "high",
                    "evidence": {"target": target, "server": server},
                })

    return alerts


def run_monitoring_check(monitor_type: str, target: str, baseline: Dict[str, Any] | None = None) -> List[Dict[str, Any]]:
    """Entry point for monitoring checks."""
    return check_target(target, monitor_type, baseline)
