"use client";
import Link from "next/link";
import Image from "next/image";
import nvltLogo from "./nvlt-official-logo.svg";
import { useRef, useState } from "react";
import { VersionSelector } from "@/components/version-selector";
import { Icon } from "@/components/icon";
import { RECONSTRUCTION, V11_DISCLAIMER } from "@/lib/v11/fixtures";
import { priorityScenarios, priorityScenario } from "@/lib/v11/prioritized/fixtures";
import { prioritize } from "@/lib/v11/prioritized/ranking";
import { suggestedUses } from "@/lib/v11/prioritized/uses";
import { reference, type Candidate } from "@/lib/v11/prioritized/types";
import base from "./workspace.module.css";
import styles from "./prioritized-evidence.module.css";

export function PrioritizedEvidence(){
  const [scenarioId,setScenarioId]=useState("global");
  const [filter,setFilter]=useState("all");
  const [source,setSource]=useState<Candidate|null>(null);
  const dialog=useRef<HTMLDialogElement>(null);
  const scenario=priorityScenario(scenarioId);
  const ranked=prioritize(scenario.rows,scenario.bottlenecks);
  const selected=ranked.filter(r=>r.selected);
  const visible=ranked.filter(r=>filter==="all"||(filter==="selected"?r.selected:!r.selected));
  const denialPresent=scenario.rows.some(r=>r.source.type==="insurance denial letter");
  return <div className={base.workspace}>
    <a className="skip-link" href="#priority-main">Skip to content</a>
    <header className={base.header}><Link href="/v1-1" className={base.brand}><Image src={nvltLogo} alt="" width={44} height={44} className={base.brandLogo}/><span>Neverlost Systems</span></Link><span>V1.1 / RECONSTRUCTION · M05</span></header>
    <main id="priority-main" className={base.main}>
      <VersionSelector current="v11"/>
      <div className="page-heading"><div><p className="eyebrow">BOUNDED REVIEW / EXPLAINABLE SELECTION</p><h1>Prioritized Evidence</h1><p className="page-description">Inspect the full candidate set and the rules behind its bounded selection.</p></div></div>
      <div className="disclaimer" role="note"><Icon name="info"/><p>{V11_DISCLAIMER}</p></div>
      <p className={base.reconstruction}>{RECONSTRUCTION}</p>
      <nav className={base.navigation} aria-label="V1.1 surfaces"><Link href="/v1-1">Source Authority / Evidence</Link><Link href="/v1-1/run-review">Run Review</Link><Link href="/v1-1/prioritized-evidence" aria-current="page">Prioritized Evidence</Link></nav>
      <p className={base.reconstruction}>Continue to M06 · <Link href="/v1-1/capacity-themes">Capacity Themes</Link> → <Link href="/v1-1/denials-bottlenecks">Denials &amp; Bottlenecks</Link></p>
      <p className={base.reconstruction}><Link href="/v1-1/final-review">Final Review / Reports</Link> · Existing results and historical limits</p>
      <section className="concept-intro panel"><p className="eyebrow">RANKING IS NOT JUDGMENT</p><h2>A smaller set, not a stronger truth.</h2><p>These historical heuristics order synthetic rows for human inspection. Scores and suggested-use labels do not establish clinical importance, truth, eligibility, medical necessity, or professional judgment. Selected and excluded are computed membership—not accept/reject decisions.</p></section>
      <details className={base.changeNote}><summary>Ranking formula & selection rules</summary>
        <p>Total = source authority + functional impact + system relevance + actionability + trunc(existing evidence-strength score / 8). Each component has multiplier 1. Open a candidate to inspect every matched contribution and its supplied inputs.</p>
        <p>Stable descending score order; equal scores keep input order. Select at most 25 rows, at most 12 per exact document name, and normally at most 5 per exact content type. Document cap is checked before content cap. No deduplication or minimum score is added.</p>
        <p>Only rows whose source type is exactly “insurance denial letter” bypass the content-type cap. They still increment that type count and remain subject to document/global caps. A payer authority string or denial mention alone is not the exception.</p>
        <p>After 25 selections, the recovered loop stops. Remaining rows are labeled here as not visited after the global cap, rather than inventing a historical exclusion decision. Full candidate ranks, score explanations and exclusion reasons are new presentation instrumentation.</p>
      </details>
      <section className={base.scenario} aria-label="Prioritization scenario"><label htmlFor="priority-scenario">Synthetic prioritization scenario</label><select id="priority-scenario" value={scenarioId} onChange={e=>{setScenarioId(e.target.value);setFilter("all");}}>{priorityScenarios.map(s=><option key={s.id} value={s.id}>{s.title}</option>)}</select><p>{scenario.description}</p><small>Static invented inputs; temporary selection only. No saved or canonical state.</small></section>
      <section className={styles.counts} aria-label="Selection summary"><div><span>Full candidate set</span><strong>{ranked.length}</strong></div><div><span>Bounded selected set</span><strong>{selected.length} / 25</strong></div><div><span>Excluded / not visited</span><strong>{ranked.length-selected.length}</strong></div></section>
      <div className={styles.filter}><label htmlFor="membership">Show candidates</label><select id="membership" value={filter} onChange={e=>setFilter(e.target.value)}><option value="all">All candidates</option><option value="selected">Selected set</option><option value="excluded">Excluded / not visited</option></select></div>
      <p role="status" className={base.result}>{visible.length} shown · {selected.length} selected from {ranked.length} candidates</p>
      {!ranked.length&&<section className={base.empty}><h2>No candidate evidence supplied</h2><p>No ranking or selection was performed. Absence is not validation.</p></section>}
      {ranked.length>0&&!visible.length&&<p>No candidates in this membership filter.</p>}
      <div className={styles.candidates}>{visible.map(item=>{
        const uses=suggestedUses(item.row,denialPresent);
        return <article className="panel" key={item.row.id} aria-label={item.row.id}>
          <div className={styles.cardTop}><div><p className="eyebrow">CANDIDATE RANK {item.rank} · INPUT POSITION {item.inputIndex+1}</p><h2>{item.row.id}</h2><p>{item.row.source.type} · {item.row.contentType}</p></div><div className={styles.score}><strong>{item.total}</strong><span>heuristic score</span></div></div>
          <div className={styles.decision}><strong>{item.selected?`Selected · set rank ${item.selectedRank}`:"Excluded / not visited"}</strong><p>{item.reason}</p></div>
          <p className={styles.reference}>{reference(item.row)}</p>
          <details className={styles.details}><summary>Inspect ranking and source for {item.row.id}</summary>
            <h3>Score components</h3><div className={styles.components}>{item.components.map(c=><section key={c.name} aria-label={c.name}><h4>{c.name} <span>{c.points}</span></h4><ul>{c.reasons.map(reason=><li key={reason}>{reason}</li>)}</ul></section>)}</div>
            <p>Selected counts before this row: document {item.docCountBefore} / 12; content type {item.typeCountBefore} / 5. {item.exceptionApplied?"Denial exception applied.":"No denial exception applied."}</p>
            <h3>Supplied analytical inputs</h3><dl className={styles.inputs}>
              {[["Direct observation · invented source",item.row.fact],["Interpretation · invented, not computed",item.row.consequence],["Functional domains",item.row.domains.join(", ")||"None supplied"],["System relevance",item.row.relevance||"Not supplied"],["Why it matters",item.row.why||"Not supplied"],["Next opportunity · text only",item.row.opportunity||"Not supplied"],["Missing evidence",item.row.missing||"Not supplied"],["Confidence · uncalibrated fixture",item.row.confidence],["Evidence-strength input",String(item.row.strength)],["Supplied support flags · not determinations",Object.entries(item.row.supports).map(([k,v])=>k+": "+v).join(" · ")]].map(([label,value])=><div key={label}><dt>{label}</dt><dd>{value}</dd></div>)}
            </dl>
            <h3>Suggested uses · historical heuristic labels</h3><p>These labels describe possible review contexts, not verified suitability, advice, or produced reports.</p><ul>{uses.map(use=><li key={use.label}><strong>{use.label}</strong> — {use.basis}</li>)}</ul>
            {item.selected&&uses.length===1&&uses[0].label==="internal review"&&<p>Historical oddity: the selected-row note attributes this default use to prioritization, although the fallback applies even without selection.</p>}
            <h3>Related bottleneck</h3>{item.linked?<><a href={"#"+item.linked.item.id}>{item.linked.item.title}</a><p>{item.linked.basis}</p></>:<p>No direct bottleneck link identified.</p>}
            <button className="primary-button" onClick={()=>{setSource(item.row);dialog.current?.showModal();}} aria-label={"Inspect source "+item.row.id}>Inspect source <Icon name="source" width="16" height="16"/></button>
          </details>
        </article>;
      })}</div>
      {scenario.bottlenecks.length>0&&<section className={base.reviewSection} aria-label="Synthetic bottleneck context"><h2>Synthetic bottleneck context</h2><p>Existing invented analytical annotations, not newly detected bottlenecks or a Denial Mapping surface.</p>{scenario.bottlenecks.map(b=><article id={b.id} key={b.id} className={base.empty}><h3>{b.title}</h3><p>{b.needed}</p><p>{b.next}</p><p>Exact source references: {b.sources.join("; ")||"None supplied; any link above is heuristic."}</p></article>)}</section>}
      <footer className={base.footer}><strong>M05 boundary</strong><p>No Capacity Themes, Denial Mapping, final synthesis, autonomous actions, approvals, uploads, persistence or external communication. Original V1 and M04 rules and fixtures are unchanged.</p><p>Recovered rules are text-sensitive and uncalibrated. Missing-evidence text can raise a score; low-authority evidence can still be selected. See the M05 reconstruction notes for weights, preserved oddities and deviations.</p></footer>
    </main>
    <dialog ref={dialog} className="detail-dialog" aria-labelledby="priority-dialog-title"><div className="dialog-header"><span className="eyebrow">M05 / SYNTHETIC PROVENANCE</span><button className="close-button" aria-label="Close source dialog" onClick={()=>dialog.current?.close()}><Icon name="close"/></button></div><h2 id="priority-dialog-title">Synthetic source inspection</h2>{source&&<><div className="source-quote"><blockquote>{source.source.excerpt}</blockquote></div><dl className="provenance-fields">{[["Evidence ID",source.id],["Document",source.source.document],["Page",String(source.source.page)],["Chunk",source.source.chunk],["Source type",source.source.type],["Authority · fixture label",source.source.authority]].map(([label,value])=><div key={label}><dt>{label}</dt><dd>{value}</dd></div>)}</dl><p className="dialog-footnote">Independently invented data. Source authority and ranking are not authenticated provenance or professional judgment. No historical record is loaded.</p></>}</dialog>
  </div>;
}
