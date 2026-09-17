import { expect, test } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import { bottlenecks, capacityWindows, DISCLAIMER, evidence, evidenceById, hiddenStates, reports, timeline } from "../src/lib/demo-data";

test("Overview is responsive, honest about scope, and accessible", async ({ page }, testInfo) => {
  const errors: string[] = [];
  const externalRequests: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  page.on("request", (request) => {
    if (!new URL(request.url()).hostname.match(/^(127\.0\.0\.1|localhost)$/)) externalRequests.push(request.url());
  });
  await page.goto("/v1");
  await expect(page.getByRole("heading", { name: "Overview." })).toBeVisible();
  await expect(page.getByText(DISCLAIMER, { exact: true }).first()).toBeVisible();
  await expect(page.getByText("Presentation only. No records are processed.")).toBeVisible();
  await expect(page.getByRole("table").getByRole("row")).toHaveCount(5);
  if (testInfo.project.name === "mobile") await page.locator(".mobile-navigation > summary").click();
  const nav = page.getByRole("navigation", { name: "Demo views" }).filter({ visible: true });
  await expect(nav.getByRole("button")).toHaveCount(0);
  await expect(nav.getByRole("link")).toHaveCount(7);
  for (const button of await nav.getByRole("button").all()) await expect(button).toBeDisabled();
  if (testInfo.project.name === "mobile") await page.locator(".mobile-navigation > summary").click();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(page.viewportSize()!.width);
  await page.screenshot({ path: testInfo.outputPath(`overview-${testInfo.project.name}.png`), fullPage: true });
  const accessibility = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze();
  expect(accessibility.violations).toEqual([]);
  expect(errors).toEqual([]);
  expect(externalRequests).toEqual([]);
});

test("evidence filters and complete provenance inspection work", async ({ page }) => {
  await page.goto("/v1");
  await page.getByRole("button", { name: "Interpretation", exact: true }).click();
  await expect(page.getByText("2 of 4 entries", { exact: true })).toBeVisible();
  await expect(page.getByRole("table").getByRole("row")).toHaveCount(3);
  const trigger = page.getByRole("button", { name: "Inspect DEMO-E03: The next-step owner is unclear" });
  await trigger.click();
  const dialog = page.getByRole("dialog");
  await expect(dialog).toBeVisible();
  const item = evidenceById("DEMO-E03");
  for (const value of [item.source.document, item.source.chunkId, item.source.sourceType, item.source.excerpt, item.date, item.category, item.interpretation]) {
    await expect(dialog.getByText(value, { exact: true })).toBeVisible();
  }
  await expect(dialog.locator("dd").filter({ hasText: /^2$/ })).toBeVisible();
  const accessibility = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze();
  expect(accessibility.violations).toEqual([]);
  await page.keyboard.press("Escape");
  await expect(dialog).not.toBeVisible();
  await expect(trigger).toBeFocused();
  await page.getByRole("button", { name: "Direct source", exact: true }).click();
  await expect(page.getByRole("table").getByText("Needs review", { exact: true })).toHaveCount(0);
  await page.getByRole("button", { name: "All evidence" }).click();
  await expect(page.getByRole("table").getByRole("row")).toHaveCount(5);
  await page.reload();
  await expect(page.getByRole("button", { name: "All evidence" })).toHaveAttribute("aria-pressed", "true");
});

test("about dialog and overview source previews behave correctly", async ({ page }) => {
  await page.goto("/v1");
  await page.getByRole("button", { name: "About this demo" }).click();
  await expect(page.getByRole("dialog")).toContainText("No LLM execution, autonomous agents, durable state, or clinical validation.");
  await page.getByRole("button", { name: "Close dialog" }).click();
  await page.getByRole("button", { name: "Inspect source for Activity noted" }).click();
  await expect(page.getByRole("dialog")).toContainText("DEMO-ACTIVITY-001");
  await page.keyboard.press("Escape");
  await page.getByRole("button", { name: "Clarify next-step ownership" }).click();
  await expect(page.getByRole("dialog")).toContainText("DEMO-COORD-002");
});

test("all synthetic category fixtures resolve to preserved source references", () => {
  const linked = [...timeline, ...bottlenecks, ...hiddenStates, ...capacityWindows];
  for (const entry of linked) {
    const source = evidenceById(entry.evidenceId).source;
    expect(source.document).toMatch(/^synthetic-/);
    expect(source.page).toBeGreaterThan(0);
    expect(source.chunkId).toMatch(/^DEMO-/);
    expect(source.excerpt).toBeTruthy();
  }
  for (const report of reports) for (const id of report.evidenceIds) expect(evidenceById(id)).toBeDefined();
  expect(new Set(evidence.map((item) => item.id)).size).toBe(evidence.length);
});
