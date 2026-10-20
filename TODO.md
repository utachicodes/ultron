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
- [x] One-click demo accounts + guided tour: `seed_demo.py` now also seeds an Admin, an
      Analyst, and a Client persona (the Client owns one of the two demo clients); the login
      screen shows a "Try as ___" button per persona that signs in and launches an in-console
      tour (`GuidedTour` in `console/page.tsx`) walking through Dashboard, Clients, Scans,
      Findings, Monitors, AI Guard, and Audit, switching the real view as it goes
- [x] Self-service client registration flow: `/signup` page (register, then auto-login and
      redirect to `/console`); the landing page's "Get Started" CTAs now point there instead
      of straight to the login screen
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

### Content
- [ ] Legal review of `/privacy-notice` and `/service-agreement`. Both are explicitly marked
      as drafts describing current code behavior, not lawyer-reviewed policy
- [ ] Sharpen subpage copy further if `/platform`, `/scanning`, `/sovereignty` still read flat
