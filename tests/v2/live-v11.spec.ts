import { expect, test } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

const surfaces = [
  ["Source Authority / Evidence", "source-authority"], ["Run Review", "run-review"],
  ["Prioritized Evidence", "prioritized-evidence"], ["Capacity Themes", "capacity-themes"],
  ["Denials & Bottlenecks", "denials"], ["Final Review / Reports", "final-review"],
] as const;

test("live recovered V1.1 case004: every surface, provenance, keyboard and accessibility", async ({ page }) => {
  test.setTimeout(180_000);
  const errors: string[] = [];
  page.on("pageerror", error => errors.push(error.message));
  await page.goto("/v2");
  await expect(page.getByLabel("Synthetic case", { exact: true })).toBeEnabled();
  await page.getByLabel("Synthetic case", { exact: true }).selectOption("case_004");
  const finished = page.waitForResponse(response => response.url().endsWith("/api/v2/run"));
  await page.getByRole("button", { name: "Run Neverlost Analysis" }).click();
  const response = await finished;
  expect(response.status()).toBe(200);
  const run = await response.json();
  expect(run.v1_1.evidence_matrix).toHaveLength(6);
  expect(run.v1_1.actual_denial_source_present).toBe(true);
  for (const [label, slug] of surfaces) {
    await page.getByRole("navigation", { name: "V2 results" }).getByRole("link", { name: label, exact: true }).click();
    await expect(page).toHaveURL(new RegExp(`/v2/${slug}$`));
    await expect(page.getByRole("heading", { level: 1, name: label, exact: true })).toBeVisible();
    await expect(page.getByText(run.run_id, { exact: true })).toBeVisible();
    expect((await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze()).violations).toEqual([]);
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBeTruthy();
    const source = page.getByRole("button", { name: "Inspect source · health record.txt", exact: true }).first();
    await source.focus();
    await page.keyboard.press("Enter");
    await expect(page.getByRole("dialog")).toContainText("Provider observed difficulty standing and walking");
    expect((await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze()).violations).toEqual([]);
    await page.keyboard.press("Escape");
    await expect(source).toBeFocused();
  }
  await page.getByText("healthcare_reality_map.md", { exact: true }).click();
  await expect(page.locator("pre").filter({ hasText: "# Healthcare Reality Map" })).toHaveText(run.v1_1.reports["healthcare_reality_map.md"]);
  await page.reload();
  await expect(page.getByRole("heading", { name: "No live run in this browser session" })).toBeVisible();
  expect(errors).toEqual([]);
});

test("live V1.1 direct routes never show fixtures and no-denial result remains explicit", async ({ page }) => {
  test.setTimeout(120_000);
  for (const [label, slug] of surfaces) {
    await page.goto(`/v2/${slug}`);
    await expect(page.getByRole("heading", { level: 1, name: label, exact: true })).toBeVisible();
    await expect(page.getByRole("heading", { name: "No live run in this browser session" })).toBeVisible();
  }
  await page.goto("/v2");
  await expect(page.getByLabel("Synthetic case", { exact: true })).toBeEnabled();
  await page.getByLabel("Synthetic case", { exact: true }).selectOption("case_003");
  await page.getByRole("button", { name: "Run Neverlost Analysis" }).click();
  await expect(page.getByRole("heading", { name: "Run ledger" })).toBeVisible({ timeout: 60_000 });
  await page.getByRole("navigation", { name: "V2 results" }).getByRole("link", { name: "Denials & Bottlenecks", exact: true }).click();
  await expect(page.getByText("Historical raw mapping exists: YES", { exact: true })).toBeVisible();
  await expect(page.getByText("Actual classified denial source present: NO", { exact: true })).toBeVisible();
});
