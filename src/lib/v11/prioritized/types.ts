import type { SourceType } from "../types";
export interface Candidate {
  id: string;
  source: { document: string; page: number; chunk: string; excerpt: string; type: SourceType; authority: string };
  contentType: string;
  domains: readonly string[];
  fact: string;
  consequence: string;
  relevance: string;
  why: string;
  opportunity: string;
  missing: string;
  supports: { disability: boolean; treatment: boolean; referral: boolean; authorization: boolean };
  confidence: "high" | "medium" | "low" | "unknown";
  strength: number;
}
export interface Bottleneck {
  id: string; title: string; needed: string; next: string; sources: readonly string[];
}
export interface PriorityScenario {
  id: string; title: string; description: string; rows: readonly Candidate[]; bottlenecks: readonly Bottleneck[];
}
export const reference = (row: Candidate) => `${row.source.document} (p. ${row.source.page} · ${row.source.chunk})`;

