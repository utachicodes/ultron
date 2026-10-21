import { defineConfig, devices } from '@playwright/test'

/**
 * End-to-end tests drive a real browser against a real running stack --
 * unlike the Jest smoke tests in src/app/console/__tests__ (which mock
 * fetch), these need BOTH the backend (http://localhost:8000) and the
 * frontend dev server actually running, with demo data seeded:
 *
 *   cd backend && python seed_demo.py
 *   cd backend && uvicorn app.main:app --reload &
 *   cd frontend && npm run dev
 *   cd frontend && npm run test:e2e
 *
 * See e2e/README.md for what each spec covers.
 */
export default defineConfig({
  testDir: './e2e',
  // Sequential, not parallel: every spec hits the same shared backend, and
  // /auth/token is rate-limited (10 attempts/60s per IP) -- several workers
  // logging in at once trips that limit and produces flaky, not real,
  // failures. Login flows are also inherently stateful (signup creates a
  // real user, demo accounts share a real session), so sequential is the
  // honest way to run this against one backend anyway.
  workers: 1,
  forbidOnly: !!process.env.CI,
  // /auth/register and /auth/token are rate-limited per IP; run the backend
  // with higher LOGIN_RATE_LIMIT/REGISTER_RATE_LIMIT for this suite (see
  // e2e/README.md). One retry is still kept as a safety net for whoever
  // forgets to -- a genuine bug fails on the retry too.
  retries: 1,
  reporter: 'list',
  use: {
    baseURL: process.env.E2E_BASE_URL || 'http://localhost:3000',
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
  ],
})
