# V2 M2 recovered V1.1 integration — implementation record

Status: local acceptance passed; protected exact-commit preview parity is the
remaining deployment gate. No production promotion is authorized by this record.

M1 baseline: `746ff9449eb72e640cc23188970320b6c86e2bdb` on `v2-live-app`.
The 25 frozen V1 files and Cases 001–003 are not edited. The historical
`/v1-1` reconstruction remains separate. No final-synthesis generator was
recovered or implemented. No Case Navigator state or autonomous action exists.

## Custody and deliberate adaptations

`engine/v11-custody.json` records repository-relative original source paths
in the recovered active V1.1 tree, original SHA-256 and derivative SHA-256.
Absolute private recovery-machine paths are deliberately not published.
This is file-comparison custody, not authenticated historical Git ancestry.
The custody manifest's bytes are protected from Git newline conversion because
its SHA-256 is the derivative engine identity in local/remote comparisons.

- Privacy/publication: remove the person and institution aliases from source
  classification. Generic health-record, therapy and payer-context rules remain.
  Alias-only documents can now remain unknown or follow another generic branch.
- Privacy/publication: remove all entity-specific payer name entries rather than
  selectively publishing names from a private classifier. Payer identity remains
  null unless separately supplied by a future reviewed implementation. The
  payer-name-only denial shortcut cannot fire; generic payer/insurance context
  and the generic insurance-denial filename branch remain intact.
- Privacy/publication: remove the named PT practice filename exemption from
  `classify_pt_evidence`. All PT inputs now require the pre-existing generic
  PT/rehabilitation domain signal. No replacement practice alias is invented.
- Packaging: normalize derivative source line endings to LF. Frozen V1 bytes
  remain untouched. The other four recovered modules have no semantic edits.
- Runtime: new orchestration, not the private batch runner, will configure an
  isolated second stage using the current V1 output. No private profile, record,
  output or identifying fixture is packaged.

## Case 004 pre-acceptance expectations (freeze before running it)

Six short, independently invented documents use generic filenames: health record,
occupational therapy, physical therapy, insurance denial, function report, and
ambiguous note. Expected document and row source classes respectively are
provider, OT, PT, payer denial, claimant function report, unknown. Subject matter
must not turn OT evidence about insurance into payer authorship.

Each document should produce one source-linked V1 chunk/event. Therapy notes
deliberately emphasize intervention/PT/OT terms rather than functional-limitation
terms so the unchanged V1 event-type gate can yield capacity windows. Unknown
`not approved` wording must retain the V1 false-positive Barrier removed candidate.
All evidence must retain actual chunk/document relationships; none are inferred
from a later UI label.

Before acceptance, inspect and record exact source-derived event/window counts,
scores, stable ordering, selection, theme membership and source-gated bottlenecks.
These are calibration observations, not acceptance merely because execution
produced them. Expected rules: descending recovered evidence strength; stable
descending recovered priority score; document cap 12, content cap 5 with exact
payer-denial exception, global cap 25. Six rows should not hit the global cap.
Only an exact classified denial row enables the insurance bottleneck gate; no
disability-appeal source is supplied. Eight-family consolidation and initial
review grouping are distinct. The ten-theme guard remains structurally
unreachable under the recovered eight-family classifier.

Denial presence is true for Case 004, payer identity unknown after publication
adaptation, OT service recognized, rationale matched only if the recovered
phrase matcher recognizes it. Missing fields remain missing. Cases 001–003
without a classified denial retain a truthy raw mapping, separately labeled as
not evidence that a denial exists. Fixed historical review counts/actions and
`Not identified.` fallback behavior are not corrected.

Controlled mutation (test-only, never an upload or fixture edit): replace the
claimant note's phrase `standing and walking` with `bathing and dressing`.
Expect source SHA, V1 chunk text/event summary, V1 evidence and digest to change;
V1.1 evidence domains/functional score and analytical digest must change.
Expect six documents/events, source classes, payer denial presence, therapy
source content and therapy window count to remain invariant. Exact changed
ordering must be reviewed before acceptance, not assumed.

## Reviewed Case 004 calibration (before acceptance tests)

One chunk/event per source; six events, two therapy intervention windows. In
filename order: administrative barrier, functional limitation, functional
limitation, insurance event, intervention, intervention. Evidence strength order:
provider 118, claimant 106, PT 51, payer 22, OT 1, unknown -54. The raw negative
strength is retained; `int(-54 / 8)` is -6, not floor -7.

