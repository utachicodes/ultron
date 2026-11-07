# Ultorn: Project Tracker

Living backlog for the Ultorn platform (Utachi Industries Labs). Update this file
as items are picked up or completed. It's the source of truth for "what's left."

## Done

- [x] FastAPI backend: auth (JWT + API keys), clients, scan scopes, scans, findings
- [x] Scan engine: Nuclei, Nmap, HTTP/HTTPS evidence extraction
- [x] AI sovereignty layer: prompt sanitization, model abstraction, local fallback, audit log
- [x] Immutable audit log for all actions
- [x] Admin panel: user role/access management, API key mint/revoke
- [x] Console app (`/console`): dashboard, clients, scans, findings, AI guard, audit, admin
- [x] Marketing site: landing (`/`) + platform, scanning, sovereignty, contact, privacy notice,
      service agreement, all on one shared dark design system
- [x] Utachi Industries branding (logo, product-name label) in every nav + the login screen
- [x] Local, compressed background video (no cross-origin hotlinking, no double full-file fetch)
- [x] Dockerfiles + docker-compose for backend/worker/frontend
- [x] `.gitignore`, repo initialized, pushed to GitHub
- [x] Centralized `NAV_LINKS`/arrow icon between `app/page.tsx`, `content/site.ts`,
      and `components/Arrow.tsx` (landing page no longer has its own copies)
- [x] Basic CI workflow (backend import check + frontend build) on push/PR
- [x] Redesigned the console (`/console`): dark sidebar nav, light content chrome, glass stat
      tiles, dark split list/detail panels for clients/scans/findings/audit/admin, popups for
      quick actions (add client, start scan, create API key)
- [x] Continuous monitoring engine (`monitor.py`): access anomaly, config drift, leaked
      credentials, policy violations; `Monitor` + `Alert` models, CRUD/check/alerts routes
- [x] AI code scanning (`code_scanner.py`): hardcoded secrets, dangerous eval/exec,
      disabled SSL verification, insecure defaults; `CodeScan` + `CodeScanIssue` models
- [x] Senegal Cyber Law 2026 compliance mapping (`compliance.py`): findings → law articles,
      CERT notification windows, sector-specific obligations
- [x] Sports sector pack (`compliance.py`, `reports.py`): matchday/ticketing availability,
      athlete/minor safeguarding data, fan/payment data, federation evidence, and AI
      scouting guidance in compliance summaries, report recommendations, and Markdown export
- [x] Sports demo tenant (`seed_demo.py`): Dakar United FC with ticketing, academy, stadium,
      membership, and fan-app findings; three monitors; alerts; a code scan; and a
      club-scoped demo persona
- [x] Report generation (`reports.py`): plain-language executive reports, recommendations,
      compliance mappings, Markdown export
- [x] Recurring monitor scheduler (`scheduler.py`) wired to `worker.process_monitor_check`
- [x] Recurring vulnerability scan schedules (`ScanSchedule`): hourly→monthly, run-now,
      pause/resume, next-run tracking, sharing `worker.execute_scan` with the API
- [x] Signed alert webhooks (`ALERT_WEBHOOK_URL`) and a real readiness probe
- [x] Friendly API root + 404 hint (helps when a tool probes `/v1/*`)
- [x] Scanner URL handling: no double schemes, preserved ports, `web`/`full` dispatch
- [x] Console sections for Monitors, Alerts, Code Scans, Compliance, and Reports
- [x] Fixed monitor-check 500 (`monitor.id` → `monitor_obj.id`) and populated
      `body_preview` so leaked-credential detection actually runs
- [x] `design.html`: static design reference for the console rework — full-screen initial
      landing page (“Know before they do.”) with a CSS globe, responsive nav/menu, console
      deep links, and a back-to-landing shortcut; 12 console views, grouped keyboard-accessible
      navigation, inline SVG icons, mobile drawer, focus states, and no horizontal page overflow
- [x] Console UX pass: shared accessible primitives (`ui.tsx`), labeled forms, error/loading/empty
      states, toasts, confirm dialogs for destructive actions, visible focus rings, contrast fixes
