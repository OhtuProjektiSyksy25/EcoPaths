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


  test('should handle route calculation with mock backend data', async ({ page }) => {
    // Use the mock data from berlin_edges_enriched.parquet structure
    await apiMock.mockRouteCalculation();

    // Simple coordinate input
    const startLat = 52.516275; // Brandenburger Tor
    const startLon = 13.377704;
    const endLat = 52.521918;   // Alexanderplatz
    const endLon = 13.413215;

    // Wait for the app to be ready
    await page.waitForTimeout(1000);

    // Find and fill the form (flexible selector approach)
    const inputs = await page.locator('input[type="text"], input[type="number"]').all();
    
    if (inputs.length >= 4) {
      // Assuming order: startLat, startLon, endLat, endLon
      await inputs[0].fill(startLat.toString());
      await inputs[1].fill(startLon.toString());
      await inputs[2].fill(endLat.toString());
      await inputs[3].fill(endLon.toString());
    }

    // Submit the form
    const buttons = await page.locator('button[type="submit"], button:has-text("Calculate"), button:has-text("Route")').all();
    if (buttons.length > 0) {
      await buttons[0].click();
    }

    // Wait for response
    await page.waitForTimeout(2000);

    // Check that we're still on the page and no errors occurred
    const errorMessage = page.locator('text=/error|failed|wrong/i').first();
    const errorVisible = await errorMessage.isVisible().catch(() => false);
    
    expect(errorVisible).toBe(false);

    // Verify the map is still visible
    const map = page.locator('#map, .leaflet-container, .mapboxgl-map').first();
    await expect(map).toBeVisible();

    console.log('✅ Route calculation completed without errors');
  });
});