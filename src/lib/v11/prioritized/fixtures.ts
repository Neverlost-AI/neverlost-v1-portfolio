import { reference, type Candidate, type PriorityScenario } from "./types";

// Newly invented boundary fixtures. No recovered document or output is an input.
export function sampleRow(id: string, changes: Partial<Candidate> = {}): Candidate {
  return {
    id, source: { document: `synthetic-${id}.md`, page: 1, chunk: `SYN05-${id}`, excerpt: "Invented training note: a sample sorting exercise ended with a recorded pause. This is not a person's record.", type: "health-system/provider record", authority: "provider-authored medical record" },
    contentType: "task observation", domains: [], fact: "A sample exercise includes a recorded pause.",
    consequence: "Interpretation: the pause does not establish sustained ability or inability.", relevance: "", why: "",
    opportunity: "", missing: "", supports: { disability:false, treatment:false, referral:false, authorization:false },
    confidence: "medium", strength: 64, ...changes,
  };
}
const globalRows = Array.from({length:30},(_,i) => {
  const row=sampleRow(`GLOBAL-${String(i+1).padStart(2,"0")}`);
  return {...row, source:{...row.source,document:`synthetic-global-group-${Math.floor(i/5)+1}.md`},contentType:["task observation","activity context","follow-up note","response observation","source context","support context"][i%6],strength:100-i*2};
});
const documentRows=Array.from({length:15},(_,i)=>{
  const row=sampleRow(`DOC-${i+1}`);
  return {...row,source:{...row.source,document:"synthetic-single-document.md"},contentType:["task observation","activity context","follow-up note"][i%3]};
});
const typeRows=Array.from({length:8},(_,i)=>sampleRow(`TYPE-${i+1}`));
const denialRows=Array.from({length:14},(_,i)=>{
  const row=sampleRow(`DENIAL-${i+1}`);
  return {...row,source:{...row.source,document:"synthetic-payer-letter.md",type:"insurance denial letter" as const,authority:"payer decision evidence",excerpt:"Invented payer sample: the letter describes a documentation-related denial. No real payer or person is represented."},contentType:"denial context",fact:"A synthetic denial statement cites incomplete documentation.",relevance:"insurance documentation",strength:64};
});
const unknown=sampleRow("UNKNOWN",{source:{document:"synthetic-unattributed.md",page:2,chunk:"SYN05-UNKNOWN",excerpt:"Invented fragment: a pause is noted, but the author is not identified.",type:"unknown",authority:"Unknown"},confidence:"unknown",strength:0});
const contextual=sampleRow("CONTEXT",{
  source:{document:"synthetic-context-note.md",page:1,chunk:"SYN05-CONTEXT",excerpt:"Invented provider training note: a practice self-care task includes pacing and a recorded pause. A follow-up note is mentioned, but task duration is not supplied. This is not a person's record.",type:"health-system/provider record",authority:"provider-authored medical record"},
  domains:["ADL","care coordination"],fact:"Invented provider observation: a practice self-care task includes pacing.",
  relevance:"provider summary and care coordination documentation",why:"A documentation gap remains visible.",
  opportunity:"Review the sample follow-up note.",missing:"Duration is not supplied.",
  supports:{disability:false,treatment:true,referral:true,authorization:false},confidence:"high",strength:72,
});
export const priorityScenarios: readonly PriorityScenario[] = [
  {id:"global",title:"Global cap · 30 candidates",description:"Thirty newly invented rows across six document groups and six content types exercise the global cap. Repetition is a test construction, not independent corroboration.",rows:globalRows,bottlenecks:[]},
  {id:"document",title:"Document cap · 15 candidates",description:"One synthetic document supplies fifteen rows across three content types. Only twelve may be selected.",rows:documentRows,bottlenecks:[]},
  {id:"content",title:"Content-type cap · 8 candidates",description:"Eight separate synthetic documents share a content type. The normal type cap permits five.",rows:typeRows,bottlenecks:[]},
  {id:"denial",title:"Denial-source exception",description:"Fourteen payer-source rows share one content type and one document. The type exception does not bypass the twelve-per-document cap. A lower-ranked unknown row shares the same content type.",rows:[...denialRows,{...unknown,id:"DENIAL-UNKNOWN",contentType:"denial context"}],bottlenecks:[{id:"B05-PAYER",title:"Synthetic insurance documentation gap",needed:"The invented letter refers to missing documentation.",next:"Human inspection only.",sources:[]}]},
  {id:"ties",title:"Tied and near-tied scores",description:"Strength inputs 64 and 65 contribute the same integer score; 72 contributes one more point. Exact ties retain original input order.",rows:[sampleRow("TIE-A"),sampleRow("TIE-B",{strength:65}),sampleRow("NEAR",{strength:72})],bottlenecks:[]},
  {id:"context",title:"Context and unknown authority",description:"Provider context, low-confidence claimant evidence, and an unknown-source fragment show score components, suggested-use labels and source-linked bottleneck context. None is a professional determination.",rows:[contextual,sampleRow("CLAIMANT",{source:{...unknown.source,document:"synthetic-function-note.md",chunk:"SYN05-CLAIMANT",excerpt:"Invented claimant-style training note: a sample exercise includes a reported pause. No real person is represented.",type:"function report",authority:"claimant functional evidence"},confidence:"low",strength:32}),unknown],bottlenecks:[{id:"B05-FOLLOWUP",title:"Synthetic follow-up documentation gap",needed:"Duration is missing from the training note.",next:"Inspect the underlying invented source.",sources:[reference(contextual)]}]},
  {id:"empty",title:"Empty input",description:"No evidence was supplied. An empty selection is not a passed validation.",rows:[],bottlenecks:[]},
];
export function priorityScenario(id:string) {
  const value=priorityScenarios.find(s=>s.id===id);
  if(!value) throw new Error("Unknown synthetic prioritization scenario");
  return value;
}
