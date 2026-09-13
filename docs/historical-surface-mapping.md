# Milestone 03: historical surface mapping

This is new demo documentation, not a historical artifact. Source inspection was read-only against frozen V1 revision `dc038b06ed52a112ac853854df044250d46f2c49`. No historical implementation, medical record, original report, or private audit was copied into the app. The historical code's output templates, public schemas, and recovery documentation establish structure; the existing demo fixtures supply all displayed observations.

## Source-to-presentation mapping

| Surface | Inspected V1 source | Demo representation |
| --- | --- | --- |
| Timeline | [build_timeline.py](https://github.com/Neverlost-AI/neverlost-v1/blob/dc038b06ed52a112ac853854df044250d46f2c49/src/build_timeline.py), [timeline schema](https://github.com/Neverlost-AI/neverlost-v1/blob/dc038b06ed52a112ac853854df044250d46f2c49/schemas/timeline_event_schema.json) | Four dated events, source excerpts, separate interpretation, document/page/chunk references and inspectable source details. All fixture dates are known; confidence and separately identified patient observation are unavailable, not invented. |
| Evidence Matrix | [build_evidence_matrix.py](https://github.com/Neverlost-AI/neverlost-v1/blob/dc038b06ed52a112ac853854df044250d46f2c49/src/build_evidence_matrix.py), [matrix schema](https://github.com/Neverlost-AI/neverlost-v1/blob/dc038b06ed52a112ac853854df044250d46f2c49/schemas/evidence_matrix_schema.json) | Record fact → functional consequence → system relevance → next available opportunity. Source excerpts remain separate from new manual annotations; domains, source type, evidence type, missing evidence and uncertainty remain visible. |
| Reports | [generate_reports.py](https://github.com/Neverlost-AI/neverlost-v1/blob/dc038b06ed52a112ac853854df044250d46f2c49/src/generate_reports.py), [read-only Streamlit viewer](https://github.com/Neverlost-AI/neverlost-v1/blob/dc038b06ed52a112ac853854df044250d46f2c49/src/app.py) | Expandable in-page timeline/evidence summaries plus a Healthcare Reality Map snapshot linking existing candidate fixtures to evidence. These render static data, not Markdown files created by the historical generator. |

The [architecture documentation](https://github.com/Neverlost-AI/neverlost-v1/blob/dc038b06ed52a112ac853854df044250d46f2c49/docs/architecture.md) supports this evidence chain and distinguishes ordinary file artifacts from accepted-state transactions.

## Annotations are not heuristic execution

The V1 domain names are retained as review lenses. Care-coordination and endurance annotations organize the four invented notes for presentation. They are hand-authored, not claimed to be exact output of the original keyword/filename heuristics. The original evidence, event IDs, dates, excerpts, and candidate data remain unchanged.

An empty domain means no evidence in this small sample, not a negative clinical finding. A null annotation renders as not established/not identified, never false or zero. Questions are not assignments or approved actions.

## Limits intentionally retained

- No original private outputs are available in this public source snapshot. The demo therefore does not claim byte-for-byte report reproduction, historical authoring, authenticated provenance, or clinically representative source material.
- The fixtures do not provide separately identified patient observations, calibrated confidence, strength scores, clinical source authority, or disability/treatment/referral/insurance support flags. V1 schema fields exist, but values are not inferred for the demo.
- The historical timeline supported missing/approximate dates. All four demo events have dates; no undated event was fabricated to simulate coverage.
- V1 also defines specialized best-evidence, source-authority, disability, provider-ready, documentation-gap, coordination, action-roadmap, capacity, hidden-state and trust-threshold reports, plus debug outputs. This milestone demonstrates the shared output structure, not every specialized narrative or report. No trust-threshold fixture exists, so the snapshot says unavailable rather than zero.
- Capacity, hidden-state, and bottleneck candidates are displayed as candidates. Unknown retained gains and missing ownership remain unchanged. No determination, diagnosis, eligibility decision, or clinical recommendation is supplied.
- The later [five-report applied system](https://github.com/Neverlost-AI/neverlost-v1/blob/dc038b06ed52a112ac853854df044250d46f2c49/docs/five-report-system.md) is not the frozen Markdown generator. Its workflows, V1.1, Neverlost OS, and Case Navigator governance are outside this milestone.
- Filters, source dialogs, and report expansion are temporary UI interactions. There is no execution pipeline, saved report, export, upload, authentication, database, approval state, or external transmission.

The visible historical/synthetic/non-clinical/human-review disclaimer is unchanged.
