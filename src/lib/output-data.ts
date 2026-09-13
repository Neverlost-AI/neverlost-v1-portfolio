import { evidenceById } from "@/lib/demo-data";

// Historical domain names; these are review lenses, not inferred diagnoses.
// Assignments below are hand-authored presentation annotations, not V1 output.
export const historicalDomains = [
  "ADL", "IADL", "mobility", "endurance", "cognition", "autonomic symptoms",
  "pain", "joint stability", "PT/rehabilitation", "treatment response",
  "care coordination", "disability process", "insurance/authorization",
  "provider support", "administrative metadata",
] as const;
export type HistoricalDomain = typeof historicalDomains[number];

export interface MatrixAnnotation {
  evidenceId: string;
  domains: readonly HistoricalDomain[];
  functionalConsequence: string | null;
  systemRelevance: string;
  nextAvailableOpportunity: string | null;
  missingEvidence: string;
}
export const matrixAnnotations: readonly MatrixAnnotation[] = [
  { evidenceId: "DEMO-E01", domains: ["care coordination"], functionalConsequence: null,
    systemRelevance: "An open follow-up request needs context before completion can be assumed.",
    nextAvailableOpportunity: "Check whether a date was agreed.",
    missingEvidence: "Follow-up date and confirmation of completion are not recorded." },
  { evidenceId: "DEMO-E02", domains: ["endurance"], functionalConsequence: "Only one short task with a break is described; sustained activity is not established.",
    systemRelevance: "A limited activity observation can inform a repeatability question.",
    nextAvailableOpportunity: null,
    missingEvidence: "Task duration and a repeat observation are not included in this note." },
  { evidenceId: "DEMO-E03", domains: ["care coordination"], functionalConsequence: null,
    systemRelevance: "Unclear ownership is a candidate coordination gap, not proof that no owner exists.",
    nextAvailableOpportunity: "Ask who owns the follow-up.",
    missingEvidence: "The next-step owner is not named in this note." },
  { evidenceId: "DEMO-E04", domains: ["endurance"], functionalConsequence: null,
    systemRelevance: "A second task description leaves sustained capacity unresolved.",
    nextAvailableOpportunity: null,
    missingEvidence: "Duration, repeatability, and retained gains are unknown." },
];
export function matrixByEvidenceId(id: string): MatrixAnnotation {
  const row = matrixAnnotations.find((entry) => entry.evidenceId === id);
  if (!row) throw new Error(`Missing synthetic matrix annotation: ${id}`);
  evidenceById(id);
  return row;
}

export const outputCopy = {
  Timeline: { title: "Context unfolds over time.", description: "Longitudinal observations, with interpretations kept separate.",
    explanation: "Four invented events in date order. The historical V1 timeline organized source-linked events; this view reads static fixtures and does not extract events or reach clinical conclusions." },
  "Evidence Matrix": { title: "Keep the evidence chain intact.", description: "Record fact, functional consequence, system relevance, and an open question.",
    explanation: "Historical V1 organized evidence across functional domains and source types. This sample uses hand-authored review lenses, not executed classification. An empty domain means no sample evidence, not absence of a condition." },
  Reports: { title: "Structured output. Human judgment.", description: "Readable drafts traced back to the sample and its sources.",
    explanation: "Historical V1 rendered analytical artifacts as Markdown reports. These in-page previews illustrate that output layer using static synthetic data. They are not historical report files or generated clinical conclusions." },
} as const;
export type OutputName = keyof typeof outputCopy;
