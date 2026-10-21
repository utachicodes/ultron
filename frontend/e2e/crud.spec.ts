import { test, expect, type Page } from '@playwright/test'

async function loginAsAdmin(page: Page) {
  await page.goto('/console')
  await page.getByRole('button', { name: 'Try as Admin' }).click()
  await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible({ timeout: 10000 })
}

test.describe.configure({ mode: 'serial' })

test('admin can create, edit, and delete a client end to end', async ({ page }) => {
  const name = `E2E Client ${Date.now()}`

  await loginAsAdmin(page)
  await page.getByRole('button', { name: 'Clients', exact: true }).click()

  // Create
  await page.getByRole('button', { name: '+ Add client' }).click()
  await page.getByLabel('Client name').fill(name)
  await page.getByLabel('Contact email').fill('ops@example.com')
  await page.getByRole('button', { name: 'Add client', exact: true }).click()
  await expect(page.getByText(name)).toBeVisible({ timeout: 10000 })

  // Select it, edit it
  await page.getByText(name).click()
  await page.getByRole('button', { name: 'Edit' }).click()
  const renamed = `${name} (renamed)`
  await page.getByLabel('Client name').fill(renamed)
  await page.getByLabel('Sector').selectOption('banking')
  await page.getByRole('button', { name: 'Save changes' }).click()
  await expect(page.getByText(renamed).first()).toBeVisible({ timeout: 10000 })
  await expect(page.getByText('Banking / Mobile Money')).toBeVisible()

  // Add a scope, exclude it, remove it
  await page.getByLabel('Scope target (domain, IP, or URL)').fill('e2e-test.example.com')
  await page.getByRole('button', { name: 'Add', exact: true }).click()
  await expect(page.getByText('e2e-test.example.com')).toBeVisible({ timeout: 10000 })
  await expect(page.getByText('Unverified')).toBeVisible()

  await page.getByRole('button', { name: 'Exclude' }).click()
  await expect(page.getByText('Excluded', { exact: true })).toBeVisible({ timeout: 10000 })

  await page.getByRole('button', { name: 'Remove' }).click()
  await page.getByRole('button', { name: 'Remove scope' }).click()
  await expect(page.getByText('e2e-test.example.com')).toHaveCount(0)

  // Delete the client itself
  await page.getByRole('button', { name: 'Delete', exact: true }).click()
  await page.getByRole('button', { name: 'Delete client' }).click()
  await expect(page.getByText(renamed)).toHaveCount(0)
})

test('admin can create a new user from the Admin panel and sign in as them', async ({ page, browser }) => {
  const email = `e2e-created-${Date.now()}@example.com`

  await loginAsAdmin(page)
  await page.getByRole('button', { name: 'Admin', exact: true }).click()
  await page.getByRole('button', { name: '+ Create user' }).click()

  await page.getByLabel('Email').fill(email)
  await page.getByLabel('Temporary password').fill('a-temp-password-1')
  await page.getByLabel('Role').selectOption('analyst')
  await page.getByRole('button', { name: 'Create user', exact: true }).click()

  await expect(page.getByText(email)).toBeVisible({ timeout: 10000 })

  // The new account can actually sign in with what we just set. A fresh,
  // isolated browser context -- not just a new tab -- since a new tab in
  // the same context would inherit the admin's token from localStorage.
  const freshContext = await browser.newContext()
  const fresh = await freshContext.newPage()
  await fresh.goto('/console')
  await fresh.getByLabel('Email').fill(email)
  await fresh.getByLabel('Password', { exact: true }).fill('a-temp-password-1')
  await fresh.getByRole('button', { name: 'Sign in' }).click()
  await expect(fresh.getByRole('heading', { name: 'Dashboard' })).toBeVisible({ timeout: 10000 })
  await expect(fresh.getByRole('button', { name: 'Audit' })).toBeVisible()
  await expect(fresh.getByRole('button', { name: 'Admin' })).toHaveCount(0)
  await freshContext.close()
})

test('admin can edit a monitor in place', async ({ page }) => {
  await loginAsAdmin(page)
  await page.getByRole('button', { name: 'Monitors' }).click()

  const target = page.locator('.split-panel-list').getByText('bank.sn').first()
  await expect(target).toBeVisible({ timeout: 10000 })
  await target.click()

  await page.getByRole('button', { name: 'Edit' }).click()
  await page.locator('#monitor-edit-target').fill('renamed-bank.sn')
  await page.getByRole('button', { name: 'Save changes' }).click()

  await expect(page.getByText('renamed-bank.sn').first()).toBeVisible({ timeout: 10000 })
})
