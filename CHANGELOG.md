# Changelog

All notable changes to Ultorn are documented in this file. Format loosely
follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); dates are
when the work was done, not necessarily when it was pushed or deployed.
Entries before 2026-11-05 are not individually itemized here — see `git log`
for the full history of the original MVP (auth, clients/scans/findings,
monitors/alerts, code scanning, Bill No. 25/2026 compliance, reports, the
console app, and the sports sector pack).

## [Unreleased] - 2026-11-05

The pivot from a passive vulnerability scanner toward autonomous,
evidence-producing security testing — "the Senegalese Wakefield." Everything
below preserves the project's existing design boundaries: proof over
suspicion, inside declared scope only, with named human-analyst review
required before anything reaches a client.

### Added

- **Authorization hunter (IDOR/BOLA proof-of-exploit)** — `app/authz_hunter.py`,
  `AuthzHunt`/`AuthzFinding` models, `POST /authz-hunts`. Replays the same
  request across two or more named, authenticated roles against a declared
  `base_url` and classifies whether cross-role access leaks the same
  resource — the "change `/invoices/1024` to `/invoices/1025`" exploit,
  automated and evidenced. Credentials are redacted before being stored.
  Confirmed leaks get an AI-drafted exploit narrative and still require
  named human-analyst review (`POST /authz-findings/{id}/review`).
  - OpenAPI-spec-driven probe discovery (`POST /authz-hunts/suggest-probes`):
    suggests GET endpoints with an id-shaped path parameter as probe
    skeletons from a spec URL or inline spec.
  - Console UI: Authorization Hunts section (build roles/probes, run, review
    findings, view redacted evidence).
- **Whitebox GitHub PR review** — `app/pr_review.py`, `PRReview`/
  `PRReviewFinding` models, `POST /pr-reviews`. Fetches a pull request's
  diff, flags risky patterns in its *added* lines only (hardcoded secrets,
  insecure defaults, dangerous calls, logic flaws — reusing `code_scanner`'s
  detectors), ranks findings by severity, and can post a single Markdown
  findings comment back on the PR. The GitHub token is used once in memory
  and never persisted. Inspired by prlens.dev's "risk-ranked findings with a
  suggested fix, posted on the PR" model, minus its animated
  architecture-diagram layer (left as a future addition).
  - Console UI: PR Reviews section.
- **SOC 2 readiness mapping** — `app/soc2.py`, `POST /compliance/soc2`. Maps
  findings (and confirmed authorization-hunt leaks) to AICPA Trust Services
  Criteria control categories (logical access, system operations, change
  management, risk management, incident response, HR security), each
  always reported as "gap" or "no gaps found" rather than omitted. Returns
  a readiness percentage, gap counts, and next steps (Type I vs Type II,
  typical 7–14 month timeline). Explicitly a readiness *signal*, not an
  audit or attestation.
  - Console UI: a SOC 2 Readiness panel inside the existing Compliance
    section, alongside the Bill No. 25/2026 mapping.
- **Commander orchestration (campaigns)** — `app/commander.py`, `Campaign`/
  `CampaignTask`/`CampaignFact` models, `POST /campaigns`. Decomposes a
  goal into tasks across the authorization hunter and PR reviewer,
  dispatches them in parallel (each on its own DB session via a
  `ThreadPoolExecutor`), and consolidates confirmed findings into a layered
  fact log (title/summary/evidence). Architecturally inspired by
  sapper-v2's commander/worker role division and three-layer fact history —
  reimplemented natively, with zero third-party code, no tmux/shell-
  spawning, and no capability beyond what the single-task engines already
  do. `run_and_persist_hunt`/`run_and_persist_review` were extracted from
  the single-task routers so both paths share one code path.
  - Console UI: Campaigns section (build task lists under one goal, run,
    view the fact log and AI-written summary).
- **AI Guard red-team (attack + defend)** — `app/ai_redteam.py` (attack) +
  `app/jailbreak_guard.py` (defend), `AIRedTeamRun`/`AIRedTeamResult`/
  `JailbreakPattern` models, `POST /ai-redteam/runs`, `GET
  /jailbreak-patterns`. Fires 8 well-known, published prompt-injection/
  jailbreak categories (instruction override, role-play/DAN-style,
  system-prompt leak, fake authority, hypothetical framing, encoding
  obfuscation, payload splitting, token smuggling) at a declared target —
  Ultron's own AI Guard pipeline or a client's own AI-powered feature over
  HTTP — using canary-based detection for deterministic grading. Closed a
  real gap: `sanitizer.py` only ever stripped PII/credentials and never
  caught prompt injection. 5 categories are pre-armed from day one; the
  other 3 start undefended and get learned automatically the first time a
  red-team run confirms a bypass, with `ai_router.route_ai_query` checking
  the guard before ever routing to an external provider. `AIQueryLog`
  gained `jailbreak_detected`/`jailbreak_category`.
  - Console UI: AI Red-Team section (run an attack, view bypass/block
    results per category, view active learned defense patterns).

