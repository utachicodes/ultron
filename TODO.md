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

## In progress / needs a pass

- [ ] CI: expand the basic build workflow with backend tests once a test suite exists

## Backlog

### Correctness / hardening
- [ ] Rate limiting on auth endpoints (`/auth/token`, `/auth/register`)
- [ ] Pagination for `/scans`, `/scans/{id}/findings`, `/audit` (currently unbounded)
- [ ] Postgres option for `DATABASE_URL` in production (SQLite is fine for MVP/single-node only)
- [ ] Secrets: generate a random `SECRET_KEY` on first boot instead of the `.env.example` default
- [ ] Replace the Celery/worker stub (`backend/app/worker.py`) with a real queue, or remove it.
      Right now scans run synchronously in the request and the worker does nothing

### Tests
- [ ] Backend: pytest suite for auth, scan scope CRUD, scan run, admin endpoints
- [ ] Frontend: at least smoke tests for the console app's auth-gated views
- [ ] Run the full test suite (backend + frontend) locally before every push, once it exists.
      CI currently only checks that each side imports/builds, not behavior

### Product
- [ ] Self-service client registration flow (today only `/auth/register` exists, no UI signup)
- [ ] Forgot-password / credential rotation flow
- [ ] Evidence file attachments on findings (screenshots, raw scanner output)
- [ ] Mobile pass on the console app (currently desktop-oriented, unlike the marketing site)

### Content
- [ ] Legal review of `/privacy-notice` and `/service-agreement`. Both are explicitly marked
      as drafts describing current code behavior, not lawyer-reviewed policy
- [ ] Sharpen subpage copy further if `/platform`, `/scanning`, `/sovereignty` still read flat
