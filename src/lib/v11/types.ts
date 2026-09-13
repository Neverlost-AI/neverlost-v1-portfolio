export type SourceType = "OT record" | "PT record" | "health-system/provider record" | "insurance denial letter" | "disability appeal" | "function report" | "unknown";
export interface DemoDocument {
  id: string;
  name: string;
  page: number;
  chunkId: string;
  excerpt: string;
  extraction: "Synthetic text" | "Simulated OCR";
}
export interface DemoEvidence {
  id: string;
  documentId: string;
  observation: string;
  interpretation: string;
  confidence: "high" | "low" | "unknown";
  declaredType?: SourceType;
}
export interface Scenario {
  id: string;
  title: string;
  description: string;
  documents: readonly DemoDocument[];
  evidence: readonly DemoEvidence[];
  candidateWindows: readonly { id: string; evidenceId: string }[];
}
