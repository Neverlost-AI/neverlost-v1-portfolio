import { expect, test } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import { scenarios, scenarioById, RECONSTRUCTION, V11_DISCLAIMER } from "../../src/lib/v11/fixtures";
import { classify, review, documentFor } from "../../src/lib/v11/rules";

test("V1.1 rules: authority is distinct from subject matter and absence", () => {
  const mixed = review(scenarioById("mixed"));
  expect(mixed.documents.map(d => d.classification.type)).toEqual(["health-system/provider record", "OT record", "insurance denial letter", "unknown"]);
  expect(mixed.documents[1].classification.payer).toBe("Sample Plan (fictional)");
  expect(review(scenarioById("no-denial")).denialPresent).toBe(false);
  expect(review(scenarioById("no-denial")).actions).toEqual([]);
  expect(review(scenarioById("unknown")).warnings.map(w => w.code)).toEqual(expect.arrayContaining(["unknown-source", "ocr-review", "confidence"]));
  expect(review(scenarioById("conflict")).classificationStatus).toBe("Classification issues need review");
  expect(scenarioById("conflict").evidence[0].declaredType).toBe("PT record");
  expect(review(scenarioById("empty")).classificationStatus).toBe("Not assessed — no input");
  expect(review(scenarioById("empty")).actions).toEqual([]);
});

test("V1.1 rules: strict volume boundaries and ordered three-action cap", () => {
  const load = scenarioById("review-load");
  const at = review({ ...load, evidence: load.evidence.slice(0,100), candidateWindows: load.candidateWindows.slice(0,20) });
  expect(at.actions).toEqual([]);
  expect(review(load).actions).toHaveLength(2);
  const mixed = scenarioById("mixed");
  const all = review({ ...load, documents: mixed.documents, evidence: [...load.evidence, ...mixed.evidence] });
  expect(all.actions).toHaveLength(3);
  expect(all.actions[0].title).toContain("unknown");
  expect(all.actions[1].title).toContain("prioritize");
  expect(all.actions[2].title).toContain("consolidate");
  expect(all.warnings.some(w => w.code === "payer-review")).toBe(true);
});

test("V1.1 fixtures: immutable evaluation and resolvable provenance", () => {
  const before = JSON.stringify(scenarios);
  for (const scenario of scenarios) {
    review(scenario);
    for (const row of scenario.evidence) expect(documentFor(scenario,row).chunkId).toMatch(/^SYN11-/);
    for (const window of scenario.candidateWindows) expect(scenario.evidence.some(e => e.id === window.evidenceId)).toBe(true);
  }
  expect(JSON.stringify(scenarios)).toBe(before);
  const row = scenarioById("mixed").evidence[0];
  expect(() => documentFor(scenarioById("empty"),row)).toThrow("Unresolved synthetic document reference");
  expect(classify({ ...scenarioById("mixed").documents[0], name:"synthetic-fragment.md", excerpt:"No source markers." }).type).toBe("unknown");
});

for (const [route,title] of [["/v1-1","Source Authority / Evidence"],["/v1-1/run-review","Run Review"]]) {
  test(`V1.1 ${title}: responsive, accessible, bounded and inspectable`, async ({page}, info) => {
    const errors:string[] = [];
    const external:string[] = [];
    page.on("pageerror", e => errors.push(e.message));
    page.on("request", r => { if (!["127.0.0.1","localhost"].includes(new URL(r.url()).hostname)) external.push(r.url()); });
    await page.goto(route);
    await expect(page.getByRole("heading",{name:title,exact:true,level:1})).toBeVisible();
    await expect(page.getByText(RECONSTRUCTION,{exact:true})).toBeVisible();
    await expect(page.getByText(V11_DISCLAIMER,{exact:true})).toBeVisible();
    await expect(page.getByRole("navigation",{name:"V1.1 surfaces"}).getByRole("link")).toHaveCount(2);
    await page.getByText("What changed from V1?",{exact:true}).click();
    await expect(page.getByText(/not authenticated Git history/)).toBeVisible();
    expect((await new AxeBuilder({page}).withTags(["wcag2a","wcag2aa","wcag21aa"]).analyze()).violations).toEqual([]);
    for (const doc of scenarioById("mixed").documents) {
      const trigger = page.getByRole("button",{name:`Inspect source ${doc.id}`,exact:true});
      await trigger.focus();
      await page.keyboard.press("Enter");
      const dialog = page.getByRole("dialog");
      await expect(dialog).toBeVisible();
      for (const value of [doc.id,doc.name,doc.chunkId,doc.excerpt]) await expect(dialog.getByText(value,{exact:true})).toBeVisible();
      await expect(dialog.locator("dd").filter({hasText:new RegExp(`^${doc.page}$`)})).toBeVisible();
      expect((await new AxeBuilder({page}).withTags(["wcag2a","wcag2aa","wcag21aa"]).analyze()).violations).toEqual([]);
      await page.keyboard.press("Escape");
      await expect(dialog).not.toBeVisible();
      await expect(trigger).toBeFocused();
    }
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    await page.screenshot({path:info.outputPath("v11-"+info.project.name+".png"),fullPage:true});
    const select=page.getByRole("combobox",{name:"Synthetic input scenario"});
    for (const id of ["no-denial","unknown","conflict","empty","review-load"]) {
      await select.selectOption(id);
      expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
      expect((await new AxeBuilder({page}).withTags(["wcag2a","wcag2aa","wcag21aa"]).analyze()).violations).toEqual([]);
      if (title==="Run Review") {
        const state=review(scenarioById(id));
        await expect(page.getByText(state.classificationStatus,{exact:true})).toBeVisible();
        for(const action of state.actions) await expect(page.getByRole("heading",{name:action.title,exact:true})).toBeVisible();
        if(id==="no-denial") await expect(page.getByText("No payer-denial source supplied",{exact:true})).toBeVisible();
      } else if(id==="empty") await expect(page.getByRole("heading",{name:"No source documents supplied"})).toBeVisible();
    }
    await page.reload();
    await expect(select).toHaveValue("mixed");
    await page.getByRole("navigation",{name:"Portfolio version"}).getByRole("link",{name:"V1 · Frozen demo",exact:true}).click();
    await expect(page.getByRole("heading",{name:"From scattered records to a clearer picture."})).toBeVisible();
    expect(errors).toEqual([]);
    expect(external).toEqual([]);
  });
}

test("V1.1 evidence exposes observations, interpretations and unrepaired mismatch",async({page})=>{
  await page.goto("/v1-1");
  await page.getByRole("combobox",{name:"Synthetic input scenario"}).selectOption("conflict");
  await page.getByText("Evidence entries (1)",{exact:true}).click();
  const row=scenarioById("conflict").evidence[0];
  await expect(page.getByText(row.observation,{exact:true})).toBeVisible();
  await expect(page.getByText(row.interpretation,{exact:true})).toBeVisible();
  await expect(page.getByText("PT record",{exact:true})).toBeVisible();
  await expect(page.getByText("OT record",{exact:true})).toBeVisible();
  await expect(page.getByText("Evidence row type differs from document classification.",{exact:true})).toBeVisible();
});

