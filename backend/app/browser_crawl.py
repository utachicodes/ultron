from __future__ import annotations

"""Browser-driven multi-role crawl for apps with no OpenAPI spec.

`authz_hunter.suggest_probes_from_spec` discovers id-shaped endpoints from a
published spec; most real apps don't publish one. This module covers that
case: it logs in as each declared role through the actual login *form*
(Playwright/Chromium, not a bearer token), crawls same-origin pages,
extracts the resulting session cookie, and records any page whose URL
contains what looks like a specific resource id (a numeric or UUID path
segment) as a candidate `authz_hunter` probe -- owned by whichever role's
crawl found it, since that role's own login proves they can reach it.

The result (`crawl_roles_and_build_authz_config`) is a ready-to-run
`authz_hunter` config: named roles with their session-cookie header, plus
probes with `owner_role`/`owner_value` already filled in from what was
actually observed -- a step beyond `suggest_probes_from_spec`, which only
gives path/id_param skeletons for the operator to fill in by hand.

Scope and safety:
- Crawling only ever follows same-origin links (the start URL's host) and
  stops at `max_pages` -- it never recurses across domains.
- Login is driven by an operator-declared form (URL + field selectors +
  credentials); it never guesses a login form or tries credentials on its
  own initiative.
- This never runs an authz hunt itself -- it only builds the config for the
  operator to review (and edit) before submitting it to
  `POST /authz-hunts`, the same human-in-the-loop step
  `suggest_probes_from_spec` already requires.
- Playwright (and its Chromium binary) is an optional runtime dependency
  separate from this package's other requirements: `pip install playwright
  && playwright install chromium`. `is_available()` reports whether the
  Python package is importable; a missing *browser* binary instead surfaces
  as a clear `RuntimeError` from `login_and_crawl` itself, since Playwright
  doesn't expose a reliable pre-flight check for it across versions.
"""

import re
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin, urlsplit

_ID_SEGMENT_PATTERN = re.compile(r"^(?:\d+|[0-9a-fA-F-]{8,})$")


def is_available() -> bool:
    try:
        import playwright  # noqa: F401

        return True
    except ImportError:
        return False


def _same_host(url: str, host: str) -> bool:
    try:
        return urlsplit(url).netloc == host
    except Exception:
        return False


def _id_segments(url: str) -> List[str]:
    """Path segments that look like a specific resource id (purely numeric,
    or long enough/hex-ish to be a UUID) -- a simple, deliberately
    conservative heuristic for "this URL references one resource"."""
    path = urlsplit(url).path
    return [seg for seg in path.strip("/").split("/") if seg and _ID_SEGMENT_PATTERN.match(seg)]


def _path_template(url: str, id_values: List[str]) -> str:
    path = urlsplit(url).path
    for value in id_values:
        path = path.replace(f"/{value}", "/{id}", 1)
    return path


def login_and_crawl(
    start_url: str,
    role_name: str,
    login: Optional[Dict[str, str]] = None,
    max_pages: int = 15,
    headless: bool = True,
) -> Dict[str, Any]:
    """Log in (if `login` is given) and crawl same-origin pages from
    `start_url`, returning visited URLs, id-shaped candidate endpoints, and
    the session cookie header resulting from login.

    `login`, if given: {"url", "username_selector", "username",
    "password_selector", "password", "submit_selector"}.

    Raises `RuntimeError` with an actionable message if Playwright or its
    Chromium binary isn't available.
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise RuntimeError(
            "Playwright is not installed. Run `pip install playwright && "
            "playwright install chromium` to enable browser-driven crawling."
        ) from exc

    host = urlsplit(start_url).netloc
    visited: List[str] = []
    candidates: List[Dict[str, Any]] = []
    seen = {start_url}
    queue = [start_url]

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=headless)
            context = browser.new_context()
            page = context.new_page()

            if login:
                page.goto(login["url"], wait_until="domcontentloaded", timeout=15000)
                page.fill(login["username_selector"], login["username"])
                page.fill(login["password_selector"], login["password"])
                page.click(login["submit_selector"])
                page.wait_for_load_state("networkidle", timeout=15000)

            cookies = context.cookies()
            cookie_header = "; ".join(f"{c['name']}={c['value']}" for c in cookies)

            while queue and len(visited) < max_pages:
                url = queue.pop(0)
                if not _same_host(url, host):
                    continue

                try:
                    page.goto(url, wait_until="domcontentloaded", timeout=15000)
                except Exception:
                    continue

                visited.append(url)
                id_values = _id_segments(url)
                if id_values:
                    candidates.append(
                        {
                            "url": url,
                            "path_template": _path_template(url, id_values),
                            "id_values": id_values,
                        }
                    )

                hrefs = page.eval_on_selector_all("a[href]", "els => els.map(e => e.getAttribute('href'))") or []
                for href in hrefs:
                    if not href or href.startswith(("mailto:", "tel:", "javascript:", "#")):
                        continue
                    absolute = urljoin(url, href)
                    if _same_host(absolute, host) and absolute not in seen:
                        seen.add(absolute)
                        queue.append(absolute)

            browser.close()
    except RuntimeError:
        raise
    except Exception as exc:
        raise RuntimeError(f"Browser crawl failed: {exc}") from exc

    return {
        "role": role_name,
        "cookie_header": cookie_header,
        "visited_urls": visited,
        "candidate_endpoints": candidates,
    }


def build_probes_from_crawl(crawl_result: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Turn one role's crawl result into ready-to-run authz_hunter probes,
    owned by that role -- their own login proves they can reach it."""
    probes = []
    for candidate in crawl_result.get("candidate_endpoints", []):
        if not candidate["id_values"]:
            continue
        probes.append(
            {
                "method": "GET",
                "path": candidate["path_template"],
                "id_param": "id",
                "owner_role": crawl_result["role"],
                "owner_value": candidate["id_values"][0],
            }
        )
    return probes


def crawl_roles_and_build_authz_config(
    base_url: str, role_configs: List[Dict[str, Any]], max_pages: int = 15
) -> Dict[str, Any]:
    """Crawl every declared role and assemble a ready-to-review
    `authz_hunter`/`POST /authz-hunts` config: `{base_url, roles, probes}`.

    `role_configs`: `[{"role_name", "start_url", "login"?}, ...]`, at least
    2 entries (authz_hunter itself requires 2+ roles to test cross-role
    access). Does not run a hunt -- only builds the config for review.
    """
    roles: List[Dict[str, Any]] = []
    probes: List[Dict[str, Any]] = []
    seen_probe_keys = set()

    for cfg in role_configs:
        result = login_and_crawl(
            cfg["start_url"], cfg["role_name"], login=cfg.get("login"), max_pages=max_pages
        )
        roles.append(
            {
                "name": cfg["role_name"],
                "headers": {"Cookie": result["cookie_header"]} if result["cookie_header"] else {},
            }
        )
        for probe in build_probes_from_crawl(result):
            key = (probe["method"], probe["path"])
            if key in seen_probe_keys:
                continue
            seen_probe_keys.add(key)
            probes.append(probe)

    return {"base_url": base_url, "roles": roles, "probes": probes}