- [x] Backend structure: `main.py` split into 12 domain routers under `app/routers/`
      (auth, clients, scans, findings, reports, monitors, code scans, compliance, AI, audit, admin, system)
- [x] Credential rotation: self-service password change with current-password proof, admin-generated
      one-time reset passwords (never written to the audit log), 8-character minimum, and disabled
      accounts now blocked at both sign-in and token/API-key validation
- [x] Console navigation: sidebar shortcut back to the landing page and a visible “Change password”
      dialog that signs the user out with a confirmation notice after rotation

## In progress / needs a pass

- [x] CI: add frontend smoke tests once a browser-level test harness exists — Jest + React
      Testing Library wired up, `npm test -- --ci` runs in the frontend CI job

## Backlog

### Correctness / hardening
- [x] Console RBAC UI gating: the frontend used to show every create/update/delete control
      (Add client, Start scan, Attest Review, Create Monitor, Run/Pause/Delete, Acknowledge/
      Resolve, Scan Code, the Audit nav item) to every signed-in role, relying on the backend's
      403 to stop a client-role user after the fact. Worse, the Dashboard bundled `/audit` (
      admin/analyst only) into the same `Promise.all` as five calls a client role CAN make, so
      that one 403 failed the *entire* dashboard for a client user. Added a `canManage` flag
      (`admin`/`analyst`) threaded through `ctx`: those controls are now hidden for a client
      role instead of rendered-then-rejected, `/audit` is skipped up front for a client role,
      and the Audit nav item is hidden when the backend would 403 it anyway
- [x] Rate limiting on auth endpoints (`/auth/token`, `/auth/register`) — in-process
      sliding window; swap for Redis when running multiple replicas
- [x] Pagination for `/scans`, `/scans/{id}/findings`, `/audit`, `/alerts` (defaults + server caps)
- [x] Prevent privilege escalation: `/auth/register` accepts no role and always creates `client`
- [x] Secrets: random `SECRET_KEY` generated on first boot (`backend/.secret_key`, chmod 600)
- [x] Scheduler wired into startup; idempotent per-monitor jobs; `ENABLE_SCHEDULER=false` opt-out
- [x] Shared `worker.process_monitor_check` for scheduled and manual checks
- [x] Replace the in-process scheduler with a real queue (Celery/Redis) for multi-replica
      deploys: the `schedule`-library loop still decides *when* a monitor check or scheduled
      scan is due, but now enqueues it (`app/tasks.py`) onto Celery instead of running it
      inline, so N API replicas never duplicate the same run. A separate `worker` service
      (`celery -A app.celery_app worker`, see `docker-compose.yml`) executes it and can be
      scaled independently. Manual "run now" actions from the API still call the plain
      functions in `worker.py` directly/synchronously. Tests set
      `CELERY_TASK_ALWAYS_EAGER=true` so `.delay()` runs inline with no Redis needed.
- [x] Postgres option for `DATABASE_URL` in production: `psycopg2-binary` added to
      `requirements.txt` (SQLite remains the default for MVP/single-node; `database.py`
      already branches its `connect_args` on the URL scheme)

### Tests
- [x] Backend: pytest suite for auth, credential rotation, disabled-account enforcement,
      clients/scopes, scans, findings, reports, monitors, alerts, code scans, compliance,
      sanitization, and AI routing (58 tests)
- [x] Frontend: at least smoke tests for the console app's auth-gated views — Jest/RTL smoke
      tests cover the login gate, form inputs, and the authenticated shell after login
- [ ] Run the full test suite (backend + frontend) locally before every push, once it exists.
      CI currently only checks that each side imports/builds, not behavior

### Product
- [x] Full CRUD completeness pass across the console: clients gained `PATCH`/`DELETE`
      (admin-only delete, cascades scans/findings/monitors/alerts/schedules/code-scans) and a
      `sector` field (drives Compliance, previously an unused `getattr(client, "sector", None)`
      with no column behind it); scan scopes gained `PATCH`/`DELETE` plus visible
      excluded/verified status; monitors and scan schedules gained inline edit (target/type,
      type/interval) on top of their existing pause/resume/delete; Admin gained `POST
      /admin/users` so an admin can hand out analyst/admin access directly instead of someone
      self-registering as a client first and being promoted. Compliance now maps a selected
      client's real findings (and real sector) instead of three hardcoded sample findings.
      Reports gained Copy/Download .md. Findings, scans, code scans, alerts, and the audit log
      stay delete-free on purpose — they're evidence of record, not configuration
