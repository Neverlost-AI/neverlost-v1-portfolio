export type Json = string | number | boolean | null | Json[] | { [key: string]: Json };
export type Row = { [key: string]: Json };
export type Source = {
  document_id: string; filename: string; synthetic: true; source_type: string;
  expected_page_count: number; description: string; fixture_version: string; sha256: string;
  pages?: { page: number | null; text: string; text_extraction_method: string }[];
};
export type SyntheticCase = { case_id: string; title: string; description: string; documents: Source[] };
export type Run = {
  v1_1?: {
    engine_identity: string; adaptation_identity: string; upstream_v1_sha256: string;
    result_sha256: string; document_statuses: Row[]; evidence_matrix: Row[];
    bottlenecks_raw: Row[]; bottlenecks: Row[]; review_manifest: Row;
    initial_review: Record<string, string>; prioritized_evidence: Row[];
    capacity_themes: Row[]; raw_denial_mapping: Row; actual_denial_source_present: boolean;
    reports: Record<string, string>; warnings: string[];
    instrumentation: { ranking_trace: Row[]; initial_review_theme_groups: Json;
      consolidation_window_membership: Row[]; source_authority_strict_helper: boolean };
  };
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
  ["source-authority", "Source Authority / Evidence", ""],
  ["run-review", "Run Review", ""], ["prioritized-evidence", "Prioritized Evidence", ""],
  ["capacity-themes", "Capacity Themes", ""], ["denials", "Denials & Bottlenecks", ""],
  ["final-review", "Final Review / Reports", ""],
] as const;
