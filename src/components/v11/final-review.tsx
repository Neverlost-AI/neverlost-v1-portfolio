"use client";

import Link from "next/link";
import {useRef, useState} from "react";
import {VersionSelector} from "@/components/version-selector";
import {Icon} from "@/components/icon";
import {RECONSTRUCTION, V11_DISCLAIMER, scenarios as foundationScenarios, scenarioById as foundationById} from "@/lib/v11/fixtures";
import {review, documentFor, classify} from "@/lib/v11/rules";
import {priorityScenarios, priorityScenario} from "@/lib/v11/prioritized/fixtures";
import {prioritize} from "@/lib/v11/prioritized/ranking";
import {reference, type Candidate} from "@/lib/v11/prioritized/types";
import {scenarios as consolidatedScenarios, scenarioById as consolidatedById} from "@/lib/v11/consolidated/fixtures";
import {detect} from "@/lib/v11/consolidated/bottlenecks";
import {consolidate} from "@/lib/v11/consolidated/themes";
import {mapDenial} from "@/lib/v11/consolidated/denials";
import base from "./workspace.module.css";
import styles from "./final-review.module.css";

type Source = {id:string; document:string; page:number; chunk:string; excerpt:string; type:string; authority:string; observation:string; interpretation:string};
const candidateSource = (row:Candidate, milestone:string):Source => ({...row.source, id:milestone+" / "+row.id, observation:row.fact, interpretation:row.consequence});
const surfaces = [["/v1-1","Source Authority / Evidence"],["/v1-1/run-review","Run Review"],["/v1-1/prioritized-evidence","Prioritized Evidence"],["/v1-1/capacity-themes","Capacity Themes"],["/v1-1/denials-bottlenecks","Denials & Bottlenecks"],["/v1-1/final-review","Final Review / Reports"]];