- [x] Self-service client registration flow: `/signup` page (register, then auto-login and
      redirect to `/console`); the landing page's hero "Get Started" CTA points there instead
      of straight to the login screen
- [x] One-click demo accounts: `seed_demo.py` seeds an Admin, an Analyst, a bank Client, and a
      club Client persona (each Client owns a different demo client, so role-based scoping has
      something real to demonstrate). The console login screen shows a "Try as ___" button per
      persona that signs in immediately with sample clients/findings already loaded
- [x] Self-service forgot-password flow: `POST /auth/forgot-password` issues a single-use,
      time-boxed token (`PasswordResetToken`, hashed at rest, previous tokens invalidated on
      re-request); `POST /auth/reset-password` redeems it. No SMTP provider is wired up yet, so
      the link is logged server-side (and echoed back as `dev_reset_token` only when
      `DEBUG=true`) via `_deliver_reset_link` in `routers/auth.py` — swap that one function for
      a real send once a provider is chosen, the token logic itself needs no changes.
- [x] Evidence file attachments on findings (screenshots, raw scanner output) — added POST/GET `/findings/{finding_id}/attachments`, GET/DELETE `/findings/{finding_id}/attachments/{attachment_id}` in `app/routers/findings.py`
- [x] Mobile pass on the console: off-canvas drawer, sticky top bar, collapsible sidebar,
      and horizontally scrollable tables in the newer sections
- [x] Deduplicate findings across recurring scans (today each scan stores its own rows) —
      `execute_scan` in `app/worker.py` now fingerprints each result (sha256 of client_id +
      normalized title/target/severity) and, if an `open` Finding with that fingerprint already
      exists for the client, bumps its `occurrence_count` instead of inserting a duplicate row;
      a finding a human already marked resolved/false_positive is left untouched and a rescan
      that still detects it gets its own fresh row instead of silently reopening the old one.
      Scan summaries count new-or-still-open issues, not just rows inserted by that run.

### Autonomous AppSec agent (the Wakefield pivot)
Ultron is pivoting from a passive scanner toward autonomous, evidence-producing
testing — blackbox proof-of-exploit (à la wakefield.co) plus whitebox
PR-generating fixes — while keeping the existing human-review gate on anything
client-facing.

- [x] **v1 slice shipped**: `app/authz_hunter.py` + `POST /authz-hunts` — an
      autonomous IDOR/BOLA (broken object-level authorization) hunter. Given a
      `base_url`, 2+ named roles (with their auth headers) and 1+ probes
      (`method`, `path` with an `{id}` placeholder, `owner_role`, `owner_value`),
      it replays the exact same request as every other role and classifies the
      result (`confirmed_leak` / `no_leak` / `inconclusive` / `probe_error`)
      by comparing response bodies — the automated version of "change
      `/invoices/1024` to `/invoices/1025` and see what comes back." Confirmed
      leaks get an AI-drafted exploit narrative (via the existing `ai_router`,
      so sanitization/audit/sovereignty rules already apply) and still require
      a named human analyst review (`POST /authz-findings/{id}/review`) before
      being reported to a client — same gate `Finding` already enforces.
      Credentials are redacted before being stored as evidence. New models:
      `AuthzHunt`, `AuthzFinding`. New router: `app/routers/authz.py`.
      No new dependencies — built on the existing `httpx`.
- [x] **Console UI for authz hunts shipped**: `AuthzSection` — a form to add
      roles/probes, a results view showing confirmed/no-leak/inconclusive
      with the redacted evidence, and the review action.
- [x] **OpenAPI-spec-driven probe discovery shipped**: `POST
      /authz-hunts/suggest-probes` auto-suggests candidate `{id}`-shaped GET
      endpoints from a spec URL or inline spec (`suggest_probes_from_spec`
      in `app/authz_hunter.py`), console button "Suggest probes from spec".
