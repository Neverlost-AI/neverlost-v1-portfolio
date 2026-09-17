import { expect, test } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import { surfaces } from "../../src/lib/v2/contracts";

test("V2 identity and navigation stay current while historical routes remain available", async ({ page }, testInfo) => {
  test.setTimeout(120_000);
  await page.goto("/");
  await expect(page).toHaveURL(/\/v2$/);
  await expect(page).toHaveTitle("Neverlost V2 · Longitudinal Evidence Analysis");
  await page.reload();
  await expect(page).toHaveURL(/\/v2$/);
  await page.goto("/v2");
  await expect(page).toHaveTitle("Neverlost V2 · Longitudinal Evidence Analysis");
  await expect(page.locator('meta[name="description"]')).toHaveAttribute("content", /Live longitudinal evidence analysis.*Curated synthetic cases only/);
  const header = page.getByRole("banner");
  await expect(header.getByRole("link")).toHaveCount(1);
  await expect(header.getByRole("link", { name: /Neverlost V2/ })).toHaveAttribute("href", "/v2");
  await expect(header).not.toContainText(/Frozen|Reconstruction|sandbox|V1/i);
  await expect(page.locator('a[href="/"], a[href="/v1"], a[href="/v1-1"]')).toHaveCount(0);
  await expect(page.getByText(/Neverlost V2 analyzes records over time/)).toBeVisible();
  await expect(page.getByText(/Engine provenance: preserved June 2026 V1 Python and recovered V1.1 processing/)).toBeVisible();
  await expect(page.getByText(/V1.1 final-synthesis generation remains unestablished/)).toBeVisible();
  await expect(page.getByLabel("Synthetic case", { exact: true })).toBeEnabled();
  expect((await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze()).violations).toEqual([]);
  await page.screenshot({ path: testInfo.outputPath("v2-public-identity.png"), fullPage: true });

  for (const [slug, label] of surfaces) {
    await page.getByRole("navigation", { name: "V2 results" }).getByRole("link", { name: label, exact: true }).click();
    await expect(page).toHaveURL(new RegExp(`/v2/${slug}$`));
    await expect(page.getByRole("heading", { level: 1, name: label, exact: true })).toBeVisible();
    await expect(header.getByRole("link")).toHaveCount(1);
    await expect(page.locator('a[href="/"], a[href="/v1"], a[href="/v1-1"]')).toHaveCount(0);
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBeTruthy();
  }
  await header.getByRole("link", { name: /Neverlost V2/ }).focus();
  await page.keyboard.press("Enter");
  await expect(page).toHaveURL(/\/v2$/);
  await page.reload();
  await expect(page).toHaveTitle("Neverlost V2 · Longitudinal Evidence Analysis");

  // Historical experiences remain reachable by direct URL, not V2 navigation.
  for (const path of ["/v1", "/v1-1"]) {
    const response = await page.goto(path);
    expect(response?.status()).toBe(200);
    await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
    expect((await page.reload())?.status()).toBe(200);
  }
  await page.getByRole("link", { name: "V1 · Frozen demo", exact: true }).click();
  await expect(page).toHaveURL(/\/v1$/);
  await expect(page.getByRole("heading", { name: "Overview." })).toBeVisible();
});
