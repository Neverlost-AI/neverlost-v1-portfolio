import {test,expect} from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import {priorityScenarios,priorityScenario,sampleRow} from "../../src/lib/v11/prioritized/fixtures";
import {prioritize,score,DOMAIN_WEIGHTS,bottleneckLink} from "../../src/lib/v11/prioritized/ranking";
import {suggestedUses} from "../../src/lib/v11/prioritized/uses";
import {reference} from "../../src/lib/v11/prioritized/types";
import {RECONSTRUCTION,V11_DISCLAIMER} from "../../src/lib/v11/fixtures";

test("M05 exact ranking weights, keyword groups and strength truncation",()=>{
  const row=sampleRow("WEIGHTS",{domains:Object.keys(DOMAIN_WEIGHTS),fact:"self-care denial walking bathing",relevance:"provider summary disability authorization insurance care coordination capacity-window functional tolerance documentation",opportunity:"Inspect synthetic note",missing:"Not supplied",supports:{disability:true,treatment:true,referral:true,authorization:true},confidence:"high",strength:80});
  expect(score(row).components.map(c=>c.points)).toEqual([40,146,70,40,10]);
  expect(score(row).total).toBe(306);
  expect(score({...row,domains:[...row.domains,...row.domains],fact:row.fact+" walking walking denial"}).total).toBe(306);
  expect(score(sampleRow("LOW",{confidence:"unknown",strength:-9})).components.map(c=>c.points)).toEqual([40,0,0,-6,-1]);
  expect(score(sampleRow("HOLD",{opportunity:"Hold this row for inspection"})).components[3].points).toBe(0);
  expect(score(sampleRow("WHITESPACE",{opportunity:" ",missing:" "})).components[3].points).toBe(18);
});

test("M05 authority precedence and case-sensitive historical oddity",()=>{
  const row=sampleRow("AUTH");
  const authority=(type:typeof row.source.type,text:string)=>score({...row,source:{...row.source,type,authority:text}}).components[0].points;
  expect(authority("unknown","provider-authored medical record")).toBe(40);
  expect(authority("unknown","Provider-authored medical record")).toBe(10);
  expect(authority("insurance denial letter","therapy payer")).toBe(36);
  expect(authority("unknown","payer")).toBe(32);
  expect(authority("function report","claimant")).toBe(24);
});

test("M05 global, document and content caps",()=>{
  for(const [id,count] of [["global",25],["document",12],["content",5]] as const){
    const s=priorityScenario(id),out=prioritize(s.rows);
    expect(out.filter(r=>r.selected)).toHaveLength(count);
    expect(out.filter(r=>!r.selected)).not.toHaveLength(0);
    expect(out.filter(r=>!r.selected).every(r=>r.reason.toLowerCase().includes(id==="content"?"content-type cap":id+" cap"))).toBe(true);
  }
  const row=sampleRow("BOTH");
  const rows=Array.from({length:14},(_,i)=>({...row,id:String(i),contentType:i<12?"type-"+i:"type-0"}));
  expect(prioritize(rows)[12].reason).toContain("Document cap");
});

test("M05 denial exception bypasses only type cap and increments its counter",()=>{
  const out=prioritize(priorityScenario("denial").rows);
  expect(out.filter(r=>r.selected)).toHaveLength(12);
  expect(out.filter(r=>r.exceptionApplied)).toHaveLength(7);
  expect(out[12].reason).toContain("Document cap");
  expect(out.find(r=>r.row.id==="DENIAL-UNKNOWN")?.reason).toContain("Content-type cap");
  expect(out.find(r=>r.row.id==="DENIAL-UNKNOWN")?.typeCountBefore).toBe(12);
  const denial=priorityScenario("denial").rows[0];
  const many=Array.from({length:30},(_,i)=>({...denial,id:String(i),source:{...denial.source,document:"synthetic-"+i+".md"}}));
  expect(prioritize(many).filter(r=>r.selected)).toHaveLength(25);
  const provider=sampleRow("PAYER-TEXT",{contentType:"denial context",source:{...denial.source,type:"unknown",authority:"payer"}});
  const normal=Array.from({length:7},(_,i)=>({...provider,id:String(i),source:{...provider.source,document:"synthetic-"+i+".md"}}));
  expect(prioritize(normal).filter(r=>r.selected)).toHaveLength(5);
});