export function FinalReview() {
  const [foundationId,setFoundationId]=useState("mixed");
  const [priorityId,setPriorityId]=useState("global");
  const [consolidatedId,setConsolidatedId]=useState("mixed");
  const [source,setSource]=useState<Source|null>(null);
  const dialog=useRef<HTMLDialogElement>(null);
  const foundation=foundationById(foundationId), run=review(foundation);
  const priority=priorityScenario(priorityId), ranked=prioritize(priority.rows,priority.bottlenecks);
  const consolidated=consolidatedById(consolidatedId), bottlenecks=detect(consolidated.rows);
  const themes=consolidate(consolidated,bottlenecks.groups), denial=mapDenial(consolidated.rows);
  const inspect=(item:Source)=>{setSource(item);dialog.current?.showModal();};

  return <div className={base.workspace}>
    <a className="skip-link" href="#m07-main">Skip to content</a>
    <header className={base.header}><Link href="/v1-1" className={base.brand}>neverlost<span>.</span></Link><span>V1.1 / RECONSTRUCTION · M07</span></header>
    <main id="m07-main" className={base.main}>
      <VersionSelector current="v11"/>
      <div className="page-heading"><div><p className="eyebrow">REVIEW INDEX / NOT A SYNTHESIS ENGINE</p><h1>Final Review / Reports</h1><p className="page-description">Follow the analytical trail. Keep judgment with the reviewer.</p></div></div>
      <div className="disclaimer" role="note"><Icon name="info"/><p>{V11_DISCLAIMER}</p></div>
      <p className={base.reconstruction}>{RECONSTRUCTION}</p>
      <nav className={base.navigation} aria-label="V1.1 surfaces">{surfaces.map(([href,label])=><Link href={href} key={href} aria-current={href==="/v1-1/final-review"?"page":undefined}>{label}</Link>)}</nav>
      <section className="concept-intro panel"><p className="eyebrow">NEW PRESENTATION / EXISTING RESULTS</p><h2>A review sequence, not a combined case.</h2><p>This index calls the unchanged M04–M06 rules. Its three fixture sets are independent demonstrations, not consecutive stages of one batch. Changing a scenario here does not change another set or transfer state to another page.</p><p>No report, final synthesis or packet is generated. The detailed surfaces remain the place to inspect individual rule traces. Navigation and reload reset these selections.</p></section>

      <section className={styles.section} aria-labelledby="foundation-heading">
        <p className="eyebrow">01–02 / M04 OUTPUTS</p><h2 id="foundation-heading">Source authority & run review</h2>
        <div className={base.scenario}><label htmlFor="review-foundation">Independent M04 scenario</label><select id="review-foundation" value={foundationId} onChange={e=>setFoundationId(e.target.value)}>{foundationScenarios.map(s=><option key={s.id} value={s.id}>{s.title}</option>)}</select><p>{foundation.description}</p></div>
        <p data-testid="foundation-counts">{foundation.documents.length} documents · {foundation.evidence.length} evidence rows · {run.warnings.length} warnings · {run.actions.length} suggested reviews</p>
        <p>{run.classificationStatus}. Confidence labels are not calibrated probabilities.</p>
        <details className={base.changeNote}><summary>Inspect warnings and suggested reviews</summary><ul>{run.warnings.map((w,i)=><li key={i}><strong>{w.code}</strong>: {w.message}<p>{w.basis}{w.documentId?" Document: "+w.documentId:""}</p></li>)}</ul>{!run.warnings.length&&<p>No modeled warnings; not a validation result.</p>}<ol>{run.actions.map(a=><li key={a.title}>{a.title}<p>{a.basis} · {a.owner} · {a.urgency}</p></li>)}</ol><p>Unchanged M04 suggestions, maximum three. These are not executed actions; references to M04 scope remain as originally documented.</p></details>
        <details className={base.changeNote}><summary>Inspect M04 source evidence ({foundation.evidence.length})</summary>{foundation.evidence.map(row=>{const doc=documentFor(foundation,row),c=classify(doc);return <article className={styles.row} key={row.id}><h3>{row.id}</h3><p>{doc.name} · p. {doc.page} · {doc.chunkId}</p><p>{c.type} · {c.authority}</p><p>Supplied row type: {row.declaredType||"Not supplied; computed document fallback"}</p><button className="primary-button" onClick={()=>inspect({id:"M04 / "+row.id,document:doc.name,page:doc.page,chunk:doc.chunkId,excerpt:doc.excerpt,type:c.type,authority:c.authority,observation:row.observation,interpretation:row.interpretation})} aria-label={"Inspect M04 source "+row.id}>Inspect source</button></article>;})}{!foundation.evidence.length&&<p>No evidence supplied.</p>}</details>
        <p><Link href="/v1-1">Source Authority / Evidence</Link> → <Link href="/v1-1/run-review">Run Review</Link></p>
      </section>

      <section className={styles.section} aria-labelledby="priority-heading">
        <p className="eyebrow">03 / M05 OUTPUTS</p><h2 id="priority-heading">Prioritized evidence</h2>
        <div className={base.scenario}><label htmlFor="review-priority">Independent M05 scenario</label><select id="review-priority" value={priorityId} onChange={e=>setPriorityId(e.target.value)}>{priorityScenarios.map(s=><option key={s.id} value={s.id}>{s.title}</option>)}</select><p>{priority.description}</p></div>
        <p data-testid="priority-counts">{ranked.length} candidates · {ranked.filter(r=>r.selected).length} selected · {ranked.filter(r=>!r.selected).length} excluded</p>
        <p>Unchanged score order and 25 / 12 / 5 caps. Only exact denial-source rows bypass the content-type cap, not document or global caps. Ranking is not clinical importance, truth or eligibility.</p>
        <details className={base.changeNote}><summary>Inspect ranked output and provenance ({ranked.length})</summary>{ranked.map(r=><article className={styles.row} key={r.row.id}><h3>Rank {r.rank} · {r.row.id}</h3><p>Score {r.total} · {r.selected?"Selected #"+r.selectedRank:"Excluded"}</p><p>{r.reason}</p><p>{r.components.map(c=>c.name+": "+c.points).join(" · ")}</p><p>{reference(r.row)}</p><button className="primary-button" onClick={()=>inspect(candidateSource(r.row,"M05"))} aria-label={"Inspect M05 source "+r.row.id}>Inspect source</button></article>)}{!ranked.length&&<p>No candidate evidence supplied.</p>}</details>
        <p><Link href="/v1-1/prioritized-evidence">Inspect ranking components, suggested uses and bottleneck links</Link> on the detailed M05 surface (its own scenario selection).</p>
      </section>

      <section className={styles.section} aria-labelledby="consolidated-heading">
        <p className="eyebrow">04–05 / M06 OUTPUTS</p><h2 id="consolidated-heading">Capacity themes, denials & bottlenecks</h2>
        <div className={base.scenario}><label htmlFor="review-consolidated">Independent M06 scenario</label><select id="review-consolidated" value={consolidatedId} onChange={e=>setConsolidatedId(e.target.value)}>{consolidatedScenarios.map(s=><option key={s.id} value={s.id}>{s.title}</option>)}</select><p>{consolidated.description}</p></div>
        <p data-testid="consolidated-counts">{consolidated.windows.length} windows · {themes.length} themes · {bottlenecks.groups.length} candidate bottlenecks</p>
        <p role="status">{denial?"Payer-denial source present; keyword mapping requires human inspection.":"No payer-denial source supplied; no denial mapping created."}</p>
        <p>Membership is not sustained or retained functional capacity, treatment effectiveness, medical necessity or a disability determination.</p>
        <div className={styles.columns}>
          <details className={base.changeNote}><summary>Inspect theme membership</summary><ol>{themes.map(t=><li key={t.name}>{t.name}<p>{t.members.length} window(s): {t.members.map(m=>m.window.id).join(", ")}</p><p>Sources: {t.members.map(m=>consolidated.rows.find(r=>r.id===m.window.evidenceId)).filter((r):r is NonNullable<typeof r>=>!!r).map(r=>r.id).join(", ")}</p></li>)}</ol>{!themes.length&&<p>No capacity themes.</p>}<p>Eight recovered families; the preserved ten-theme guard is structurally unreachable under this classifier.</p></details>
          <details className={base.changeNote}><summary>Inspect candidate bottlenecks</summary><ol>{bottlenecks.groups.map(b=><li key={b.id}>{b.title}<p>{b.needed}</p><p>Source evidence: {b.rows.map(r=>r.id).join(", ")}</p><p>Uncalibrated confidence heuristic: {b.confidence}</p></li>)}</ol>{!bottlenecks.groups.length&&<p>No candidate bottlenecks.</p>}</details>
        </div>
        <details className={base.changeNote}><summary>Inspect denial context and unresolved information</summary>{denial?<><p>Payer: {denial.payer||"Not identified"} · Service: {denial.service||"Not identified"}</p><p>{denial.context||"Denial context not identified"}</p><p>Contributing payer evidence: {denial.sources.map(r=>r.id).join(", ")}</p><ul>{denial.rationale.map(r=><li key={r.label}>{r.label}: {r.result?r.result.excerpt:"Not detected; human inspection required."}</li>)}</ul><ul>{denial.gaps.map(g=><li key={g}>{g}</li>)}</ul><p>Candidate provider support: {denial.provider.map(r=>r.row.id).join(", ")||"None supplied"}. Candidate OT support: {denial.ot.map(r=>r.row.id).join(", ")||"None supplied"}.</p><p>Joined source facts and first available fields can cross document boundaries. Keyword snippets do not establish actual criteria, deadlines or support sufficiency.</p></>:<p>No denial mapping. Absence is not a coverage or eligibility conclusion.</p>}</details>
        <details className={base.changeNote}><summary>Inspect M06 source evidence ({consolidated.rows.length})</summary>{consolidated.rows.map(row=><article className={styles.row} key={row.id}><h3>{row.id}</h3><p>{reference(row)}</p><button className="primary-button" onClick={()=>inspect(candidateSource(row,"M06"))} aria-label={"Inspect M06 source "+row.id}>Inspect source</button></article>)}{!consolidated.rows.length&&<p>No evidence supplied.</p>}</details>
        <p><Link href="/v1-1/capacity-themes">Capacity Themes</Link> → <Link href="/v1-1/denials-bottlenecks">Denials &amp; Bottlenecks</Link> for complete triggers, member/source links and mapping limitations.</p>
      </section>

      <section className={styles.section} aria-labelledby="reports-heading"><p className="eyebrow">06 / REPORTING STATUS & HISTORICAL LIMITS</p><h2 id="reports-heading">What this review does — and does not — establish</h2>
        <dl className={styles.ledger}>
          <div><dt>Recovered historical behavior</dt><dd>Source-sensitive evidence, deterministic review, ranking, grouping and denial context are supported by recovered code. File comparison supports V1.1 as a direct V1 extension: three modified modules, three added modules and 21 unchanged source/schema files. This is not authenticated historical Git ancestry.</dd></div>
          <div><dt>Reconstructed rules</dt><dd>M04–M06 are new deterministic TypeScript implementations of selected recovered rules, using independent synthetic fixtures. Their documented generalizations and historical quirks remain intact.</dd></div>
          <div><dt>New presentation</dt><dd>This read-only review index, selectors, score traces and source dialogs are new. They summarize existing reconstructed results; they are not the historical interface or a report-generation pipeline.</dd></div>
          <div><dt>Intentionally corrected defects</dt><dd>Earlier milestones replaced fixed batch counts and unconditional success claims, show missing input and classification issues explicitly, and suppress denial mapping when no denial source exists. Service fallback attribution and missing-field warnings are explicit. M07 changes no analytical rule.</dd></div>
          <div><dt>Ordinary reports versus final synthesis</dt><dd>Recovered ordinary report code is distinct from surviving final-synthesis artifacts. Project records report surviving provider-ready, appeal/authorization, care-coordination and combined final-packet artifacts. Their exact generating implementation was not recovered; authorship and exact regeneration remain unestablished. No private artifact is displayed or regenerated here.</dd></div>
          <div><dt>Private batch runner</dt><dd>The recovered batch-specific runner called the added layers, but does not establish a general reusable end-to-end pipeline. The historical main/viewer did not invoke those layers. Full private-batch reproducibility remains unestablished.</dd></div>
          <div><dt>Outside this reconstruction</dt><dd>The five-report system and other APPLIED_ON_TOP_OF_V1 workflows remain separate. Case Navigator, Neverlost OS, Command Center and later projects are excluded. There is no LLM/API execution, autonomous action, approval workflow, canonical state, persistence, upload, sending or packet generation.</dd></div>
        </dl>
      </section>
      <footer className={base.footer}>Analytical output remains distinct from human judgment. No clinical validation, eligibility, medical necessity or measured functional outcome is established.</footer>
    </main>
    <dialog ref={dialog} className="detail-dialog" aria-labelledby="m07-source-title"><div className="dialog-header"><span className="eyebrow">SYNTHETIC SOURCE / REVIEW INDEX</span><button className="close-button" aria-label="Close source dialog" onClick={()=>dialog.current?.close()}><Icon name="close"/></button></div><h2 id="m07-source-title">Synthetic source inspection</h2>{source&&<><div className="source-quote"><blockquote>{source.excerpt}</blockquote></div><dl className="provenance-fields">{[["Evidence / fixture set",source.id],["Document",source.document],["Page",String(source.page)],["Chunk",source.chunk],["Source type",source.type],["Authority · heuristic or supplied label",source.authority],["Source observation · synthetic",source.observation],["Interpretation · synthetic",source.interpretation]].map(([label,value])=><div key={label}><dt>{label}</dt><dd>{value||"Not supplied"}</dd></div>)}</dl><p className="dialog-footnote">Independently invented content. Source linkage is preserved, not authenticated. An interpretation is not a verified finding.</p></>}</dialog>
  </div>;
}
