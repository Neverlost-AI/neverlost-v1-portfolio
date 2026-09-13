import { reference, type Candidate, type Bottleneck } from "./types";
export const LIMITS = { global:25, document:12, content:5 } as const;
export const DOMAIN_WEIGHTS: Readonly<Record<string,number>> = {ADL:16,IADL:14,mobility:14,endurance:12,"treatment response":12,"care coordination":10,"insurance/authorization":14,"disability process":12,pain:8,"joint stability":8,cognition:8};
export const SYSTEM_WEIGHTS: Readonly<Record<string,number>> = {"provider summary":10,disability:10,authorization:10,insurance:10,"care coordination":8,"capacity-window":8,"functional tolerance":8,documentation:6};
const matches=(text:string,terms:readonly string[])=>terms.filter(t=>text.includes(t));
export interface Component { name:string; points:number; reasons:string[] }
export function score(row:Candidate) {
  const components:Component[]=[];
  const add=(name:string,points:number,reasons:string[])=>components.push({name,points,reasons});
  const type=row.source.type, authority=row.source.authority;
  const a=type==="health-system/provider record"||authority.includes("provider-authored medical record") ? 40
    : ["OT record","PT record"].includes(type)||authority.toLowerCase().includes("therapy") ? 36
    : type==="insurance denial letter"||authority.toLowerCase().includes("payer") ? 32
    : ["function report","disability appeal"].includes(type) ? 24 : 10;
  add("Source authority",a,[`First matching authority branch: ${a} points. Supplied type: ${type}; authority text: ${authority}.`]);
  let functional=0;
  const f:string[]=[];
  for(const [domain,weight] of Object.entries(DOMAIN_WEIGHTS)) if(row.domains.includes(domain)){functional+=weight;f.push(`Exact domain “${domain}”: +${weight}`);}
  const functionalText=[row.contentType,row.fact,row.consequence,row.relevance].join(" ").toLowerCase();
  for(const [terms,weight] of [
    [["functional limitation","self-care","medical necessity","authorization barrier","denial"],10],
    [["bathing","standing","walking","stairs","lifting","pacing","care coordination"],8],
  ] as const) {const hits=matches(functionalText,terms);if(hits.length){functional+=weight;f.push(`Keyword group +${weight} once: ${hits.join(", ")} (content type, fact, consequence, relevance).`);}}
  add("Functional impact",functional,f.length?f:["No supported domain or keyword group matched."]);
  const systemText=[row.relevance,row.why,row.opportunity,row.missing].join(" ").toLowerCase();
  let system=0;const s:string[]=[];
  for(const [term,weight] of Object.entries(SYSTEM_WEIGHTS)) if(systemText.includes(term)){system+=weight;s.push(`“${term}”: +${weight} once (relevance, why, opportunity, missing evidence).`);}
  add("System relevance",system,s.length?s:["No supported system substring matched."]);
  let actionable=0;const reasons:string[]=[];
  const act=(condition:boolean,points:number,basis:string)=>{if(condition){actionable+=points;reasons.push(`${points>=0?"+":""}${points}: ${basis}`);}};
  act(!!row.opportunity&&!row.opportunity.toLowerCase().includes("hold this row"),12,"nonempty opportunity without the literal hold-this-row marker");
  act(!!row.missing,6,"nonempty missing-evidence field");
  act(row.supports.disability,5,"supplied supports_disability flag");
  act(row.supports.treatment,4,"supplied supports_treatment flag");
  act(row.supports.referral,4,"supplied supports_referral flag");
  act(row.supports.authorization,5,"supplied supports_insurance_authorization flag");
  act(row.confidence==="high",4,"high confidence label");
  act(["low","unknown"].includes(row.confidence),-6,"low/unknown confidence label");
  add("Actionability",actionable,reasons.length?reasons:["No actionability condition matched."]);
  add("Existing strength contribution",Math.trunc(row.strength/8),[`trunc(${row.strength} / 8) = ${Math.trunc(row.strength/8)}. Supplied synthetic upstream score, not recalculated or calibrated.`]);
  return {components,total:components.reduce((n,c)=>n+c.points,0)};
}
export function bottleneckLink(row:Candidate,items:readonly Bottleneck[]) {
  const direct=items.find(item=>item.sources.includes(reference(row)));
  if(direct) return {item:direct,basis:"Exact source-reference match; first matching bottleneck."};
  const rowText=[row.relevance,row.opportunity,row.contentType].join(" ").toLowerCase();
  for(const item of items) {
    const text=[item.title,item.needed,item.next].join(" ").toLowerCase();
    for(const term of ["insurance","care coordination","capacity"]) if(rowText.includes(term)&&text.includes(term)) return {item,basis:`Heuristic shared “${term}” substring; first matching bottleneck, not an established causal link.`};
  }
  return null;
}
export function prioritize(rows:readonly Candidate[],bottlenecks:readonly Bottleneck[]=[]) {
  const ranked=rows.map((row,index)=>({row,inputIndex:index,...score(row)})).sort((a,b)=>b.total-a.total||a.inputIndex-b.inputIndex);
  const perDoc=new Map<string,number>(), perContent=new Map<string,number>();
  let count=0;
  return ranked.map((item,index)=>{
    const docCount=perDoc.get(item.row.source.document)||0, typeCount=perContent.get(item.row.contentType)||0;
    const denial=item.row.source.type==="insurance denial letter";
    let reason="Selected in score order within available caps.";
    let selected=false;
    if(count>=LIMITS.global) reason="Global cap: 25 selected rows already reached; this lower-ranked row was not visited by the recovered selector.";
    else if(docCount>=LIMITS.document) reason="Document cap: 12 selected rows already use this exact document name.";
    else if(typeCount>=LIMITS.content&&!denial) reason="Content-type cap: 5 or more selected rows already use this exact content type.";
    else {selected=true;count++;perDoc.set(item.row.source.document,docCount+1);perContent.set(item.row.contentType,typeCount+1);}
    const exceptionApplied=selected&&denial&&typeCount>=LIMITS.content;
    if(exceptionApplied) reason="Selected using denial-source exception to the content-type cap; document and global caps still apply.";
    return {...item,rank:index+1,selected,selectedRank:selected?count:null,reason,exceptionApplied,docCountBefore:docCount,typeCountBefore:typeCount,linked:bottleneckLink(item.row,bottlenecks)};
  });
}