Priority order/score: provider 193, claimant 158, payer 140, OT 137, PT 115,
unknown 38. All six selected. This is heuristic ranking, not clinical importance.
Source/chunk pairs are checked against actual V1 chunks for every matrix and
selected row. Only the payer row enters the insurance bottleneck category;
no disability-appeal category is enabled.

The two V1 therapy windows generate four consolidated themes, ordered:
treatment response/carryover (2), pacing/energy conservation (2), insurance/
authorization (1, OT), IADL/home-management (1, PT). The initial review instead
groups both as pain/symptom response because V1 template text contains symptom
language. Related bottleneck links are broad historical heuristics, not newly
verified causal relationships.

The payer source is present, payer identity is `Not identified.`, service is OT.
The snippet chosen by recovered evidence construction favors the additional
documentation sentence; although the original source mentions medical necessity,
the mapping does not detect that language in the selected record facts. This
loss is preserved and asserted, not repaired from full source text.

## Runtime and presentation deviations

The second stage uses a fresh Python subprocess and isolated copy of actual V1
state, after V1 serialization. Original V1 artifacts/reports/digest are unchanged.
Both child processes share a total 45-second budget (including setup), inside
the unchanged 60-second Vercel function configuration. The complete response,
not just V1, is bounded to 3 MB. Missing upstream/generated artifacts fail
explicitly; no prepared JSON or frontend fixture substitutes for execution.

Recovered review manifest runtime locations are replaced by logical labels;
its timestamp moves to execution metadata outside the V1.1 analytical digest.
Initial and post-consolidation review text are both retained, including fixed
counts, OCR claims and unconditional suggested actions. Batch-only index targets
can remain absent and are disclosed rather than generating fake validation files.
Only explicitly allowlisted ordinary reports/review texts are serialized.

Ranking traces are V2 instrumentation: components call the recovered functions,
and the explained selection is asserted against the actual recovered selector.
Input-order indices are not historical finding IDs. Theme membership indices
point to actual V1 windows and do not imply stronger source evidence.

`execute(case_id, include_v11=False)` preserves an M1-only verification mode;
the public API accepts only a curated case ID and runs both stages. Execution
times and available Linux V1.1 peak RSS are metadata, never analytical inputs.

## Verification commands

Run the original five tests in the separate frozen recovery repository, then
`engine/.venv/Scripts/python.exe -B -m unittest discover -s tests/v2 -p test_*.py`,
`npm run lint`, `npm run typecheck`, `npm run build`, and
`npx playwright test --workers=2`. Linux uses the equivalent venv `bin/python`.
Browser verification uses the existing Playwright harness when agent-browser
is unavailable. No authentication protection is disabled for preview testing.

Local verification: 5 original V1 tests, 20 existing V2 Python tests and 16 new
V1.1 integration/rule tests passed. All 100 desktop/mobile Playwright tests
passed, including all historical routes and six live V1.1 views. Lint,
TypeScript, production build and whitespace checks passed. On Windows the
Playwright run needed its verified test-server processes stopped after all
tests completed; the runner then exited successfully with `100 passed`.
No application or test behavior was changed to work around teardown.

All 25 V1 hashes match. Cases 001–003 retain their exact M1 V1 digests. The
controlled claimant-source mutation changes both stages while retaining source
classes, six events, denial presence and the same two therapy windows. Four of
the five recovered V1.1 modules remain byte-identical; only the evidence module
has the documented alias-removal changes. Scoped path/credential/alias scanning
found no matches in new runtime, UI, fixtures, tests or documentation.

Representative Case 004 local measurement: 4.407 seconds combined, 1.375 seconds
V1 subprocess and 2.422 seconds V1.1 subprocess; serialized response 386,738
bytes. Timings and timestamp lengths vary and are excluded from the analytical
digest. Windows peak RSS was unavailable; Linux child peak RSS is reported when
available. Limits remain 45 seconds / 60 seconds / 3 MB, unchanged.

Known non-blocking tooling warnings: Starlette's existing httpx TestClient
deprecation and Playwright's NO_COLOR/FORCE_COLOR warning. Automated accessibility
checks are not a complete accessibility certification. Synthetic parity does not
establish clinical validity or reproduction of private historical outcomes.
