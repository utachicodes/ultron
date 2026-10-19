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

## In progress / needs a pass

- [ ] CI: add frontend smoke tests once a browser-level test harness exists

## Backlog

### Correctness / hardening
- [x] Rate limiting on auth endpoints (`/auth/token`, `/auth/register`) — in-process
      sliding window; swap for Redis when running multiple replicas
- [x] Pagination for `/scans`, `/scans/{id}/findings`, `/audit`, `/alerts` (defaults + server caps)
- [x] Prevent privilege escalation: `/auth/register` accepts no role and always creates `client`
- [x] Secrets: random `SECRET_KEY` generated on first boot (`backend/.secret_key`, chmod 600)
- [x] Scheduler wired into startup; idempotent per-monitor jobs; `ENABLE_SCHEDULER=false` opt-out
- [x] Shared `worker.process_monitor_check` for scheduled and manual checks
- [ ] Replace the in-process scheduler with a real queue (Celery/Redis) for multi-replica deploys
- [ ] Postgres option for `DATABASE_URL` in production (SQLite is fine for MVP/single-node only)

### Tests
- [x] Backend: pytest suite for auth, clients/scopes, scans, findings, reports, monitors,
      alerts, code scans, compliance, sanitization, and AI routing (51 tests)
- [ ] Frontend: at least smoke tests for the console app's auth-gated views
- [ ] Run the full test suite (backend + frontend) locally before every push, once it exists.
      CI currently only checks that each side imports/builds, not behavior

### Product
- [ ] Self-service client registration flow (today only `/auth/register` exists, no UI signup)
- [ ] Forgot-password / credential rotation flow
- [ ] Evidence file attachments on findings (screenshots, raw scanner output)
- [x] Mobile pass on the console: off-canvas drawer, sticky top bar, collapsible sidebar,
      and horizontally scrollable tables in the newer sections
- [ ] Deduplicate findings across recurring scans (today each scan stores its own rows)

### Content
- [ ] Legal review of `/privacy-notice` and `/service-agreement`. Both are explicitly marked
      as drafts describing current code behavior, not lawyer-reviewed policy
- [ ] Sharpen subpage copy further if `/platform`, `/scanning`, `/sovereignty` still read flat
