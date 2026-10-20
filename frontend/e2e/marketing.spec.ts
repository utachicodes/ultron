import { test, expect } from '@playwright/test'

test('landing page header is decluttered: no Contact or Get Started in the nav', async ({ page }) => {
  await page.goto('/')
  const nav = page.locator('header.nav')
  await expect(nav.getByRole('link', { name: 'Platform' })).toBeVisible()
  await expect(nav.getByRole('link', { name: 'Scanning' })).toBeVisible()
  await expect(nav.getByRole('link', { name: 'Sovereignty' })).toBeVisible()
  await expect(nav.getByRole('link', { name: 'Login' })).toBeVisible()
  await expect(nav.getByRole('link', { name: 'Contact', exact: false })).toHaveCount(0)
  await expect(nav.getByRole('link', { name: 'Get Started', exact: false })).toHaveCount(0)

  // The hero body still has its own "Get Started" CTA -- just not duplicated in the header.
  await expect(page.locator('.hero-inner').getByRole('link', { name: /Get Started/ })).toBeVisible()
})

test('a subpage reaches Contact from the footer, not the header', async ({ page }) => {
  await page.goto('/platform')
  await expect(page.locator('.mnav').getByRole('link', { name: 'Contact', exact: false })).toHaveCount(0)
  await expect(page.locator('.mfooter').getByRole('link', { name: 'Contact' })).toBeVisible()
})
