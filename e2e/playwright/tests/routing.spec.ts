import { test, expect } from '@playwright/test';

test.describe('EcoPaths E2E - Full Routing Flow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:3000');
    await page.waitForLoadState('networkidle');

    const areaButton = page.locator('button:has-text("Berlin")');
    if (await areaButton.isVisible()) {
      await areaButton.click();
      await page.waitForSelector('text=Where would you like to go?', { timeout: 10000 });
    }
  });

  test('search suggestions appear', async ({ page }) => {
    const startInput = page.getByRole('textbox', { name: /Start location/i });
    await startInput.fill('Berlin');

    await page.waitForSelector('.originli', { timeout: 10000 });
    await page.locator('.originli', { hasText: 'Berlin' }).first().click();

    await expect(startInput).toHaveValue(/Berlin/, { timeout: 10000 });
  });

  test('route results are displayed', async ({ page }) => {
    await page.fill('input[placeholder="Start location"]', 'Mitte Berlin');
    await page.waitForSelector('text=Mitte Berlin');
    await page.locator('text=Mitte Berlin').first().click();

    await page.fill('input[placeholder="Destination"]', 'Checkpoint Charlie');
    await page.waitForSelector('text=Checkpoint Charlie');
    await page.locator('text=Checkpoint Charlie').first().click();

    await page.waitForSelector('text=Your Route', { timeout: 20000 });

    await expect(page.getByText('Best Air Quality')).toBeVisible();
    await expect(page.getByText('Fastest Route')).toBeVisible();
    await expect(page.locator('span.route_type').first()).toBeVisible();
  });

  test('route results contain AQI and time info', async ({ page }) => {
    await page.fill('input[placeholder="Start location"]', 'Mitte Berlin');
    await page.waitForSelector('text=Mitte Berlin');
    await page.locator('text=Mitte Berlin').first().click();

    await page.fill('input[placeholder="Destination"]', 'Checkpoint Charlie');
    await page.waitForSelector('text=Checkpoint Charlie');
    await page.locator('text=Checkpoint Charlie').first().click();

    await page.waitForSelector('text=Your Route', { timeout: 20000 });

    await expect(page.locator('.time_estimate').first()).toBeVisible({ timeout: 10000 });
    await expect(page.locator('.total_length').first()).toContainText(/km/, { timeout: 10000 });
    await expect(page.locator('.aq_average').first()).toContainText(/AQI/i, { timeout: 10000 });
  });

  test('user can adjust the route balance slider', async ({ page }) => {
    await page.fill('input[placeholder="Start location"]', 'Mitte Berlin');
    await page.waitForSelector('text=Mitte Berlin');
    await page.locator('text=Mitte Berlin').first().click();

    await page.fill('input[placeholder="Destination"]', 'Checkpoint Charlie');
    await page.waitForSelector('text=Checkpoint Charlie');
    await page.locator('text=Checkpoint Charlie').first().click();

    const slider = page.locator('input[type="range"]');
    await slider.waitFor({ timeout: 10000 });
    await slider.focus();
    await slider.press('ArrowRight');
    await expect(slider).toBeVisible();
  });

  test('AQ map toggle is visible', async ({ page }) => {
    await page.fill('input[placeholder="Start location"]', 'Mitte Berlin');
    await page.waitForSelector('text=Mitte Berlin');
    await page.locator('text=Mitte Berlin').first().click();

    await page.fill('input[placeholder="Destination"]', 'Checkpoint Charlie');
    await page.waitForSelector('text=Checkpoint Charlie');
    await page.locator('text=Checkpoint Charlie').first().click();

    await page.waitForSelector('text=Your Route', { timeout: 20000 });

    const toggleButton = page.getByRole('button', { name: /(Show|Hide) air quality on map/i });
    await expect(toggleButton).toBeVisible({ timeout: 20000 });
  });
});
