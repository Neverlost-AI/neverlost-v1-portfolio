export type Json = string | number | boolean | null | Json[] | { [key: string]: Json };
export type Row = { [key: string]: Json };
export type Source = {
  document_id: string; filename: string; synthetic: true; source_type: string;
  expected_page_count: number; description: string; fixture_version: string; sha256: string;
  pages?: { page: number | null; text: string; text_extraction_method: string }[];
};
export type SyntheticCase = { case_id: string; title: string; description: string; documents: Source[] };
export type Run = {
  run_id: string; case_id: string; status: "completed"; started: string; completed: string;
  engine: { v1: string; v1_1: string; runtime: string }; result_sha256: string;
  counts: Record<string, number>; warnings: string[]; artifacts: Record<string, Row[]>;
  reports: Record<string, string>; sources: Source[];
};
export const surfaces = [
  ["run", "Execution", ""], ["timeline", "Timeline", "timeline"],
  ["evidence", "Evidence", "evidence_matrix"], ["hidden-states", "Hidden States", "hidden_states"],
  ["trust-thresholds", "Trust Thresholds", "trust_thresholds"],
  ["bottlenecks", "Bottlenecks", "bottlenecks"], ["capacity", "Capacity Windows", "capacity_windows"],
  ["reports", "Reports", ""],
] as const;
