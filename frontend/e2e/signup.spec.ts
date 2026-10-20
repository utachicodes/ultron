import { test, expect } from '@playwright/test'

test('a new visitor can sign up and lands in the console, signed in', async ({ page }) => {
  const email = `e2e-${Date.now()}@example.com`

  await page.goto('/signup')
  await page.getByLabel('Email').fill(email)
  await page.getByLabel('Password', { exact: true }).fill('a-strong-password-1')
  await page.getByLabel('Confirm password').fill('a-strong-password-1')
  await page.getByRole('button', { name: 'Create account' }).click()

  await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible({ timeout: 10000 })
  await expect(page.getByText(email)).toBeVisible()

  // A brand-new signup is always role "client" -- never a privileged role.
  await expect(page.getByRole('button', { name: 'Admin' })).toHaveCount(0)
  await expect(page.getByRole('button', { name: 'Audit' })).toHaveCount(0)
})

test('signup rejects a password under 8 characters before hitting the API', async ({ page }) => {
  await page.goto('/signup')
  await page.getByLabel('Email').fill(`e2e-short-${Date.now()}@example.com`)
  await page.getByLabel('Password', { exact: true }).fill('short')
  await page.getByLabel('Confirm password').fill('short')
  await page.getByRole('button', { name: 'Create account' }).click()
  await expect(page.locator('.login-error')).toContainText(/8 characters/)
})
