import { reference } from "../prioritized/types";
import type { Evidence } from "./types";
export const CATEGORIES=[
 {id:"functional",title:"Disability functional evidence formatting gap",domains:["ADL","IADL","mobility","endurance","cognition","disability process"],needed:"Concrete functional examples, duration, recovery and source citations."},
 {id:"coordination",title:"Care coordination / administrative capacity bottleneck",domains:["care coordination","IADL"],needed:"Missing records, follow-up requirements and administrative burden."},
 {id:"therapy",title:"Therapy/provider functional limitation and treatment-response tracking gap",domains:["PT/rehabilitation","treatment response"],needed:"Observed tolerance, response and carryover between observations."},
 {id:"summary",title:"Provider-ready longitudinal summary gap",domains:["provider support","care coordination","disability process","treatment response"],needed:"A source-linked distinction between observations and interpretations."},
 {id:"daily",title:"ADL/IADL documentation gap",domains:["ADL","IADL"],needed:"Daily-function examples, frequency, duration, assistance and recovery."},
 {id:"insurance",title:"Insurance authorization/documentation barrier",domains:[],needed:"Payer rationale, actual criteria, source-linked provider/OT evidence and rights/deadline verification."},
 {id:"appeal",title:"Appeal/DDS evidence organization gap",domains:[],needed:"Claimant narrative separated from provider records, corroboration and discrepancies."},
 {id:"capacity",title:"Capacity window tracking gap",domains:["treatment response"],needed:"Repeated daily-function observations, retained gains and carryover; grouping alone supplies none."},
] as const;
export function capBottlenecks<T>(items:readonly T[]):T[]{return items.slice(0,8);}
export function matchingCategories(row:Evidence){
 return CATEGORIES.filter(c=>c.id==="insurance"?row.source.type==="insurance denial letter":c.id==="appeal"?row.source.type==="disability appeal":c.domains.some(d=>row.domains.includes(d)));
}
export function confidence(rows:readonly Evidence[]){
 const positive=rows.filter(r=>r.strength>0),use=positive.length?positive:rows;
 if(use.some(r=>r.confidence==="high")&&use.length>=2)return "high";
 if(use.some(r=>["high","medium"].includes(r.confidence)))return "medium";
 return rows.length?"low":"unknown";
}
export function detect(rows:readonly Evidence[]){
 const groups=CATEGORIES.map(category=>{
  const members=rows.filter(r=>matchingCategories(r).some(c=>c.id===category.id)).map((row,index)=>({row,index})).sort((a,b)=>b.row.strength-a.row.strength||a.index-b.index).map(x=>x.row);
  const types=[...new Set(members.map(r=>r.source.type))];
  const sources=[...new Set(members.map(reference))].slice(0,6);
  return {...category,rows:members,sources,types,confidence:confidence(members),summary:types.map(type=>({
   "health-system/provider record":"Provider-authored source context",
   "OT record":"OT functional-observation source context","PT record":"PT rehabilitation source context",
   "function report":"Claimant-reported function context","disability appeal":"Claimant appeal/process context — not provider evidence",
   "insurance denial letter":"Payer decision/rationale context — not a therapy assessment",unknown:"Unknown author — no source authority inferred",
  })[type]).join("; ")};
 }).filter(g=>g.rows.length);
 return {rawCount:rows.reduce((n,r)=>n+matchingCategories(r).length,0),groups:capBottlenecks(groups)};
}
export type Group=ReturnType<typeof detect>["groups"][number];