- [x] **Commander orchestration shipped**: `app/commander.py` + `POST /campaigns`
      — architecturally inspired by sapper-v2 (github.com/N1nEmAn/sapper-v2)'s
      commander/worker role division and three-layer fact history
      (title/summary/evidence), reimplemented natively with zero third-party
      code: no tmux, no shell-spawning, no separate agent processes. A
      campaign decomposes a goal into tasks (authz hunts, PR reviews), runs
      them through the exact same persistence paths (`run_and_persist_hunt`,
      `run_and_persist_review`) their single-task endpoints use — same scope
      limits, same redaction, same human-review gates — and consolidates
      confirmed findings into a `CampaignFact` log. `role` on each task
      (scout/soldier/general) is a descriptive label sized by workload, not
      a spawned agent. Evaluated and explicitly declined to vendor T3MP3ST
      (AGPL-3.0 — would force Ultron's backend to go AGPL to stay compliant
      as a hosted service) or sapper-v2's actual runtime (opens real shells
      and executes exploits/shellcode, a different safety posture than
      Ultron's authenticated-replay-only model) — see the PR/commit message
      for the full reasoning.
      New models: `Campaign`, `CampaignTask`, `CampaignFact`.
- [x] **Campaign tasks now run in parallel**: `commander._execute_task` runs
      each task on its own DB session inside a `ThreadPoolExecutor` (not a
      Celery group — this is a synchronous, request-scoped action like
      `worker.execute_scan`'s "run now" path, and the engines are I/O-bound,
      so threads get real concurrency without a broker/worker-process
      dependency). Verified with a test that two artificially slow tasks
      complete in ~1x a single task's duration, not 2x.
- [x] **Console UI for Campaigns and AI Red-Team shipped**: `CampaignsSection`
      (build authz-hunt/PR-review task lists under one goal, view the
      consolidated fact log) and `AIRedTeamSection` (run an attack against
      Ultron's own AI Guard or a client's HTTP endpoint, view bypass
      results, view active learned defense patterns) — same patterns as
      the Authorization Hunts / PR Reviews sections.
- [x] **AI Guard red-team (attack + defend) shipped**: `app/ai_redteam.py` +
      `app/jailbreak_guard.py` + `POST /ai-redteam/runs`. Context: asked to
      implement and "set up" elder-plinius's L1B3RT4S (a jailbreak-prompt
      library) and OBLITERATUS (a model refusal-ablation toolkit) —
      declined both: L1B3RT4S has no declared authorized target, it's built
      to defeat guardrails on *any* AI system including Ultron's own, and
      OBLITERATUS removes safety behavior at the weight/activation level,
      a different category of risk entirely from authorized pentesting.
      Built the legitimate attack+defend equivalent instead, scoped the
      same way as `authz_hunter`/`pr_review`: it only ever targets a
      declared endpoint (Ultron's own AI Guard, or a client's own
      AI-powered feature the operator points it at over HTTP) and never
      discovers a target on its own.
      - **Attack**: fires 8 well-known, published prompt-injection/jailbreak
        categories (instruction override, role-play/DAN-style, system-prompt
        leak, fake authority, hypothetical framing, encoding obfuscation,
        payload splitting, token smuggling) using canary-based detection —
        each payload asks the model to echo a unique token if it complies,
        so grading is a deterministic substring check, not a fuzzy heuristic.
      - **Defend**: `sanitizer.py` only ever stripped PII/credentials, it
        never caught prompt injection at all — `jailbreak_guard.py` is a new
        layer `ai_router.route_ai_query` now checks before routing to an
        external provider. 5 well-known categories are pre-armed from day
        one; the other 3 start undefended and get learned the first time a
        red-team run confirms a bypass (`JailbreakPattern`, one active
        pattern per category) — closing the loop without touching source
        code. `AIQueryLog` gained `jailbreak_detected`/`jailbreak_category`.
      - New models: `AIRedTeamRun`, `AIRedTeamResult`, `JailbreakPattern`.
      - Tests include a full end-to-end attack -> learn -> reblock loop
        through the real API, not just mocked pieces.
