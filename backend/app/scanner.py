from __future__ import annotations

"""Vulnerability scanning engine with full data extraction.

For sandbox testing: connects to targets, grabs service banners, HTTP
headers, page titles, response bodies, and stores everything as evidence.
No redaction, no restraints.
"""

import subprocess
import json
import socket
import ssl
import xml.etree.ElementTree as ET
import re
import urllib.request
import urllib.error
from typing import List, Dict, Any
from app.config import settings


def _grab_banner(host: str, port: int, timeout: float = 5.0) -> str:
    """Connect to a port and grab the service banner."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect((host, port))
        try:
            sock.sendall(b"GET / HTTP/1.0\r\nHost: %s\r\n\r\n" % host.encode())
        except Exception:
            pass
        data = sock.recv(2048)
        sock.close()
        return data.decode("utf-8", errors="replace").strip()
    except Exception as e:
        return f"[banner_grab_failed] {str(e)}"


def _http_fetch(target: str, timeout: float = 8.0) -> Dict[str, Any]:
    """Fetch a target over HTTP/HTTPS and extract headers, title, body."""
    result: Dict[str, Any] = {
        "status_code": None,
        "headers": {},
        "title": None,
        "body_preview": None,
        "server": None,
    }

    if target.startswith("http://"):
        url = target
    elif target.startswith("https://"):
        url = target
    else:
        url = "http://" + target

    try:
        req = urllib.request.Request(
            url, headers={"User-Agent": "Ultorn-Scanner/1.0"}
        )
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            result["status_code"] = resp.getcode()
            result["headers"] = dict(resp.headers)
            result["server"] = resp.headers.get("Server")
            body = resp.read(4096).decode("utf-8", errors="replace")
            result["body_preview"] = body[:2000]

            m = re.search(r"<title>(.*?)</title>", body, re.IGNORECASE | re.DOTALL)
            if m:
                result["title"] = m.group(1).strip()
    except Exception as e:
        result["error"] = str(e)

    return result


def run_nuclei(target: str, template: str | None = None) -> List[Dict[str, Any]]:
    """Run Nuclei scanner. Extracts matched data as evidence."""
    findings: List[Dict[str, Any]] = []
    cmd = [settings.nuclei_path, "-target", target, "-json", "-silent"]
    if template:
        cmd.extend(["-t", template])

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=settings.scanner_timeout
        )
        if result.returncode not in (0, 1):
            return [{"error": f"nuclei exited {result.returncode}: {result.stderr}"}]

        for line in result.stdout.strip().splitlines():
            if not line:
                continue
            try:
                entry = json.loads(line)
                findings.append(_normalize_nuclei_finding(entry))
            except json.JSONDecodeError:
                continue
    except FileNotFoundError:
        return [{"error": "nuclei binary not found"}]
    except subprocess.TimeoutExpired:
        return [{"error": "nuclei scan timed out"}]
    except Exception as e:
        return [{"error": str(e)}]

    return findings


def _normalize_nuclei_finding(entry: Dict[str, Any]) -> Dict[str, Any]:
    info = entry.get("info", {})
    matched_at = entry.get("matched-at", "")
    extracted = entry.get("extracted-extractor", "")
    name = info.get("name", "Unknown")
    severity = info.get("severity", "info").lower()

    return {
        "title": name,
        "description": info.get("description", ""),
        "severity": severity,
        "target": matched_at,
        "evidence": {
            "matched_at": matched_at,
            "extracted_content": extracted,
            "matcher_name": info.get("matcher-name", ""),
            "raw": entry,
        },
        "remediation": info.get("remediation", "Review and remediate per vendor guidance."),
        "reference": info.get("reference", ""),
        "tags": info.get("tags", []),
    }


def run_nmap(target: str) -> List[Dict[str, Any]]:
    """Run nmap with version detection and banner grabbing. Extracts real data."""
    findings: List[Dict[str, Any]] = []
    cmd = ["nmap", "-sV", "-sC", "-T4", "-oX", "-", target]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=settings.scanner_timeout)
        if result.returncode != 0:
            return [{"error": f"nmap exited {result.returncode}: {result.stderr}"}]

        root = ET.fromstring(result.stdout)
        for host in root.findall("host"):
            addr_el = host.find("address")
            host_ip = addr_el.get("addr") if addr_el is not None else target

            for port in host.findall(".//port"):
                portid = port.get("portid")
                protocol = port.get("protocol")
                state = port.find("state")
                service = port.find("service")
                script = port.find("script")

                if state is not None and state.get("state") == "open":
                    svc_name = service.get("name", "") if service is not None else ""
                    svc_product = service.get("product", "") if service is not None else ""
                    svc_version = service.get("version", "") if service is not None else ""

                    banner = _grab_banner(host_ip, int(portid))

                    script_output: Dict[str, str] = {}
                    if script is not None:
                        for elem in script.findall("script"):
                            script_output[elem.get("id", "")] = elem.get("output", "")

                    evidence: Dict[str, Any] = {
                        "port": portid,
                        "protocol": protocol,
                        "service_name": svc_name,
                        "product": svc_product,
                        "version": svc_version,
                        "banner": banner,
                        "scripts": script_output,
                    }

                    findings.append({
                        "title": f"Open {protocol.upper()} port {portid}",
                        "description": f"Port {portid}/{protocol} is open ({svc_product} {svc_version}).",
                        "severity": "info",
                        "target": target,
                        "evidence": evidence,
                        "remediation": "Review exposed service and restrict access if unnecessary.",
                    })

    except FileNotFoundError:
        return [{"error": "nmap binary not found"}]
    except ET.ParseError:
        return [{"error": "failed to parse nmap output"}]
    except subprocess.TimeoutExpired:
        return [{"error": "nmap scan timed out"}]
    except Exception as e:
        return [{"error": str(e)}]

    return findings


def run_http_extraction(target: str) -> List[Dict[str, Any]]:
    """Extract HTTP data: headers, titles, server banners, body previews.

    Handles targets with or without a scheme, and never forces a port onto a
    URL that already specifies one. Probes a small, ordered candidate list so
    a normal host costs at most two requests.
    """
    import urllib.parse

    findings: List[Dict[str, Any]] = []
    candidates: List[str] = []

    if target.startswith(("http://", "https://")):
        parsed = urllib.parse.urlsplit(target)
        if parsed.port:
            candidates.append(target)
        else:
            candidates.append(target)
            # Try the other scheme as well; many hosts redirect one to the other.
            other = "https" if parsed.scheme == "http" else "http"
            candidates.append(f"{other}://{parsed.netloc}{parsed.path or ''}")
    else:
        candidates = [f"http://{target}", f"https://{target}"]

    seen_urls = set()
    for url in candidates:
        if url in seen_urls:
            continue
        seen_urls.add(url)
        result = _http_fetch(url, timeout=6.0)
        if "error" in result:
            continue

        findings.append({
            "title": f"HTTP service on {url}",
            "description": f"Extracted HTTP data from {url}",
            "severity": "info",
            "target": url,
            "evidence": {
                "url": url,
                "status_code": result.get("status_code"),
                "server": result.get("server"),
                "title": result.get("title"),
                "headers": result.get("headers"),
                "body_preview": result.get("body_preview"),
            },
            "remediation": "Review exposed HTTP service and headers.",
        })

    # Only probe alternate ports when nothing responded on 80/443.
    if not findings and not target.startswith(("http://", "https://")):
        for url in (f"http://{target}:8080", f"https://{target}:8443"):
            result = _http_fetch(url, timeout=6.0)
            if "error" in result:
                continue
            findings.append({
                "title": f"HTTP service on {url}",
                "description": f"Extracted HTTP data from {url}",
                "severity": "info",
                "target": url,
                "evidence": {
                    "url": url,
                    "status_code": result.get("status_code"),
                    "server": result.get("server"),
                    "title": result.get("title"),
                    "headers": result.get("headers"),
                    "body_preview": result.get("body_preview"),
                },
                "remediation": "Review exposed HTTP service and headers.",
            })

    return findings


def run_scan(target: str, scan_type: str = "vulnerability") -> List[Dict[str, Any]]:
    """Dispatch to scanners with full data extraction."""
    if scan_type in ("vulnerability", "full"):
        results = run_nuclei(target)
        port_results = run_nmap(target)
        results.extend(port_results)
        http_results = run_http_extraction(target)
        results.extend(http_results)
        return results
    elif scan_type == "web":
        return run_http_extraction(target)
    elif scan_type == "code":
        return [{"error": "use POST /code-scans for repository scanning"}]
    elif scan_type == "monitoring":
        return [{"error": "use POST /monitors for continuous monitoring"}]
    else:
        return [{"error": f"unknown scan type: {scan_type}"}]
