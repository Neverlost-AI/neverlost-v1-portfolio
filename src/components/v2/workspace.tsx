"use client";
import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import Image from "next/image";
import logo from "@/components/v11/nvlt-official-logo.svg";
import { surfaces, type Json, type Row, type Run, type Source, type SyntheticCase } from "@/lib/v2/contracts";
import { useRun } from "./run-context";
import { LiveV11 } from "./live-v11";
import styles from "./workspace.module.css";

function valueText(value: Json): string {
  if (value === null || value === "") return "Not supplied by the historical engine";
  return typeof value === "object" ? JSON.stringify(value, null, 2) : String(value);
}
function sourceFor(row: Row, run: Run): { source?: Source; chunk?: Row } {
  const nested = row.source && typeof row.source === "object" && !Array.isArray(row.source) ? row.source : {};
  const chunkId = row.source_page_or_chunk ?? nested.chunk_id;
  const chunk = run.artifacts.chunks.find((item) => item.chunk_id === chunkId);
  const filename = row.source_document ?? nested.document ?? chunk?.document;
  return { source: run.sources.find((item) => item.filename === filename), chunk };
}

export function V2Workspace({ view }: { view: string }) {
  const { run, setRun } = useRun();
  const [cases, setCases] = useState<SyntheticCase[]>([]);
  const [caseId, setCaseId] = useState(run?.case_id ?? "case_001");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [inspected, setInspected] = useState<{ source: Source; chunk?: Row } | null>(null);
  const dialog = useRef<HTMLDialogElement>(null);
  const opener = useRef<HTMLElement | null>(null);
  const current = surfaces.find(([key]) => key === view)!;

  useEffect(() => {
    const controller = new AbortController();
    fetch("/api/v2/cases", { signal: controller.signal, cache: "no-store" })
      .then(async (response) => {
        if (!response.ok) throw new Error("The Python service is unavailable. No fixture data is substituted.");
        const body = await response.json();
        setCases(body.cases);
      })
      .catch((failure) => { if (!controller.signal.aborted) setError(String(failure.message)); });
    return () => controller.abort();
  }, []);
  useEffect(() => {
    if (inspected && dialog.current && !dialog.current.open) dialog.current.showModal();
  }, [inspected]);

  function inspect(source: Source, chunk?: Row) {
    opener.current = document.activeElement as HTMLElement;
    setInspected({ source, chunk });
  }
  function closeSource() {
    dialog.current?.close();
    setInspected(null);
    opener.current?.focus();
  }
  async function analyze() {
    setBusy(true); setError(""); setRun(null);
    try {
      const response = await fetch("/api/v2/run", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ case_id: caseId }),
      });
      const result = await response.json();
      if (!response.ok) throw new Error(result.error ?? "Analysis failed.");
      setRun(result as Run);
    } catch (failure) {
      setError(failure instanceof Error ? failure.message : "Analysis failed. No fixture result was substituted.");
    } finally { setBusy(false); }
  }
  const selected = cases.find((item) => item.case_id === caseId);
  const rows = run && current[2] ? run.artifacts[current[2]] : [];
  return <div className={styles.shell}>
    <a className="skip-link" href="#v2-main">Skip to results</a>
    <header className={styles.header}>
      <Link href="/v2" className={styles.brand}><Image src={logo} alt="NVLT" width={48} height={48} /><span>Neverlost V2<small>Neverlost Systems · Longitudinal evidence analysis</small></span></Link>
    </header>
    <div className={styles.frame}>
      <nav className={styles.navigation} aria-label="V2 results">
        {surfaces.map(([key, label]) => <Link key={key} href={"/v2/" + key} aria-current={view === key ? "page" : undefined}>{label}</Link>)}
        <span>Source-linked analysis · Human review required</span>
      </nav>
      <main id="v2-main" className={styles.main}>
        <p className={styles.kicker}>LIVE EVIDENCE ANALYSIS / CURATED SYNTHETIC CASES</p>
        <h1>{current[1]}</h1>
        <p className={styles.notice}>Synthetic demonstration data · Not a clinical decision system · Human review required.</p>
        <p>Neverlost V2 analyzes records over time to produce source-linked timelines, evidence, bottleneck candidates, capacity windows, and reports. Live processing adds evidence prioritization, deterministic validation, and review tools. Explore a curated synthetic case, inspect its sources, and review the generated outputs.</p>
        <p className={styles.notice}>Engine provenance: preserved June 2026 V1 Python and recovered V1.1 processing. Results are generated on request; historical rules and limitations remain in effect.</p>
        <aside className={styles.warning}><strong>Historical limitations remain active.</strong> Keyword matching can misread negation, including “not approved.” Candidate names and report prose are historical output—not verified conclusions. V1.1 final-synthesis generation remains unestablished.</aside>
        {error && <p role="alert" className={styles.warning}>{error}</p>}
        {view === "run" && <section className={styles.panel} aria-labelledby="case-heading">
          <h2 id="case-heading">Choose an approved synthetic case</h2>
          <label htmlFor="case-select">Synthetic case</label>
          <select id="case-select" value={caseId} disabled={busy || !cases.length} onChange={(event) => { setCaseId(event.target.value); setRun(null); }}>
            {cases.map((item) => <option key={item.case_id} value={item.case_id}>{item.title}</option>)}
          </select>
          <p>{selected?.description ?? "Loading synthetic cases…"}</p>
          <details open><summary>Source manifest · {selected?.documents.length ?? 0} documents</summary>
            {selected?.documents.map((source) => <div key={source.document_id} className={styles.source}>
              <strong>{source.filename}</strong><p>{source.document_id} · {source.source_type} · Synthetic · Version {source.fixture_version} · {source.expected_page_count} page/text record</p>
              <p>{source.description}</p><code>SHA-256 {source.sha256}</code>
            </div>)}
          </details>
          <button className={styles.primary} disabled={busy || !selected} onClick={analyze}>{busy ? "Running analysis…" : "Run Neverlost Analysis"}</button>
          <p role="status">{busy ? "Executing in an isolated temporary workspace. Please wait." : run ? "Analysis complete. Generated results are available." : "No analysis has run. Arbitrary uploads are unavailable."}</p>
        </section>}
        {!run && view !== "run" && <section className={styles.panel}><h2>No live run in this browser session</h2><p>Run a curated case to see actual output. Refresh discards ephemeral results; it does not recover a saved case.</p><Link href="/v2/run">Choose a synthetic case</Link></section>}
        {run && <>
          <section className={styles.panel} aria-labelledby="ledger-heading"><h2 id="ledger-heading">Run ledger</h2>
            <dl className={styles.ledger}>
              <dt>Run ID</dt><dd>{run.run_id}</dd><dt>Synthetic case</dt><dd>{run.case_id}</dd>
              <dt>Execution</dt><dd>Completed · Real Python V1</dd><dt>Started</dt><dd>{run.started}</dd>
              <dt>Completed</dt><dd>{run.completed}</dd><dt>Engine SHA-256</dt><dd>{run.engine.v1}</dd>
              <dt>Result SHA-256</dt><dd>{run.result_sha256}</dd><dt>V1.1</dt><dd>{run.v1_1 ? "Recovered Python · Live second stage" : "Not integrated"}</dd>
            </dl>
            <div className={styles.metrics}>{Object.entries(run.counts).map(([key, count]) => <div key={key}><strong>{count}</strong><span>{key.replaceAll("_", " ")}</span></div>)}</div>
            <details><summary>Execution warnings and provenance limits</summary><ul>{run.warnings.map((warning) => <li key={warning}>{warning}</li>)}</ul></details>
          </section>
          {view === "run" && <section className={styles.panel}><h2>Generated outputs</h2><p>Use the navigation to inspect this run’s timeline, evidence, candidates and generated reports.</p><Link href="/v2/timeline">Inspect generated timeline →</Link></section>}
          {current[2] && <section aria-label={current[1] + " results"}>
            <h2>{rows.length} generated {rows.length === 1 ? "output" : "outputs"}</h2>
            {!rows.length && <p className={styles.panel}>The historical engine produced no rows for this surface. No substitute candidates have been invented.</p>}
            {rows.map((row, index) => {
              const reference = sourceFor(row, run);
              const title = row.state_change ?? row.current_bottleneck ?? row.capacity_window_created ?? row.event_type ?? row.evidence_content_type ?? row.provider_involved ?? "Evidence row";
              return <article key={index} className={styles.panel}>
                <p className={styles.kicker}>HISTORICAL RULE OUTPUT {index + 1} · HUMAN REVIEW REQUIRED</p>
                <h3>{valueText(title)}</h3>
                <p>{valueText(row.event_summary ?? row.record_fact ?? row.source_evidence ?? row.why_it_exists ?? row.intervention ?? null)}</p>
                {reference.source ? <button className={styles.secondary} onClick={() => inspect(reference.source!, reference.chunk)}>Inspect source · {reference.source.filename}</button> : <p>Historical source references, if supplied, are preserved below. No exact document/chunk link has been established for this row.</p>}
                <details><summary>All generated fields · observations and interpretations remain labeled</summary>
                  <dl>{Object.entries(row).map(([key, value]) => <div key={key} className={styles.field}><dt>{key.replaceAll("_", " ")}</dt><dd><pre>{valueText(value)}</pre></dd></div>)}</dl>
                </details>
              </article>;
            })}
          </section>}
          {view === "reports" && <section aria-label="Generated reports"><h2>{Object.keys(run.reports).length} generated Markdown reports</h2>
            <p>These are the actual ordinary V1 report-generator outputs, not a recovered V1.1 final-synthesis packet. Historical template prose is preserved and may exceed what this input establishes.</p>
            {Object.entries(run.reports).map(([name, content]) => <details key={name} className={styles.panel}><summary>{name}</summary><pre className={styles.report}>{content}</pre></details>)}
          </section>}
          <LiveV11 run={run} view={view} inspect={inspect} />
          <section className={styles.panel}><h2>Synthetic source library</h2><p>Original extracted text for this run. A text file has no historical page number; PDFs retain page numbers.</p>
            {run.sources.map((source) => <button key={source.document_id} className={styles.secondary} onClick={() => inspect(source)}>Inspect source · {source.filename}</button>)}
          </section>
        </>}
      </main>
    </div>
    <dialog ref={dialog} className={styles.dialog} aria-labelledby="source-title" onCancel={(event) => { event.preventDefault(); closeSource(); }}>
      {inspected && <><div className={styles.dialogHeading}><h2 id="source-title">{inspected.source.filename}</h2><button className={styles.secondary} onClick={closeSource}>Close source</button></div>
        <p>Synthetic source · {inspected.source.document_id} · {inspected.source.source_type}</p>
        <code>Source SHA-256: {inspected.source.sha256}</code>
        {inspected.chunk && <section><h3>Exact historical chunk</h3><p>{valueText(inspected.chunk.chunk_id)}</p><pre>{valueText(inspected.chunk.text)}</pre></section>}
        {inspected.source.pages?.map((page, index) => <section key={index}><h3>{page.page === null ? "Text record · page not supplied" : "Page " + page.page}</h3><p>Extraction: {page.text_extraction_method}</p><pre>{page.text}</pre></section>)}
      </>}
    </dialog>
  </div>;
}
