"use client";

import { useState } from "react";
import Link from "next/link";
import { Icon } from "@/components/icon";
import { bottlenecks, capacityWindows, evidence, evidenceById, formatDemoDate, hiddenStates, reports, timeline, type EvidenceItem } from "@/lib/demo-data";
import { historicalDomains, matrixAnnotations, matrixByEvidenceId, outputCopy, type OutputName, type MatrixAnnotation } from "@/lib/output-data";

type Props = { view: OutputName; openSource: (item: EvidenceItem) => void };
type SourceProps = { evidenceId: string; context: string; openSource: Props["openSource"] };

function SourceFooter({ evidenceId, context, openSource }: SourceProps) {
  const item = evidenceById(evidenceId);
  return <footer className="concept-source">
    <div><span className="source-filename">{item.source.document}</span><span className="source-location">{item.id} · p. {item.source.page} · {item.source.chunkId}</span><span className="source-location">{item.source.sourceType} · {item.kind}</span></div>
    <button className="primary-button" aria-label={`Inspect source for ${context}`} onClick={() => openSource(item)}>Inspect source <Icon name="source" width="16" height="16" /></button>
  </footer>;
}

function TimelineRows({ openSource, prefix = "timeline" }: { openSource: Props["openSource"]; prefix?: string }) {
  const ordered = [...timeline].sort((a, b) => a.date.localeCompare(b.date) || a.id.localeCompare(b.id));
  return <ol className="longitudinal-list">
    {ordered.map((event) => {
      const item = evidenceById(event.evidenceId);
      return <li key={event.id}>
        <div className="event-date"><time dateTime={event.date}>{formatDemoDate(event.date)}</time><span>2026</span></div>
        <article className="panel output-card" aria-label={event.label}>
          <header className="concept-card-header"><div><p className="eyebrow">{event.id} · {item.category}</p><h3>{event.label}</h3></div><span className="status-tag needs-review">{item.kind}</span></header>
          <div className="output-pair"><section><h4>Recorded source</h4><blockquote>{item.source.excerpt}</blockquote></section><section><h4>Interpretation & limitation</h4><p>{item.interpretation}</p><p className="output-muted">Confidence: not provided in the fixture. Patient observation: not separately identified.</p></section></div>
          <SourceFooter evidenceId={item.id} context={`${prefix} ${event.id}`} openSource={openSource} />
        </article>
      </li>;
    })}
  </ol>;
}

function MatrixRow({ row, openSource, prefix = "matrix" }: { row: MatrixAnnotation; openSource: Props["openSource"]; prefix?: string }) {
  const item = evidenceById(row.evidenceId);
  return <article className="panel output-card" aria-label={item.title}>
    <header className="concept-card-header"><div><p className="eyebrow">{item.id} · {item.date} · {row.domains.join(" / ")}</p><h3>{item.title}</h3></div><span className="status-tag needs-review">{item.kind}</span></header>
    <dl className="matrix-chain">
      <div><dt>Record fact · source excerpt</dt><dd>{item.source.excerpt}</dd></div>
      <div><dt>Functional consequence · annotation</dt><dd>{row.functionalConsequence ?? "Not established in the fixture."}</dd></div>
      <div><dt>System relevance · annotation</dt><dd>{row.systemRelevance}</dd></div>
      <div><dt>Next available opportunity · question only</dt><dd>{row.nextAvailableOpportunity ?? "Not identified in the fixture."}</dd></div>
    </dl>
    <div className="matrix-limits"><p><strong>Missing / uncertain evidence</strong> {row.missingEvidence}</p><p><strong>Interpretation & limitation</strong> {item.interpretation}</p><p className="output-muted">Source authority: synthetic note, not authenticated. Confidence, strength score, and disability/treatment/referral/authorization support flags: not supplied by these fixtures; not assessed here.</p></div>
    <SourceFooter evidenceId={item.id} context={`${prefix} ${item.id}`} openSource={openSource} />
  </article>;
}

function EvidenceMatrix({ openSource }: { openSource: Props["openSource"] }) {
  const [domain, setDomain] = useState("All domains");
  const [kind, setKind] = useState("All evidence");
  const visible = matrixAnnotations.filter((row) => (domain === "All domains" || row.domains.some((value) => value === domain)) && (kind === "All evidence" || evidenceById(row.evidenceId).kind === kind));
  return <>
    <div className="matrix-controls panel">
      <label>Functional domain<select value={domain} onChange={(event) => setDomain(event.target.value)}><option>All domains</option>{historicalDomains.map((value) => <option key={value}>{value}</option>)}</select></label>
      <label>Evidence type<select value={kind} onChange={(event) => setKind(event.target.value)}><option>All evidence</option><option>Direct source</option><option>Interpretation</option></select></label>
      <p role="status">{visible.length} of {matrixAnnotations.length} sample rows</p>
    </div>
    <details className="domain-coverage panel"><summary>Historical domain coverage · synthetic sample only</summary><p>Domain assignments are manually authored review lenses. Zero is not a clinical finding.</p><ul>{historicalDomains.map((value) => <li key={value}><span>{value}</span><span>{matrixAnnotations.filter((row) => row.domains.includes(value)).length} sample rows</span></li>)}</ul></details>
    <div className="output-list">{visible.map((row) => <MatrixRow key={row.evidenceId} row={row} openSource={openSource} />)}</div>
    {visible.length === 0 && <div className="panel output-empty"><h3>No sample evidence in this selection</h3><p>This does not establish absence of a condition or resolve an evidence gap.</p><button className="primary-button" onClick={() => { setDomain("All domains"); setKind("All evidence"); }}>Reset filters</button></div>}
  </>;
}

