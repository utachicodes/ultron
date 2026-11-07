<p align="center">
  <img src="frontend/public/brand/utachi-logo.png" alt="Utachi Industries" width="220" />
</p>

<h1 align="center">Ultorn</h1>
<p align="center">Sovereign Cybersecurity Platform, a Utachi Industries Labs product</p>

<p align="center">
  <img alt="CI" src="https://github.com/utachicodes/ultron/actions/workflows/ci.yml/badge.svg" />
  <img alt="Python" src="https://img.shields.io/badge/python-3.9%2B-blue" />
  <img alt="FastAPI" src="https://img.shields.io/badge/FastAPI-0.109-009688" />
  <img alt="Next.js" src="https://img.shields.io/badge/next.js-14-black" />
  <img alt="Status" src="https://img.shields.io/badge/status-MVP-orange" />
</p>

A West African-owned cybersecurity and digital-trust infrastructure platform.
Defensive-only. No verification gate for sandbox testing. Full data extraction.

Built by [Utachi Industries](https://www.utachiindustries.space/), a Dakar, Senegal-based
studio spanning brand/product design (Studio) and
digital products, automation, and AI (Labs). Ultorn is a Labs project.

## What this is

MVP backend (FastAPI + SQLAlchemy + SQLite) + frontend (Next.js) implementing:

- **Client onboarding** with scoped authorization agreements
- **Scan scopes**: add targets (domains, IPs, URLs) per client
- **Vulnerability scanning** with full data extraction: HTTP headers, server banners,
  page titles, response bodies, Nmap service detection, Nuclei template matching
- **Autonomous authorization hunting (IDOR/BOLA proof-of-exploit)**: given a target
  `base_url`, two or more named roles (with their own auth headers), and one or more
  probes, replays the same request across roles and proves — not just flags — broken
  object-level authorization (the "change `/invoices/1024` to `/invoices/1025`" class
  of bug), with full redacted request/response evidence and an AI-drafted exploit
  narrative. Confirmed leaks still require named human analyst review before being
  reported to a client. Probes can be hand-entered, auto-suggested from an OpenAPI
  spec (`POST /authz-hunts/suggest-probes`), or discovered by logging in as each role
  through its real login form and crawling same-origin pages with a headless browser
  (`POST /authz-hunts/crawl-and-suggest`, Playwright/Chromium) for apps with no spec.
  A client's declared `ScanScope` exclusions are enforced before any request goes out.
  See `POST /authz-hunts`
- **Continuous monitoring**: access anomalies, configuration drift, leaked credentials, and
  policy violations, with scheduled checks, alert triage, and acknowledgement/resolution
- **Alert webhooks**: optional signed POST delivery of new alerts to Slack, Teams, or a SIEM
  (`ALERT_WEBHOOK_URL`, `ALERT_WEBHOOK_SECRET`)
- **Recurring scans**: per-client vulnerability scan schedules (hourly to monthly) with
  run-now, pause/resume, and next-run tracking
- **AI code scanning**: detects hardcoded secrets, `eval`/`exec`, disabled TLS verification,
  and insecure defaults in AI-generated or human-written code
- **Bill No. 25/2026 compliance mapping (draft)**: maps findings to article references,
  CERT notification windows, and sector-specific obligations where a pack exists (sports pack live; banking, telecom, and government on the roadmap).
  The bill passed the National Assembly on 21 August 2026; the mapping is not a legal opinion.
- **SOC 2 readiness mapping**: maps findings (and confirmed authorization-hunt leaks) to AICPA
  Trust Services Criteria control categories — logical access, system operations, change
  management, risk management, incident response, HR security — with a readiness percentage,
  gap list, and next steps (Type I vs Type II, typical timeline). A readiness signal, not an
  audit or attestation. See `POST /compliance/soc2` and the console's SOC 2 Readiness panel
- **ISO/IEC 27001:2022 readiness mapping**: maps findings (and confirmed authorization-hunt
  leaks) to Annex A control categories — identity/access management, vulnerability management,
  secure development, logging/monitoring, network security, incident management — alongside
  supplier, people, and physical controls explicitly marked "not assessed by automated
  scanning" rather than scored as passing. A readiness signal, not a certification or Statement
  of Applicability. See `POST /compliance/iso27001` and the console's ISO 27001 Readiness panel
- **Whitebox PR review (GitHub, Bitbucket, or Forgejo)**: fetches a pull request's diff,
  flags risky patterns in its added lines — hardcoded secrets, insecure defaults, dangerous
  calls, logic flaws (regex), plus two AST-aware custom rules when semgrep is installed
  (a FastAPI route with no `Depends(...)` authorization parameter; an f-string passed
  straight into `cursor.execute()`) — ranks findings by severity, embeds a Mermaid diagram
  of the changed files (colored by worst finding severity) on providers that render it
  inline, and can post the result as a single Markdown comment back on the PR. The access
  token is used once in memory and never persisted. See `POST /pr-reviews`
- **Campaigns (commander orchestration)**: decomposes a goal into tasks across Ultron's own
  proof engines (authorization hunts, PR reviews), dispatches them, and consolidates results
  into a layered fact log (title/summary/evidence). Architecturally inspired by sapper-v2's
  commander/worker role division — reimplemented natively, with no third-party code, no
  shell/tmux spawning, and no capability beyond what the single-task engines already do. Tasks
  run in parallel (each on its own DB session). See `POST /campaigns` and the console's
  Campaigns section
- **Sports sector pack**: operational guidance for clubs, federations, and academies —
  matchday and ticketing availability, athlete/minor safeguarding data, fan/payment data,
  federation evidence, and AI in scouting/selection. Included in compliance summaries,
  report recommendations, and the Markdown export
- **Reports**: plain-language executive reports with recommendations, compliance mappings,
  sector guidance, and Markdown export
- **No verification gate**: scans run on all non-excluded scopes immediately
- **Findings + human review**: critical/high findings require named analyst attestation
- **AI sovereignty layer**: prompt sanitization (client names, IPs, credentials, PII stripped),
  model-abstraction (Anthropic/OpenAI swappable), local fallback, immutable AI query audit log.
  Responses report which provider handled the request
- **AI Guard red-team (attack + defend)**: fires a curated set of known prompt-injection/
  jailbreak patterns (instruction override, role-play jailbreaks, system-prompt leaks, fake
  authority, hypothetical framing, encoding obfuscation, payload splitting, token smuggling) at
  a declared target — Ultron's own AI Guard pipeline, or a client's own AI-powered feature over
  HTTP — using canary-based detection. Every confirmed bypass is turned into a defense pattern
  `ai_router.py` checks on every future query, closing the loop without touching source code.
  See `POST /ai-redteam/runs`, `GET /jailbreak-patterns`, and the console's AI Red-Team section
- **Immutable audit log**: every action, scan, AI query, and review logged
- **Admin panel**: manage user roles/access and issue/revoke API keys for programmatic access
- **Marketing landing page**: dark full-viewport hero at `/`, with the operator console at `/console`

## Quick Start

### Prerequisites
- Python 3.9+
- Node.js 20+
- Docker (optional)

### Backend

```bash
cd backend
cp .env.example .env
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be at `http://localhost:8000`. Interactive docs at `http://localhost:8000/docs`.

Default admin: `admin@ultorn.local` / `admin123` — change it from **Change password**
in the console sidebar immediately after first sign-in.

Optional demo data (three clients — a bank, a telco, and the
sports-sector Dakar United FC — with findings, monitors, alerts, and a code
scan), plus four one-click demo personas (Admin, Analyst, a bank Client, and
a club Client scoped to Dakar United FC) that appear as "Try as ___" buttons
on the console login screen:

```bash
cd backend
python seed_demo.py          # add demo data + demo accounts
python seed_demo.py --reset  # rebuild it
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend at `http://localhost:3000`. Set `NEXT_PUBLIC_API_URL=http://localhost:8000`.

- `/`: marketing landing page (sign-in entry point)
- `/console`: the operator app (role-specific dashboard, clients, scans, findings, AI guard,
  audit, admin) with a persisted dark/light theme toggle in the sidebar (and mobile top bar)
- `/signup`: self-service account creation (new accounts are always role "client")
- `/forgot-password` and `/reset-password`: self-service password reset. The reset link is
  logged server-side until a mail provider is configured; with `DEBUG=true` the API also
  returns a development-only token so the flow can be completed locally.

### Docker

```bash
docker-compose up --build
```

## Core Design Boundaries

1. **Proof over suspicion, inside declared scope only.** The authorization hunter only
   ever replays operator-declared requests (named roles + explicit probes) against an
   operator-declared `base_url` — it does not crawl, does not discover resource ids on
   its own, and never acts outside the scope it's given.
2. **No autonomous disclosure.** A `confirmed_leak` is a strong automated signal, not a
   verified report: critical/high findings (scanner findings and authz-hunt leaks alike)
   require named human analyst review before anything reaches a client.
3. **No single foreign AI dependency.** Model-abstraction layer lets you swap providers.
   `force_local` keeps sensitive prompts on-premises.
4. **Full audit trail.** Every action, scan, AI query, authz hunt, and review immutably logged.
5. **Credentials never persist as evidence.** Role headers (Authorization, cookies, API
   keys) used to prove an authz finding are redacted before being written to the database.

## Key API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | API index (app, docs, health links) |
| GET | `/health` | Readiness: database + scheduler state |
| POST | `/auth/token` | Login (JWT) |
| GET | `/auth/me` | Current authenticated user |
| POST | `/auth/register` | Register user |
| POST | `/auth/change-password` | Rotate your own password (requires the current password) |
| GET/POST | `/clients` | Client management |
| POST | `/clients/{id}/scopes` | Add scan target |
| POST | `/scopes/{id}/verify` | Verify ownership (optional) |
| POST | `/scans` | Create a scan |
| POST | `/scans/{id}/run` | Run scan (no verification gate) |
| GET | `/scans/{id}/findings` | Get findings with extracted evidence |
| GET | `/scans/{id}/report` | Executive report (JSON) |
| GET | `/scans/{id}/report/markdown` | Executive report (Markdown) |
| POST | `/findings/{id}/review` | Human analyst review |
| GET/POST | `/scan-schedules` | Recurring scan schedules |
| PATCH/DELETE | `/scan-schedules/{id}` | Pause/resume or remove a schedule |
| POST | `/scan-schedules/{id}/run` | Run a scheduled scan immediately |
| GET/POST | `/monitors` | Continuous monitoring targets |
| PATCH/DELETE | `/monitors/{id}` | Pause/resume or remove a monitor |
| POST | `/monitors/{id}/check` | Run a monitor check now |
| GET | `/monitors/{id}/alerts` | Alerts for one monitor |
| GET | `/alerts` | All alerts (filter by `status`, `severity`) |
| PATCH | `/alerts/{id}` | Acknowledge / resolve / mark false positive |
| GET/POST | `/code-scans` | AI code scanning |
| GET | `/code-scans/{id}/issues` | Issues found in a code scan |
| POST | `/authz-hunts` | Run an autonomous IDOR/BOLA proof-of-exploit hunt |
| GET | `/authz-hunts` | List authorization hunts |
| GET | `/authz-hunts/{id}` | Get one hunt (with its findings) |
| GET | `/authz-hunts/{id}/findings` | Findings for one hunt |
| POST | `/authz-findings/{id}/review` | Human analyst review (required before client-facing use) |
| POST | `/authz-hunts/suggest-probes` | Suggest probes from an OpenAPI spec |
| POST | `/authz-hunts/crawl-and-suggest` | Discover roles/probes via browser login + crawl |
| POST | `/pr-reviews` | Review a pull request's diff (GitHub/Bitbucket/Forgejo), ranked by risk |
| GET | `/pr-reviews` | List PR reviews |
| GET | `/pr-reviews/{id}` | Get one PR review (with its findings) |
| GET | `/pr-reviews/{id}/findings` | Findings for one PR review |
| POST | `/compliance/soc2` | SOC 2 readiness mapping (AICPA Trust Services Criteria) |
| POST | `/compliance/iso27001` | ISO/IEC 27001:2022 readiness mapping (Annex A) |
| POST | `/campaigns` | Run a commander-orchestrated campaign (authz hunts + PR reviews) |
| GET | `/campaigns` | List campaigns |
| GET | `/campaigns/{id}` | Get one campaign (with its tasks) |
| GET | `/campaigns/{id}/facts` | The campaign's consolidated fact log |
| POST | `/ai-redteam/runs` | Run an AI Guard red-team attack (internal or external target) |
| GET | `/ai-redteam/runs` | List red-team runs |
| GET | `/ai-redteam/runs/{id}` | Get one run (with its results) |
| GET | `/ai-redteam/runs/{id}/results` | Results for one run |
| GET | `/jailbreak-patterns` | Active, learned jailbreak-defense patterns |
| POST | `/compliance/map` | Map findings to Bill No. 25/2026 article references (draft) |
| GET | `/compliance/summary` | Sector compliance summary and next steps |
| POST | `/ai/query` | Sanitized AI query (logged, returns provider + model) |
| GET | `/ai/audit` | AI query audit log |
| GET | `/audit` | Full audit log (paginated, filter by `action`) |
| POST | `/sanitize` | Preview sanitization |
| GET | `/health` | Health check |
| GET | `/admin/users` | List users (admin) |
| PATCH | `/admin/users/{id}` | Update a user's role / active status (admin) |
| POST | `/admin/users/{id}/reset-password` | Generate a one-time temporary password (admin) |
| GET | `/admin/api-keys` | List API keys (admin) |
| POST | `/admin/api-keys` | Mint an API key, raw key shown once (admin) |
| DELETE | `/admin/api-keys/{id}` | Revoke an API key (admin) |

API keys authenticate like a user session: send `X-API-Key: <key>` instead of a `Bearer` JWT
on any endpoint, scoped to the admin account that minted the key.

List endpoints accept `limit`/`offset` (defaults: scans 100, findings 200, audit 200) and cap
page size server-side.

## Tests

```bash
cd backend
pip install -r requirements-dev.txt
python -m pytest tests
```

The suite uses an isolated temporary SQLite database and runs with the scheduler disabled.
It covers auth (including the no-self-admin-registration rule and login rate limiting),
clients/scans/findings/reports, monitors and alerts, code scanning, the authorization
(IDOR/BOLA) hunter, compliance mapping, sanitization, and AI routing.

```bash
cd frontend
npm test            # Jest smoke tests (mocked API, no backend needed)
npm run test:e2e    # Playwright, drives a real browser against a real running stack
```

`test:e2e` needs the backend and frontend actually running, with demo data
seeded (`python seed_demo.py`) -- see `frontend/e2e/README.md` for the full
setup and what each spec covers: the marketing nav, signup, each demo
persona's role-gated UI (this is also where the client-persona dashboard
RBAC regression lives), and the AI Guard flow.

