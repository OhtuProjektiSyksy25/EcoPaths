import { Page, Route } from '@playwright/test';
import { mockData } from '../fixtures/mockData';

export class ApiMock {
  constructor(private page: Page, private baseURL: string = 'http://127.0.0.1:8000') {}

  /**
   * Mock the FastAPI route calculation endpoint
   * Matches: GET /api/route?start_lat=...&start_lon=...&end_lat=...&end_lon=...
   */
  async mockRouteCalculation(customResponse?: any) {
    await this.page.route('**/api/route*', (route: Route) => {
      console.log('Intercepted route calculation request');
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(customResponse || mockData.routeResponse)
      });
    });
  }

  /**
   * Mock the edges data endpoint (if you have one)
   */
  async mockEdges(customResponse?: any) {
    await this.page.route('**/api/edges*', (route: Route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(customResponse || mockData.edgesData)
      });
    });
  }

  /**
   * Mock the grid/tiles endpoint (if you have one)
   */
  async mockGrid(customResponse?: any) {
    await this.page.route('**/api/grid*', (route: Route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(customResponse || mockData.gridData)
      });
    });
  }

  /**
   * Mock API error response
   */
  async mockError(endpoint: string, statusCode: number = 404) {
    await this.page.route(endpoint, (route: Route) => {
      route.fulfill({
        status: statusCode,
        contentType: 'application/json',
        body: JSON.stringify(mockData.errorResponse)
      });
    });
  }

  /**
   * Mock all common API endpoints at once
   */
  async mockAllApis() {
    await this.mockRouteCalculation();
    await this.mockEdges();
    await this.mockGrid();
  }

  /**
   * Allow a specific API call to go through (don't mock it)
   */
  async allowApiCall(pattern: string) {
    await this.page.unroute(pattern);
  }

  /**
   * Clear all route mocks
   */
  async clearMocks() {
    await this.page.unroute('**/api/**');
  }
}