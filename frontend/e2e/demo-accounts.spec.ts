import { test, expect, type Page } from '@playwright/test'

/**
 * Requires `python seed_demo.py` to have been run against the backend this
 * suite points at -- these personas don't exist otherwise, and the buttons
 * will surface the backend's normal "incorrect email or password" error.
 */

async function loginAsDemo(page: Page, role: 'Admin' | 'Analyst' | 'Client') {
  await page.goto('/console')
  await expect(page.getByText('Sign in to the operator console.')).toBeVisible()
  await page.getByRole('button', { name: `Try as ${role}` }).click()
  await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible({ timeout: 10000 })
}

async function signOut(page: Page) {
  await page.getByRole('button', { name: 'Sign out' }).click()
  await expect(page.getByText('Sign in to the operator console.')).toBeVisible()
}

test('Try as Admin signs in as the admin persona with full nav', async ({ page }) => {
  await loginAsDemo(page, 'Admin')
  await expect(page.getByText('admin@ultorn.local')).toBeVisible()
  await expect(page.getByRole('button', { name: 'Admin' })).toBeVisible()
  await expect(page.getByRole('button', { name: 'Audit' })).toBeVisible()
})

test('Try as Analyst signs in as the analyst persona, no Admin nav item', async ({ page }) => {
  await loginAsDemo(page, 'Analyst')
  await expect(page.getByText('analyst-demo@ultorn.local')).toBeVisible()
  await expect(page.getByRole('button', { name: 'Audit' })).toBeVisible()
  await expect(page.getByRole('button', { name: 'Admin' })).toHaveCount(0)
})

test('Try as Client signs in as the client persona: no Audit, no mutation controls', async ({ page }) => {
  await loginAsDemo(page, 'Client')
  await expect(page.getByText('client-demo@sahelbank.sn')).toBeVisible()

  // Regression test: the dashboard used to bundle the admin/analyst-only
  // /audit call into the same Promise.all as calls a client role CAN make,
  // so one 403 failed the whole dashboard. It must render real content.
  await expect(page.getByText('Could not load the dashboard')).toHaveCount(0)
  await expect(page.getByText('Total scans')).toBeVisible()

  await expect(page.getByRole('button', { name: 'Audit' })).toHaveCount(0)
  await expect(page.getByRole('button', { name: 'Admin' })).toHaveCount(0)

  await page.getByRole('button', { name: 'Clients' }).click()
  await expect(page.getByRole('button', { name: '+ Add client' })).toHaveCount(0)

  await page.getByRole('button', { name: 'Scans', exact: true }).click()
  await expect(page.getByRole('button', { name: '+ Start scan' })).toHaveCount(0)
})

test('switching between demo personas never leaks the wrong role (regression)', async ({ page }) => {
  await loginAsDemo(page, 'Admin')
  await expect(page.getByText('admin@ultorn.local')).toBeVisible()
  await signOut(page)

  await loginAsDemo(page, 'Analyst')
  await expect(page.getByText('analyst-demo@ultorn.local')).toBeVisible()
  await expect(page.getByText('admin@ultorn.local')).toHaveCount(0)
  await signOut(page)

  await loginAsDemo(page, 'Client')
  await expect(page.getByText('client-demo@sahelbank.sn')).toBeVisible()
  await expect(page.getByText('analyst-demo@ultorn.local')).toHaveCount(0)
})
