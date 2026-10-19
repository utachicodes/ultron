from __future__ import annotations

"""In-process sliding-window rate limiting.

Deliberately dependency-free and per-process: adequate for a single-node
MVP. If Ultorn is ever scaled horizontally, swap the store for Redis while
keeping the same `check()` interface.
"""

import threading
import time
from collections import defaultdict, deque
from typing import Deque, Dict, Tuple

from fastapi import HTTPException, Request, status

# bucket key -> timestamps of recent hits
_hits: Dict[str, Deque[float]] = defaultdict(deque)
_lock = threading.Lock()


def client_ip(request: Request) -> str:
    """Best-effort client identity. Trusts X-Forwarded-For only when
    explicitly deployed behind a proxy (configured via TRUSTED_PROXY)."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def check(
    bucket: str,
    identity: str,
    *,
    limit: int,
    window_seconds: int,
) -> Tuple[int, int]:
    """Record a hit and raise 429 if the window is exhausted.

    Returns (remaining, retry_after_seconds) when allowed.
    """
    key = f"{bucket}:{identity}"
    now = time.monotonic()
    cutoff = now - window_seconds

    with _lock:
        hits = _hits[key]
        while hits and hits[0] < cutoff:
            hits.popleft()

        if len(hits) >= limit:
            retry_after = max(1, int(window_seconds - (now - hits[0])))
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests. Please try again later.",
                headers={"Retry-After": str(retry_after)},
            )

        hits.append(now)
        return limit - len(hits), window_seconds


def reset() -> None:
    """Clear all buckets. Used by tests."""
    with _lock:
        _hits.clear()
