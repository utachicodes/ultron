from __future__ import annotations

"""Best-effort alert delivery to an external webhook (Slack, Teams, SIEM).

Configure with:
    ALERT_WEBHOOK_URL=https://hooks.example.com/...
    ALERT_WEBHOOK_SECRET=optional-shared-secret

Delivery runs on a daemon thread and never blocks or fails a monitoring check.
If a secret is set, the JSON body is signed with HMAC-SHA256 and sent in the
`X-Ultorn-Signature` header (`sha256=<hex>`).
"""

import hashlib
import hmac
import json
import threading
import urllib.request

from app.config import settings


def _post(url: str, payload: bytes, secret: str) -> None:
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Ultorn-Alerts/1.0",
    }
    if secret:
        digest = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
        headers["X-Ultorn-Signature"] = f"sha256={digest}"

    req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            resp.read()
    except Exception:
        # Delivery is best-effort: never surface failures to the caller.
        pass


def dispatch_alert(alert: dict) -> None:
    """Queue an alert for delivery if a webhook is configured."""
    url = settings.alert_webhook_url
    if not url:
        return

    payload = json.dumps(
        {
            "event": "alert.created",
            "alert": alert,
            "source": "ultorn",
        },
        default=str,
    ).encode()

    threading.Thread(
        target=_post,
        args=(url, payload, settings.alert_webhook_secret),
        name="ultorn-webhook",
        daemon=True,
    ).start()