- [x] **Browser-driven multi-role crawl shipped**: `app/browser_crawl.py` +
      `POST /authz-hunts/crawl-and-suggest`. For apps with no OpenAPI spec:
      logs in as each declared role through its *real login form*
      (Playwright/Chromium, not a token), crawls same-origin pages, extracts
      the resulting session cookie, and returns a ready-to-review
      `{base_url, roles, probes}` config with `owner_role`/`owner_value`
      already filled in from what each role's crawl actually reached — a
      step beyond spec-based suggestion, which only gives path skeletons.
      Verified end-to-end against a real local HTTP server and real
      headless Chromium (not mocked): login, cookie extraction, same-origin
      crawl, and id-shaped-URL detection all genuinely exercised. Playwright
      is an optional dependency (`is_available()` gate); a missing Chromium
      binary surfaces as an actionable `RuntimeError`
      (`playwright install chromium`). Console UI: a "No spec? Discover via
      browser crawl" panel inside Authorization Hunts.
- [x] **Whitebox v1 slice shipped**: `app/pr_review.py` + `POST /pr-reviews`
      — a GitHub PR review bot inspired by prlens.dev's "risk-ranked findings
      with a suggested fix, posted on the PR" idea (minus its animated
      architecture-diagram layer, a separate, much larger investment left
      for later). Fetches a PR's diff via PyGithub, scans only the *added*
      lines against the same detectors as `code_scanner.py` (hardcoded
      secrets, insecure defaults, dangerous calls, logic flaws), ranks
      findings by severity, and — only when the caller opts in — posts one
      Markdown comment on the PR. The GitHub token is used once in memory
      and is never written to the database or audit log. New models:
      `PRReview`, `PRReviewFinding`. New router: `app/routers/pr_reviews.py`.
      Console UI: a "PR Reviews" section (`PRReviewsSection`).
- [x] **PR review bot extended to Bitbucket and Forgejo**: `provider="github"`
      (default) / `"bitbucket"` / `"forgejo"` on `POST /pr-reviews` and
      `app.pr_review.analyze_pull_request`. GitHub goes through PyGithub;
      Bitbucket Cloud and Forgejo/Gitea go through their plain REST APIs via
      `httpx`, with a shared `_parse_unified_diff` turning their raw
      multi-file diff text into the same `{filename, patch}` shape GitHub's
      API gives natively, so `analyze_pr_files` is provider-agnostic.
      Forgejo additionally takes `host` (self-hosted). `PRReview` gained a
      `provider` column; console PR Reviews form gained a provider selector
      and conditional host field. Verified against mocked Bitbucket/Forgejo
      REST responses (fetch, analyze, and post-comment paths all covered).
- [x] **OpenGrep/semgrep custom authz rule shipped** (in place of the pure
      regex heuristic for Python specifically): `app/semgrep_scanner.py` +
      two bundled, hand-verified rules in `app/semgrep_rules/` —
      `fastapi-route-missing-authz-dependency` (flags a FastAPI route with
      no `Depends(...)` parameter) and `sql-injection-fstring-execute`
      (flags an f-string passed straight into `cursor.execute()`). Both were
      verified against real sample code with the actual `semgrep` binary,
      not just written and hoped to work — confirmed to flag exactly the
      vulnerable lines and not the safe ones. `code_scanner.scan_directory`
      runs semgrep when installed (optional dependency, `is_available()`
      gate) and skips the regex `missing_authz_check` heuristic for `.py`
      files in that case to avoid double-reporting the same route; falls
      back to the regex heuristic (now extended to also cover
      Express-style and Spring MVC routes, not just FastAPI/Flask) when
      semgrep isn't installed. Fixed a real bug surfaced while testing this:
      the heuristic's lookahead window didn't stop at the *next* route
      definition, so one route's `Depends(...)` could incorrectly clear an
      adjacent, actually-undefended route a few lines away.
      LLM-drafted patches opened as a follow-up PR (rather than just a
      finding) remain a future step.
