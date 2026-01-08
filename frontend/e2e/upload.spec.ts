import { test, expect } from '@playwright/test';

test.describe('CSV Upload Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Start from the English home page
    await page.goto('/en');
  });

  test('should display upload page', async ({ page }) => {
    // Check for the main page title (in the page content, not the header)
    await expect(page.getByRole('heading', { name: 'Network Traffic Analysis' }).nth(1)).toBeVisible();
    await expect(page.getByText('Upload CSV files containing network traffic data')).toBeVisible();
  });

  test('should navigate to dashboard', async ({ page }) => {
    await page.getByRole('link', { name: 'Dashboard' }).click();
    await expect(page).toHaveURL('/en/dashboard');
  });

  test('should navigate to realtime monitor', async ({ page }) => {
    await page.getByRole('link', { name: 'Real-time Monitor' }).click();
    await expect(page).toHaveURL('/en/realtime');
  });
});
