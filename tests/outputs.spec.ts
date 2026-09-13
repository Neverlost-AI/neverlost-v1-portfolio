import { expect, test, type Page } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import { DISCLAIMER, evidenceById, timeline, reports, hiddenStates, bottlenecks, capacityWindows } from "../src/lib/demo-data";
import { historicalDomains, matrixAnnotations } from "../src/lib/output-data";

async function inspect(page: Page, context: string, id: string) {
  const item = evidenceById(id);
  const trigger = page.getByRole("button", { name: `Inspect source for ${context}`, exact: true });
  await trigger.focus();
  await page.keyboard.press("Enter");
  const dialog = page.getByRole("dialog");
  await expect(dialog).toBeVisible();
  for (const value of [item.source.document, item.source.chunkId, item.source.sourceType, item.source.excerpt, item.date, item.category, item.reviewStatus, item.interpretation]) {
    await expect(dialog.getByText(value, { exact: true })).toBeVisible();
  }
  await expect(dialog.locator("dd").filter({ hasText: new RegExp(`^${item.source.page}$`) })).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(dialog).not.toBeVisible();
  await expect(trigger).toBeFocused();
}

for (const [route, title] of [["timeline", "Timeline"], ["evidence-matrix", "Evidence Matrix"], ["reports", "Reports"]]) {
  test(`${title}: responsive, accessible and source-bounded`, async ({ page }, testInfo) => {
    const errors: string[] = [];
    const external: string[] = [];
    page.on("pageerror", (error) => errors.push(error.message));
    page.on("request", (request) => {
      if (!["localhost", "127.0.0.1"].includes(new URL(request.url()).hostname)) external.push(request.url());
    });
    await page.goto("/" + route);
    await expect(page.getByRole("heading", { name: title + ".", level: 1 })).toBeVisible();
    await expect(page.getByText(DISCLAIMER, { exact: true }).first()).toBeVisible();
    await expect(page.getByText("Presentation only. No historical pipeline is executed. Human review remains required.")).toBeVisible();
    if (testInfo.project.name === "mobile") await page.locator(".mobile-navigation > summary").click();
    const nav = page.getByRole("navigation", { name: "Demo views", exact: true }).filter({ visible: true });
    await expect(nav.getByRole("link")).toHaveCount(7);
    await expect(nav.getByRole("button")).toHaveCount(0);
    await expect(nav.locator('[aria-current="page"]')).toHaveText(title);
    if (testInfo.project.name === "mobile") await page.locator(".mobile-navigation > summary").click();
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    expect((await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze()).violations).toEqual([]);
    await page.screenshot({ path: testInfo.outputPath(route + "-" + testInfo.project.name + ".png"), fullPage: true });
    if (testInfo.project.name === "mobile") await page.locator(".mobile-navigation > summary").click();
    await nav.getByRole("link", { name: "Overview", exact: true }).click();
    await expect(page).toHaveURL("/");
    await expect(page.getByRole("heading", { name: "From scattered records to a clearer picture." })).toBeVisible();
    expect(errors).toEqual([]);
    expect(external).toEqual([]);
  });
}

test("Timeline preserves chronological observations, interpretations and every source", async ({ page }) => {
  await page.goto("/timeline");
  await expect(page.locator(".longitudinal-list time")).toHaveText(["Jun 03", "Jun 06", "Jun 10", "Jun 14"]);
  await expect(page.locator(".longitudinal-list .status-tag")).toHaveText(["Direct source", "Direct source", "Interpretation", "Interpretation"]);
  for (const event of timeline) {
    await expect(page.getByRole("article", { name: event.label })).toContainText(evidenceById(event.evidenceId).source.excerpt);
    await inspect(page, `timeline ${event.id}`, event.evidenceId);
  }
  await page.getByRole("button", { name: "Inspect source for timeline DEMO-T01", exact: true }).click();
  expect((await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze()).violations).toEqual([]);
});

test("Evidence Matrix preserves domain gaps, annotations, types and complete provenance", async ({ page }) => {
  await page.goto("/evidence-matrix");
  for (const row of matrixAnnotations) await inspect(page, `matrix ${row.evidenceId}`, row.evidenceId);
  await page.getByRole("combobox", { name: "Functional domain", exact: true }).selectOption("care coordination");
  await expect(page.getByRole("status")).toHaveText("2 of 4 sample rows");
  await page.getByRole("combobox", { name: "Evidence type", exact: true }).selectOption("Interpretation");
  await expect(page.getByRole("status")).toHaveText("1 of 4 sample rows");
  await expect(page.getByRole("article")).toContainText("The next-step owner is not named in this note.");
  await page.getByRole("combobox", { name: "Evidence type", exact: true }).selectOption("All evidence");
  for (const domain of historicalDomains) {
    await page.getByRole("combobox", { name: "Functional domain", exact: true }).selectOption(domain);
    const count = matrixAnnotations.filter((row) => row.domains.includes(domain)).length;
    await expect(page.getByRole("status")).toHaveText(`${count} of 4 sample rows`);
    if (!count) await expect(page.getByText("This does not establish absence of a condition or resolve an evidence gap.")).toBeVisible();
  }
  await page.getByRole("button", { name: "Reset filters" }).click();
  await expect(page.getByRole("article")).toHaveCount(4);
  await page.locator(".domain-coverage > summary").click();
  await expect(page.locator(".domain-coverage li")).toHaveCount(historicalDomains.length);
  expect((await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze()).violations).toEqual([]);
  await page.getByRole("combobox", { name: "Functional domain", exact: true }).selectOption("pain");
  await page.reload();
  await expect(page.getByRole("combobox", { name: "Functional domain", exact: true })).toHaveValue("All domains");
  await expect(page.getByRole("status")).toHaveText("4 of 4 sample rows");
});

test("Reports expose readable drafts traceable to every synthetic input and candidate", async ({ page }, testInfo) => {
  test.setTimeout(90000);
  await page.goto("/reports");
  await expect(page.getByText(/Not a verified clinical, disability, legal, or benefits determination/)).toBeVisible();
  await expect(page.locator(".report-preview")).toHaveCount(3);
  for (const report of reports) {
    const panel = page.locator(".report-preview").filter({ has: page.locator("summary", { hasText: report.title }) });
    await panel.locator("summary").click();
    await expect(panel).toContainText(report.evidenceIds.join(" · "));
    if (report.id === "DEMO-R01") {
      for (const event of timeline) await inspect(page, `report timeline ${event.id}`, event.evidenceId);
    } else {
      for (const id of report.evidenceIds) await inspect(page, `report matrix ${id}`, id);
    }
    expect((await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze()).violations).toEqual([]);
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    await panel.locator("summary").click();
  }
  const reality = page.locator(".report-preview").filter({ has: page.locator("summary", { hasText: "Healthcare Reality Map" }) });
  await reality.locator("summary").click();
  for (const item of [...hiddenStates, ...bottlenecks, ...capacityWindows]) {
    await expect(reality.getByRole("article", { name: item.title, exact: true })).toContainText(item.status);
    await inspect(page, `reality map ${item.id}`, item.evidenceId);
  }
  await expect(reality).toContainText("Retained gains: Unknown");
  await expect(reality).toContainText("No trust-threshold fixture is available");
  expect((await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze()).violations).toEqual([]);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.screenshot({ path: testInfo.outputPath("reality-report-" + testInfo.project.name + ".png"), fullPage: true });
  await page.reload();
  await expect(page.locator(".report-preview[open]")).toHaveCount(0);
});