test("M05 ties, unknown, empty and immutable complete provenance",()=>{
  const tied=prioritize(priorityScenario("ties").rows);
  expect(tied.map(r=>r.row.id)).toEqual(["NEAR","TIE-A","TIE-B"]);
  expect(tied.map(r=>r.total)).toEqual([49,48,48]);
  expect(prioritize(priorityScenario("empty").rows)).toEqual([]);
  const before=JSON.stringify(priorityScenarios);
  for(const s of priorityScenarios)for(const item of prioritize(s.rows,s.bottlenecks)){
    expect(item.row).toBe(s.rows[item.inputIndex]);
    expect(item.row.source.excerpt).toContain("Invented");
    expect(reference(item.row)).toContain(item.row.source.chunk);
  }
  expect(JSON.stringify(priorityScenarios)).toBe(before);
  expect(prioritize(priorityScenario("context").rows).find(r=>r.row.id==="UNKNOWN")?.selected).toBe(true);
});

test("M05 suggested uses and first exact/heuristic bottleneck links",()=>{
  const context=priorityScenario("context");
  expect(bottleneckLink(context.rows[0],context.bottlenecks)?.basis).toContain("Exact");
  const denial=priorityScenario("denial");
  expect(bottleneckLink(denial.rows[0],denial.bottlenecks)?.basis).toContain("Heuristic");
  expect(suggestedUses(context.rows[2],false).map(u=>u.label)).toEqual(["internal review"]);
  const base=sampleRow("OT"), ot={...base,source:{...base.source,type:"OT record" as const,authority:"occupational therapy"}};
  expect(suggestedUses(ot,false).map(u=>u.label)).not.toContain("insurance appeal");
  expect(suggestedUses(ot,true).map(u=>u.label)).toContain("insurance appeal");
  expect(bottleneckLink(base,[])).toBeNull();
});

test("M05 responsive accessible scenarios and membership filters",async({page},info)=>{
  test.setTimeout(60000);
  const errors:string[]=[],external:string[]=[];
  page.on("pageerror",e=>errors.push(e.message));
  page.on("request",r=>{if(!["127.0.0.1","localhost"].includes(new URL(r.url()).hostname))external.push(r.url());});
  await page.goto("/v1-1/prioritized-evidence");
  await expect(page.getByRole("heading",{name:"Prioritized Evidence",level:1,exact:true})).toBeVisible();
  await expect(page.getByText(RECONSTRUCTION,{exact:true})).toBeVisible();
  await expect(page.getByText(V11_DISCLAIMER,{exact:true})).toBeVisible();
  await expect(page.getByRole("navigation",{name:"V1.1 surfaces"}).getByRole("link")).toHaveCount(3);
  for(const s of priorityScenarios){
    await page.getByRole("combobox",{name:"Synthetic prioritization scenario"}).selectOption(s.id);
    const selected=prioritize(s.rows).filter(r=>r.selected).length;
    await expect(page.getByRole("status")).toHaveText(`${s.rows.length} shown · ${selected} selected from ${s.rows.length} candidates`);
    await page.getByRole("combobox",{name:"Show candidates"}).selectOption("selected");
    await expect(page.getByRole("status")).toHaveText(`${selected} shown · ${selected} selected from ${s.rows.length} candidates`);
    await page.getByRole("combobox",{name:"Show candidates"}).selectOption("excluded");
    await expect(page.getByRole("status")).toHaveText(`${s.rows.length-selected} shown · ${selected} selected from ${s.rows.length} candidates`);
    await page.getByRole("combobox",{name:"Show candidates"}).selectOption("all");
    expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
    expect((await new AxeBuilder({page}).withTags(["wcag2a","wcag2aa","wcag21aa"]).analyze()).violations).toEqual([]);
  }
  await expect(page.getByRole("heading",{name:"No candidate evidence supplied"})).toBeVisible();
  await page.reload();
  await expect(page.getByRole("combobox",{name:"Synthetic prioritization scenario"})).toHaveValue("global");
  await page.screenshot({path:info.outputPath("priority-"+info.project.name+".png"),fullPage:true});
  expect(errors).toEqual([]);expect(external).toEqual([]);
});

