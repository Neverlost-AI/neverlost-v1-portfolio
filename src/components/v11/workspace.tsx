"use client";

import Link from "next/link";
import { useRef, useState } from "react";
import { Icon } from "@/components/icon";
import { VersionSelector } from "@/components/version-selector";
import { scenarios, scenarioById, RECONSTRUCTION, V11_DISCLAIMER } from "@/lib/v11/fixtures";
import { classify, review } from "@/lib/v11/rules";
import type { DemoDocument } from "@/lib/v11/types";
import styles from "./workspace.module.css";

export function V11Workspace({ view }: { view: "source" | "review" }) {
  const [scenarioId, setScenarioId] = useState("mixed");
  const [selected, setSelected] = useState<DemoDocument | null>(null);
  const dialog = useRef<HTMLDialogElement>(null);
  const scenario = scenarioById(scenarioId);
  const result = review(scenario);
  const title = view === "source" ? "Source Authority / Evidence" : "Run Review";
  function inspect(document: DemoDocument) {
    setSelected(document);
    dialog.current?.showModal();
  }
  function sourceButton(document: DemoDocument) {
    return <button className="primary-button" onClick={() => inspect(document)} aria-label={`Inspect source ${document.id}`}>Inspect source <Icon name="source" width="16" height="16" /></button>;
  }

  return <div className={styles.workspace}>
    <a className="skip-link" href="#v11-main">Skip to content</a>
    <header className={styles.header}><Link href="/v1-1" className={styles.brand}>neverlost<span>.</span></Link><span>V1.1 / RECONSTRUCTION · M04</span></header>
    <main id="v11-main" className={styles.main}>
      <VersionSelector current="v11" />
      <div className="page-heading"><div><p className="eyebrow">RECOVERED EXTENSION / NEW PRESENTATION</p><h1>{title}</h1><p className="page-description">Source-bounded evidence. Deterministic review. Human judgment.</p></div></div>
      <div className="disclaimer" role="note"><Icon name="info" /><p>{V11_DISCLAIMER}</p></div>
      <p className={styles.reconstruction}>{RECONSTRUCTION}</p>
      <nav className={styles.navigation} aria-label="V1.1 surfaces"><Link href="/v1-1" aria-current={view === "source" ? "page" : undefined}>Source Authority / Evidence</Link><Link href="/v1-1/run-review" aria-current={view === "review" ? "page" : undefined}>Run Review</Link></nav>
      <details className={styles.changeNote}><summary>What changed from V1?</summary><p>Recovered V1.1 extended source-authority, bottleneck, and report handling and added deterministic review, prioritization, and batch orchestration. File comparison supports direct code extension: 21 unchanged source/schema files, three modified modules, and three added modules—not authenticated Git history.</p><p>M04 reconstructs only source/evidence handling and the initial run-review layer. Ordinary historical main did not invoke the added review layers. This browser computes selected rules on synthetic inputs; it does not run the Python pipeline.</p><p>Prioritized Evidence, Capacity Themes, Denial Mapping, final synthesis, and the later five-report applied workflow are not implemented here. Final-synthesis authorship and regeneration remain uncertain.</p></details>
      <section className={styles.scenario} aria-label="Synthetic scenario">
        <label htmlFor="v11-scenario">Synthetic input scenario</label>
        <select id="v11-scenario" value={scenarioId} onChange={(event) => setScenarioId(event.target.value)}>{scenarios.map((item) => <option key={item.id} value={item.id}>{item.title}</option>)}</select>
        <p>{scenario.description}</p><small>Selection is temporary and resets on reload or a change of surface. No data is uploaded or saved.</small>
      </section>

      {view === "source" ? <>
        <section className="concept-intro panel"><p className="eyebrow">WHO AUTHORED IT ≠ WHAT IT MENTIONS</p><h2>Keep source authority separate.</h2><p>Filename/content markers suggest a source type; they do not authenticate its author. Evidence observations remain separate from hand-authored interpretations. Payer, service, and denial context are labels for inspection—not a denial mapping or a determination.</p></section>
        <p className={styles.result} role="status">{scenario.documents.length} synthetic documents · {scenario.evidence.length} evidence rows</p>
        <div className={styles.cards}>{result.documents.map(({ document, classification, rowCount, warnings }) => <article className="panel" key={document.id} aria-labelledby={document.id}>
          <header className={styles.cardHeader}><div><p className="eyebrow">{document.id}</p><h2 id={document.id}>{document.name}</h2></div><span className="status-tag needs-review">{classification.type}</span></header>
          <dl className={styles.fields}><div><dt>Computed source authority</dt><dd>{classification.authority}</dd></div><div><dt>Classification basis</dt><dd>{classification.basis}</dd></div><div><dt>Payer mentioned</dt><dd>{classification.payer ?? "Not identified"}</dd></div><div><dt>Service context</dt><dd>{classification.service ?? "Not identified"}</dd></div><div><dt>Denial / insurance context</dt><dd>{classification.context}</dd></div><div><dt>Source reference</dt><dd>p. {document.page} · {document.chunkId}</dd></div></dl>
          <div className={styles.excerpt}><p className="eyebrow">INVENTED SOURCE EXCERPT</p><blockquote>{document.excerpt}</blockquote></div>
          <details className={styles.entries}><summary>Evidence entries ({rowCount})</summary>{scenario.evidence.filter((row) => row.documentId === document.id).map((row) => <div className={styles.entry} key={row.id}><p className="eyebrow">{row.id}</p><dl><div><dt>Direct observation · fixture</dt><dd>{row.observation}</dd></div><div><dt>Interpretation · fixture, not computed</dt><dd>{row.interpretation}</dd></div><div><dt>{row.declaredType ? "Supplied row classification" : "Computed row classification · document fallback"}</dt><dd>{row.declaredType ?? classification.type}</dd></div><div><dt>Confidence · fixture label, not calibrated</dt><dd>{row.confidence}</dd></div></dl></div>)}</details>
          {warnings.length > 0 && <ul className={styles.inlineWarnings}>{warnings.map((warning) => <li key={warning.code}>{warning.message}</li>)}</ul>}
          <footer className={styles.cardFooter}><span>Source references support inspection, not authenticity.</span>{sourceButton(document)}</footer>
        </article>)}</div>
        {!scenario.documents.length && <section className={styles.empty}><h2>No source documents supplied</h2><p>Source authority and evidence are not assessed. No author, classification, or evidence is invented.</p></section>}
      </> : <>
        <section className="concept-intro panel"><p className="eyebrow">DETERMINISTIC REVIEW / NOT APPROVAL</p><h2>Make the review basis visible.</h2><p>This manifest summarizes synthetic inputs, not a completed extraction run. Warnings use recovered count/classification conditions. Suggested actions are plain review prose, not assignments, saved decisions, or executable commands.</p></section>
        <section className={styles.manifest} aria-labelledby="manifest-title"><h2 id="manifest-title">Synthetic input manifest</h2><dl><div><dt>Scenario ID</dt><dd>{scenario.id}</dd></div><div><dt>Documents</dt><dd>{scenario.documents.length}</dd></div><div><dt>Evidence rows</dt><dd>{scenario.evidence.length}</dd></div><div><dt>Candidate-window stubs</dt><dd>{scenario.candidateWindows.length}</dd></div><div><dt>Unknown source documents</dt><dd>{result.unknownCount}</dd></div><div><dt>Low/unknown-confidence rows</dt><dd>{result.lowConfidenceCount}</dd></div><div><dt>Payer-denial source present</dt><dd>{result.denialPresent ? "Yes — heuristic classification" : "No payer-denial source supplied"}</dd></div><div><dt>Classification review</dt><dd>{result.classificationStatus}</dd></div></dl><p>No timestamp, private path, extraction-success claim, or generated-file claim is fabricated.</p></section>
        <section className={styles.reviewSection} aria-labelledby="document-review-title"><h2 id="document-review-title">Document review</h2><div className={styles.cards}>{result.documents.map(({ document, classification, rowCount, warnings }) => <article className="panel" key={document.id} aria-label={document.name}><div className={styles.documentReview}><h3>{document.name}</h3><p>{classification.type} · {classification.authority}</p><p>{rowCount} evidence row(s) · {document.extraction} · p. {document.page} · {document.chunkId}</p><p>{warnings.length ? warnings.map((warning) => warning.message).join(" ") : "No modeled document warning detected. Human review still required."}</p>{sourceButton(document)}</div></article>)}</div>{!result.documents.length && <p>No documents to review.</p>}</section>
        <section className={styles.reviewSection} aria-labelledby="warnings-title"><h2 id="warnings-title">Warnings & classification issues</h2><ul className={styles.warningList}>{result.warnings.map((warning, index) => <li key={index}><strong>{warning.message}</strong><p>{warning.documentId && <span>{warning.documentId} · </span>}{warning.basis}</p></li>)}</ul>{!result.warnings.length && <p>No modeled warning detected. This is not clinical validation or approval.</p>}</section>
        <section className={styles.reviewSection} aria-labelledby="actions-title"><h2 id="actions-title">Deterministic suggested actions</h2><p>At most three suggestions, in recovered rule order. No action is executed.</p><ol className={styles.actions}>{result.actions.map((action) => <li key={action.title}><h3>{action.title}</h3><p>{action.basis}</p><p>Suggested reviewer: {action.owner} · Historical urgency label: {action.urgency}</p></li>)}</ol>{!result.actions.length && <p>No rule-based next actions generated. Human review is still required.</p>}</section>
      </>}
      <footer className={styles.footer}><strong>M04 boundary</strong><p>No Prioritized Evidence, Capacity Themes, Denial Mapping, final synthesis, approval workflow, persistence, or external communication. The five-report system and other applied workflows are separate.</p><p>Source patterns are generic, sample counts replace historical hard-coded counts, and empty/mismatched inputs are never shown as passed validation. See the reconstruction notes in the project documentation.</p></footer>
    </main>
    <dialog ref={dialog} className="detail-dialog" aria-labelledby="v11-dialog-title">
      <div className="dialog-header"><span className="eyebrow">V1.1 / SYNTHETIC PROVENANCE</span><button className="close-button" onClick={() => dialog.current?.close()} aria-label="Close source dialog"><Icon name="close" /></button></div>
      <h2 id="v11-dialog-title">Synthetic source inspection</h2>
      {selected && <><div className="source-quote"><blockquote>{selected.excerpt}</blockquote></div><dl className="provenance-fields"><div><dt>Document</dt><dd>{selected.name}</dd></div><div><dt>Document ID</dt><dd>{selected.id}</dd></div><div><dt>Page</dt><dd>{selected.page}</dd></div><div><dt>Chunk</dt><dd>{selected.chunkId}</dd></div><div><dt>Source type</dt><dd>{classify(selected).type}</dd></div><div><dt>Input flag</dt><dd>{selected.extraction}</dd></div></dl><p className="dialog-footnote">All content is invented. Classification is a computed heuristic, not authenticated provenance. No historical record is loaded or available for download.</p></>}
    </dialog>
  </div>;
}
