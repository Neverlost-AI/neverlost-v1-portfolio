// Explicitly invoked smoke check. Optional CLI-issued preview cookie stays local.
import { chromium } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import { mkdir, readFile } from "node:fs/promises";

const base = process.argv[2];
if (!base || !/^https?:\/\//.test(base)) throw new Error("Supply the preview or local base URL.");
await mkdir("test-results/v2-preview", { recursive: true });
const browser = await chromium.launch();
try {
  for (const [name, viewport] of [["desktop", { width: 1440, height: 1080 }], ["mobile", { width: 390, height: 844 }]]) {
    const context = await browser.newContext({ viewport });
    if (process.env.V2_PREVIEW_COOKIE_JAR) {
      const jar = await readFile(process.env.V2_PREVIEW_COOKIE_JAR, "utf8");
      const cookies = jar.split(/\r?\n/).filter((line) => line && (!line.startsWith("#") || line.startsWith("#HttpOnly_"))).map((line) => {
        const [domain, , path, secure, expires, name, value] = line.replace(/^#HttpOnly_/, "").split("\t");
        if (domain.replace(/^\./, "") !== new URL(base).hostname) throw new Error("Preview cookie hostname mismatch.");
        return { domain, path, secure: secure === "TRUE", expires: Number(expires) || -1, name, value, httpOnly: line.startsWith("#HttpOnly_") };
      });
      await context.addCookies(cookies);
    }
    const page = await context.newPage();
    const errors = [];
    page.on("pageerror", (error) => errors.push(error.message));
    const response = await page.goto(base + "/v2");
    if (response.status() !== 200) throw new Error("V2 entry did not return 200.");
    await page.getByLabel("Synthetic case", { exact: true }).selectOption("case_002", { timeout: 30_000 });
    const finished = page.waitForResponse((r) => r.url().includes("/api/v2/run"), { timeout: 60_000 });
    await page.getByRole("button", { name: "Run Neverlost Analysis" }).click();
    const result = await finished;
    if (!result.ok()) throw new Error("Python execution failed with " + result.status());
    const run = await result.json();
    await page.getByText(run.run_id, { exact: true }).waitFor();
    await page.screenshot({ path: "test-results/v2-preview/" + name + ".png", fullPage: true });
    for (const label of ["Timeline", "Evidence", "Hidden States", "Trust Thresholds", "Bottlenecks", "Capacity Windows", "Reports"]) {
      await page.getByRole("navigation", { name: "V2 results" }).getByRole("link", { name: label, exact: true }).click();
      await page.getByRole("heading", { level: 1, name: label }).waitFor();
      await page.getByText(run.run_id, { exact: true }).waitFor();
      const axe = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze();
      if (axe.violations.length) throw new Error(label + ": " + JSON.stringify(axe.violations));
      if (await page.evaluate(() => document.documentElement.scrollWidth > innerWidth)) throw new Error("Horizontal overflow");
    }
    await page.getByRole("button", { name: "Inspect source · physical_therapy.pdf", exact: true }).click();
    await page.getByRole("dialog").getByRole("heading", { name: "Page 1" }).waitFor();
    await page.keyboard.press("Escape");
    await page.reload();
    await page.getByRole("heading", { name: "No live run in this browser session" }).waitFor();
    if (errors.length) throw new Error(errors.join("\n"));
    console.log(JSON.stringify({ viewport: name, status: "passed", case_id: run.case_id, result_sha256: run.result_sha256, counts: run.counts }));
    await context.close();
  }
} finally {
  await browser.close();
}
