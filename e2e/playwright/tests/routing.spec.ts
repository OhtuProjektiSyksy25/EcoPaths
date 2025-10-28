import { test, expect } from '@playwright/test';
import { ApiMock } from '../helpers/apiMock';

test.describe('EcoPaths E2E - Full Routing Flow', () => {
  let apiMock: ApiMock;

  test.beforeEach(async ({ page }) => {
    apiMock = new ApiMock(page);
    await page.goto('http://localhost:3000');
    await page.waitForLoadState('networkidle');
  });

    test('user gets a route based on air quality', async ({ page }) => {
        await page.goto('/');
        await page.getByPlaceholder('From').fill('Berlin');
        await page.getByText('Berlin').click();
        await page.getByPlaceholder('To').fill('Alexanderplatz');
        await page.getByText('Alexanderplatz Berlin').click();
        await expect(page.locator('#route-summary')).toContainText('AQI');
        });
});
