import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests',
  timeout: 60 * 1000,
  expect: { timeout: 5000 },
  fullyParallel: false, // Sequential to avoid DB conflicts
  workers: 1, // Single worker for test DB

  use: {
    baseURL: 'http://localhost:3000',
    headless: true,
    trace: 'on-first-retry',
  },

  webServer: [
    // Backend server
    {
      command: 'cd ../../backend && poetry run uvicorn src.main:app --host 0.0.0.0 --port 8000',
      url: 'http://localhost:8000/docs',
      reuseExistingServer: !process.env.CI,
      timeout: 120 * 1000,
      env: {
        ENV: '.env.test',
        NODE_ENV: 'test',
        TEST_MODE: 'True',
        DB_HOST: '127.0.0.1',
        DB_PORT: '5432',
        DB_USER_TEST: 'pathplanner',
        DB_PASSWORD_TEST: 'sekret',
        DB_NAME_TEST: 'ecopaths_test',
      },
      stdout: 'pipe',
      stderr: 'pipe',
    },
    // Frontend server
    {
      command: 'cd ../../frontend && npm start',
      url: 'http://localhost:3000',
      reuseExistingServer: !process.env.CI,
      timeout: 120 * 1000,
      env: {
        BROWSER: 'none',
        REACT_APP_API_URL: 'http://localhost:8000',
      },
      stdout: 'pipe',
      stderr: 'pipe',
    },
  ],

  projects: [
    { name: 'Chromium', use: { ...devices['Desktop Chrome'] } }
  ],

  outputDir: 'playwright-results/',
});