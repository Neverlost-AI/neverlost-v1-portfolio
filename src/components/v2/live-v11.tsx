"use client";
import type { Json, Row, Run, Source } from "@/lib/v2/contracts";
import styles from "./workspace.module.css";

const views = ["source-authority", "run-review", "prioritized-evidence", "capacity-themes", "denials", "final-review"];
const text = (value: Json | undefined) => value == null ? "Not supplied" : typeof value === "object" ? JSON.stringify(value, null, 2) : String(value);

export function LiveV11({ run, view, inspect }: { run: Run; view: string; inspect: (source: Source, chunk?: Row) => void }) {
  if (!views.includes(view)) return null;
  const result = run.v1_1;
  if (!result) return <p className={styles.warning}>No recovered V1.1 result is available. No fixture result is substituted.</p>;
  function references(row: Row) {
    const nested = row.source && typeof row.source === "object" && !Array.isArray(row.source) ? row.source : {};
    const filename = row.source_document ?? row.file_name ?? row.document_name ?? nested.document;
    const names = typeof filename === "string" ? [filename] : Array.isArray(row.source_documents_supporting_it) ? row.source_documents_supporting_it : [];
    const chunk = run.artifacts.chunks.find(item => item.chunk_id === (row.source_page_or_chunk ?? nested.chunk_id));
    return names.map(name => {
      const source = run.sources.find(item => item.filename === name);
      return source ? <button key={source.filename} className={styles.secondary} onClick={() => inspect(source, chunk?.document === source.filename ? chunk : undefined)}>Inspect source · {source.filename}</button> : null;
    });
  }
  function fields(row: Row) {
    return <dl>{Object.entries(row).map(([key, value]) => <div key={key} className={styles.field}><dt>{key.replaceAll("_", " ")}</dt><dd><pre>{text(value)}</pre></dd></div>)}</dl>;
  }
  function rows(title: string, items: Row[]) {
    return <section aria-label={title}><h2>{title} · {items.length}</h2>
      {!items.length && <p>No generated rows. Missing evidence is not silently resolved.</p>}
      {items.map((row, index) => <article key={index} className={styles.panel}>
        <p className={styles.kicker}>RECOVERED PYTHON OUTPUT {index + 1} · HUMAN REVIEW REQUIRED</p>
        <h3>{text(row.theme_name ?? row.current_bottleneck ?? row.file_name ?? row.document_name ?? row.source_document ?? "Generated item")}</h3>
        <p>{text(row.record_fact ?? row.evidence_summary ?? row.source_authority ?? row.why_it_exists ?? null)}</p>
        {references(row)}
        <details><summary>Generated fields and provenance</summary>{fields(row)}</details>
      </article>)}
    </section>;
  }
  function reports(items: Record<string, string>, label: string) {
    return <section aria-label={label}><h2>{label}</h2>{Object.entries(items).map(([name, content]) =>
      <details key={name} className={styles.panel}><summary>{name}</summary><pre className={styles.report}>{content}</pre></details>)}</section>;
  }
  return <section aria-label="Live recovered V1.1">
    <div className={styles.panel}><h2>Recovered V1.1 · live second stage</h2>
      <p>Actual V1 output processed by recovered Python with explicit publication adaptations. New V2 interface, not the historical V1.1 interface. File comparison supports direct extension, not authenticated Git ancestry.</p>
      <dl className={styles.ledger}><dt>Upstream V1 digest</dt><dd>{result.upstream_v1_sha256}</dd><dt>V1.1 digest</dt><dd>{result.result_sha256}</dd><dt>Adaptation</dt><dd>{result.adaptation_identity}</dd></dl>
      <details><summary>Recovered limitations and V2 adaptations</summary><ul>{result.warnings.map(warning => <li key={warning}>{warning}</li>)}</ul></details>
    </div>
    {view === "source-authority" && <>{rows("Document source authority", result.document_statuses)}{rows("Generated V1.1 evidence", result.evidence_matrix)}</>}
    {view === "run-review" && <>
      <div className={styles.panel}><h2>Manifest and document warnings</h2><p>V2 projection: execution paths replaced with logical locations; timestamp excluded from analytical digest. Historical fixed counts/actions below are not measurements of this run.</p>{fields(result.review_manifest)}</div>
      {reports(result.initial_review, "Initial deterministic review")}
      {reports(Object.fromEntries(Object.entries(result.reports).filter(([name]) => ["run_review.md", "agent_review.md", "next_actions.md"].includes(name))), "Post-consolidation review")}
    </>}
    {view === "prioritized-evidence" && <>
      <div className={styles.panel}><h2>{result.evidence_matrix.length} candidates → {result.prioritized_evidence.length} selected</h2><p>Ranking is a heuristic review aid, not clinical importance, truth, eligibility, or professional judgment. Global cap 25; document cap 12; content-type cap 5. Exact denial rows bypass only the content-type cap. Ties retain input order.</p><p>Score = source authority + functional impact + system relevance + actionability + trunc(existing evidence strength / 8).</p></div>
      {rows("Selected evidence", result.prioritized_evidence)}
      <h2>All candidates · V2 instrumentation</h2><p>Components call recovered scoring functions. Selection reasons explain the recovered selector; display indices are not historical provenance.</p>
      {result.instrumentation.ranking_trace.map((row, index) => <article key={index} className={styles.panel}><h3>Candidate rank {text(row.candidate_rank)} · {text(row.source_document)}</h3><p>Score {text(row.score)} · {text(row.selection_reason)}</p>{references(row)}{fields(row)}</article>)}
    </>}
    {view === "capacity-themes" && <>
      <div className={styles.panel}><h2>Two recovered groupings</h2><p>The initial review uses a different first-match classifier. Later consolidation exposes eight theme families; its ten-theme guard is structurally unreachable under that classifier. Template wording can itself trigger themes.</p><h3>Initial review grouping</h3><pre>{text(result.instrumentation.initial_review_theme_groups)}</pre></div>
      {rows("Consolidated capacity themes", result.capacity_themes)}
      <details className={styles.panel}><summary>V2 instrumentation · contributing V1 window indices</summary><pre>{text(result.instrumentation.consolidation_window_membership)}</pre></details>
    </>}
    {view === "denials" && <>
      <div className={styles.panel}><h2>Denial presence is distinct from mapping existence</h2><p>Historical raw mapping exists: {Object.keys(result.raw_denial_mapping).length ? "YES" : "NO"}</p><p>Actual classified denial source present: {result.actual_denial_source_present ? "YES" : "NO"}</p><p>V2 interpretation: a mapping object and its fixed suggested action do not establish a payer decision or authorize action.</p>{fields(result.raw_denial_mapping)}</div>
      {rows("Consolidated bottlenecks", result.bottlenecks)}{rows("Raw bottleneck candidates", result.bottlenecks_raw)}
    </>}
    {view === "final-review" && <>
      <div className={styles.panel}><h2>Ordinary reports, not final synthesis</h2><p>Final-synthesis generation remains unestablished. These texts were generated from this run’s evidence and sources. Historical prose may overstate evidence or suggest actions; nothing is accepted, verified, executed, or persisted. No clinical, disability, legal, or benefits determination is made.</p></div>
      {reports(result.reports, "Generated V1.1 reports")}
    </>}
  </section>;
}
