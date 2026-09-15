# Frozen V1/V1.1 — deployment readiness

Baseline: `882d94c5bd963a035aeb2a3e55bc8e60718e48de`; the working tree was clean before this pass. This is deployment preparation only. No reconstruction milestone, deployment, push or commit is performed.

## Hosting settings

Use a repository containing **this application only**, with its root as the Vercel Root Directory (`.`). Never import the surrounding recovery workspace or historical repositories. If the app is intentionally placed in a larger public-only repository later, select its app subdirectory and disable inclusion of files outside that root. Do not use the private parent workspace as a monorepo.

| Setting | Required value |
| --- | --- |
| Framework preset | Next.js |
| Node.js | 24.x |
| Install command | `npx --yes npm@11.17.0 ci --include=dev` |
| Build command | `npm run build` |
| Output directory | Next.js default; leave override disabled |
| Development command | Next.js default / `npm run dev` |
| Environment variables | None required for build or application runtime |
| External services / integrations | None |

The explicit install override runs the tested npm version rather than relying on Vercel's inferred npm version. `packageManager` records that version for local tooling; it is not assumed to pin npm on Vercel by itself. Do not set production-only dependency omission: TypeScript/build tooling needs development dependencies. Do not set `NODE_ENV`, `NEXT_PUBLIC_*`, tokens or healthcare configuration manually. No Corepack switch or Vercel credentials are needed for the application. Account-level deployment authorization is separate and not stored here.

