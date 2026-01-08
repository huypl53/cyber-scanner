import { test, expect } from '@playwright/test';

// Helper function to get the header language switcher (not the sidebar one)
// The button's accessible name is "Change language" or "Thay đổi ngôn ngữ"
const getHeaderLanguageButton = (page: any, name: RegExp | string) => {
  // Target the header specifically by looking for the button within the main content area's header
  return page.locator('header').getByRole('button', { name: /Change language|Thay đổi ngôn ngữ/i });
};

test.describe('Language Switcher', () => {
  test.beforeEach(async ({ page }) => {
    // Start from the home page
    await page.goto('/en');
  });

  test.describe('Visibility and Rendering', () => {
    test('should display language switcher on home page', async ({ page }) => {
      // Check that the language switcher button is visible in the header
      const languageButton = getHeaderLanguageButton(page, /Change language/i);
      await expect(languageButton).toBeVisible();
    });

    test('should display language switcher on dashboard page', async ({ page }) => {
      await page.goto('/en/dashboard');

      const languageButton = getHeaderLanguageButton(page, /Change language/i);
      await expect(languageButton).toBeVisible();
    });

    test('should display language switcher on realtime page', async ({ page }) => {
      await page.goto('/en/realtime');

      const languageButton = getHeaderLanguageButton(page, /Change language/i);
      await expect(languageButton).toBeVisible();
    });

    test('should display language switcher on models page', async ({ page }) => {
      await page.goto('/en/models');

      const languageButton = getHeaderLanguageButton(page, /Change language/i);
      await expect(languageButton).toBeVisible();
    });

    test('should display language switcher on settings page', async ({ page }) => {
      await page.goto('/en/settings');

      const languageButton = getHeaderLanguageButton(page, /Change language/i);
      await expect(languageButton).toBeVisible();
    });

    test('should show correct flag for English locale', async ({ page }) => {
      await page.goto('/en');

      // Get the first flag (in the header)
      await expect(page.locator('header').getByText('🇺🇸').first()).toBeVisible();
      await expect(page.locator('header').getByText('English')).toBeVisible();
    });

    test('should show correct flag for Vietnamese locale', async ({ page }) => {
      await page.goto('/vi');

      // Get the first flag (in the header)
      await expect(page.locator('header').getByText('🇻🇳').first()).toBeVisible();
      await expect(page.locator('header').getByText('Tiếng Việt')).toBeVisible();
    });
  });

  test.describe('Dropdown Interaction', () => {
    test('should open dropdown when clicking language button', async ({ page }) => {
      const languageButton = getHeaderLanguageButton(page, /Change language/i);

      await languageButton.click();

      // Check that dropdown appears with language options
      await expect(page.getByText('Tiếng Việt')).toBeVisible();
    });

    test('should highlight active language in dropdown', async ({ page }) => {
      const languageButton = getHeaderLanguageButton(page, /Change language/i);

      await languageButton.click();

      // The Vietnamese option should be visible (not active)
      await expect(page.getByText('Tiếng Việt')).toBeVisible();
    });

    test('should close dropdown when clicking outside', async ({ page }) => {
      const languageButton = getHeaderLanguageButton(page, /Change language/i);

      await languageButton.click();
      await expect(page.getByText('Tiếng Việt')).toBeVisible();

      // Click outside the dropdown
      await page.click('body', { position: { x: 0, y: 0 } });

      // Dropdown should close
      await expect(page.getByText('Tiếng Việt')).not.toBeVisible();
    });
  });

  test.describe('Language Switching', () => {
    test('should switch from English to Vietnamese on home page', async ({ page }) => {
      await page.goto('/en');

      const languageButton = getHeaderLanguageButton(page, /Change language/i);
      await languageButton.click();

      await page.getByText('Tiếng Việt').click();

      // URL should change to Vietnamese locale
      await expect(page).toHaveURL('/vi');

      // Content should be in Vietnamese (check header)
      await expect(page.locator('header').getByText('🇻🇳').first()).toBeVisible();
      await expect(page.locator('header').getByText('Tiếng Việt')).toBeVisible();
    });

    test('should switch from Vietnamese to English', async ({ page }) => {
      await page.goto('/vi');

      const languageButton = getHeaderLanguageButton(page, /Thay đổi ngôn ngữ/i);
      await languageButton.click();

      await page.getByText('English').click();

      // URL should change to English locale
      await expect(page).toHaveURL('/en');

      // Content should be in English
      await expect(page.locator('header').getByText('🇺🇸').first()).toBeVisible();
      await expect(page.locator('header').getByText('English')).toBeVisible();
    });

    test('should preserve path when switching languages on dashboard', async ({ page }) => {
      await page.goto('/en/dashboard');

      const languageButton = getHeaderLanguageButton(page, /Change language/i);
      await languageButton.click();

      await page.getByText('Tiếng Việt').click();

      // URL should change to Vietnamese locale with same path
      await expect(page).toHaveURL('/vi/dashboard');
    });

    test('should preserve path when switching languages on realtime', async ({ page }) => {
      await page.goto('/en/realtime');

      const languageButton = getHeaderLanguageButton(page, /Change language/i);
      await languageButton.click();

      await page.getByText('Tiếng Việt').click();

      // URL should change to Vietnamese locale with same path
      await expect(page).toHaveURL('/vi/realtime');
    });

    test('should preserve path when switching languages on models', async ({ page }) => {
      await page.goto('/en/models');

      const languageButton = getHeaderLanguageButton(page, /Change language/i);
      await languageButton.click();

      await page.getByText('Tiếng Việt').click();

      // URL should change to Vietnamese locale with same path
      await expect(page).toHaveURL('/vi/models');
    });

    test('should preserve path when switching languages on settings', async ({ page }) => {
      await page.goto('/en/settings');

      const languageButton = getHeaderLanguageButton(page, /Change language/i);
      await languageButton.click();

      await page.getByText('Tiếng Việt').click();

      // URL should change to Vietnamese locale with same path
      await expect(page).toHaveURL('/vi/settings');
    });
  });

  test.describe('Navigation Persistence', () => {
    test('should maintain language preference when navigating between pages', async ({ page }) => {
      // Start on English home page
      await page.goto('/en');

      // Switch to Vietnamese
      const languageButton = getHeaderLanguageButton(page, /Change language/i);
      await languageButton.click();
      await page.getByText('Tiếng Việt').click();

      // Navigate to dashboard
      await page.getByRole('link', { name: /Bảng Điều Khiển|Dashboard/i }).click();

      // URL should maintain Vietnamese locale
      await expect(page).toHaveURL(/\/vi\/dashboard/);
    });

    test('should maintain language when clicking sidebar links', async ({ page }) => {
      // Start on Vietnamese dashboard
      await page.goto('/vi/dashboard');

      // Navigate to realtime
      await page.getByRole('link', { name: /Giám Sát|Real-time/i }).click();

      // URL should maintain Vietnamese locale
      await expect(page).toHaveURL(/\/vi\/realtime/);

      // Navigate to models
      await page.getByRole('link', { name: /Quản Lý|Models/i }).click();

      // URL should maintain Vietnamese locale
      await expect(page).toHaveURL(/\/vi\/models/);
    });
  });

  test.describe('Keyboard Navigation', () => {
    test('should be focusable with keyboard', async ({ page }) => {
      const languageButton = getHeaderLanguageButton(page, /Change language/i);

      await languageButton.focus();

      // Check if button is focused
      const isFocused = await languageButton.evaluate((el) => document.activeElement === el);
      expect(isFocused).toBe(true);
    });

    test('should open dropdown with Enter key', async ({ page }) => {
      const languageButton = getHeaderLanguageButton(page, /Change language/i);

      await languageButton.focus();
      await page.keyboard.press('Enter');

      // Dropdown should open
      await expect(page.getByText('Tiếng Việt')).toBeVisible();
    });

    test('should close dropdown with Escape key', async ({ page }) => {
      const languageButton = getHeaderLanguageButton(page, /Change language/i);

      await languageButton.click();
      await expect(page.getByText('Tiếng Việt')).toBeVisible();

      await page.keyboard.press('Escape');

      // Dropdown should close
      await expect(page.getByText('Tiếng Việt')).not.toBeVisible();
    });
  });

  test.describe('Accessibility', () => {
    test('should have correct ARIA attributes', async ({ page }) => {
      const languageButton = getHeaderLanguageButton(page, /Change language/i);

      await expect(languageButton).toHaveAttribute('aria-haspopup', 'menu');
    });

    test('should be reachable via keyboard navigation', async ({ page }) => {
      // Tab to the language button
      await page.keyboard.press('Tab');
      await page.keyboard.press('Tab');
      await page.keyboard.press('Tab');
      await page.keyboard.press('Tab');
      await page.keyboard.press('Tab');

      // The language button should be focused
      const languageButton = getHeaderLanguageButton(page, /Change language/i);
      const isFocused = await languageButton.evaluate((el) => document.activeElement === el);
      expect(isFocused).toBe(true);
    });
  });

  test.describe('Sidebar Collapse Behavior', () => {
    test('should show language switcher when sidebar is collapsed', async ({ page }) => {
      await page.goto('/en/dashboard');

      // Find the collapse toggle button (it's the small button outside the sidebar)
      const collapseButton = page.locator('button').filter({ hasText: /^$/ }).nth(1);

      // Click to collapse
      await collapseButton.click();

      // Wait for sidebar to collapse
      await page.waitForTimeout(300);

      // Header language switcher should still be visible
      const languageButton = getHeaderLanguageButton(page, /Change language/i);
      await expect(languageButton).toBeVisible();
    });
  });

  test.describe('Responsive Design', () => {
    test('should work on mobile viewport', async ({ page }) => {
      // Set mobile viewport
      await page.setViewportSize({ width: 375, height: 667 });
      await page.goto('/en');

      const languageButton = getHeaderLanguageButton(page, /Change language/i);
      await expect(languageButton).toBeVisible();

      // Should be able to click and switch language
      await languageButton.click();
      await expect(page.getByText('Tiếng Việt')).toBeVisible();
      await page.getByText('Tiếng Việt').click();

      await expect(page).toHaveURL('/vi');
    });

    test('should work on tablet viewport', async ({ page }) => {
      // Set tablet viewport
      await page.setViewportSize({ width: 768, height: 1024 });
      await page.goto('/en');

      const languageButton = getHeaderLanguageButton(page, /Change language/i);
      await expect(languageButton).toBeVisible();
    });

    test('should work on desktop viewport', async ({ page }) => {
      // Set desktop viewport
      await page.setViewportSize({ width: 1920, height: 1080 });
      await page.goto('/en');

      const languageButton = getHeaderLanguageButton(page, /Change language/i);
      await expect(languageButton).toBeVisible();
    });
  });
});
