import { score } from "../prioritized/ranking";
import type { Evidence } from "./types";
const OT=["adl","iadl","self-care","self care","adaptive","energy conservation","pacing","functional rehabilitation","treatment response","joint protection"];
const PROVIDER=["diagnosis","problem list","treatment plan","referral","medication","functional limitation","medical necessity","assessment"];
export const RATIONALE_RULES={
 "Denial reason":["not medically necessary","denied","denial","not approved"],
 "Medical-necessity language":["medical necessity","medically necessary","criteria"],
 "Missing documentation":["missing","documentation","records","information"],
 "Criteria mentioned":["criteria","guideline","benefit","coverage"],
 "Appeal rights / deadline":["appeal","appeal rights","deadline","hearing"],
} as const;
export function phrase(text:string,terms:readonly string[]){
 const normalized=text.replace(/\s+/g," ").trim();
 for(const term of terms){const index=normalized.toLowerCase().indexOf(term);if(index>=0){let excerpt=normalized.slice(Math.max(0,index-120),index+260);if(excerpt.length>360){excerpt=excerpt.slice(0,360);const space=excerpt.lastIndexOf(" ");if(space>=0)excerpt=excerpt.slice(0,space);excerpt+=".";}return {term,excerpt};}}
 return null;
}
export function supporting(rows:readonly Evidence[],type:"OT record"|"health-system/provider record"){
 const terms=type==="OT record"?OT:PROVIDER;
 return rows.filter(r=>r.source.type===type).map((row,index)=>({row,index,hits:terms.filter(t=>[row.contentType,row.fact,row.consequence,row.relevance].join(" ").toLowerCase().includes(t)),score:score(row).total})).filter(r=>r.hits.length).sort((a,b)=>b.score-a.score||a.index-b.index).slice(0,10);
}
export function mapDenial(rows:readonly Evidence[]){
 const sources=rows.filter(r=>r.source.type==="insurance denial letter");
 if(!sources.length)return null; // Explicit M06 correction: no truthy mapping without a denial source.
 const text=sources.map(r=>r.fact).join(" ");
 const rationale=Object.entries(RATIONALE_RULES).map(([label,terms])=>({label,result:phrase(text,terms)}));
 const payer=sources.find(r=>r.payer)?.payer??null,service=sources.find(r=>r.service)?.service??null,context=sources.find(r=>r.denialContext)?.denialContext??null;
 const servicePhrase=service?null:phrase(text,["service","therapy","occupational therapy","authorization"]);
 return {sources,payer,service,servicePhrase,context,rationale,ot:supporting(rows,"OT record"),provider:supporting(rows,"health-system/provider record"),gaps:rationale.filter(r=>!r.result).map(r=>r.label+" not detected; human inspection required.")};
}
