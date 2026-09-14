import {expect,test} from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import {scenarios,scenarioById} from "../../src/lib/v11/consolidated/fixtures";
import {evidenceFor} from "../../src/lib/v11/consolidated/types";
import {THEME_RULES,memberships,consolidate,capThemes,related} from "../../src/lib/v11/consolidated/themes";
import {CATEGORIES,detect,matchingCategories,capBottlenecks,confidence} from "../../src/lib/v11/consolidated/bottlenecks";
import {mapDenial,phrase,supporting} from "../../src/lib/v11/consolidated/denials";
import {RECONSTRUCTION,V11_DISCLAIMER} from "../../src/lib/v11/fixtures";

test("M06 eight recovered families, multi-membership, fallback and authority mix",()=>{
 const s=scenarioById("mixed"),groups=detect(s.rows).groups,themes=consolidate(s,groups);
 expect(THEME_RULES).toHaveLength(8);
 expect(themes).toHaveLength(8);
 expect(memberships(s.windows[3])).toHaveLength(8);
 expect(themes.find(t=>t.name==="treatment response/carryover capacity")?.authorities).toEqual(expect.arrayContaining(["occupational therapy functional evidence","unknown source authority"]));
 expect(memberships(scenarioById("unknown").windows[0])[0].fallback).toBe(true);
 const duplicate={...s,windows:[s.windows[0],s.windows[0]]};
 expect(consolidate(duplicate,groups).every(t=>t.members.length===2)).toBe(true);
 const iadl={...s.windows[0],intervention:"",sourceEvidence:"IADL",possible:"",learning:""};
 expect(memberships(iadl).map(m=>m.name)).toEqual(["ADL/self-care capacity","IADL/home-management capacity"]);
});

test("M06 artificial test-only groups preserve unreachable ten-theme guard",()=>{
 // These labels are not themes exposed by the recovered classifier or production UI.
 const artificial=Array.from({length:12},(_,i)=>({name:"ARTIFICIAL TEST GROUP "+i}));
 expect(capThemes(artificial)).toEqual(artificial.slice(0,10));
 expect(capThemes(artificial.slice(0,10))).toHaveLength(10);
 expect(capThemes([])).toEqual([]);
 for(const s of scenarios)expect(consolidate(s,detect(s.rows).groups).length).toBeLessThanOrEqual(8);
});

test("M06 eight bottlenecks, ordered raw grouping, key-source and confidence rules",()=>{
 const s=scenarioById("mixed"),result=detect(s.rows);
 expect(CATEGORIES).toHaveLength(8);
 expect(result.rawCount).toBeGreaterThan(8);
 expect(result.groups.map(g=>g.id)).toEqual(CATEGORIES.map(c=>c.id));
 expect(capBottlenecks(Array.from({length:10},(_,i)=>i))).toEqual([0,1,2,3,4,5,6,7]);
 const row=s.rows[0],many=Array.from({length:9},(_,i)=>({...row,id:"SYN-TEST-"+i,source:{...row.source,document:"synthetic-"+i+".md"},strength:i}));
 const group=detect(many).groups[0];
 expect(group.sources).toHaveLength(6);
 expect(group.rows[0].strength).toBe(8);
 expect(confidence([{...row,strength:0,confidence:"high"},{...row,strength:1,confidence:"low"}])).toBe("low");
 expect(confidence([{...row,strength:1,confidence:"high"}])).toBe("medium");
 expect(confidence([{...row,strength:1,confidence:"high"},{...row,strength:1,confidence:"low"}])).toBe("high");
});

