import { expect, test } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import { bottlenecks, capacityWindows, hiddenStates, evidenceById, DISCLAIMER } from "../src/lib/demo-data";

const views = [
  { route: "/hidden-states", title: "Hidden States", items: hiddenStates },
  { route: "/bottlenecks", title: "Bottlenecks", items: bottlenecks },
  { route: "/capacity-windows", title: "Capacity Windows", items: capacityWindows },
] as const;

for (const view of views) {
  test(`${view.title}: responsive concept, navigation, boundaries and accessibility`, async ({ page }, testInfo) => {
    const errors: string[] = [];
    const external: string[] = [];
    page.on("pageerror", (error) => errors.push(error.message));
    page.on("request", (request) => {
      if (!["127.0.0.1", "localhost"].includes(new URL(request.url()).hostname)) external.push(request.url());
    });
    await page.goto(view.route);
    await expect(page.getByRole("heading", { level: 1, name: `${view.title}.` })).toBeVisible();
    await expect(page.getByText(DISCLAIMER, { exact: true }).first()).toBeVisible();
    await expect(page.getByRole("article")).toHaveCount(view.items.length);
    await expect(page.getByText(/Reading order only/)).toBeVisible();
    for (const item of view.items) {
      const record = evidenceById(item.evidenceId);
      const card = page.getByRole("article", { name: item.title, exact: true });
      for (const value of [item.title, record.source.excerpt, record.interpretation, record.source.document]) {
        await expect(card.getByText(value, { exact: true }).first()).toBeVisible();
      }
      await expect(card).toContainText(item.id);
      await expect(card).toContainText(record.id);
      await expect(card).toContainText(record.source.chunkId);
      await expect(card).toContainText(item.status);
      if ("owner" in item) {
        await expect(card.getByText(item.owner, { exact: true })).toBeVisible();
        await expect(card.getByText(item.nextSmallestAction, { exact: true })).toBeVisible();
      }
      if ("retainedGains" in item) await expect(card.getByText(item.retainedGains, { exact: true })).toBeVisible();
    }
    if (testInfo.project.name === "mobile") await page.locator(".mobile-navigation > summary").click();
    const nav = page.getByRole("navigation", { name: "Demo views", exact: true }).filter({ visible: true });
    await expect(nav.getByRole("link")).toHaveCount(7);
    await expect(nav.locator('[aria-current="page"]')).toHaveText(view.title);
    for (const label of ["Timeline", "Evidence Matrix", "Reports"]) {
      await expect(nav.getByRole("link", { name: label, exact: true })).toBeVisible();
    }
    if (testInfo.project.name === "mobile") await page.locator(".mobile-navigation > summary").click();
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    await page.screenshot({ path: testInfo.outputPath(`${view.route.slice(1)}-${testInfo.project.name}.png`), fullPage: true });
    expect((await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze()).violations).toEqual([]);
    await page.getByRole("button", { name: "About this demo" }).click();
    await expect(page.getByRole("dialog")).toContainText("not saved review decisions");
    await page.keyboard.press("Escape");
    for (const destination of views) {
      await page.getByRole("navigation", { name: "Analytical concept views", exact: true }).getByRole("link", { name: new RegExp(destination.title) }).click();
      await expect(page).toHaveURL(destination.route);
      await expect(page.getByRole("heading", { level: 1 })).toHaveText(destination.title + ".");
    }
    await page.reload();
    await expect(page.getByRole("dialog")).not.toBeVisible();
    expect(errors).toEqual([]);
    expect(external).toEqual([]);
  });

  test(`${view.title}: every candidate preserves complete source details and keyboard dialog behavior`, async ({ page }) => {
    await page.goto(view.route);
    for (const item of view.items) {
      const record = evidenceById(item.evidenceId);
      const trigger = page.getByRole("button", { name: `Inspect source for ${item.id}`, exact: true });
      await trigger.focus();
      await page.keyboard.press("Enter");
      const dialog = page.getByRole("dialog");
      await expect(dialog).toBeVisible();
      for (const value of [record.source.document, record.source.chunkId, record.source.sourceType, record.source.excerpt, record.date, record.category, record.reviewStatus, record.interpretation]) {
        await expect(dialog.getByText(value, { exact: true })).toBeVisible();
      }
      await expect(dialog.locator("dd").filter({ hasText: new RegExp(`^${record.source.page}$`) })).toBeVisible();
      expect((await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze()).violations).toEqual([]);
      await expect(dialog.getByRole("button", { name: "Close dialog" })).toBeFocused();
      // Native dialogs may allow Tab into browser chrome (reported as body).
      // No background document control may receive focus while the modal is open.
      await page.keyboard.press("Tab");
      expect(await page.evaluate(() => document.activeElement === document.body || !!document.activeElement?.closest("dialog"))).toBe(true);
      await page.keyboard.press("Shift+Tab");
      await expect(dialog.getByRole("button", { name: "Close dialog" })).toBeFocused();
      await page.keyboard.press("Escape");
      await expect(dialog).not.toBeVisible();
      await expect(trigger).toBeFocused();
    }
  });
}
