# Milestone 04 — V1.1 Foundation

This is a new deterministic reconstruction of selected recovered V1.1 rules, using independently invented synthetic fixtures. The browser interface is new, not a recovered historical V1.1 interface. V1 remains frozen at portfolio commit 0271ab2d4d996ea5edb696210765127fd503b418 except for the separate version entry.

## Evidence basis

The recovery repository's docs/v1-1-audit-summary.md, system-lineage.md, extensions.md, implementation-status.md, evidence-index.md and five-report-system.md distinguish a recovered direct code extension from applied documentary workflows. File comparison, not authenticated Git history, supports 21 unchanged source/schema files, three modified modules (build_evidence_matrix.py, detect_bottlenecks.py, generate_reports.py) and three added modules (light_agentic_review.py, prioritization_consolidation.py, run_batch_02_validation.py).

Read-only comparison with the recovered modules informed this fresh implementation. No historical Python source, private documents, outputs, identifying aliases, paths or batch inputs are copied into this project. The historical main and viewer did not invoke the added review layers. The batch runner did; its private orchestration is not reconstructed here.

## Implemented rules

- Source type/authority is distinct from subject matter. Generic filename and content markers distinguish provider, OT, PT, payer, claimant and unknown sources. Provider filename context prevents an insurance mention alone from relabeling a provider note as payer evidence.
- Only explicitly invented Sample Plan mentions produce a fictional payer label. OT/PT service context is shown separately. These heuristic labels do not authenticate authorship or establish a determination.
- Unknown sources remain unknown; no author is inferred from absence.
- Supplied row/document classification differences and simulated OCR flags produce document warnings. Low/unknown fixture confidence produces a review warning, not a probability estimate.
- More than 100 evidence rows and more than 20 candidate windows trigger volume warnings. Equality does not trigger them.
- A classified payer-denial document triggers payer-context review; a therapy note mentioning denial does not satisfy that condition.
- Conditional suggestions follow the initial recovered order: unknown source review, evidence prioritization review, window consolidation review, payer-context review; retain at most three. Suggestions are prose only, not executed actions or approval state.
- Every evidence row resolves to a document with an invented excerpt, page and chunk identifier. Observations and hand-authored interpretations remain separate.

Six scenarios cover mixed authority, no payer-denial source, unknown source, a deliberate classification conflict, empty input and volume boundaries. The volume fixture repeats one invented observation into 101 rows and references 21 window stubs solely to exercise thresholds; it is not 101 independent facts or computed capacity analysis. Scenario selection is ephemeral and resets on reload or navigation.

## Explicit deviations and preserved limitations

This is selective reconstruction, not full classifier parity. Generic filename rules replace identifying historical aliases; the fictional payer matcher and limited service patterns replace historical entity-specific handling. Some historical content categories and generic-content review checks are not modeled. Filename/content heuristics can misclassify ambiguous prose and do not authenticate source authority.

Historical review prose included fixed 659/47 counts and unconditional success/conflict claims. Here counts derive from current fixtures, absent input is “not assessed,” and mismatches cannot produce a clean classification status. These are deliberate corrections, not claims that recovered V1.1 behaved that way. No extraction success, timestamp, generated file or OCR execution is fabricated. A missing supplied row type is visibly labeled as a computed document fallback.

Suggested-action wording and reviewer labels are deliberately generalized to human inspection; historical urgency labels and conditional order are retained. Historical opportunity prose is not reproduced as promised outcomes.

The later prioritization pass replaced conditional suggestions with three fixed suggestions; that post-processing is excluded. The recovered denial-mapping-created flag could be truthy for an object without a denial source; this defect is recorded, not reproduced as a false success. No denial mapping is implemented. Historical capacity grouping could fall back to treatment-response themes without establishing measured retained gains; no such themes are computed here.

Recovered final-synthesis artifacts do not establish a recovered generator or exact reproducibility/authorship. Final synthesis and final packets remain excluded. The five-report system and other APPLIED_ON_TOP_OF_V1 workflows are separate, as are Neverlost OS, Case Navigator and later projects.

## Verification and boundaries

Isolated Playwright coverage exercises the pure rules, exact thresholds, three-action cap, immutable input/provenance, missing references, all six scenarios, source dialogs, keyboard focus, desktop/mobile layout and WCAG A/AA checks. Existing V1 tests are retained without edits.

Run npm run lint, npm run typecheck, npm run build, then npm run test:e2e. There are no API calls, uploads, authentication, persistence, autonomous execution or external communications. M04 does not implement Prioritized Evidence, Capacity Themes, Denial Mapping or V1.1 final synthesis.
