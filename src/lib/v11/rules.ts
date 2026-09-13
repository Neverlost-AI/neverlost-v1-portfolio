import type { DemoDocument, DemoEvidence, Scenario, SourceType } from "./types";

const has = (text: string, terms: readonly string[]) => terms.some((term) => text.includes(term));
const authority: Record<SourceType, string> = {
  "OT record": "Provider / occupational therapy functional evidence",
  "PT record": "Provider / physical therapy evidence",
  "health-system/provider record": "Provider-authored medical evidence",
  "insurance denial letter": "Payer / insurance decision evidence",
  "function report": "Claimant functional evidence",
  "disability appeal": "Claimant appeal / process evidence",
  unknown: "Unknown source authority",
};
// New implementation of selected generic rules, not copied historical source.
// Identifying name aliases and batch-specific configuration are deliberately absent.
export function classify(document: DemoDocument) {
  const name = document.name.toLowerCase();
  const content = document.excerpt.toLowerCase();
  const text = name + " " + content;
  let type: SourceType = "unknown";
  let basis = "No supported source marker matched; author remains unknown.";
  const providerContext = has(name, ["occupational therapy", "occupational-therapy", "physical therapy", "physical-therapy", "health record", "health-record"]);
  const payerDecision = has(text, ["insurance", "payer", "health plan"]) && has(text, ["denial", "denied", "not medically necessary", "utilization review"]);
  if (has(name, ["insurance denial", "insurance-denial"]) || (payerDecision && !providerContext)) {
    type = "insurance denial letter"; basis = "Payer/decision markers with no provider filename context, or an explicit denial filename.";
  } else if (name.includes("appeal")) {
    type = "disability appeal"; basis = "Claimant appeal filename marker.";
  } else if (has(name, ["function report", "function-report"])) {
    type = "function report"; basis = "Functional-report filename marker.";
  } else if (has(name, ["physical therapy", "physical-therapy"]) || /\bpt\b/.test(name)) {
    type = "PT record"; basis = "Physical-therapy filename marker.";
  } else if (has(name, ["occupational therapy", "occupational-therapy"]) || /\bot\b/.test(name)) {
    type = "OT record"; basis = "Occupational-therapy filename marker; insurance subject matter does not change the source label.";
  } else if (has(name, ["health record", "health-record"])) {
    type = "health-system/provider record"; basis = "Generic health-record filename marker.";
  } else if (has(content, ["not medically necessary", "utilization review", "appeal rights", "medical necessity criteria"])) {
    type = "insurance denial letter"; basis = "Generic payer-decision content marker; heuristic attribution only.";
  } else if (content.includes("health record")) {
    type = "health-system/provider record"; basis = "Generic health-record content marker.";
  } else if (content.includes("occupational therapy")) {
    type = "OT record"; basis = "Occupational-therapy content marker.";
  }
  const insuranceMention = has(text, ["insurance", "authorization", "denial", "denied", "coverage", "appeal"]);
  const service = insuranceMention && has(text, ["occupational therapy", "occupational-therapy", "ot visits"])
    ? "Occupational therapy visits" : insuranceMention && has(text, ["physical therapy", "physical-therapy", "pt visits"])
      ? "Physical therapy visits" : null;
  return {
    type, basis, authority: authority[type],
    payer: insuranceMention && text.includes("sample plan") ? "Sample Plan (fictional)" : null,
    service,
    context: type === "insurance denial letter" ? "Payer-source denial context; rationale is not a verified determination."
      : insuranceMention ? "Insurance is mentioned inside another source type; do not relabel it as payer evidence."
        : "No insurance context identified.",
  };
}
export function documentFor(scenario: Scenario, row: DemoEvidence): DemoDocument {
  const document = scenario.documents.find((item) => item.id === row.documentId);
  if (!document) throw new Error(`Unresolved synthetic document reference: ${row.documentId}`);
  return document;
}
export interface Warning { code: string; message: string; basis: string; documentId?: string }
export function review(scenario: Scenario) {
  const documents = scenario.documents.map((document) => {
    const classification = classify(document);
    const rows = scenario.evidence.filter((row) => row.documentId === document.id);
    const warnings: Warning[] = [];
    if (classification.type === "unknown") warnings.push({ code: "unknown-source", message: "Unknown source document type.", basis: "No supported source marker matched.", documentId: document.id });
    if (rows.some((row) => row.declaredType && row.declaredType !== classification.type)) warnings.push({ code: "classification-mismatch", message: "Evidence row type differs from document classification.", basis: "Supplied row label compared with computed document type; neither input is repaired.", documentId: document.id });
    if (document.extraction === "Simulated OCR") warnings.push({ code: "ocr-review", message: "Simulated OCR source needs a text accuracy spot-check.", basis: "Fixture OCR flag only; no OCR was executed.", documentId: document.id });
    return { document, classification, rowCount: rows.length, warnings };
  });
  scenario.evidence.forEach((row) => documentFor(scenario, row));
  const unknownCount = documents.filter((item) => item.classification.type === "unknown").length;
  const lowConfidenceCount = scenario.evidence.filter((row) => row.confidence === "low" || row.confidence === "unknown").length;
  const denialPresent = documents.some((item) => item.classification.type === "insurance denial letter");
  const hasInput = documents.length > 0;
  const warnings: Warning[] = documents.flatMap((item) => item.warnings);
  if (!hasInput) warnings.push({ code: "no-input", message: "No input supplied; classification is not assessed.", basis: "Zero synthetic documents." });
  if (lowConfidenceCount) warnings.push({ code: "confidence", message: `${lowConfidenceCount} low/unknown-confidence evidence row(s) need review.`, basis: "Fixture confidence labels, not calibrated probabilities." });
  if (scenario.evidence.length > 100) warnings.push({ code: "evidence-volume", message: `${scenario.evidence.length} evidence rows exceed the review-volume threshold.`, basis: "Recovered condition: more than 100 evidence rows." });
  if (scenario.candidateWindows.length > 20) warnings.push({ code: "window-volume", message: `${scenario.candidateWindows.length} candidate windows exceed the review-volume threshold.`, basis: "Recovered condition: more than 20 candidate windows; no themes are computed." });
  if (denialPresent) warnings.push({ code: "payer-review", message: "Payer rationale requires human comparison with provider/therapy evidence.", basis: "A payer-denial source was classified; no denial mapping is executed." });
  const actions: { title: string; basis: string; owner: string; urgency: string }[] = [];
  if (unknownCount) actions.push({ title: "Review unknown source classifications.", basis: `${unknownCount} unknown document(s).`, owner: "Human reviewer", urgency: "High" });
  if (scenario.evidence.length > 100) actions.push({ title: `Review the need to prioritize ${scenario.evidence.length} evidence rows.`, basis: "Evidence count > 100. Prioritization is outside M04.", owner: "Human reviewer", urgency: "High" });
  if (scenario.candidateWindows.length > 20) actions.push({ title: `Review the need to consolidate ${scenario.candidateWindows.length} candidate windows.`, basis: "Window count > 20. Capacity Themes is outside M04.", owner: "Human reviewer", urgency: "Medium" });
  if (denialPresent) actions.push({ title: "Inspect the payer rationale and supporting source context.", basis: "Payer-denial source present. Denial Mapping is outside M04.", owner: "Human reviewer / care coordination", urgency: "High" });
  const classificationStatus = !hasInput ? "Not assessed — no input" : documents.some((item) => item.warnings.some((warning) => ["unknown-source", "classification-mismatch"].includes(warning.code))) ? "Classification issues need review" : "No modeled classification issue detected";
  return { documents, warnings, actions: actions.slice(0, 3), unknownCount, lowConfidenceCount, denialPresent, classificationStatus };
}
