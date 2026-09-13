"use client";

import { useRef, useState } from "react";
import { Icon, type IconName } from "@/components/icon";
import {
  bottlenecks, capacityWindows, DISCLAIMER, evidence, evidenceById,
  formatDemoDate, hiddenStates, HISTORICAL_SOURCE_URL, navigation, reports, timeline,
  type EvidenceItem,
} from "@/lib/demo-data";

type Filter = "All evidence" | "Direct source" | "Interpretation";

function Wordmark() {
  return <div className="wordmark"><svg aria-hidden="true" width="30" height="30" viewBox="0 0 32 32" fill="none"><path d="M6 25V7l20 18V7" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" /><circle cx="26" cy="7" r="3" fill="currentColor" /></svg><span>neverlost<span className="wordmark-dot">.</span></span></div>;
}

function Navigation() {
  return <nav aria-label="Demo views">
    {navigation.map((item) => item.available
      ? <a key={item.label} className="nav-item active" href="#overview" aria-current="page"><Icon name={item.icon} /><span>{item.label}</span><span className="active-mark" /></a>
      : <button key={item.label} className="nav-item" disabled title={`${item.label} view is not built in this milestone`}><Icon name={item.icon} /><span>{item.label}</span><span className="nav-planned">Later</span></button>)}
  </nav>;
}