test("M06 no-denial and strict claimant source gates cannot be triggered by mentions",()=>{
 const s=scenarioById("no-denial");
 expect(s.rows.some(r=>r.fact.toLowerCase().includes("denial"))).toBe(true);
 expect(mapDenial(s.rows)).toBeNull();
 expect(detect(s.rows).groups.some(g=>["insurance","appeal"].includes(g.id))).toBe(false);
 const row={...s.rows[0],fact:"appeal DDS denial insurance authorization provider",domains:["insurance/authorization"]};
 expect(matchingCategories(row)).toEqual([]);
 const appeal=scenarioById("appeal");
 expect(detect(appeal.rows).groups.find(g=>g.id==="appeal")?.rows.map(r=>r.source.type)).toEqual(["disability appeal"]);
 expect(mapDenial(appeal.rows)).toBeNull();
});

test("M06 denial mapping exact source classes, caps and weak support",()=>{
 const s=scenarioById("mixed"),mapping=mapDenial(s.rows)!;
 expect(mapping.ot.map(r=>r.row.id)).toEqual(["E06-OT"]);
 expect(mapping.provider.map(r=>r.row.id)).toEqual(["E06-PROVIDER"]);
 expect(mapping.payer).toBe("Sample Coverage (fictional)");
 expect(mapping.service).toContain("Occupational therapy");
 const weak=mapDenial(scenarioById("weak").rows)!;
 expect(weak.provider).toEqual([]);expect(weak.ot).toEqual([]);
 expect(weak.gaps.length).toBeGreaterThan(0);
 const ot=s.rows.find(r=>r.id==="E06-OT")!;
 expect(supporting(Array.from({length:12},(_,i)=>({...ot,id:"TEST-"+i,strength:i*8})),"OT record")).toHaveLength(10);
 expect(supporting([{...ot,source:{...ot.source,type:"PT record"}}],"OT record")).toEqual([]);
 expect(phrase("No deadline is supplied.",["appeal","deadline"])?.term).toBe("deadline");
 expect(phrase("denial appears first; denied appears later",["denied","denial"])?.term).toBe("denied");
 expect(phrase("Unspecified.",["denied"])).toBeNull();
});

test("M06 theme ordering, broad links, empty and immutable provenance",()=>{
 const before=JSON.stringify(scenarios);
 for(const s of scenarios){
  const groups=detect(s.rows).groups;
  for(const theme of consolidate(s,groups)){
   for(const m of theme.members)expect(evidenceFor(s,m.window.evidenceId).source.chunk).toMatch(/^SYN06-/);
   expect(theme.related.length).toBeLessThanOrEqual(3);
  }
  mapDenial(s.rows);
 }
 expect(JSON.stringify(scenarios)).toBe(before);
 const mixed=scenarioById("mixed");
 const tied={...mixed,windows:[{...mixed.windows[0],sourceEvidence:"bathing household",intervention:"",possible:"",learning:""}]};
 expect(consolidate(tied,[]).map(t=>t.name)).toEqual(["ADL/self-care capacity","IADL/home-management capacity"]);
 expect(related("insurance/authorization capacity",detect(mixed.rows).groups).map(g=>g.id)).toEqual(["functional","coordination","therapy"]);
 const empty=scenarioById("empty");
 expect(consolidate(empty,[])).toEqual([]);expect(detect(empty.rows).groups).toEqual([]);expect(mapDenial(empty.rows)).toBeNull();
 expect(()=>evidenceFor(empty,"missing")).toThrow("Unresolved synthetic M06 evidence reference");
});

