import { expect, test } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

test("real Python run, every output surface, provenance and refresh boundary", async ({ page }, testInfo) => {
  test.setTimeout(120_000);
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await page.goto("/v2");
  await expect(page.getByLabel("Synthetic case", { exact: true })).toBeEnabled();
  await page.getByLabel("Synthetic case", { exact: true }).selectOption("case_002");
  const responsePromise = page.waitForResponse((response) => response.url().endsWith("/api/v2/run"));
  await page.getByRole("button", { name: "Run Neverlost Analysis" }).click();
  const response = await responsePromise;
  expect(response.status()).toBe(200);
  const output = await response.json();
  expect(output.engine.v1_1).toBe(output.v1_1.engine_identity);
  expect(output.v1_1.upstream_v1_sha256).toBe(output.result_sha256);
  expect(output.counts.capacity_windows).toBeGreaterThan(0);
  await expect(page.getByText(output.run_id, { exact: true })).toBeVisible();
  for (const [label, slug] of [
    ["Timeline", "timeline"], ["Evidence", "evidence"], ["Hidden States", "hidden-states"],
    ["Trust Thresholds", "trust-thresholds"], ["Bottlenecks", "bottlenecks"],
    ["Capacity Windows", "capacity"], ["Reports", "reports"],
  ]) {
    await page.getByRole("navigation", { name: "V2 results" }).getByRole("link", { name: label, exact: true }).click();
    await expect(page).toHaveURL(new RegExp("/v2/" + slug + "$"));
    await expect(page.getByRole("heading", { level: 1, name: label })).toBeVisible();
    await expect(page.getByText(output.run_id, { exact: true })).toBeVisible();
    expect((await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze()).violations).toEqual([]);
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBeTruthy();
  }
  await page.getByText("healthcare_reality_map.md", { exact: true }).click();
  await expect(page.locator("pre").filter({ hasText: "# Healthcare Reality Map" })).toHaveText(output.reports["healthcare_reality_map.md"]);
  const source = page.getByRole("button", { name: "Inspect source · physical_therapy.pdf", exact: true });
  await source.focus();
  await page.keyboard.press("Enter");
  await expect(page.getByRole("dialog")).toBeVisible();
  await expect(page.getByRole("dialog").getByRole("heading", { name: "Page 1" })).toBeVisible();
  expect((await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze()).violations).toEqual([]);
  await page.keyboard.press("Escape");
  await expect(source).toBeFocused();
  await page.screenshot({ path: testInfo.outputPath("v2-results.png"), fullPage: true });
  await page.reload();
  await expect(page.getByRole("heading", { name: "No live run in this browser session" })).toBeVisible();
  expect(errors).toEqual([]);
});

test("direct entry, real failure and no fixture fallback", async ({ page }) => {
  await page.goto("/v2/evidence");
  await expect(page.getByRole("heading", { name: "No live run in this browser session" })).toBeVisible();
  await page.getByRole("link", { name: "Choose a synthetic case" }).click();
  await expect(page.getByRole("button", { name: "Run Neverlost Analysis" })).toBeEnabled();
  await page.route("**/api/v2/run", (route) => route.fulfill({
    status: 503, contentType: "application/json",
    body: JSON.stringify({ error: "Execution unavailable. No fixture result was substituted." }),
  }));
  await page.getByRole("button", { name: "Run Neverlost Analysis" }).click();
  await expect(page.getByRole("main").getByRole("alert")).toContainText("No fixture result");
  await expect(page.getByRole("heading", { name: "Run ledger" })).toHaveCount(0);
});
