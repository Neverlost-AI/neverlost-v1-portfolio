/** Newly invented portfolio fixtures. No original records, outputs, or code are imported. */
export const DISCLAIMER =
  "Historical June 2026 prototype · Synthetic demonstration data · Not a clinical decision system · Human review required.";

export const HISTORICAL_SOURCE_URL =
  "https://github.com/Neverlost-AI/neverlost-v1/tree/dc038b06ed52a112ac853854df044250d46f2c49";

export const navigation = [
  { label: "Overview", icon: "overview", available: true },
  { label: "Timeline", icon: "timeline", available: false },
  { label: "Evidence Matrix", icon: "evidence", available: false },
  { label: "Hidden States", icon: "hidden", available: true },
  { label: "Bottlenecks", icon: "bottleneck", available: true },
  { label: "Capacity Windows", icon: "capacity", available: true },
  { label: "Reports", icon: "reports", available: false },
] as const;

export interface SourceReference {
  document: string;
  page: number;
  chunkId: string;
  sourceType: "Synthetic coordination note" | "Synthetic activity note";
  excerpt: string;
}

export interface EvidenceItem {
  id: string;
  date: string;
  title: string;
  category: "Care coordination" | "Daily activity" | "Follow-up";
  kind: "Direct source" | "Interpretation";
  reviewStatus: "Source-linked" | "Needs review";
  interpretation: string;
  source: SourceReference;
}

export const evidence: readonly EvidenceItem[] = [
  {
    id: "DEMO-E01",
    date: "2026-06-03",
    title: "A follow-up was requested",
    category: "Care coordination",
    kind: "Direct source",
    reviewStatus: "Source-linked",
    interpretation: "The note records a request, not a completed appointment.",
    source: {
      document: "synthetic-coordination-note.md",
      page: 1,
      chunkId: "DEMO-COORD-001",
      sourceType: "Synthetic coordination note",
      excerpt: "A follow-up conversation was requested. No date is recorded in this sample note.",
    },
  },
  {
    id: "DEMO-E02",
    date: "2026-06-06",
    title: "A short activity was recorded",
    category: "Daily activity",
    kind: "Direct source",
    reviewStatus: "Source-linked",
    interpretation: "One recorded activity does not establish sustained capacity.",
    source: {
      document: "synthetic-activity-note.md",
      page: 1,
      chunkId: "DEMO-ACTIVITY-001",
      sourceType: "Synthetic activity note",
      excerpt: "A short organizing task was completed with a break. No repeat observation is included.",
    },
  },
  {
    id: "DEMO-E03",
    date: "2026-06-10",
    title: "The next-step owner is unclear",
    category: "Care coordination",
    kind: "Interpretation",
    reviewStatus: "Needs review",
    interpretation: "Candidate ownership gap. Absence in this note is not proof that no owner exists.",
    source: {
      document: "synthetic-coordination-note.md",
      page: 2,
      chunkId: "DEMO-COORD-002",
      sourceType: "Synthetic coordination note",
      excerpt: "The sample follow-up remains open. This note does not name the next-step owner.",
    },
  },
  {
    id: "DEMO-E04",
    date: "2026-06-14",
    title: "A repeat observation may add context",
    category: "Follow-up",
    kind: "Interpretation",
    reviewStatus: "Needs review",
    interpretation: "A review question, not an inferred improvement or clinical recommendation.",
    source: {
      document: "synthetic-activity-note.md",
      page: 2,
      chunkId: "DEMO-ACTIVITY-002",
      sourceType: "Synthetic activity note",
      excerpt: "A second short task is described. Duration and repeatability are not documented.",
    },
  },
];

// Static category fixtures. Only the three analytical concept views are implemented.
export const timeline = [
  { id: "DEMO-T01", date: "2026-06-03", label: "Follow-up requested", evidenceId: "DEMO-E01" },
  { id: "DEMO-T02", date: "2026-06-06", label: "Activity noted", evidenceId: "DEMO-E02" },
  { id: "DEMO-T03", date: "2026-06-10", label: "Open loop noted", evidenceId: "DEMO-E03" },
  { id: "DEMO-T04", date: "2026-06-14", label: "Repeat observation", evidenceId: "DEMO-E04" },
] as const;

export const bottlenecks = [
  { id: "DEMO-B01", title: "Clarify next-step ownership", evidenceId: "DEMO-E03", owner: "Not recorded", nextSmallestAction: "Ask who owns the follow-up.", status: "Candidate — human review required" },
  { id: "DEMO-B02", title: "Confirm the follow-up date", evidenceId: "DEMO-E01", owner: "Not recorded", nextSmallestAction: "Check whether a date was agreed.", status: "Candidate — human review required" },
] as const;

export const hiddenStates = [
  { id: "DEMO-H01", title: "Possible coordination uncertainty", evidenceId: "DEMO-E03", status: "Candidate, not verified" },
] as const;

export const capacityWindows = [
  { id: "DEMO-C01", title: "Short activity window", evidenceId: "DEMO-E02", retainedGains: "Unknown", status: "Candidate, not measured capacity" },
  { id: "DEMO-C02", title: "Repeatability question", evidenceId: "DEMO-E04", retainedGains: "Unknown", status: "Candidate, not measured capacity" },
] as const;

export const reports = [
  { id: "DEMO-R01", title: "Timeline summary", evidenceIds: ["DEMO-E01", "DEMO-E02", "DEMO-E03", "DEMO-E04"], status: "Static category fixture; report view not built" },
  { id: "DEMO-R02", title: "Evidence summary", evidenceIds: ["DEMO-E01", "DEMO-E02", "DEMO-E03", "DEMO-E04"], status: "Static category fixture; report view not built" },
] as const;

export function evidenceById(id: string): EvidenceItem {
  const item = evidence.find((entry) => entry.id === id);
  if (!item) throw new Error(`Invalid synthetic evidence reference: ${id}`);
  return item;
}

export function formatDemoDate(date: string): string {
  return new Intl.DateTimeFormat("en-US", {
    month: "short", day: "2-digit", timeZone: "UTC",
  }).format(new Date(`${date}T12:00:00Z`));
}