export function Overview() {
  const [filter, setFilter] = useState<Filter>("All evidence");
  const [selectedEvidence, setSelectedEvidence] = useState<EvidenceItem>(evidence[0]);
  const [dialogMode, setDialogMode] = useState<"source" | "about">("source");
  const dialogRef = useRef<HTMLDialogElement>(null);
  const visibleEvidence = evidence.filter((item) => filter === "All evidence" || item.kind === filter);

  function openSource(item: EvidenceItem) {
    setSelectedEvidence(item);
    setDialogMode("source");
    dialogRef.current?.showModal();
  }

  function openAbout() {
    setDialogMode("about");
    dialogRef.current?.showModal();
  }

  const stats: { label: string; value: number; note: string; icon: IconName }[] = [
    { label: "Source documents", value: new Set(evidence.map((item) => item.source.document)).size, note: "Invented notes only", icon: "reports" },
    { label: "Evidence entries", value: evidence.length, note: "Each linked to a source", icon: "evidence" },
    { label: "Candidate bottlenecks", value: bottlenecks.length, note: "Awaiting human review", icon: "bottleneck" },
    { label: "Capacity windows", value: capacityWindows.length, note: "Candidates, not outcomes", icon: "capacity" },
  ];

  return <div className="app-shell">
    <a className="skip-link" href="#main-content">Skip to content</a>
    <aside className="sidebar">
      <a className="brand-link" href="#overview" aria-label="Neverlost demo overview"><Wordmark /></a>
      <div className="workspace-label"><span className="version-square">V1</span><div>Healthcare Roadmap<small>Historical prototype</small></div></div>
      <p className="nav-heading">WORKSPACE</p>
      <Navigation />
      <p className="nav-scope">Overview is ready to explore.<br />Remaining views are planned.</p>
      <div className="sidebar-bottom">
        <div className="archive-note"><span className="archive-symbol">↳</span><p>A preserved beginning.<small>June 2026 · Python prototype</small></p></div>
        <a className="source-link" href={HISTORICAL_SOURCE_URL} target="_blank" rel="noreferrer">Historical source <Icon name="external" width="14" height="14" /></a>
        <div className="sidebar-edition"><span>PORTFOLIO EDITION</span><span>01</span></div>
      </div>
    </aside>

    <div className="workspace" id="overview">
      <header className="topbar">
        <div className="breadcrumb"><span>Neverlost V1</span><span className="breadcrumb-slash">/</span><span>Overview</span></div>
        <div className="topbar-actions"><span className="static-label"><span />Static demonstration</span><button className="about-button" onClick={openAbout}><Icon name="info" width="16" height="16" /><span>About this demo</span></button></div>
      </header>
      <div className="mobile-brand"><Wordmark /><span className="tag">V1 / DEMO</span></div>
      <details className="mobile-navigation"><summary>Overview <span>Browse categories</span><Icon name="chevron" width="16" height="16" /></summary><Navigation /><p>Only the Overview is implemented in this milestone.</p></details>

      <main id="main-content">
        <div className="page-heading"><div><p className="eyebrow">THE HEALTHCARE ROADMAP / V1</p><h1>Overview<span className="heading-period">.</span></h1><p className="page-description">A source-linked perspective. A human-reviewed next step.</p></div><span className="sample-label">SAMPLE WORKSPACE <span>01</span></span></div>

        <div className="disclaimer" role="note"><Icon name="info" width="17" height="17" /><p>{DISCLAIMER}</p></div>

        <section className="hero" aria-labelledby="hero-title">
          <div className="hero-copy"><span className="hero-kicker"><span className="small-line" />CONTEXT BEFORE CONCLUSIONS</span><h2 id="hero-title">From scattered records<br />to a clearer picture.</h2><p>An interface study of the original healthcare prototype. Explore a hand-authored sample, with the source and its interpretation kept in view.</p><a className="primary-button" href="#evidence">Inspect sample evidence <Icon name="arrow" width="17" height="17" /></a><span className="hero-footnote">Presentation only. No records are processed.</span></div>
          <div className="hero-path" aria-label="Historical review model, illustrated only">
            <div className="path-label">THE REVIEW MODEL <span>01 — 03</span></div>
            <ol>
              <li><span className="path-number">01</span><div><strong>Start with the source</strong><p>Document · page · chunk</p></div><Icon name="reports" /></li>
              <li><span className="path-number">02</span><div><strong>Keep candidates separate</strong><p>Evidence is not interpretation</p></div><Icon name="evidence" /></li>
              <li><span className="path-number">03</span><div><strong>Leave judgment to people</strong><p>Review before taking action</p></div><Icon name="source" /></li>
            </ol>
            <div className="path-footer"><span className="tiny-square" />Traceable references. Not verified conclusions.</div>
          </div>
        </section>

        <section className="stats-grid" aria-label="Synthetic sample counts">
          {stats.map((stat) => <article className="stat-card" key={stat.label}><div className="stat-top"><span>{stat.label}</span><Icon name={stat.icon} width="18" height="18" /></div><div className="stat-value">{String(stat.value).padStart(2, "0")}<span>IN THIS SAMPLE</span></div><p>{stat.note}</p></article>)}
        </section>

        <div className="overview-grid">
          <section className="panel timeline-panel" aria-labelledby="timeline-title">
            <div className="section-heading"><div><p className="eyebrow">THE RECORD, IN SEQUENCE</p><h2 id="timeline-title">A small timeline of context</h2></div><span className="quiet-tag">Jun 03–14</span></div>
            <p className="section-description">Four invented events. No personal history.</p>
            <ol className="timeline-preview">
              {timeline.map((event, index) => <li key={event.id}><div className="timeline-marker"><span>{String(index + 1).padStart(2, "0")}</span></div><time dateTime={event.date}>{formatDemoDate(event.date)}</time><h3>{event.label}</h3><button className="text-link" onClick={() => openSource(evidenceById(event.evidenceId))} aria-label={`Inspect source for ${event.label}`}>{event.evidenceId}<Icon name="source" width="13" height="13" /></button></li>)}
            </ol>
            <div className="panel-bottom"><Icon name="info" width="14" height="14" /><span>Dates belong to this invented example, not an actual record.</span></div>
          </section>

          <section className="panel attention-panel" aria-labelledby="attention-title">
            <div className="section-heading"><div><p className="eyebrow">KEEP THE GAPS VISIBLE</p><h2 id="attention-title">For a human to review</h2></div><span className="count-badge">{bottlenecks.length}</span></div>
            <p className="section-description">Candidate questions, not instructions.</p>
            <div className="review-list">{bottlenecks.map((item) => <button className="review-item" onClick={() => openSource(evidenceById(item.evidenceId))} key={item.id}><span className="review-dot" /><span><strong>{item.title}</strong><small>{item.owner} · {item.evidenceId}</small></span><Icon name="chevron" width="15" height="15" /></button>)}</div>
          </section>
        </div>

        <section className="panel evidence-panel" aria-labelledby="evidence-title" id="evidence">
          <div className="section-heading evidence-heading"><div><p className="eyebrow">A LOOK INSIDE THE SAMPLE</p><h2 id="evidence-title">Evidence, with its context.</h2><p className="section-description">Inspect an entry to see its complete synthetic source reference.</p></div><span className="quiet-tag"><Icon name="source" width="13" height="13" />Source-linked sample</span></div>
          <div className="table-tools"><div className="filters" role="group" aria-label="Filter evidence">{(["All evidence", "Direct source", "Interpretation"] as const).map((label) => <button key={label} aria-pressed={filter === label} onClick={() => setFilter(label)}>{label}{label === "All evidence" && <span>{evidence.length}</span>}</button>)}</div><p className="result-count" aria-live="polite">{visibleEvidence.length} of {evidence.length} entries</p></div>
          <div className="table-scroll" role="region" aria-label="Synthetic evidence table" tabIndex={0}>
            <table><caption className="sr-only">Synthetic evidence preview. Source-linked does not mean independently verified.</caption><thead><tr><th scope="col">Evidence entry</th><th scope="col">Source reference</th><th scope="col">Review status</th><th scope="col"><span className="sr-only">Inspect entry</span></th></tr></thead><tbody>
              {visibleEvidence.map((item) => <tr key={item.id}><td><div className="entry-title">{item.title}</div><div className="entry-meta"><span>{item.id}</span><span className="meta-dot">·</span>{item.kind}<span className="meta-dot">·</span>{formatDemoDate(item.date)}</div></td><td><span className="source-filename">{item.source.document}</span><span className="source-location">p. {item.source.page} <span>·</span> {item.source.chunkId}</span></td><td><span className={`status-tag ${item.reviewStatus === "Needs review" ? "needs-review" : "source-linked"}`}><span />{item.reviewStatus}</span></td><td><button className="inspect-button" onClick={() => openSource(item)} aria-label={`Inspect ${item.id}: ${item.title}`}><Icon name="arrow" width="18" height="18" /></button></td></tr>)}
            </tbody></table>
          </div>
          <div className="evidence-footer"><span><span className="tiny-square" />All entries are synthetic and require human review.</span><span>No uploads. No background processing.</span></div>
        </section>

        <section className="scope-strip" aria-label="Milestone scope"><Icon name="overview" /><div><strong>One overview. A deliberately limited demonstration.</strong><p>The fixtures also include {hiddenStates.length} candidate hidden state and {reports.length} report categories. Their dedicated views, along with the other planned categories, are not built yet.</p></div><span className="tag">MILESTONE 01</span></section>
        <footer className="page-footer"><span>Neverlost V1 <span className="footer-divider">/</span> Portfolio presentation layer</span><span>New interface · September 2026</span></footer>
      </main>
    </div>

    <dialog ref={dialogRef} className="detail-dialog" aria-labelledby="dialog-title">
      <div className="dialog-header"><span className="eyebrow">{dialogMode === "source" ? "SYNTHETIC PROVENANCE" : "PRESENTATION BOUNDARY"}</span><button className="close-button" onClick={() => dialogRef.current?.close()} aria-label="Close dialog"><Icon name="close" /></button></div>
      {dialogMode === "source" ? <>
        <h2 id="dialog-title">{selectedEvidence.title}</h2>
        <span className="dialog-entry-id">{selectedEvidence.id} · {selectedEvidence.kind}</span>
        <div className="source-quote"><span className="eyebrow">INVENTED SOURCE EXCERPT</span><blockquote>{selectedEvidence.source.excerpt}</blockquote></div>
        <dl className="provenance-fields"><div><dt>Document</dt><dd>{selectedEvidence.source.document}</dd></div><div><dt>Page</dt><dd>{selectedEvidence.source.page}</dd></div><div><dt>Chunk ID</dt><dd>{selectedEvidence.source.chunkId}</dd></div><div><dt>Source type</dt><dd>{selectedEvidence.source.sourceType}</dd></div><div><dt>Event date</dt><dd>{selectedEvidence.date}</dd></div><div><dt>Category</dt><dd>{selectedEvidence.category}</dd></div><div><dt>Review status</dt><dd>{selectedEvidence.reviewStatus}</dd></div></dl>
        <div className="interpretation-note"><strong>Interpretation & limitation</strong><p>{selectedEvidence.interpretation}</p></div>
        <p className="dialog-footnote">Every field is hand-authored synthetic data. Source references describe the fixture; they are not authenticated provenance or downloadable historical records.</p>
      </> : <>
        <h2 id="dialog-title">A new window into an old prototype.</h2>
        <p className="about-lead">This is a standalone portfolio interface, built in September 2026. It is not the historical June Python application and does not run its pipeline.</p>
        <ul className="about-list"><li>All displayed records and source excerpts are invented.</li><li>No authentication, database, API keys, uploads, or record processing.</li><li>No LLM execution, autonomous agents, durable state, or clinical validation.</li><li>Only the Overview is implemented. Filters and dialogs are temporary browser interactions, not saved review decisions.</li></ul>
        <p className="dialog-footnote">{DISCLAIMER}</p>
        <a className="primary-button" href={HISTORICAL_SOURCE_URL} target="_blank" rel="noreferrer">Read the historical source <Icon name="external" width="16" height="16" /></a>
      </>}
    </dialog>
  </div>;
}
