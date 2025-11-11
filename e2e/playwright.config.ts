import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './playwright/tests',
  timeout: 60 * 1000,
  expect: { timeout: 5000 },
  fullyParallel: true,

  use: {
    baseURL: 'http://localhost:3000',
    headless: true,
    trace: 'on-first-retry',
  },

  webServer: {
    // ✅ Starts both backend & frontend using your invoke task
    // ✅ Forces backend to use `.env.test`
    command: 'cd .. && ENV_FILE=.env.test TEST_MODE=True invoke run-all',

    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,

    env: {
      ...process.env,
      TEST_MODE: 'True',
      ENV_FILE: '.env.test',
      NODE_ENV: 'test',
    },

    stdout: 'pipe',
    stderr: 'pipe',
  },

  projects: [
    { name: 'Chromium', use: { ...devices['Desktop Chrome'] } }
  ],

  outputDir: 'playwright-results/',
});