for(const [route,title]of [["capacity-themes","Capacity Themes"],["denials-bottlenecks","Denials & Bottlenecks"]]){
 test(`M06 ${title}: responsive scenarios, accessibility and source inspection`,async({page},info)=>{
  test.setTimeout(90000);
  const errors:string[]=[],external:string[]=[];
  page.on("pageerror",e=>errors.push(e.message));
  page.on("request",r=>{if(!["localhost","127.0.0.1"].includes(new URL(r.url()).hostname))external.push(r.url());});
  await page.goto("/v1-1/"+route);
  await expect(page.getByRole("heading",{name:title,level:1,exact:true})).toBeVisible();
  await expect(page.getByText(RECONSTRUCTION,{exact:true})).toBeVisible();
  await expect(page.getByText(V11_DISCLAIMER,{exact:true})).toBeVisible();
  await expect(page.getByRole("navigation",{name:"V1.1 surfaces"}).getByRole("link")).toHaveCount(5);
  for(const s of scenarios){
   await page.getByRole("combobox",{name:"Synthetic M06 scenario"}).selectOption(s.id);
   expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
   expect((await new AxeBuilder({page}).withTags(["wcag2a","wcag2aa","wcag21aa"]).analyze()).violations).toEqual([]);
   if(!mapDenial(s.rows)){
    await expect(page.getByRole("status")).toContainText("No payer-denial source supplied");
    await expect(page.getByRole("article",{name:"Insurance authorization/documentation barrier",exact:true})).toHaveCount(0);
    if(route==="denials-bottlenecks")await expect(page.getByText("No denial mapping created. Absence is not an eligibility or coverage conclusion.",{exact:true})).toBeVisible();
   }
  }
  await page.getByRole("combobox",{name:"Synthetic M06 scenario"}).selectOption("mixed");
  for(const row of scenarioById("mixed").rows){
   const trigger=page.getByRole("button",{name:"Inspect source "+row.id,exact:true});
   await trigger.focus();await page.keyboard.press("Enter");
   const dialog=page.getByRole("dialog");
   for(const value of [row.id,row.source.document,row.source.chunk,row.source.excerpt])await expect(dialog.getByText(value,{exact:true})).toBeVisible();
   await expect(dialog.locator("dd").filter({hasText:new RegExp("^"+row.source.page+"$")})).toBeVisible();
   expect((await new AxeBuilder({page}).withTags(["wcag2a","wcag2aa","wcag21aa"]).analyze()).violations).toEqual([]);
   await page.keyboard.press("Escape");await expect(dialog).not.toBeVisible();await expect(trigger).toBeFocused();
  }
  await page.screenshot({path:info.outputPath(route+"-"+info.project.name+".png"),fullPage:true});
  await page.getByRole("combobox",{name:"Synthetic M06 scenario"}).selectOption("empty");await page.reload();
  await expect(page.getByRole("combobox",{name:"Synthetic M06 scenario"})).toHaveValue("mixed");
  await page.getByRole("navigation",{name:"Portfolio version"}).getByRole("link",{name:"V1 · Frozen demo",exact:true}).click();
  await expect(page.getByRole("heading",{name:"From scattered records to a clearer picture."})).toBeVisible();
  expect(errors).toEqual([]);expect(external).toEqual([]);
 });
}

test("M06 theme-to-window-to-source links and expanded accessibility",async({page})=>{
 await page.goto("/v1-1/capacity-themes");
 const theme=page.getByRole("article",{name:"ADL/self-care capacity",exact:true});
 await theme.getByText("Contributing windows for ADL/self-care capacity",{exact:true}).click();
 await theme.getByRole("link",{name:"W06-OT",exact:true}).click();
 await expect(page).toHaveURL(/#window-W06-OT$/);
 const window=page.getByRole("article",{name:"W06-OT",exact:true});
 await window.getByRole("link").click();
 await expect(page).toHaveURL(/#source-E06-OT$/);
 expect((await new AxeBuilder({page}).withTags(["wcag2a","wcag2aa","wcag21aa"]).analyze()).violations).toEqual([]);
 await page.getByRole("navigation",{name:"V1.1 surfaces"}).getByRole("link",{name:"Denials & Bottlenecks",exact:true}).click();
 const barrier=page.getByRole("article",{name:"Insurance authorization/documentation barrier",exact:true});
 await barrier.getByText("Triggering evidence for Insurance authorization/documentation barrier",{exact:true}).click();
 await expect(barrier).toContainText("E06-PAYER");
 await expect(page.getByRole("region",{name:"Candidate OT support"})).toContainText("synthetic-m06-e06-ot.md");
 expect((await new AxeBuilder({page}).withTags(["wcag2a","wcag2aa","wcag21aa"]).analyze()).violations).toEqual([]);
});