test("M05 every selected row retains keyboard-inspectable source provenance",async({page})=>{
  test.setTimeout(60000);
  await page.goto("/v1-1/prioritized-evidence");
  for(const item of prioritize(priorityScenario("global").rows).filter(r=>r.selected)){
    const article=page.getByRole("article",{name:item.row.id,exact:true});
    await article.getByText("Inspect ranking and source for "+item.row.id,{exact:true}).click();
    const trigger=article.getByRole("button",{name:"Inspect source "+item.row.id,exact:true});
    await trigger.focus();await page.keyboard.press("Enter");
    const dialog=page.getByRole("dialog");
    for(const value of [item.row.id,item.row.source.document,item.row.source.chunk,item.row.source.excerpt])await expect(dialog.getByText(value,{exact:true})).toBeVisible();
    await expect(dialog.locator("dd").filter({hasText:new RegExp("^"+item.row.source.page+"$")})).toBeVisible();
    await page.keyboard.press("Escape");await expect(dialog).not.toBeVisible();await expect(trigger).toBeFocused();
    await article.getByText("Inspect ranking and source for "+item.row.id,{exact:true}).click();
  }
});

test("M05 expanded ranking, source modal and related bottleneck are accessible",async({page},info)=>{
  await page.goto("/v1-1/prioritized-evidence");
  await page.getByRole("combobox",{name:"Synthetic prioritization scenario"}).selectOption("context");
  const article=page.getByRole("article",{name:"CONTEXT",exact:true});
  await article.getByText("Inspect ranking and source for CONTEXT",{exact:true}).click();
  await expect(article.getByRole("heading",{name:"Score components"})).toBeVisible();
  for(const component of score(priorityScenario("context").rows[0]).components)await expect(article.getByRole("region",{name:component.name,exact:true})).toBeVisible();
  await article.getByRole("link",{name:"Synthetic follow-up documentation gap"}).click();
  await expect(page).toHaveURL(/#B05-FOLLOWUP$/);
  expect((await new AxeBuilder({page}).withTags(["wcag2a","wcag2aa","wcag21aa"]).analyze()).violations).toEqual([]);
  await page.screenshot({path:info.outputPath("expanded-"+info.project.name+".png"),fullPage:true});
  await article.getByRole("button",{name:"Inspect source CONTEXT",exact:true}).click();
  expect((await new AxeBuilder({page}).withTags(["wcag2a","wcag2aa","wcag21aa"]).analyze()).violations).toEqual([]);
  await page.getByRole("button",{name:"Close source dialog"}).click();
  await page.getByRole("navigation",{name:"V1.1 surfaces"}).getByRole("link",{name:"Run Review",exact:true}).click();
  await expect(page.getByRole("heading",{name:"Run Review",level:1})).toBeVisible();
  await page.getByRole("link",{name:"Continue to M05 · Prioritized Evidence"}).click();
  await expect(page.getByRole("heading",{name:"Prioritized Evidence",level:1})).toBeVisible();
  await page.getByRole("navigation",{name:"Portfolio version"}).getByRole("link",{name:"V1 · Frozen demo",exact:true}).click();
  await expect(page.getByRole("heading",{name:"From scattered records to a clearer picture."})).toBeVisible();
});
