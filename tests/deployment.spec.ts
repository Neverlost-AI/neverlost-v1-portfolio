import {test,expect} from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import {DISCLAIMER} from "../src/lib/demo-data";

const routes=["/v1","/timeline","/evidence-matrix","/hidden-states","/bottlenecks","/capacity-windows","/reports","/v1-1","/v1-1/run-review","/v1-1/prioritized-evidence","/v1-1/capacity-themes","/v1-1/denials-bottlenecks","/v1-1/final-review"];

test("deployment: all public routes support direct entry, refresh and local assets",async({page},info)=>{
  test.setTimeout(180000);
  const errors:string[]=[],failed:string[]=[],external:string[]=[];
  page.on("pageerror",e=>errors.push(e.message));
  page.on("console",m=>{if(m.type()==="error")errors.push(m.text());});
  page.on("response",r=>{if(r.status()>=400)failed.push(r.status()+" "+new URL(r.url()).pathname);});
  page.on("request",r=>{if(!["127.0.0.1","localhost"].includes(new URL(r.url()).hostname))external.push(r.url());});
  for(const route of routes){
    expect((await page.goto(route))?.status()).toBe(200);
    await expect(page.getByRole("heading",{level:1})).toBeVisible();
    await expect(page.getByText(DISCLAIMER,{exact:true})).toBeVisible();
    expect((await page.reload())?.status()).toBe(200);
    await expect(page.getByRole("heading",{level:1})).toBeVisible();
    await page.evaluate(()=>document.fonts.ready);
    expect(await page.evaluate(()=>document.fonts.check('14px "Inter Variable"')&&document.fonts.check('28px "Manrope Variable"'))).toBe(true);
    expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
    expect((await new AxeBuilder({page}).withTags(["wcag2a","wcag2aa","wcag21aa"]).analyze()).violations).toEqual([]);
    await page.screenshot({path:info.outputPath((route==="/"?"home":route.slice(1).replaceAll("/","-"))+".png")});
  }
  const icon=await page.request.get("/icon.svg");
  expect(icon.status()).toBe(200);expect(icon.headers()["content-type"]).toContain("image/svg+xml");
  expect(errors).toEqual([]);expect(failed).toEqual([]);expect(external).toEqual([]);
});

test("deployment: source, environment and local artifacts are not public routes",async({request})=>{
  for(const route of ["/.env","/.env.local","/.git/config","/package.json","/package-lock.json","/docs/v11-final-verification.md","/tests/deployment.spec.ts","/test-results/.last-run.json","/src/lib/demo-data.ts"]){
    expect((await request.get(route)).status(),route).toBe(404);
  }
});
