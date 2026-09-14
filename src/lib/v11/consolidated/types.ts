import type { Candidate } from "../prioritized/types";
export interface Evidence extends Candidate { payer?:string; service?:string; denialContext?:string }
export interface Window {id:string; evidenceId:string; intervention:string; sourceEvidence:string; possible:string; learning:string}
export interface Scenario {id:string; title:string; description:string; rows:readonly Evidence[]; windows:readonly Window[]}
export function evidenceFor(s:Scenario,id:string){
  const row=s.rows.find(r=>r.id===id);
  if(!row)throw new Error("Unresolved synthetic M06 evidence reference: "+id);
  return row;
}

