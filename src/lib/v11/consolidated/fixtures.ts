import { sampleRow } from "../prioritized/fixtures";
import type { Evidence, Scenario, Window } from "./types";
function invented(id:string,type:Evidence["source"]["type"],authority:string,fact:string,domains:string[],extra:Partial<Evidence>={}):Evidence {
  const base=sampleRow(id);
  return {...base,source:{document:"synthetic-m06-"+id.toLowerCase()+".md",page:1,chunk:"SYN06-"+id,excerpt:"Invented training source. "+fact+" No real person or organization is represented.",type,authority},fact,domains,consequence:"Candidate interpretation only; this training observation does not establish retained gains or clinical significance.",...extra};
}
const provider=invented("E06-PROVIDER","health-system/provider record","provider-authored medical record","A fictional provider assessment records a treatment plan, referral and functional limitation during a practice walking task.",["ADL","IADL","mobility","treatment response","care coordination","provider support"],{confidence:"high",strength:80,relevance:"provider summary and care coordination",missing:"Carryover and duration are not supplied."});
const ot=invented("E06-OT","OT record","occupational therapy functional evidence","A synthetic self-care exercise includes pacing, joint protection and a pause. The OT note mentions an insurance denial but is not a payer decision.",["ADL","IADL","treatment response"],{confidence:"high",strength:72,relevance:"functional tolerance",missing:"Repeated daily-function observations are absent."});
const pt=invented("E06-PT","PT record","physical therapy evidence","A fictional therapy note describes walking practice and treatment response.",["PT/rehabilitation","treatment response"],{strength:64});
const payer=invented("E06-PAYER","insurance denial letter","payer decision evidence","A fictional Sample Coverage letter states occupational therapy visits were denied for missing documentation. The letter mentions medical necessity criteria but supplies no actual criteria text or dated appeal deadline.",[],{payer:"Sample Coverage (fictional)",service:"Occupational therapy visits (synthetic)",denialContext:"Documentation-related sample denial; no verified determination.",relevance:"insurance authorization documentation",strength:56});
const appeal=invented("E06-APPEAL","disability appeal","claimant appeal/process evidence","A fictional claimant appeal narrative mentions a provider and therapy. Those mentions do not make it provider-authored evidence.",["disability process"],{strength:40,confidence:"low"});
const unknown=invented("E06-UNKNOWN","unknown","unknown source authority","A training fragment describes a pause with no identified author.",["treatment response"],{strength:0,confidence:"unknown"});
const weakPayer=invented("E06-WEAK-PAYER","insurance denial letter","payer decision evidence","A fictional payer-source fragment is incomplete. Its decision details are absent.",[],{strength:16,confidence:"low"});
function window(id:string,evidenceId:string,intervention:string,sourceEvidence:string,possible:string="",learning:string=""):Window{return{id,evidenceId,intervention,sourceEvidence,possible,learning};}
const windows=[
  window("W06-OT",ot.id,"Practice task","A synthetic self-care task includes pacing and joint protection.","One task segment was attempted.","Carryover not established."),
  window("W06-PROVIDER",provider.id,"Practice walking","A provider training note describes walking and a follow-up.","A task was attempted.","No repeated measurements."),
  window("W06-UNKNOWN",unknown.id,"Unspecified exercise","An unattributed training fragment describes a pause."),
  window("W06-ALL",pt.id,"Classifier coverage probe","Test-only prose within an invented window: bathing, household, walking, joint protection, treatment, records, authorization, pacing.","Keyword coverage is not a measured outcome."),
];
export const scenarios:readonly Scenario[]=[
  {id:"mixed",title:"Mixed sources and multi-theme windows",description:"Invented provider, OT, PT, payer, claimant and unknown sources. One window can join several themes. The broad keyword probe demonstrates only classifier coverage, not actual functional capacity.",rows:[provider,ot,pt,payer,appeal,unknown],windows},
  {id:"no-denial",title:"No payer-denial source",description:"OT prose mentions a denial and provider/claimant-style words, but no payer-denial source or claimant appeal is supplied. No insurance bottleneck or denial mapping should appear.",rows:[provider,ot,pt,unknown],windows:windows.slice(0,3)},
  {id:"weak",title:"Denial with missing support",description:"An incomplete payer-source fragment and unknown-author evidence. No provider or OT evidence supports a keyword mapping.",rows:[weakPayer,unknown],windows:[windows[2]]},
  {id:"appeal",title:"Claimant appeal distinction",description:"A claimant-authored appeal is kept separate from provider-authored evidence. Mentioning a provider does not change its source type.",rows:[appeal,provider],windows:[windows[1]]},
  {id:"unknown",title:"Unknown authority and fallback",description:"No classifier keyword matches this window. The recovered treatment-response fallback is shown explicitly, not as evidence of treatment response.",rows:[unknown],windows:[windows[2]]},
  {id:"empty",title:"Empty input",description:"No evidence or windows supplied. Nothing is inferred from absence.",rows:[],windows:[]},
];
export function scenarioById(id:string){const s=scenarios.find(s=>s.id===id);if(!s)throw new Error("Unknown M06 synthetic scenario");return s;}

