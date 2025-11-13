import { test, expect } from '@playwright/test';

test.describe('CSV Upload Flow', () => {
  test('should display upload page', async ({ page }) => {
    await page.goto('/');

    await expect(page.locator('h1')).toContainText('Network Traffic Analysis');
    await expect(page.getByText('Upload Network Traffic Data')).toBeVisible();
  });

  test('should navigate to dashboard', async ({ page }) => {
    await page.goto('/');

    await page.getByRole('link', { name: 'Dashboard' }).click();
    await expect(page).toHaveURL('/dashboard');
  });

  test('should navigate to realtime monitor', async ({ page }) => {
    await page.goto('/');

    await page.getByRole('link', { name: 'Real-time Monitor' }).click();
    await expect(page).toHaveURL('/realtime');
  });
});
