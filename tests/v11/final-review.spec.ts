import {test,expect} from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import {scenarios as foundationScenarios,scenarioById as foundationById,RECONSTRUCTION,V11_DISCLAIMER} from "../../src/lib/v11/fixtures";
import {review,documentFor} from "../../src/lib/v11/rules";
import {priorityScenarios,priorityScenario} from "../../src/lib/v11/prioritized/fixtures";
import {prioritize} from "../../src/lib/v11/prioritized/ranking";
import {scenarios as consolidatedScenarios,scenarioById as consolidatedById} from "../../src/lib/v11/consolidated/fixtures";
import {detect} from "../../src/lib/v11/consolidated/bottlenecks";
import {consolidate} from "../../src/lib/v11/consolidated/themes";
import {mapDenial} from "../../src/lib/v11/consolidated/denials";

test("M07 existing outputs stay independent across every scenario",async({page})=>{
  await page.goto("/v1-1/final-review");
  const before=JSON.stringify([foundationScenarios,priorityScenarios,consolidatedScenarios]);
  for(const s of foundationScenarios){
    await page.getByLabel("Independent M04 scenario").selectOption(s.id);
    const r=review(s);
    await expect(page.getByTestId("foundation-counts")).toHaveText(`${s.documents.length} documents · ${s.evidence.length} evidence rows · ${r.warnings.length} warnings · ${r.actions.length} suggested reviews`);
    await expect(page.getByLabel("Independent M05 scenario")).toHaveValue("global");
    await expect(page.getByLabel("Independent M06 scenario")).toHaveValue("mixed");
  }
  for(const s of priorityScenarios){
    await page.getByLabel("Independent M05 scenario").selectOption(s.id);
    const selected=prioritize(s.rows,s.bottlenecks).filter(r=>r.selected).length;
    await expect(page.getByTestId("priority-counts")).toHaveText(`${s.rows.length} candidates · ${selected} selected · ${s.rows.length-selected} excluded`);
  }
  for(const s of consolidatedScenarios){
    await page.getByLabel("Independent M06 scenario").selectOption(s.id);
    const groups=detect(s.rows).groups;
    await expect(page.getByTestId("consolidated-counts")).toHaveText(`${s.windows.length} windows · ${consolidate(s,groups).length} themes · ${groups.length} candidate bottlenecks`);
    await expect(page.getByRole("status")).toContainText(mapDenial(s.rows)?"Payer-denial source present":"No payer-denial source supplied; no denial mapping created.");
  }
  expect(JSON.stringify([foundationScenarios,priorityScenarios,consolidatedScenarios])).toBe(before);
  await page.reload();
  await expect(page.getByLabel("Independent M04 scenario")).toHaveValue("mixed");
  await expect(page.getByLabel("Independent M05 scenario")).toHaveValue("global");
  await expect(page.getByLabel("Independent M06 scenario")).toHaveValue("mixed");
});

test("M07 source inspection preserves all default-set references and observation boundaries",async({page})=>{
  test.setTimeout(90000);
  await page.goto("/v1-1/final-review");
  await page.getByText("Inspect M04 source evidence (4)",{exact:true}).click();
  await page.getByText("Inspect ranked output and provenance (30)",{exact:true}).click();
  await page.getByText("Inspect M06 source evidence (6)",{exact:true}).click();
  const foundation=foundationById("mixed");
  const sources=[
    ...foundation.evidence.map(r=>{const d=documentFor(foundation,r);return {button:"Inspect M04 source "+r.id,document:d.name,chunk:d.chunkId,page:d.page,excerpt:d.excerpt,observation:r.observation,interpretation:r.interpretation};}),
    ...[["M05",priorityScenario("global").rows],["M06",consolidatedById("mixed").rows]].flatMap(([set,rows])=>
      (rows as ReturnType<typeof priorityScenario>["rows"]).map(r=>({button:"Inspect "+set+" source "+r.id,...r.source,observation:r.fact,interpretation:r.consequence}))),
  ];
  for(const s of sources){
    const trigger=page.getByRole("button",{name:s.button,exact:true});
    await trigger.focus();await page.keyboard.press("Enter");
    const dialog=page.getByRole("dialog");
    for(const value of [s.document,s.chunk,s.excerpt])await expect(dialog.getByText(value,{exact:true})).toBeVisible();
    for(const [label,value] of [["Page",String(s.page)],["Source observation · synthetic",s.observation],["Interpretation · synthetic",s.interpretation]]){
      await expect(dialog.locator("dl > div").filter({has:page.locator("dt").filter({hasText:new RegExp("^"+label+"$")})}).getByRole("definition")).toHaveText(value||"Not supplied");
    }
    await page.keyboard.press("Escape");await expect(dialog).not.toBeVisible();await expect(trigger).toBeFocused();
  }
});

