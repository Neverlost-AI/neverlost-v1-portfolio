import Link from "next/link";
import { Icon } from "@/components/icon";
import { bottlenecks, capacityWindows, hiddenStates, evidenceById, formatDemoDate, type EvidenceItem } from "@/lib/demo-data";

export const conceptCopy = {
  "Hidden States": {
    description: "A possible explanation is not an observed fact.",
    title: "Make uncertainty visible.",
    explanation: "Hidden states represent candidate conditions that may help explain an observation. This sample keeps the recorded note separate from a possible interpretation; it does not detect or verify a hidden state.",
    boundary: "Missing information is not proof of an underlying condition.",
  },
  "Bottlenecks": {
    description: "A candidate constraint. A question small enough to inspect.",
    title: "Name the gap, keep the question open.",
    explanation: "Bottlenecks represent possible constraints on a next step. These fixtures pair an unresolved detail with a small question for human review, not an assigned task or an approved course of action.",
    boundary: "No owner is assigned, no action is executed, and no resolution is inferred.",
  },
  "Capacity Windows": {
    description: "A recorded activity is not a measure of sustained capacity.",
    title: "Keep the limits of an observation in view.",
    explanation: "Capacity windows draw attention to activity in context and what remains unknown about repeatability or retained gains. These fixtures are candidate windows, not measured durations, forecasts, or recommendations.",
    boundary: "Unknown retained gains remain unknown. No capacity score or improvement is inferred.",
  },
} as const;
export type ConceptName = keyof typeof conceptCopy;

const conceptLinks = [
  { label: "Hidden States", href: "/hidden-states" },
  { label: "Bottlenecks", href: "/bottlenecks" },
  { label: "Capacity Windows", href: "/capacity-windows" },
] as const;

export function ConceptView({ view, openSource }: { view: ConceptName; openSource: (item: EvidenceItem) => void }) {
  const copy = conceptCopy[view];
  const items = view === "Hidden States" ? hiddenStates : view === "Bottlenecks" ? bottlenecks : capacityWindows;
  return <div className="concept-view">
    <section className="concept-intro panel" aria-labelledby="concept-title">
      <p className="eyebrow">ANALYTICAL CONCEPT / STATIC ILLUSTRATION</p>
      <h2 id="concept-title">{copy.title}</h2>
      <p>{copy.explanation}</p>
      <div className="concept-boundary"><Icon name="info" /><span>{copy.boundary}</span></div>
    </section>
    <nav className="concept-navigation" aria-label="Analytical concept views">
      {conceptLinks.map((link, index) => <Link key={link.href} href={link.href} aria-current={link.label === view ? "page" : undefined}><span className="path-number">0{index + 1}</span>{link.label}<Icon name="chevron" width="14" height="14" /></Link>)}
    </nav>
    <p className="concept-reading-note">Reading order only — not an execution pipeline or a claim of causation between categories.</p>
    <section aria-labelledby="candidate-title">
      <div className="section-heading concept-list-heading"><h2 id="candidate-title">Synthetic candidates</h2><span className="quiet-tag">{items.length} IN THIS SAMPLE</span></div>
      <div className="concept-cards">
        {items.map((item) => {
          const record = evidenceById(item.evidenceId);
          return <article className="panel concept-card" key={item.id} aria-labelledby={item.id}>
            <header className="concept-card-header"><div><p className="eyebrow">{item.id} · {record.date}</p><h3 id={item.id}>{item.title}</h3></div><span className="status-tag needs-review">{item.status}</span></header>
            <div className="concept-columns">
              <section className="concept-cell">
                <p className="eyebrow">01 / RECORDED OBSERVATION</p>
                <blockquote>{record.source.excerpt}</blockquote>
                <p className="concept-record-date">Invented note · <time dateTime={record.date}>{formatDemoDate(record.date)}</time></p>
              </section>
              <section className="concept-cell concept-candidate">
                <p className="eyebrow">02 / CANDIDATE CONTEXT</p>
                {"owner" in item ? <dl><div><dt>Owner</dt><dd>{item.owner}</dd></div><div><dt>Next smallest action · fixture question only</dt><dd>{item.nextSmallestAction}</dd></div></dl>
                  : "retainedGains" in item ? <dl><div><dt>Retained gains</dt><dd>{item.retainedGains}</dd></div><div><dt>Capacity status</dt><dd>{item.status}</dd></div></dl>
                  : <><p>{item.title}</p><p className="concept-caution">{item.status}. This is an interpretation, not a diagnosis or a confirmed condition.</p></>}
              </section>
              <section className="concept-cell">
                <p className="eyebrow">03 / INTERPRETATION & LIMITATION</p>
                <p>{record.interpretation}</p>
                <span className="quiet-tag">Human review required</span>
              </section>
            </div>
            <footer className="concept-source">
              <div><span className="source-filename">{record.source.document}</span><span className="source-location">{record.id} · p. {record.source.page} · {record.source.chunkId}</span><span className="source-location">{record.source.sourceType} · {record.kind}</span></div>
              <button className="primary-button" onClick={() => openSource(record)} aria-label={`Inspect source for ${item.id}`}>Inspect source<Icon name="source" width="16" height="16" /></button>
            </footer>
          </article>;
        })}
      </div>
    </section>
  </div>;
}
