# V2 public identity and root-entry cleanup

Scope: presentation and entry routing only, based on M2 commit `4d34af56dabfe6c462b3004d32e3362ef5918ece`. No Python, fixtures, generated outputs, analytical contracts, historical defects, or V1.1 synthesis behavior are changed. No M3 or OS work is included.

## Entry points

- `/` now redirects to `/v2` through the Next.js root page.
- `/v2` and every `/v2/*` surface keep their existing route behavior.
- The unchanged historical V1 Overview component is now mounted at `/v1`. Only its Overview/home link destinations change; its UI, fixtures, filters, dialogs, and analytical presentation are unchanged.
- Existing historical `/timeline`, `/evidence-matrix`, `/hidden-states`, `/bottlenecks`, `/capacity-windows`, `/reports`, and `/v1-1` routes remain available.
- Historical version selection remains within the historical experiences, not in V2's public header/navigation.

## Complete public-facing string/link inventory

| Location | Before | After |
| --- | --- | --- |
| V2 browser/page title | Neverlost V2 · Synthetic execution sandbox | Neverlost V2 · Longitudinal Evidence Analysis |
| V2 metadata description | Actual historical Python execution against curated synthetic sources. Human review required. | Live longitudinal evidence analysis with source-linked outputs, prioritization, deterministic validation, and human review. Curated synthetic cases only. |
| V2 wordmark text | Neverlost Systems | Neverlost V2 |
| V2 wordmark subtitle | V2 Live App · Execution sandbox | Neverlost Systems · Longitudinal evidence analysis |
| V2 top-right link | Historical V1 → `/` | Removed |
| V2 top-right link | V1.1 reconstruction → `/v1-1` | Removed |
| V2 top-right navigation accessible name | Historical versions | Removed with its navigation container |
| V2 sidebar/mobile-navigation note | V1.1 live processing · Recovered Python | Source-linked analysis · Human review required |
| V2 introductory kicker | ACTUAL PYTHON EXECUTION / CURATED SYNTHETIC INPUTS | LIVE EVIDENCE ANALYSIS / CURATED SYNTHETIC CASES |
| V2 disclaimer | Historical June 2026 prototype · Synthetic demonstration data · Not a clinical decision system · Human review required. | Synthetic demonstration data · Not a clinical decision system · Human review required. |
| V2 introduction | New V2 runtime around preserved V1 Python. Results are generated on request, not loaded from the historical portfolio fixtures. No Case Navigator state or human acceptance workflow. | Neverlost V2 analyzes records over time to produce source-linked timelines, evidence, bottleneck candidates, capacity windows, and reports. Live processing adds evidence prioritization, deterministic validation, and review tools. Explore a curated synthetic case, inspect its sources, and review the generated outputs. |
| V2 secondary provenance note | No separate note | Engine provenance: preserved June 2026 V1 Python and recovered V1.1 processing. Results are generated on request; historical rules and limitations remain in effect. |
| Case-list loading text | Loading manifest from the Python service… | Loading synthetic cases… |
| Busy analysis button | Running historical Python… | Running analysis… |
| V1-stage result count heading | `{count} historical output/outputs` | `{count} generated output/outputs` |
| Public root | `/` rendered historical V1 Overview | `/` redirects to `/v2` |
| Historical V1 Overview navigation item | `/` | `/v1` (same text, desktop and mobile) |
| Historical V1 wordmark link | `/` | `/v1` (same text and accessible name) |
| Historical version-selector V1 link | `/` | `/v1` (same historical label) |

## Audit findings and deliberate preservation

The old-version links originated in `src/components/v2/workspace.tsx`, not a global header. Its shared header serves both screen sizes. V2 metadata originates in `src/app/v2/layout.tsx`; historical root metadata remains applicable to the preserved historical routes, while V2 overrides it. The root page previously mounted `Overview` directly.

V2 has no separate footer to clean up. Functional navigation labels, the idle “Run Neverlost Analysis” CTA, source inspection controls, error/failure messages, run ledger, output fields, report contents, and detailed rule explanations remain unchanged. The recovered-stage headings are retained inside explanatory/provenance UI; they are not version-selection links. The existing warning explicitly preserves the unrecovered final-synthesis limitation and negation defect. Search-indexing settings are unchanged.

Before: the header offered competing historical versions and described the live product as a sandbox. After: root visitors reach Neverlost V2, see what it analyzes and that inputs are curated synthetic cases, and can use the existing analysis navigation without choosing a historical version. Engine lineage remains visible as secondary provenance, with limitations intact.

## Verification coverage

`tests/v2/identity.spec.ts` covers root redirect, direct V2 entry, title/metadata, absence of historical links, all V2 navigation destinations, responsive overflow, keyboard home navigation, accessibility, refresh, screenshots, and direct historical access with a V1.1-to-V1 return link. Existing Overview/deployment tests target `/v1` instead of the former root; their historical behavior assertions remain unchanged. Existing live V2 tests continue to exercise real Python execution, source dialogs, reports, failure behavior, and V1.1 integration.

## Verification results

- Lint, TypeScript, production build, and whitespace checks passed.
- All 36 Python tests passed. All 102 desktop/mobile Playwright tests passed on the final full run, including the existing V2 suite and two new identity checks.
- The first browser run exposed six stale root-URL assertions (three historical output views on two screen sizes). Updating their expected Overview destination to `/v1` resolved them; no analytical or historical display behavior was changed.
- Cases 001–004 reproduced their pre-edit M2 V1 and V1.1 analytical SHA-256 digests exactly. All 25 historical V1 hashes passed; no engine, API, analytical contract, or synthetic-case file changed.
- Desktop and mobile screenshots were visually inspected; no horizontal overflow or old-version header links were present. Browser accessibility, keyboard source inspection, direct entry and refresh checks passed. Automated accessibility tests are not a complete accessibility certification.
- Existing tool warnings: Starlette/httpx deprecation, Playwright color-environment warning, and Git's Windows newline-conversion notice. No build warning required an application change.
- The pre-existing `.gitignore` edit was preserved and excluded from the cleanup commit. This record describes local verification, not a production deployment.
