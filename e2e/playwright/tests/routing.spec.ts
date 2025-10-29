import { test, expect } from '@playwright/test';
import { ApiMock } from '../helpers/apiMock';

test.describe('EcoPaths E2E - Full Routing Flow', () => {
  let apiMock: ApiMock;

  test.beforeEach(async ({ page }) => {
    apiMock = new ApiMock(page);
    await page.goto('http://localhost:3000');
    await page.waitForLoadState('networkidle');
  });


    test('homepage loads', async ({ page }) => {
      await expect(page.getByText('Where would you like to go?')).toBeVisible();
    });


    test('search suggestions appear', async ({ page }) => {
      
      // Fill start location
      await page.fill('input[placeholder="Start location"]', 'Berlin');
      
      // Wait for suggestions to appear
      await page.waitForSelector('text=Berlin');
      
      // Click the first suggestion
      await page.locator('text=Berlin').first().click();

      // Expect the input to contain "Berlin"
      await expect(page.locator('input[placeholder="Start location"]')).toHaveValue(/Berlin/);
    });


    test('route results are displayed', async ({ page }) => {

      // Start and destination
      await page.fill('input[placeholder="Start location"]', 'Berlin');
      await page.waitForSelector('text=Berlin');
      await page.locator('text=Berlin').first().click();

      await page.fill('input[placeholder="Destination"]', 'Zoo Berlin');
      await page.waitForSelector('text=Zoo Berlin');
      await page.locator('text=Zoo Berlin').first().click();

      // Wait for results — assuming 3 boxes are rendered
      await page.waitForSelector('text=Balanced route');

      // Expect the route boxes to exist
      const boxes = page.locator('.route-card'); // or use a more specific class if available
      await expect(boxes).toHaveCount(3);
    });


    test('route results contain AQI and time info', async ({ page }) => {

      await page.fill('input[placeholder="Start location"]', 'Berlin');
      await page.waitForSelector('text=Berlin');
      await page.locator('text=Berlin').first().click();

      await page.fill('input[placeholder="Destination"]', 'Zoo Berlin');
      await page.waitForSelector('text=Zoo Berlin');
      await page.locator('text=Zoo Berlin').first().click();

      await page.waitForSelector('text=Balanced route');
      
      // Check the boxes contain some text about AQI and time
      await expect(page.locator('text=AQI')).toBeVisible();
      await expect(page.locator('text=min')).toBeVisible();  // assuming time like "12 min"
    });

});