Vercel supports Node 24.x and honors package engine constraints; the previous open-ended range could float to a later major. The new range selects the tested major, while Vercel controls patch updates. The package-manager and Node documentation do not guarantee our specific remote build without running it: an authorized preview remains the final platform check. See [Vercel Node versions](https://vercel.com/docs/functions/runtimes/node-js/node-js-versions) and [package managers](https://vercel.com/docs/package-managers).

No custom `vercel.json`, static-export conversion, rewrites, middleware, functions, base path or output override is needed. This remains a conventional Next.js App Router build, not an SPA fallback deployed as arbitrary static files.

## Deployment-only changes

- `package.json`: record npm 11.17.0 and constrain Node to 24.x. No dependency version, script or runtime behavior changed.
- `package-lock.json`: synchronize the root Node engine metadata only. All locked dependency entries, versions, registry URLs and integrity values remain frozen.
- `.vercelignore`: root upload allowlist for source and required build configuration, with recursive exclusions for Git/local environment, dependencies, logs, caches and test artifacts. Docs, tests and private/unrecognized root files are not upload inputs. [Vercel's ignore documentation](https://vercel.com/docs/deployments/vercel-ignore) explains why explicit upload exclusions matter.
- `tests/deployment.spec.ts`: direct navigation and refresh of all 13 public pages on both viewports; local fonts/icon/assets, runtime/console errors, responsive layout and accessibility; non-public source/config/artifact URL checks. Existing tests remain unchanged.
- `README.md`: align only the local toolchain instruction with Node 24/npm 11.17 and link this deployment guide; historical descriptions are unchanged.
- This deployment document records readiness and the precise operational boundaries. Historical milestone documentation and labels are not rewritten.

The allowlist is not a substitute for reviewing future files under `src`. Never put private or ignored material under a served directory. Do not use `--prebuilt` to upload local output from this private workstation; build from the reviewed application-only checkout on Vercel. Do not expose any Git-ignored files. Review both Git and upload inclusion before eventual publication.

## Public-safety review

The application uses bundled, independently invented synthetic fixtures. No historical Python, private case files, patient records, private output packets, authentication, uploads, persistence, APIs or environment-variable reads are application inputs. Source/provenance fields are synthetic and preserved. The public GitHub historical-revision link is intentional; the SVG namespace is not a network request. Localhost addresses belong to development documentation/test configuration, not production data or asset URLs.

The scoped review checks source content and imports, personal-identifier/credential/path patterns, Git-tracked inventory, ignored root inventory and production browser assets. Pattern checks cannot certify the absence of every possible secret; they supplement the fixture provenance and source review. No hidden environment values are printed or imported.

Only application source, local SVG branding and npm-bundled Inter/Manrope fonts are runtime assets. No remote fonts or analytics are introduced. All 401 locked package entries have integrity fields and public npm registry URLs; Linux Next compiler packages are present in the cross-platform lockfile.

Existing labels remain unchanged: V1 is historical presentation; V1.1 is a deterministic reconstruction supported by file comparison rather than authenticated Git ancestry; outputs are heuristic and require human review. Final-synthesis generation and private-batch reproducibility remain unestablished. Case Navigator, Neverlost OS, five-report applied workflows and later systems remain separate. See [final historical verification](v11-final-verification.md).

## Issues and warnings

1. Open-ended Node engine range: constrained to the already-tested Node 24 major, without changing dependencies.
2. No explicit Vercel upload policy: added the narrow allowlist. Existing Git-ignored content remains excluded.
3. npm version inference: recorded the tested version and recommend an explicit pinned install override.
4. First locked install was blocked by the local execution sandbox's registry access policy. Retrying with authorized registry access succeeded; this was not an application or lockfile failure.
5. Three upstream lint plugins advertise peer ranges ending at ESLint 9 while the frozen toolchain uses ESLint 10. The existing official compatibility adapter is retained. Do not use force, legacy-peer-deps, dependency upgrades or disabled lint rules to hide warnings.
6. npm 11.17 reports an unapproved `unrs-resolver` postinstall script. No approval was granted. Clean-install lint and build passed using the shipped packages on this Windows host; no claim is made that every install script ran or that this proves Linux execution.
7. Linux/Vercel remote build, deployment settings and public-domain checks cannot be verified without the separately authorized deployment. Local verification is not a claim that deployment has occurred.

## Verification

Completed September 14, 2026 on Node 24.19.0 / npm 11.17.0:

| Check | Result |
| --- | --- |
| Frozen-lockfile install | Passed with registry permission; repeated successfully after root engine metadata update |
| Dependency audit | Zero reported vulnerabilities; no dependency graph changes |
| Typecheck | Passed |
| Lint | Passed, zero lint warnings/errors |
| Production build | Passed, no build warnings; all 13 application pages prerendered |
| Complete Playwright suite | **92 passed in 10.6 minutes**: 88 existing cases plus four deployment cases across desktop/mobile |
| Direct entry and refresh | All 13 public pages returned 200 on both viewports, including refresh |
| Assets and runtime | Local fonts and SVG loaded; no console/page errors, failed HTTP responses or automatic external requests in deployment smoke checks |
| Accessibility / responsive | Axe WCAG 2 A/AA and 2.1 AA checks passed; no horizontal overflow; representative desktop/mobile screenshots visually reviewed |
| Keyboard / provenance | Existing complete source-dialog, Escape/focus-return, filter, navigation and scenario tests passed unchanged |
| Public source/config/artifact probes | All nine tested non-public paths returned 404 |
| Whitespace | `git diff --check` passed; new-file trailing-whitespace checks passed |

Browser tests start the production server on loopback port 3100, not a development server. Playwright was used because the prescribed agent-browser CLI is unavailable. Tests emitted only a harmless NO_COLOR/FORCE_COLOR terminal warning. No production account was contacted, linked or configured.

Safety/preservation findings:

- No private records, personal identifiers, credentials, real local absolute paths or private configuration were found in scoped source/built-browser checks. One match was Turbopack's generic `file:///ROOT/` placeholder, not a workstation path.
- No application `.env` files, inherited `NEXT_PUBLIC_*` variables or tracked symlinks were present. No environment values were added to the app.
- No browser source-map files, dynamic routes or Server Actions were generated. Build tracing checked 2,745 dependency references; all resolved inside the application root. Framework-generated server-only build metadata was not found in browser static assets.
- Upload-policy checks included all 45 tracked source files and six build-input files; no unexpected tracked input was allowed. Ignored/private-file probes were excluded. The allowlist itself is also permitted as configuration. This policy was tested locally, not by uploading files to Vercel.
- All 401 locked package entries retained public registry URLs and integrity metadata. Registry lookup confirmed availability of npm 11.17.0 for the pinned install override.
- `src`, existing tests, Next configuration, historical descriptions and reconstructed labels are unchanged from the frozen commit. All analytical behavior, weights, caps, order, provenance and limitations remain intact.
- The historical repository remained clean and all 25 recorded source hashes matched. Historical Python was not modified or incorporated.

No local readiness blocker remains. Ready for a separately authorized Vercel preview with the settings above, not a claim of verified Vercel/Linux deployment or production-domain behavior. The six deployment-only files remain unstaged/uncommitted for review; application source and the locked dependency graph remain frozen.

Public page inventory: `/`, `/timeline`, `/evidence-matrix`, `/hidden-states`, `/bottlenecks`, `/capacity-windows`, `/reports`, `/v1-1`, `/v1-1/run-review`, `/v1-1/prioritized-evidence`, `/v1-1/capacity-themes`, `/v1-1/denials-bottlenecks`, `/v1-1/final-review`.

## Release gate

Leave these changes unstaged and uncommitted for review. After separate approval, review the exact application-only source inclusion, commit it, and authorize a Vercel preview. Recheck the same routes, refreshes, assets and public-safety boundaries on that preview before authorizing public production. Keep Vercel source/build-log protection enabled. No clinical/security/compliance certification is implied.
