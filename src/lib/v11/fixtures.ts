import type { DemoDocument, DemoEvidence, Scenario } from "./types";

// Independently invented M04 input. Never imported from a historical record/output.
export const V11_DISCLAIMER = "Historical June 2026 prototype · Synthetic demonstration data · Not a clinical decision system · Human review required.";
export const RECONSTRUCTION = "New deterministic reconstruction of recovered V1.1 rules. This is not the historical V1.1 interface.";

const provider: DemoDocument = {
  id: "SYN11-D01", name: "synthetic-health-record.md", page: 1, chunkId: "SYN11-PROVIDER-001",
  excerpt: "Invented health record for a training exercise. The provider recorded a short practice task and a follow-up question. Sample Plan insurance authorization is mentioned; this provider note does not record a payer decision.",
  extraction: "Synthetic text",
};
const ot: DemoDocument = {
  id: "SYN11-D02", name: "synthetic-occupational-therapy.md", page: 2, chunkId: "SYN11-OT-001",
  excerpt: "Invented occupational therapy note. A practice organizing task required a break. The note mentions a Sample Plan insurance denial involving occupational therapy visits. This is a therapy observation, not the payer letter.",
  extraction: "Synthetic text",
};
const payer: DemoDocument = {
  id: "SYN11-D03", name: "synthetic-insurance-denial.md", page: 1, chunkId: "SYN11-PAYER-001",
  excerpt: "Invented Sample Plan payer letter for training only. Occupational therapy visits were denied because supporting documentation was described as incomplete. Therapy is the subject of the decision; this letter is not a therapy assessment. No appeal deadline is supplied.",
  extraction: "Synthetic text",
};
const unknown: DemoDocument = {
  id: "SYN11-D04", name: "synthetic-unlabeled-fragment.md", page: 3, chunkId: "SYN11-UNKNOWN-001",
  excerpt: "Invented fragment: a practice activity is mentioned, but its author and context are not identified. The missing context remains unresolved.",
  extraction: "Simulated OCR",
};
const observations: readonly DemoEvidence[] = [
  { id: "SYN11-E01", documentId: provider.id, observation: "A provider note describes a practice task and a follow-up question.", interpretation: "A mention of insurance does not make this a payer-authored decision.", confidence: "high" },
  { id: "SYN11-E02", documentId: ot.id, observation: "A therapy note records a break during a practice task.", interpretation: "The denial reference remains attributed to a therapy note; no payer decision is established by this note alone.", confidence: "low" },
  { id: "SYN11-E03", documentId: payer.id, observation: "A fictional payer letter describes a documentation-related denial.", interpretation: "A payer statement about therapy is not a provider assessment or an eligibility conclusion.", confidence: "high" },
  { id: "SYN11-E04", documentId: unknown.id, observation: "An unattributed fragment mentions an activity.", interpretation: "Do not infer an author, clinical finding, or sustained capacity.", confidence: "unknown" },
];
const loadRows: readonly DemoEvidence[] = Array.from({ length: 101 }, (_, i) => ({
  ...observations[0], id: `SYN11-LOAD-E${String(i + 1).padStart(3, "0")}`,
}));
export const scenarios: readonly Scenario[] = [
  { id: "mixed", title: "Mixed source sample", description: "Four independently invented documents. Source authority and subject matter are deliberately different. Confidence and extraction flags are synthetic inputs, not measured results.", documents: [provider, ot, payer, unknown], evidence: observations, candidateWindows: [] },
  { id: "no-denial", title: "No payer-denial source", description: "Provider and OT notes mention insurance, but no payer-authored denial letter is supplied. A mention is not a decision source.", documents: [provider, ot], evidence: observations.slice(0, 2), candidateWindows: [] },
  { id: "unknown", title: "Unknown source", description: "One unattributed fragment with a simulated OCR flag. No OCR is performed by this demo.", documents: [unknown], evidence: [observations[3]], candidateWindows: [] },
  { id: "conflict", title: "Classification mismatch", description: "An intentionally incorrect PT row label is supplied for the OT document. The reconstruction flags the mismatch without repairing the input.", documents: [ot], evidence: [{ ...observations[1], declaredType: "PT record" }], candidateWindows: [] },
  { id: "empty", title: "No input", description: "No documents, evidence rows, or candidate windows. Absence of input is not a passed validation.", documents: [], evidence: [], candidateWindows: [] },
  { id: "review-load", title: "Review-volume boundary", description: "101 synthetic rows deliberately repeat one invented observation; 21 candidate-window stubs exercise count thresholds only. They are not 101 independent observations, measured capacity, or processed historical records.", documents: [provider], evidence: loadRows, candidateWindows: Array.from({ length: 21 }, (_, i) => ({ id: `SYN11-LOAD-W${i + 1}`, evidenceId: loadRows[i].id })) },
];
export function scenarioById(id: string): Scenario {
  const result = scenarios.find((item) => item.id === id);
  if (!result) throw new Error("Unknown synthetic V1.1 scenario");
  return result;
}
