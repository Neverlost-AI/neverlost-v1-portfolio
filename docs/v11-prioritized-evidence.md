# Milestone 05 — Prioritized Evidence

New deterministic reconstruction of recovered V1.1 rules; this is not the historical interface. Uses independently invented, typed synthetic inputs. The recovered prioritization_consolidation.py was inspected read-only, together with the public v1-1-audit-summary and extensions documentation. Recovery establishes direct code extension through file comparison, not authenticated Git ancestry. No private records, aliases, outputs or paths are incorporated.

## Exact ranking formula

Total = authority + functional impact + system relevance + actionability + trunc(evidence_strength_score / 8). All five components have multiplier 1. Truncation is toward zero, matching Python int division conversion, not rounding. The existing strength score is a supplied synthetic upstream input; its upstream computation is not reconstructed here.

Authority uses the first matching branch:
- 40: provider source type OR case-sensitive authority substring “provider-authored medical record”.
- 36: OT/PT source type OR case-insensitive “therapy” authority substring.
- 32: insurance denial letter source type OR case-insensitive “payer” authority substring.
- 24: function report / disability appeal source type.
- 10: otherwise.

Functional impact sums each unique exact-case domain: ADL 16; IADL 14; mobility 14; endurance 12; treatment response 12; care coordination 10; insurance/authorization 14; disability process 12; pain 8; joint stability 8; cognition 8.
Search content type, fact, functional consequence and system relevance as one lowercase text:
- Add 10 once if any of functional limitation, self-care, medical necessity, authorization barrier, denial matches.
- Add 8 once if any of bathing, standing, walking, stairs, lifting, pacing, care coordination matches.

System relevance searches relevance, why-it-matters, next opportunity and missing evidence as lowercase text. Add each matching substring once: provider summary 10; disability 10; authorization 10; insurance 10; care coordination 8; capacity-window 8; functional tolerance 8; documentation 6.

Actionability: nonempty opportunity without “hold this row” +12; nonempty missing evidence +6; supplied support flags disability +5, treatment +4, referral +4, insurance authorization +5; high confidence +4; low/unknown confidence -6; other confidence 0. No trimming, semantic negation handling or calibration is added. Literal hold wording only suppresses a score contribution; no hold state exists.

## Selection

Stable descending score order retains original input order for ties. Check exact document-name count first (12), then exact content-type count (5). Counters include selected rows only. Stop once 25 rows are selected. No minimum score or deduplication is introduced. Selected-set ranks are contiguous and can differ from full candidate ranks.

Only exact source type “insurance denial letter” bypasses the content-type check. Such rows still increment both counters and cannot bypass document/global limits. A denial mention or payer authority string is insufficient. Denial rows can therefore exhaust the shared type budget for subsequent non-denial rows. Therapy authority wording can win the earlier 36-point branch even on a denial row; exception eligibility still follows source type, not that score branch.

The recovered selector only emitted selected rows. This UI adds full candidate ranks, score traces, counters and exclusion reasons. Rows after the global cap are explicitly not visited by the historical loop; no hypothetical per-document/type rejection is claimed for them.

## Suggested uses and links

Reconstructs the recovered provider, therapy, payer and claimant branches plus generic substring fallbacks for provider summary, disability evidence, insurance appeal, care coordination and internal review. Ordered labels are deduplicated. Each shows its branch basis. A denial source anywhere in the full candidate set can add insurance-appeal use to therapy rows, even if that denial row is not selected. Unknown authority does not prohibit keyword-based use labels. These are historical labels, not established suitability, generated reports or professional recommendations.

Internal review is the default even without selection. The recovered prioritized-only note attributed that fallback to selection; the UI explains this oddity instead of presenting the attribution as valid reasoning.

Bottleneck linking takes the first exact document/page-or-chunk source-reference match; otherwise the first bottleneck sharing insurance, care coordination or capacity substrings across the recovered field groups. UI links identify exact versus heuristic basis and open independently invented annotations on the same page. No bottleneck engine, capacity analysis or denial mapping is added.

## Preserved oddities and explicit deviations

- Ranking mixes source labels, substrings, support flags and a prior score without validation. Missing evidence and even whitespace-only opportunity/missing fields can increase the score. Repeated domains/terms do not increase their within-group contributions, but terms can contribute in multiple components.
- Case sensitivity differs between the provider authority branch and other branches. Broad substring matching can count negated or unrelated prose. No semantic fixes are silently applied.
- Strength division creates ties; input order and exact document/type strings affect membership. Scores can be negative and low-authority rows can be selected. Selection is not clinical importance or truth.
- Fresh TypeScript implementation uses explicit typed fields and integer finite fixtures rather than the historical loose dictionaries. Malformed historical payload coercion is not claimed. Upstream evidence-strength generation, extraction and source classification are not rerun.
- New interface, complete candidate inspection, exclusion explanations and suggested-use branch explanations are presentation instrumentation absent from recovered selected-row outputs. Suggested uses are also inspectable for excluded candidates, clearly outside the selected set.
- Bottleneck references use the demo's explicit page/chunk formatting; exact-string matching semantics are preserved. Fixtures and bottleneck annotations are all new.
- Historical report serialization, short-text truncation, fixed batch counts, manifest updates and next-action rewriting are not reproduced. M04 review results are not mutated after ranking.
- Capacity Themes, Denial Mapping, final synthesis, five-report applied workflows, approvals, uploads, persistence, agents and external communication remain excluded.

## Fixtures and verification

Seven scenarios exercise 30-row global volume; 15 rows in one document; eight same-type rows; fourteen denial rows plus a same-type unknown row; tied/near-tied scores; contextual/claimant/unknown evidence; and empty input. Synthetic repetition is not corroboration. Provenance includes invented source excerpt, exact document, page, chunk, source type and authority for every row.

Tests cover exact weights, truncation, case/precedence oddities, strict caps, denial exception counter effects, ties, empty input, immutable provenance, suggested uses, exact/heuristic links, every selected source dialog, desktop/mobile accessibility and unchanged V1/M04 behavior. Run lint, typecheck, production build and the full Playwright suite.

Historical final-synthesis generation remains uncertain and outside M05. No full historical private batch or clinical validity is claimed. M04 commit: 848150e6055ec9b19ea9fc75b89700f230602f22.