function RealityMap({ openSource }: { openSource: Props["openSource"] }) {
  const candidates = [...hiddenStates, ...bottlenecks, ...capacityWindows];
  return <div className="reality-preview">
    <h3>Snapshot of the synthetic analytical state</h3>
    <p>{timeline.length} events · {evidence.length} evidence entries · {hiddenStates.length} hidden-state candidate · {bottlenecks.length} bottleneck candidates · {capacityWindows.length} capacity-window candidates</p>
    <p className="output-muted">Counts describe fixtures, not conclusions. No trust-threshold fixture is available; it is not represented as a zero finding.</p>
    {candidates.map((item) => <article className="panel output-card" key={item.id} aria-label={item.title}>
      <div className="report-candidate"><p className="eyebrow">{item.id}</p><h4>{item.title}</h4><p>{item.status}</p>{"owner" in item && <p>Owner: {item.owner}. Fixture question: {item.nextSmallestAction}</p>}{"retainedGains" in item && <p>Retained gains: {item.retainedGains}</p>}<p>{evidenceById(item.evidenceId).interpretation}</p></div>
      <SourceFooter evidenceId={item.evidenceId} context={`reality map ${item.id}`} openSource={openSource} />
    </article>)}
    <p>Review the record-fact chain in the <Link href="/evidence-matrix">Evidence Matrix</Link>. These are linked views of the same sample, not accepted canonical state.</p>
  </div>;
}

function ReportPreviews({ openSource }: { openSource: Props["openSource"] }) {
  return <>
    <div className="output-warning" role="note">Not a verified clinical, disability, legal, or benefits determination. Analytical output remains separate from human judgment. No reports are generated, saved, or submitted by this demo.</div>
    {reports.map((report) => <details className="panel report-preview" key={report.id}>
      <summary><span><span className="eyebrow">{report.id} · STATIC DRAFT PREVIEW</span><strong>{report.title}</strong></span><Icon name="chevron" /></summary>
      <div className="report-body"><p>Inputs: {report.evidenceIds.join(" · ")}. All references resolve to the same synthetic sample.</p>
        {report.id === "DEMO-R01" ? <TimelineRows openSource={openSource} prefix="report timeline" /> : <div className="output-list">{report.evidenceIds.map((id) => <MatrixRow key={id} row={matrixByEvidenceId(id)} openSource={openSource} prefix="report matrix" />)}</div>}
      </div>
    </details>)}
    <details className="panel report-preview"><summary><span><span className="eyebrow">V1 OUTPUT STRUCTURE · STATIC DRAFT PREVIEW</span><strong>Healthcare Reality Map</strong></span><Icon name="chevron" /></summary><div className="report-body"><RealityMap openSource={openSource} /></div></details>
    <div className="output-warning"><strong>Representation limits</strong><p>V1 also defined specialized provider, disability, documentation-gap, coordination, action-roadmap, trust-threshold, source-authority, and evidence-ranking reports. The available synthetic sample does not support faithful previews of every field or report. No scores, support determinations, patient observations, or clinical narratives have been invented to fill them. This is not the later applied five-report packet or a V1.1 workflow.</p></div>
  </>;
}

export function OutputView({ view, openSource }: Props) {
  const copy = outputCopy[view];
  return <div className="output-view">
    <section className="concept-intro panel" aria-labelledby="output-title"><p className="eyebrow">HISTORICAL V1 STRUCTURE / SYNTHETIC PRESENTATION</p><h2 id="output-title">{copy.title}</h2><p>{copy.explanation}</p><div className="concept-boundary"><Icon name="info" /><span>Presentation only. No historical pipeline is executed. Human review remains required.</span></div></section>
    {view === "Timeline" ? <><p className="concept-reading-note">June 03–14, 2026 · Dates belong to invented notes. Sequence does not establish cause, improvement, or a clinical conclusion.</p><TimelineRows openSource={openSource} /></> : view === "Evidence Matrix" ? <EvidenceMatrix openSource={openSource} /> : <ReportPreviews openSource={openSource} />}
  </div>;
}
