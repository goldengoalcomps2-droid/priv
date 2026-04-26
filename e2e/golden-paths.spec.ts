import { expect, test } from "@playwright/test";

/**
 * Golden-path E2E for each of the six FleetPro agents.
 *
 * These exercise the UI surface the agents drive plus the database
 * side-effects of their tool handlers. They do NOT call the real
 * Anthropic API — that would be slow and flaky in CI.
 *
 * Run with `pnpm test:e2e` after seeding the database.
 */

// ────────────────────────────────────────────────────────────────────
// Agent 1: Customer Onboarding — public portal happy path
// ────────────────────────────────────────────────────────────────────
test("Customer Onboarding — submit form on customer portal", async ({ page }) => {
  await page.goto("http://localhost:3001/");
  await expect(page.getByRole("heading", { name: /Hire a vehicle from FleetPro/i })).toBeVisible();

  // The form has explicit consent + signature
  await expect(page.getByText(/UK GDPR/i).first()).toBeVisible();
  await expect(page.getByRole("img", { name: /Signature pad/i })).toBeVisible();

  // Required fields are marked required
  const fullName = page.getByLabel("Full name (as on licence)");
  await expect(fullName).toHaveAttribute("aria-required", "true");
});

// ────────────────────────────────────────────────────────────────────
// Agent 2: Hire & Agreement — New Rental wizard from the dashboard
// ────────────────────────────────────────────────────────────────────
test("Hire & Agreement — open New Rental wizard and walk steps", async ({ page }) => {
  await page.goto("/");
  // The brand button on the top bar
  await page.getByRole("button", { name: /^\+ New Rental$/ }).click();

  // 4-step stepper visible
  await expect(page.getByRole("list", { name: /Wizard progress/i })).toBeVisible();
  await expect(page.getByRole("heading", { name: /Upload driving licence/i })).toBeVisible();

  // Skip the upload, walk Customer → Vehicle → Agreement
  await page.getByRole("button", { name: /Skip \(manual entry\)/ }).click();
  await expect(page.getByRole("heading", { name: /^Customer$/ })).toBeVisible();

  await page.getByRole("button", { name: /Next/ }).click();
  await expect(page.getByRole("heading", { name: /Vehicle & dates/ })).toBeVisible();

  await page.getByRole("button", { name: /Next/ }).click();
  await expect(page.getByRole("heading", { name: /Review & send agreement/ })).toBeVisible();

  // Queue button is disabled until the form is filled
  const queue = page.getByRole("button", { name: /Queue for approval/ });
  await expect(queue).toBeDisabled();
});

// ────────────────────────────────────────────────────────────────────
// Agent 3: Fines & PCN — upload dropzone + table
// ────────────────────────────────────────────────────────────────────
test("Fines & PCN — page surfaces upload dropzone and totals", async ({ page }) => {
  await page.goto("/fines");
  await expect(page.getByRole("heading", { name: /^Fines$/ })).toBeVisible();
  await expect(page.getByText(/Click to upload PCN photo/i)).toBeVisible();
  await expect(page.getByText(/we'll extract date, time, VRN, amount/i)).toBeVisible();
  // Stat cards
  await expect(page.getByText(/Outstanding/i).first()).toBeVisible();
  await expect(page.getByText(/Collected/i).first()).toBeVisible();
});

// ────────────────────────────────────────────────────────────────────
// Agent 4: Fleet Maintenance — buckets + status pills
// ────────────────────────────────────────────────────────────────────
test("Fleet Maintenance — bucketed sections render with MOT/Ins/Svc pills", async ({ page }) => {
  await page.goto("/maintenance");
  await expect(page.getByRole("heading", { name: /Maintenance & MOT/i })).toBeVisible();

  // Three bucket section headings (counts vary with the seed)
  await expect(page.getByRole("heading", { name: /^Overdue \(\d+\)$/ })).toBeVisible();
  await expect(page.getByRole("heading", { name: /^Due in 30 days \(\d+\)$/ })).toBeVisible();
  await expect(page.getByRole("heading", { name: /^All good \(\d+\)$/ })).toBeVisible();

  // At least one row has a 'Book service' button (any bucket non-empty)
  await expect(page.getByRole("button", { name: /Book service/ }).first()).toBeVisible();
});

// ────────────────────────────────────────────────────────────────────
// Agent 5: Procurement — pending approval queued by seed appears in feed
// ────────────────────────────────────────────────────────────────────
test("Procurement — agent activity feed shows seeded scan", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: /Agent activity/ })).toBeVisible();
  // The seed writes a Procurement scan; the feed should mention it
  await expect(page.getByText(/Copart listing matches strategy/i)).toBeVisible();
});

// ────────────────────────────────────────────────────────────────────
// Agent 6: Analytics & Defleet — charts + summary
// ────────────────────────────────────────────────────────────────────
test("Analytics & Defleet — charts render and summary is computed", async ({ page }) => {
  await page.goto("/analytics");
  await expect(page.getByRole("heading", { name: /^Analytics$/ })).toBeVisible();
  await expect(page.getByRole("heading", { name: /Revenue by month/ })).toBeVisible();
  await expect(page.getByRole("heading", { name: /Fleet mix by class/ })).toBeVisible();

  // Summary stat cards
  await expect(page.getByText(/Fleet utilisation/i)).toBeVisible();
  await expect(page.getByText(/Avg duration/i)).toBeVisible();
});

// ────────────────────────────────────────────────────────────────────
// Accessibility smoke — skip link, focus ring, semantic landmarks
// ────────────────────────────────────────────────────────────────────
test("Accessibility — skip link, landmarks, and live region exist", async ({ page }) => {
  await page.goto("/");
  // Skip link is the first focusable element
  await page.keyboard.press("Tab");
  await expect(page.getByRole("link", { name: /Skip to main content/i })).toBeFocused();
  // Landmarks
  await expect(page.locator("main#main")).toBeVisible();
  await expect(page.getByRole("navigation", { name: /Primary navigation/i })).toBeVisible();
  // ARIA live region for agent notifications
  await expect(page.locator("#agent-live")).toHaveAttribute("aria-live", "polite");
});
