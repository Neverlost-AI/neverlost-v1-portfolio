# Neverlost V1 — portfolio presentation

A new, standalone Next.js + TypeScript interface built in September 2026. **This is not the historical June 2026 Python implementation.** No historical code, records, examples, generated reports, or private census files are imported or copied into this project.

> Historical June 2026 prototype · Synthetic demonstration data · Not a clinical decision system · Human review required.

## Milestone 03: Timeline, Evidence Matrix, and Reports

Milestone 01's branded Overview is preserved in local commit `54d8fab2e07527ed6352508a55a9d099aadfc830`. It provides a synthetic sample summary, a small timeline preview, candidate review questions, an evidence preview with filters, and a native accessible source-detail dialog.

Milestone 02 adds only `/hidden-states`, `/bottlenecks`, and `/capacity-windows`. Each illustrates existing typed fixtures through recorded observations, candidate context, and explicit limitations, with complete source details available through the shared dialog. The reading order is not an execution pipeline or a causal claim. Missing ownership remains "Not recorded"; retained gains remain "Unknown". Fixture questions are illustrative, not assigned or approved actions.

Milestone 02 is preserved in local commit `b7dee500c27bea2bf0b827ef335bea485444320d`.

Milestone 03 adds only `/timeline`, `/evidence-matrix`, and `/reports`. Timeline orders the four existing events and separates source excerpts from interpretation. Evidence Matrix presents the V1 record-fact / functional-consequence / system-relevance / next-opportunity chain with manually authored synthetic annotations, domain/type filters, and explicit missing fields. Reports offers expandable timeline, evidence, and Healthcare Reality Map draft previews linked to those same fixtures. All seven navigation links are available; the Overview's existing sections, filters, and dialogs remain intact.

There are no accept/reject/approval workflows, proposal governance, analysis execution, saved decisions, V1.1 workflows, or external submission. Report previews are not verified clinical, disability, legal, or benefits determinations. See [historical surface mapping and representation limits](docs/historical-surface-mapping.md).

Static, hand-authored TypeScript fixtures represent Overview, Timeline, Evidence Matrix, Bottlenecks, Hidden States, Capacity Windows, and Reports. Source document, page, chunk ID, excerpt, date, category, and interpretation are preserved in the fixture/detail interface. Other fixture records reference evidence IDs rather than dropping source linkage. A source-linked badge does not mean verified evidence.

No authentication, database, API keys, uploads, external data calls, processing pipeline, LLM execution, autonomous agents, persisted review state, or clinical validation. UI filters/dialogs are temporary React state and reset on reload. No analytics or remote fonts. These fictional observations are not derived from a person or historical record; report fixtures are category metadata, not generated reports.

## Local development

Use Node.js 22.13 or newer and npm.

```sh
npm ci
npm run dev
```

Open http://localhost:3000. For production verification:

```sh
npm run lint
npm run build
npm run typecheck
npm exec playwright install chromium
npm run test:e2e
```

The browser tests launch the production build on port 3100. They cover all seven surfaces on desktop/mobile: layout, navigation, chronological ordering, domain/type filters and empty selections, report previews, complete provenance, dialog keyboard/focus/Escape behavior, no runtime external requests, category references, and automated accessibility checks. Automated checks are not a complete accessibility certification.

Lint uses ESLint 10 with the official `@eslint/compat` adapter because Next's bundled React plugin still uses removed context methods. No lint rules are disabled. See [ESLint's migration guidance](https://eslint.org/docs/latest/use/migrate-to-10.0.0).

### Milestone 01 verification

On September 12, 2026: lint (zero warnings/errors), production build, TypeScript, and all eight Chromium desktop/mobile tests passed. Automated accessibility checks found no violations in the tested Overview and source dialog. Desktop and phone screenshots were visually inspected. The published historical repository stayed clean and all 25 historical hashes remained unchanged.

`npm ci --dry-run --ignore-scripts --no-audit --no-fund` also passed. npm still reports upstream peer-range warnings for three bundled lint plugins whose declared ranges stop at ESLint 9; the official compatibility adapter handles their runtime APIs. These are install warnings, not suppressed lint failures. The dependency audit reported zero vulnerabilities at installation. Neither a Vercel deployment nor real-record validation was performed.

## Vercel deployment

This is a conventional App Router app using Next.js's default deployment output. Import **this project directory only** as the Vercel project root; select the Next.js framework preset. Build command: `npm run build`. No environment variables, authentication, database, custom output-directory override, or API keys are required. Deployment itself is not performed by creating this demo.

Do not select a parent workspace containing historical/private material as the deployment root. If creating a separate Git repository for this demo, include only this app and its lockfile; exclude dependencies, build output and test artifacts via `.gitignore`.

Configuration follows the official [Next.js installation documentation](https://nextjs.org/docs/app/getting-started/installation) and [Vercel Next.js deployment guidance](https://vercel.com/docs/frameworks/full-stack/nextjs).

## Structure

```text
src/app/                 Seven presentation routes, styles and local icon
src/components/          New presentation components only
src/lib/demo-data.ts     Typed synthetic fixture data and source references
src/lib/output-data.ts   Manual synthetic matrix annotations and V1 domain names
docs/                   Historical surface mapping and limits
tests/                   Browser, accessibility and fixture-integrity tests
```

The original project remains separately preserved at [the reviewed historical repository revision](https://github.com/Neverlost-AI/neverlost-v1/tree/dc038b06ed52a112ac853854df044250d46f2c49). This demo presents a few output categories; it is not a rewrite, executable descendant, reconstruction of original UI, or evidence of capabilities absent from historical V1.