### Testing the AI flow with a free, open-source model

`AI_PROVIDER=anthropic`/`openai` need a paid API key, and `AI_PROVIDER=local`
is pattern-matched canned text, not a model. To exercise the AI Guard flow
end to end with a real model and no API key, run a local one via
[Ollama](https://ollama.com):

```bash
ollama serve &
ollama pull llama3.2
```

Then in `backend/.env`:

```
AI_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
```

Restart the backend and submit a prompt from AI Guard in the console (or run
`E2E_OLLAMA=1 npm run test:e2e -- ai-guard.spec.ts` from `frontend/`). Prompts
that still look sensitive after sanitization (or that set "Force local
processing") still never reach Ollama or anywhere else -- they get the
rule-based `local` response regardless of `AI_PROVIDER`.

## File Layout

```
backend/
  app/
    __init__.py
    config.py        # Settings (Pydantic, env-backed)
    database.py      # SQLAlchemy engine + session
    models.py        # DB models (User, Client, ScanScope, Scan, Finding, AuditLog, AIQueryLog, APIKey)
    schemas.py       # Pydantic request/response schemas
    auth.py          # JWT auth + role-based access control
    sanitizer.py     # PII/IP/credential stripping (sovereignty layer)
    scanner.py       # Nuclei + Nmap + HTTP extraction engine
    authz_hunter.py  # Autonomous IDOR/BOLA proof-of-exploit engine (role-pair replay)
    browser_crawl.py # Browser-driven multi-role crawl (Playwright) feeding authz_hunter
    scope_guard.py   # Enforces a client's declared ScanScope exclusions on outbound requests
    pr_review.py     # Whitebox PR review (GitHub/Bitbucket/Forgejo): diff-aware risk + Mermaid diagram
    semgrep_scanner.py  # Optional AST-aware custom rules (semgrep), falls back to regex
    soc2.py          # SOC 2 readiness mapping (AICPA Trust Services Criteria)
    iso27001.py      # ISO/IEC 27001:2022 readiness mapping (Annex A)
    commander.py     # Multi-task campaign orchestration across the above engines
    ai_redteam.py    # AI Guard attack engine: canary-based prompt-injection/jailbreak tests
    jailbreak_guard.py  # AI Guard defense: built-in + learned jailbreak detectors
    ai_router.py     # AI routing w/ sanitization + audit logging
    audit.py         # Immutable audit-log writer
    main.py          # FastAPI app + all routes
    worker.py        # Background scan worker (Celery)
  Dockerfile
  requirements.txt
  .env.example

frontend/
  src/app/page.tsx              # Marketing landing page (hero, video bg, entrance animation)
  src/app/hero.css              # Landing-page design system (reference-pixel --u scaling)
  src/app/marketing-page.css    # Shared dark theme for marketing subpages
  src/app/auth.css              # Auth screens: dark/light design system
  src/app/console/page.tsx      # Operator app (role dashboards, clients, scans, findings, AI, audit, admin)
  src/app/{platform,scanning,sovereignty,contact,privacy-notice,service-agreement}/page.tsx
  src/content/site.ts           # Single source of truth for nav links + all marketing copy
  src/components/               # MarketingNav, MarketingFooter, MarketingPageShell, Arrow
  public/brand/                 # Utachi Industries logo (dark + white variants)
  public/media/                 # Locally-hosted, compressed hero background video + poster
  Dockerfile
  package.json
  next.config.js

.github/workflows/ci.yml   # Backend import check + frontend build, on push/PR
docker-compose.yml
TODO.md
CHANGELOG.md
README.md
```

## About Utachi Industries

[Utachi Industries](https://www.utachiindustries.space/) builds brands, products, and
companies from scratch out of Dakar, Senegal, working remotely and globally across two
divisions:

- **Studio**: branding, identity, UI/UX, fashion
- **Labs**: websites, SaaS, automation, and AI (Ultorn is a Labs product)

Contact: [WhatsApp +221 78 108 05 06](https://wa.me/221781080506) · [@utachiindustries](https://instagram.com/utachiindustries)

## Roadmap

See [TODO.md](TODO.md) for what's done and what's left, and
[CHANGELOG.md](CHANGELOG.md) for what shipped and why (including tools
evaluated and deliberately declined).