test("M07 review is responsive, accessible and bounded, including expanded and empty states",async({page},info)=>{
  test.setTimeout(90000);
  const errors:string[]=[],external:string[]=[];
  page.on("pageerror",e=>errors.push(e.message));
  page.on("request",r=>{if(!["localhost","127.0.0.1"].includes(new URL(r.url()).hostname))external.push(r.url());});
  await page.goto("/v1-1/final-review");
  await expect(page.getByRole("heading",{level:1,name:"Final Review / Reports",exact:true})).toBeVisible();
  await expect(page.getByText(RECONSTRUCTION,{exact:true})).toBeVisible();
  await expect(page.getByText(V11_DISCLAIMER,{exact:true})).toBeVisible();
  await expect(page.getByText(/Their exact generating implementation was not recovered/)).toBeVisible();
  await expect(page.getByText(/Full private-batch reproducibility remains unestablished/)).toBeVisible();
  const check=async()=>{
    expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
    expect((await new AxeBuilder({page}).withTags(["wcag2a","wcag2aa","wcag21aa"]).analyze()).violations).toEqual([]);
  };
  await check();
  await page.screenshot({path:info.outputPath("final-review-"+info.project.name+".png"),fullPage:true});
  await page.getByLabel("Independent M05 scenario").selectOption("ties");
  for(const summary of await page.locator("summary").all())await summary.click();
  await check();
  const trigger=page.getByRole("button",{name:"Inspect M06 source E06-OT",exact:true});
  await trigger.focus();await page.keyboard.press("Enter");await check();
  await page.screenshot({path:info.outputPath("final-review-source-"+info.project.name+".png")});
  await page.keyboard.press("Escape");await expect(trigger).toBeFocused();
  for(const set of ["M04","M05","M06"])await page.getByLabel("Independent "+set+" scenario").selectOption("empty");
  await check();
  await expect(page.getByRole("button",{name:/Inspect .* source/})).toHaveCount(0);
  expect(errors).toEqual([]);expect(external).toEqual([]);
});

test("M07 complete review sequence and frozen V1 entry remain navigable",async({page})=>{
  const sequence=["/v1-1","/v1-1/run-review","/v1-1/prioritized-evidence","/v1-1/capacity-themes","/v1-1/denials-bottlenecks"];
  await page.goto("/v1-1/final-review");
  await expect(page.getByRole("navigation",{name:"V1.1 surfaces"}).getByRole("link")).toHaveCount(6);
  for(const route of sequence){
    await page.getByRole("navigation",{name:"V1.1 surfaces"}).locator(`a[href="${route}"]`).click();
    await expect(page).toHaveURL(route);
    const next=page.getByRole("link",{name:"Final Review / Reports",exact:true});
    await next.focus();await page.keyboard.press("Enter");
    await expect(page).toHaveURL("/v1-1/final-review");
  }
  await page.getByRole("navigation",{name:"Portfolio version"}).getByRole("link",{name:"V1 · Frozen demo",exact:true}).click();
  await expect(page.getByRole("heading",{name:"From scattered records to a clearer picture."})).toBeVisible();
});
