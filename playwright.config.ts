import { defineConfig, devices } from "@playwright/test";

/**
 * Playwright config for FleetPro E2E.
 *
 * Tests assume:
 *   - Postgres seeded via `pnpm --filter @fleetpro/db seed`
 *   - Dashboard running on :3000 (`pnpm dev:dashboard`)
 *   - Customer portal running on :3001 (`pnpm dev:portal`)
 *
 * The webServer block boots both apps automatically when running CI.
 * Tests do NOT exercise the real Anthropic API — they smoke-test the
 * dashboard / portal UI surface that the agents drive, plus the
 * tool-handler database side-effects.
 */
export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false, // shared seed; serial keeps assertions deterministic
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? "line" : "list",
  use: {
    baseURL: "http://localhost:3000",
    actionTimeout: 10_000,
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  projects: [
    { name: "chromium", use: { ...devices["Desktop Chrome"] } },
  ],
  webServer: process.env.CI
    ? [
        { command: "pnpm --filter @fleetpro/dashboard dev", port: 3000, reuseExistingServer: false, timeout: 120_000 },
        { command: "pnpm --filter @fleetpro/customer-portal dev", port: 3001, reuseExistingServer: false, timeout: 120_000 },
      ]
    : undefined,
});
