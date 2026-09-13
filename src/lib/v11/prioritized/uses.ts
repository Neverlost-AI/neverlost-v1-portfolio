import type { Candidate } from "./types";
export function suggestedUses(row:Candidate,denialPresent:boolean) {
  const result:{label:string;basis:string}[]=[];
  const add=(label:string,basis:string)=>{if(!result.some(x=>x.label===label))result.push({label,basis});};
  const type=row.source.type, a=row.source.authority.toLowerCase();
  const text=[a,type,row.contentType,row.fact,row.consequence,row.relevance,row.why,row.opportunity,row.missing].join(" ").toLowerCase();
  const has=(terms:readonly string[])=>terms.some(t=>text.includes(t));
  const functional=row.supports.disability||row.domains.includes("disability process")||has(["adl","iadl","self-care","self care","mobility","functional limitation","walking","standing","stairs","bathing","hygiene","carryover","pacing","energy conservation","joint protection"]);
  const treatment=has(["treatment","medical necessity","medically necessary","authorization","therapy","medication","care plan"]);
  const follow=row.domains.includes("care coordination")||has(["care coordination","follow-up","follow through","referral","records","forms","support need"]);
  const denial=has(["denial","denied","criteria","missing documentation","coverage","authorization"]);
  if(type==="health-system/provider record"||a.includes("provider-authored medical record")){
    add("provider summary","Provider source/authority branch.");
    if(functional)add("disability evidence","Provider branch with functional markers.");
    if(treatment||row.supports.authorization)add("insurance appeal","Provider branch with treatment/authorization markers.");
  }
  if(["OT record","PT record"].includes(type)||a.includes("occupational therapy")||a.includes("physical therapy")){
    add("provider summary","Therapy source/authority branch.");
    if(functional)add("disability evidence","Therapy branch with functional markers.");
    if(denialPresent||denial)add("insurance appeal","Therapy branch: denial source exists anywhere in the candidate set, or this row has denial/criteria markers.");
    if(follow)add("care coordination","Therapy branch with follow-through markers.");
  }
  if(type==="insurance denial letter"||a.includes("payer")||a.includes("insurance utilization review")){
    add("insurance appeal","Payer source/authority branch.");
    if(denial)add("care coordination","Payer branch with denial/criteria markers.");
    if(denial||has(["evidence gap","missing","documentation"]))add("internal review","Payer branch with denial/gap markers.");
  }
  if(["function report","disability appeal"].includes(type)||a.includes("claimant")){
    add("disability evidence","Claimant source/authority branch.");
    if(follow)add("care coordination","Claimant branch with follow-through markers.");
    if(has(["corroborat","claimant","appeal","patient reported","self-report"]))add("internal review","Claimant/corroboration markers.");
  }
  for(const [label,terms] of [
    ["provider summary",["provider","clinician","doctor","medical record"]],
    ["disability evidence",["disability","functional limitation","adl","iadl","self-care","self care","mobility"]],
    ["insurance appeal",["insurance","appeal","authorization","denial","coverage","medical necessity"]],
    ["care coordination",["care coordination","referral","follow-up","forms","records","appointment"]],
    ["internal review",["internal review","evidence gap","documentation gap","missing documentation"]],
  ] as const) if(has(terms))add(label,"Generic keyword fallback across source and analytical fields.");
  if(!result.length)add("internal review","Recovered default when no use rule matches.");
  return result;
}

