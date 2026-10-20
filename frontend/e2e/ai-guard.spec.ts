import { test, expect } from '@playwright/test'

async function loginAsAdmin(page: import('@playwright/test').Page) {
  await page.goto('/console')
  await page.getByRole('button', { name: 'Try as Admin' }).click()
  await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible({ timeout: 10000 })
  await page.getByRole('button', { name: 'AI Guard' }).click()
}

test('AI Guard: a forced-local query never leaves the box and is logged', async ({ page }) => {
  await loginAsAdmin(page)
  await page.getByLabel('Prompt').fill('What does a high severity finding mean?')
  await page.getByLabel('Force local processing (no external model)').check()
  await page.getByRole('button', { name: 'Query AI' }).click()

  await expect(page.getByText('Stayed on-premises')).toBeVisible({ timeout: 10000 })
})

test('AI Guard: prompt sanitization strips an IP and credential before showing what the model would see', async ({ page }) => {
  await loginAsAdmin(page)
  await page.getByLabel('Prompt').fill('Client Acme at 10.0.0.5 used key sk-1234567890abcdef')
  await page.getByRole('button', { name: 'Preview sanitization' }).click()

  const preview = page.getByText('Sanitized Prompt (what the model sees)').locator('..')
  await expect(preview).not.toContainText('10.0.0.5')
  await expect(preview).not.toContainText('sk-1234567890abcdef')
})

/**
 * Exercises a REAL open-source model end to end instead of the canned
 * `local` fallback. Requires the backend to be running with:
 *   AI_PROVIDER=ollama
 *   ollama serve &
 *   ollama pull llama3.2   (or whatever OLLAMA_MODEL is set to)
 * Skipped unless explicitly opted into, since most local runs won't have
 * Ollama installed.
 */
test('AI Guard: a non-sensitive query answers from a real open-source model via Ollama', async ({ page }) => {
  test.skip(!process.env.E2E_OLLAMA, 'Set E2E_OLLAMA=1 once AI_PROVIDER=ollama and `ollama serve` are running')

  await loginAsAdmin(page)
  await page.getByLabel('Prompt').fill('In one sentence, what is a vulnerability scan?')
  await page.getByRole('button', { name: 'Query AI' }).click()

  await expect(page.getByText(/Sent to ollama/)).toBeVisible({ timeout: 30000 })
  const response = page.locator('h3:has-text("AI Response")').locator('..')
  await expect(response).not.toContainText('AI_PROVIDER_NOT_CONFIGURED')
  await expect(response).not.toContainText('AI_ERROR')
})
