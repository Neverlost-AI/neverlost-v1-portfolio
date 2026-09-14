# M06 — Capacity Themes + Denials & Bottlenecks

New deterministic reconstruction of recovered V1.1 rules, not a historical interface. Continues the V1 capacity-window/bottleneck concepts inside the V1.1 extension. M05 baseline: 0b3ecbe0b51ddb2bb433b341894bce953d7c797f. No historical Python or private record/output is copied or changed.

## Capacity rules

Lowercase substring matching across intervention, source_evidence, what_became_possible and learning. Each matching family receives the window once:

- ADL/self-care: bathing, self-care, self care, adl, dressing, hygiene.
- IADL/home-management: home, vacuuming, household, iadl, daily activities, functional activity.
- Mobility/stairs/walking: walking, stairs, standing, mobility, gait.
- Upper-extremity/joint-protection: upper extremity, joint protection, joint stabilization, hypermobility, supportive garments, supportive devices.
- Treatment response/carryover: improvement, treatment, medication, respond, carryover, symptoms, pain.
- Care coordination/administrative: coordinate, records, follow-up, appointment, referral, provider.
- Insurance/authorization: authorization, insurance, denial, coverage.
- Pacing/energy conservation: pacing, energy conservation, fatigue, breathwork, somatic, regulating.

No match falls back to treatment response/carryover. This is a historical default, not evidence of response. One window can join multiple groups. “IADL” also contains “ADL”; negated carryover wording can still match. Repetition is retained: there is no equivalent-evidence deduplication, measured improvement or retained-gain inference.

Groups sort by membership count descending; ties retain first-seen theme order. Display document names and authority labels as sorted unique inventories, taking first matching document authority. Unique inventories do not deduplicate windows.

The recovered classifier exposes eight families. The implementation nevertheless returns themes[:10]. Under this classifier the ten-theme limit appears structurally unreachable. Unit tests supply clearly artificial groups to verify the guard itself, not a historically demonstrated ten-theme state. No artificial ninth/tenth family is available in the UI.

Related bottlenecks preserve the broad insurance, care coordination, capacity/functional/treatment-response and ADL substring rules, first three matches. All family names include “capacity,” so unrelated-looking links can occur and earlier matches can hide a later insurance match. A source-audited projection of the matching terms in the recovered bottleneck/needed/action templates is used, so safer new UI prose does not change link results.

## V1.1 bottleneck changes reconstructed

Consolidate in the recovered eight-category order:

1. Functional evidence formatting: ADL, IADL, mobility, endurance, cognition, disability process.
2. Care coordination/admin: care coordination or IADL.
3. Therapy/provider tracking: PT/rehabilitation or treatment response.
4. Provider summary: provider support, care coordination, disability process, treatment response.
5. Daily-function documentation: ADL or IADL.
6. Insurance authorization/documentation: exact insurance denial letter source type only.
7. Appeal/DDS organization: exact disability appeal source type only.
8. Capacity-window tracking: treatment response.

The ordinary domain rules do not establish that evidence is missing; these are candidate templates triggered by supplied domains. The insurance category has no domain-only or keyword-only fallback. Claimant appeal text mentioning providers/therapy remains claimant process evidence, not provider evidence. The historical appeal template asserted OCR availability; the reconstruction does not assert OCR execution or success.

Rows inside each category sort stably by existing evidence-strength input, not the M05 combined score. Unique key-source labels retain that order and are limited to six; output is limited to eight consolidated categories. Full triggering rows remain inspectable as new provenance instrumentation. The UI demonstrates more than eight raw evidence/category matches producing eight categories. A separate artificial guard test checks truncation beyond eight; no ninth category is invented.

Historical confidence: use positive-strength rows if any, otherwise all rows. High label plus at least two considered rows gives high; any high/medium otherwise gives medium; remaining nonempty input gives low; empty gives unknown. These uncalibrated labels are not validation.

Source-sensitive summary inventories distinguish provider, OT, PT, claimant function/appeal, payer and unknown sources. Historical summary/action/benefit prose is generalized to bounded context and unresolved-information descriptions; no professional conclusions, retained gains, improved outcomes or autonomous action claims are reproduced.

## Denial mapping

Actual classified denial-source presence gates the insurance candidate and mapping. No-denial returns null and renders no insurance barrier or mapping. This explicitly corrects the recovered truthy-object false positive; no historical parity is claimed for that result. An insurance mention in an OT/provider note is insufficient.

When a denial source exists, join its record facts. Take first available payer, service and context fields; all contributing sources remain visible. This preserves the cross-document aggregation limitation rather than implying separate denial-case mappings. Batch document-status fallback metadata is not reconstructed because no private extraction manifest is used.

For rationale, normalize whitespace and scan term lists in order, taking the first occurrence of the first matching term. Extract up to 120 characters before and 260 after; shorten to 360 at a word boundary where needed:

- Reason: not medically necessary, denied, denial, not approved.
- Necessity language: medical necessity, medically necessary, criteria.
- Missing documentation: missing, documentation, records, information.
- Criteria: criteria, guideline, benefit, coverage.
- Rights/deadline: appeal, appeal rights, deadline, hearing.
- Service fallback when no supplied label: service, therapy, occupational therapy, authorization.

These are snippets, not structured truth. Negated or incomplete phrases still match. Requested-service fallback is shown separately from supplied service labels; this improves attribution over an indistinguishable combined output.

Candidate support uses exact OT record or health-system/provider record source types, searching content type, fact, functional consequence and system relevance. Sort stably by unchanged M05 score, maximum ten per source class:

- OT terms: adl, iadl, self-care, self care, adaptive, energy conservation, pacing, functional rehabilitation, treatment response, joint protection.
- Provider terms: diagnosis, problem list, treatment plan, referral, medication, functional limitation, medical necessity, assessment.

PT and claimant sources are not selected by these two recovered selectors. No denial-criteria-specific comparison, semantic verification, causal match or support sufficiency is performed. Weak/missing support remains visible.

## Explicit deviations and exclusions

New typed fixtures, UI, full member/source inspection, trigger traces and M05 membership on M06 inputs are presentation/reconstruction additions. The M05 surface retains its independent scenarios; navigation does not transfer canonical state.

Historical grouping output showed only three shortened examples; this UI exposes all contributing windows and their source references instead. Static historical functional-meaning/increase/decrease/opportunity templates are not emitted as findings. Warnings emphasize that membership cannot establish sustained function, clinical significance, disability/work capacity, necessity, eligibility or improvement/decline.

Unknown source summaries are explicit instead of relying on generic source-description fallback. Missing rationale fields all receive warnings, extending the historical subset of missing-field checks. No-denial null gating and separately labeled service fallback are documented corrections/generalizations. Source labels and payer/service fields are supplied synthetic inputs, not a new entity-extraction pipeline.

No final synthesis, final packets, appeal generation/submission, LLM/API, agents, accept/reject/hold, uploads, persistence, external communication, Case Navigator or applied five-report workflows. M04/M05 code changes are navigation only. Historical final-synthesis generation and full private-batch reproducibility remain uncertain and unclaimed.

## Verification

Six independent synthetic scenarios cover mixed authority/multi-theme membership, no denial despite mentions, weak denial with absent support, claimant appeal, unknown-source fallback and empty input. Tests cover eight families; artificial ten-theme guard; eight-category guard; raw count grouping; confidence/source caps; exact source gates; mapping selectors and limits; stable ordering; links and complete provenance; desktop/mobile accessibility; keyboard dialogs; V1/M04/M05 regressions.

Run npm run lint, npm run typecheck, npm run build and npm run test:e2e. M06 remains unstaged/uncommitted for review.

