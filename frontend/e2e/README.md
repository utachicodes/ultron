# End-to-end tests

Real browser, real backend -- these drive the actual app instead of mocking
`fetch` the way the Jest smoke tests (`src/app/console/__tests__`) do.

## Run them

```bash
# 1. Backend, with demo data seeded and generous auth rate limits (the
#    suite logs in dozens of times across its specs -- the production
#    defaults of 10 logins/60s and 5 registrations/300s per IP are tuned
#    for one real client and will 429 a full local run)
cd backend
python seed_demo.py
LOGIN_RATE_LIMIT=1000 REGISTER_RATE_LIMIT=1000 uvicorn app.main:app --reload &

# 2. Frontend
cd frontend
npm run dev &

# 3. Tests (first run only: npx playwright install chromium)
npm run test:e2e          # headless
npm run test:e2e:ui       # interactive UI mode, lets you step through each test
```

If you run the backend with its normal rate limits and see a spec fail with
a login that silently lands back on the sign-in screen (or a 429), that's
the limiter doing its job against the suite's login volume, not a bug --
restart the backend to clear its in-memory counters, or use the env vars
above.

## What's covered

- `marketing.spec.ts` -- the header nav is decluttered (no Contact/Get
  Started), Contact is still reachable from the footer.
- `signup.spec.ts` -- a new visitor can register and lands in the console
  signed in as a `client` role; weak passwords are rejected client-side.
- `demo-accounts.spec.ts` -- each "Try as ___" login button signs in as the
  right persona with the right role-gated nav, including a direct regression
  test for the bug where the client persona's dashboard used to fail
  entirely because it bundled an admin/analyst-only API call into the same
  batch as calls a client role can actually make.
- `ai-guard.spec.ts` -- prompt sanitization and the forced-local AI path,
  plus an opt-in test that exercises a **real open-source model** via
  [Ollama](https://ollama.com) instead of the canned local fallback:

  ```bash
  ollama serve &
  ollama pull llama3.2
  # backend/.env: AI_PROVIDER=ollama
  E2E_OLLAMA=1 npm run test:e2e -- ai-guard.spec.ts
  ```

  This is also the easiest way to manually try the AI Guard flow with a
  free, local model instead of paying for an Anthropic/OpenAI key: set
  `AI_PROVIDER=ollama` in `backend/.env`, restart the backend, and submit a
  prompt from the console -- no code changes needed either way.
