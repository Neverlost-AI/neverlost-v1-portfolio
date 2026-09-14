import { evidenceFor, type Scenario, type Window } from "./types";
import type { Group } from "./bottlenecks";
export const THEME_RULES=[
 ["ADL/self-care capacity",["bathing","self-care","self care","adl","dressing","hygiene"]],
 ["IADL/home-management capacity",["home","vacuuming","household","iadl","daily activities","functional activity"]],
 ["mobility/stairs/walking capacity",["walking","stairs","standing","mobility","gait"]],
 ["upper-extremity/joint-protection capacity",["upper extremity","joint protection","joint stabilization","hypermobility","supportive garments","supportive devices"]],
 ["treatment response/carryover capacity",["improvement","treatment","medication","respond","carryover","symptoms","pain"]],
 ["care coordination/administrative capacity",["coordinate","records","follow-up","appointment","referral","provider"]],
 ["insurance/authorization capacity",["authorization","insurance","denial","coverage"]],
 ["pacing/energy conservation capacity",["pacing","energy conservation","fatigue","breathwork","somatic","regulating"]],
] as const;
export function memberships(w:Window){
 const text=[w.intervention,w.sourceEvidence,w.possible,w.learning].join(" ").toLowerCase();
 const matches=THEME_RULES.flatMap(([name,terms])=>{const hits=terms.filter(t=>text.includes(t));return hits.length?[{name,basis:"Matched substrings: "+hits.join(", "),fallback:false}]:[];});
 return matches.length?matches:[{name:THEME_RULES[4][0],basis:"No keyword matched. Recovered treatment-response fallback; not observed treatment response.",fallback:true}];
}
export function capThemes<T>(items:readonly T[]):T[]{return items.slice(0,10);}
// Audited projection of the substrings in the recovered bottleneck/needed/action
// templates. New, bounded UI prose must not silently change these broad links.
const LINK_TERMS:Record<Group["id"],string>={functional:"functional adl",coordination:"care coordination capacity",therapy:"functional treatment response",summary:"functional treatment response",daily:"functional adl",insurance:"insurance functional",appeal:"",capacity:"capacity treatment response functional"};
export function related(name:string,groups:readonly Group[]){
 const t=name.toLowerCase();
 return groups.filter(g=>{
  const text=LINK_TERMS[g.id];
  return (t.includes("insurance")&&text.includes("insurance"))||(t.includes("care coordination")&&text.includes("care coordination"))||(t.includes("capacity")&&["capacity","treatment response","functional"].some(x=>text.includes(x)))||(t.includes("adl")&&text.includes("adl"));
 }).slice(0,3);
}
export function consolidate(s:Scenario,groups:readonly Group[]){
 const buckets=new Map<string,{window:Window;basis:string;fallback:boolean}[]>();
 for(const w of s.windows){evidenceFor(s,w.evidenceId);for(const m of memberships(w)){const list=buckets.get(m.name)||[];list.push({window:w,basis:m.basis,fallback:m.fallback});buckets.set(m.name,list);}}
 return capThemes([...buckets.entries()].map(([name,members],index)=>{
  const documents=[...new Set(members.map(m=>evidenceFor(s,m.window.evidenceId).source.document))].sort();
  const authorities=[...new Set(documents.map(doc=>s.rows.find(r=>r.source.document===doc)?.source.authority||"unknown source authority"))].sort();
  return {name,members,index,documents,authorities,related:related(name,groups)};
 }).sort((a,b)=>b.members.length-a.members.length||a.index-b.index));
}
