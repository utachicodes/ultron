from __future__ import annotations

"""Scope enforcement for the autonomous proof engines.

Ultron runs as a single Python service, not a per-job sandboxed container,
so there is no OS-level network namespace to put a hard egress block on
(that's tracked separately -- see TODO.md, "network-level scope
enforcement"). What *is* buildable and meaningful today: every outbound
request `authz_hunter` and `ai_redteam` (external mode) make funnels through
one call site each. This module is the one check both call sites run before
issuing a single request -- against the client's own declared `ScanScope`
exclusions, which until now existed only in the data model and were
enforced solely by the passive scanner (`worker.execute_scan`), not by any
of the newer engines.

A host that isn't declared at all is allowed by default (operators often
run a hunt or red-team attempt against a target before formally registering
it as a scope) -- but a host the operator has explicitly marked
`is_excluded=True` is refused outright, the same guarantee
`worker.execute_scan` already gives the passive scanner.
"""

import urllib.parse
from typing import Optional

from sqlalchemy.orm import Session

from app import models


class ScopeViolation(Exception):
    """Raised when a target host is explicitly excluded from a client's scope."""


def extract_host(url: str) -> Optional[str]:
    """Pull the bare hostname (no scheme, no port) out of a URL."""
    if not url:
        return None
    parsed = urllib.parse.urlsplit(url if "://" in url else f"//{url}")
    host = parsed.hostname
    return host.lower() if host else None


def _host_matches(host: str, target: str) -> bool:
    """A declared scope target matches a host if it's the same host, or the
    host is a subdomain of it (so excluding "example.sn" also excludes
    "api.example.sn")."""
    target = target.lower().strip()
    # Strip a scheme/path if the operator stored the scope as a full URL.
    target_host = extract_host(target) or target
    return host == target_host or host.endswith("." + target_host)


def is_excluded(host: str, client_id: int, db: Session) -> bool:
    if not host:
        return False
    excluded_scopes = (
        db.query(models.ScanScope)
        .filter(models.ScanScope.client_id == client_id, models.ScanScope.is_excluded == True)  # noqa: E712
        .all()
    )
    return any(_host_matches(host, scope.target) for scope in excluded_scopes)


def enforce_scope(url: str, client: "models.Client", db: Session) -> None:
    """Raise `ScopeViolation` if `url`'s host is explicitly excluded from
    `client`'s declared scope. Does nothing (host allowed) otherwise,
    including when the host has no scope record at all."""
    host = extract_host(url)
    if host and is_excluded(host, client.id, db):
        raise ScopeViolation(
            f"'{host}' is explicitly excluded from {client.name}'s scope -- refusing to target it"
        )
