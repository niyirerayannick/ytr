// @ts-check
const { defineConfig, devices } = require("playwright/test");

const PORT = process.env.YTR_E2E_PORT || "8799";
const BASE_URL = `http://127.0.0.1:${PORT}`;

module.exports = defineConfig({
  testDir: "./e2e",
  timeout: 30_000,
  fullyParallel: false,
  workers: 1,
  retries: 0,
  reporter: [["list"]],
  use: {
    baseURL: BASE_URL,
    trace: "retain-on-failure",
  },
  webServer: {
    command: "node scripts/run-e2e-server.js",
    url: `${BASE_URL}/health/`,
    reuseExistingServer: !process.env.CI,
    timeout: 60_000,
    env: { YTR_E2E_PORT: PORT },
  },
  projects: [
    { name: "chromium", use: { ...devices["Desktop Chrome"] } },
  ],
});