- [x] **The prlens.dev-style diagram layer shipped**, scoped to what's
      actually achievable without new hosting infrastructure: `
      build_review_diagram` in `app/pr_review.py` renders a Mermaid
      flowchart of the PR's changed files, colored by worst finding
      severity, embedded directly in the Markdown comment via a fenced
      ` ```mermaid ` block — GitHub and Forgejo/Gitea render it inline
      natively, no image hosting or custom SVG renderer needed. Skipped for
      Bitbucket, which doesn't render Mermaid in PR comments.
- [x] **Network-level scope enforcement shipped** (as an application-layer
      allow-list, the honest equivalent available to a single Python
      service without per-job network namespaces — true OS-level egress
      control is still a separate follow-up, see below): `app/scope_guard.py`
      + enforcement wired into `run_and_persist_hunt` (authz hunter,
      including campaigns that dispatch through it) and `/ai-redteam/runs`
      external mode. Both now actually honor a client's existing
      `ScanScope.is_excluded` records — previously that exclusion flag was
      only consulted by the passive scanner (`worker.execute_scan`), so the
      newer proof engines could unknowingly target a host the operator had
      explicitly carved out. A host with no scope record at all is still
      allowed by default (operators often test before formally registering
      a scope); an explicitly excluded host (or any of its subdomains) is
      refused with HTTP 403.
- [ ] True OS-level/network-level egress control (a sidecar proxy or
      per-job container with default-deny network policy) once multi-tenant
      isolation is actually needed — `scope_guard.py` covers the
      single-service case today.
- [ ] Sandbox exploit execution classes beyond authenticated HTTP replay
      (XSS, SSRF, command injection) in ephemeral containers before
      investing in Firecracker/gVisor-grade isolation. Deliberately still
      not pursued: nothing in Ultron executes arbitrary exploit payloads
      today (every engine replays authenticated HTTP requests or analyzes a
      diff/prompt) — building VM-grade sandboxing now would be
      infrastructure with no corresponding capability to sandbox. Revisit
      once an actual exploit-execution engine is built.

### Compliance frameworks
- [x] **SOC 2 readiness mapping shipped**: `app/soc2.py` + `POST /compliance/soc2`
      — maps a client's findings (and confirmed authorization-hunt leaks) to
      AICPA Trust Services Criteria control categories (logical access,
      system operations, change management, risk management, incident
      response, HR security), each always reported as "gap" or "no gaps
      found" rather than omitted. Returns a readiness percentage, gap counts,
      and next steps (including the Type I vs Type II distinction and the
      typical 7-14 month path), inspired by the SOC 2 readiness-guide model
      at soc2compliance.com. Explicitly a readiness *signal*, not an audit or
      attestation — only a licensed CPA firm can issue a SOC 2 report.
      Console UI: a "SOC 2 Readiness" panel inside the existing Compliance
      section, alongside the Bill No. 25/2026 mapping.
- [x] **SOC 2's HR Security category now honestly reports "not assessed"**
      instead of silently defaulting to "no gaps found" — it isn't
      derivable from scan findings, so readiness % now excludes it from the
      denominator entirely (a new `not_assessed_count` field), matching the
      same treatment used in the new ISO 27001 module below. The remaining
      gap: still no manual checklist/evidence-upload path for it.
- [x] **ISO/IEC 27001:2022 readiness mapping shipped**: `app/iso27001.py` +
      `POST /compliance/iso27001` — the other framework soc2compliance.com
      positions against SOC 2, built alongside it on the same pattern. Maps
      findings (and confirmed authz leaks) to Annex A control categories
      across all four 2022 themes (organizational, people, physical,
      technological); physical, people, and supplier-relationship controls
      are explicitly `not_assessed` (out of scope for network/code
      scanning) rather than scored as passing. Console UI: an "ISO/IEC
      27001:2022 Readiness" panel inside Compliance, next to SOC 2.

### Content
- [x] Header nav decluttered: dropped "Contact" and "Get Started" from the primary nav
      (`MarketingNav.tsx` and the landing page's own header) to cut it down to Platform/
      Scanning/Sovereignty + Login. Contact is still reachable from the footer; "Get Started"
      remains as the hero's own primary CTA on the landing page, just not duplicated in the header
- [ ] Legal review of `/privacy-notice` and `/service-agreement`. Both are explicitly marked
      as drafts describing current code behavior, not lawyer-reviewed policy
- [ ] Sharpen subpage copy further if `/platform`, `/scanning`, `/sovereignty` still read flat