- **Commander tasks now run in parallel** — `commander._execute_task` runs
  each campaign task on its own DB session inside a `ThreadPoolExecutor`
  instead of sequentially. No new broker/worker dependency: this is a
  synchronous, request-scoped action (the same convention
  `worker.execute_scan`'s "run now" path already follows), and the engines
  are I/O-bound, so threads give real concurrency on their own. Verified
  with a test proving two artificially-slowed tasks finish in ~1x a single
  task's duration, not 2x.
- **Console UI for Campaigns and AI Red-Team** — `CampaignsSection` (build
  authz-hunt/PR-review task lists under one goal, run, view the fact log
  and AI-written summary) and `AIRedTeamSection` (run an attack against
  Ultron's own AI Guard or a client's HTTP endpoint, view bypass/block
  results, view active learned defense patterns).
- **ISO/IEC 27001:2022 readiness mapping** — `app/iso27001.py`, `POST
  /compliance/iso27001`. The other framework soc2compliance.com positions
  against SOC 2, built on the same pattern: maps findings (and confirmed
  authz leaks) to Annex A control categories across all four 2022 themes.
  Physical, people, and supplier-relationship controls are explicitly
  `not_assessed` rather than scored as passing, since network/code scanning
  can't speak to them. Console UI: an ISO 27001 Readiness panel inside
  Compliance, next to SOC 2.
- **`CHANGELOG.md`** — this file.

### Changed

- `requirements.txt`: added `PyGithub` for the PR review and campaign
  GitHub integration.
- Design boundaries in `README.md` revised from "no offensive capability"
  to "proof over suspicion, inside declared scope only" — scanners and the
  new proof engines only ever act on operator-declared targets, and
  confirmed findings (scanner findings, authz leaks, and red-team bypasses
  alike) require named human-analyst review before reaching a client.
- `app/soc2.py`: HR Security now reports `not_assessed` instead of
  silently defaulting to "no gaps found" — it isn't derivable from scan
  findings, and readiness % now excludes non-assessable categories from
  the denominator (new `not_assessed_count` field), matching the honesty
  standard set by the new ISO 27001 module.

### Evaluated and declined

- **sapper-v2** (github.com/N1nEmAn/sapper-v2, MIT) — a tmux-based
  multi-agent orchestration harness that opens real shells and lets AI
  agents execute exploits/shellcode autonomously, built for CTF
  competitions. Borrowed its commander/worker architecture (see
  "Commander orchestration" above); declined to vendor its actual runtime
  — a different safety posture than Ultron's authenticated-replay-only
  model.
- **T3MP3ST** (github.com/elder-plinius/T3MP3ST, AGPL-3.0) — an autonomous
  exploitation harness. Declined: AGPL-3.0 is network copyleft, so
  embedding it would likely force Ultron's backend to go AGPL to stay
  compliant as a hosted service; it also runs real exploits autonomously,
  beyond Ultron's current scope-and-review model.
- **L1B3RT4S** (github.com/elder-plinius/L1B3RT4S) — a jailbreak-prompt
  library built to defeat AI safety guardrails on any model, with no
  declared authorized target. Declined outright; built the legitimate
  attack+defend equivalent instead (see "AI Guard red-team" above), scoped
  to a declared target the same way every other engine here is.
- **OBLITERATUS** (github.com/elder-plinius/OBLITERATUS) — a model
  refusal-ablation toolkit (removes safety behavior at the weight/
  activation level). Declined outright: a different category of risk than
  authorized pentesting, and not something a security product should ship.

### Known gaps / next up

See `TODO.md` for the live backlog. Notably still open: browser-driven
multi-role crawl for apps with no OpenAPI spec, Bitbucket/Forgejo support
for the PR reviewer, OpenGrep-based custom authz rules replacing the
current regex detectors, network-level scope enforcement (default-deny
egress outside a client's declared scope), and the prlens.dev-style
animated diagram layer on PR reviews.
