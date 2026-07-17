# AI Observatory Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and deploy Subaash Nair's immersive, reproducible data-science portfolio with Penang Pulse and Forecasting Lab launch stories.

**Architecture:** A Next.js App Router application owns the accessible content and persistent React Three Fiber scene. A separate Python workspace produces validated, versioned geospatial and forecasting artefacts consumed through typed manifests; production always retains the last valid snapshot.

**Tech Stack:** Next.js, TypeScript, React, Three.js, React Three Fiber, Vitest, Playwright, Python 3.12, uv, Pydantic, pandas/Polars, GeoPandas, scikit-learn, PyTorch, Vercel, GitHub Actions.

## Global Constraints

- Vercel is the deployment target; do not constrain the app to GitHub Pages static export.
- All essential content and navigation must work without WebGL.
- Respect `prefers-reduced-motion` and provide mobile quality reduction.
- Never publish an analytical claim without source, timestamp, method, uncertainty/limitation, and reproducibility metadata.
- Launch contains exactly two complete studies: Penang Pulse and Forecasting Lab; NASA is marked upcoming.
- Do not add authentication, on-site comments, a CMS, or runtime model training.

---

### Task 1: Repository foundation and design-system shell

**Files:**
- Create: `package.json`, `pnpm-workspace.yaml`, `.gitignore`, `README.md`
- Create: `apps/web/package.json`, `apps/web/src/app/layout.tsx`, `apps/web/src/app/page.tsx`, `apps/web/src/app/globals.css`
- Create: `apps/web/src/components/shell/site-header.tsx`, `apps/web/src/components/shell/site-footer.tsx`
- Test: `apps/web/src/components/shell/site-header.test.tsx`

**Interfaces:**
- Produces: semantic application shell and CSS tokens `--ink`, `--signal`, `--neural`, `--surface`, `--text`.

- [ ] Write a failing component test asserting the brand, Work, Experiments, About, and GitHub navigation are available by accessible name.
- [ ] Run `pnpm --filter web test site-header` and verify it fails before the component exists.
- [ ] Implement the root layout, metadata, global tokens, responsive header/footer, and an editorial non-WebGL landing shell.
- [ ] Run `pnpm --filter web test` and `pnpm --filter web lint`; expect both to pass.
- [ ] Commit with `git commit -m "feat: establish AI Observatory web foundation"`.

### Task 2: Typed story and artefact contracts

**Files:**
- Create: `apps/web/src/content/schema.ts`, `apps/web/src/content/stories.ts`
- Create: `apps/web/src/content/penang-pulse.mdx`, `apps/web/src/content/forecasting-lab.mdx`
- Create: `apps/web/src/lib/artefacts.ts`
- Test: `apps/web/src/lib/artefacts.test.ts`

**Interfaces:**
- Produces: `Story`, `SourceCitation`, `ArtefactManifest`, and `loadArtefactManifest(slug: string): Promise<ArtefactManifest>`.

- [ ] Write failing tests for a valid manifest, missing citation, invalid timestamp, and unsupported story slug.
- [ ] Run `pnpm --filter web test artefacts`; expect schema-validation failures.
- [ ] Implement Zod contracts and two content records with explicit `status: "published"`; add NASA with `status: "upcoming"` only.
- [ ] Render a semantic story index from the typed records and verify invalid artefacts fail closed.
- [ ] Run web tests and type checking; expect all to pass.
- [ ] Commit with `git commit -m "feat: add reproducible story contracts"`.

### Task 3: Observatory scene and progressive rendering

**Files:**
- Create: `apps/web/src/components/observatory/observatory-canvas.tsx`
- Create: `apps/web/src/components/observatory/data-world.tsx`, `signal-path.tsx`, `neural-preview.tsx`
- Create: `apps/web/src/components/observatory/observatory-fallback.tsx`, `quality.ts`
- Test: `apps/web/src/components/observatory/quality.test.ts`

**Interfaces:**
- Consumes: story slugs from `stories.ts`.
- Produces: `ObservatoryCanvas`, `ObservatoryFallback`, and `selectQuality({ width, reducedMotion, devicePixelRatio }): "full" | "reduced" | "fallback"`.

- [ ] Write failing tests for desktop, mobile, reduced-motion, and WebGL-unavailable quality decisions.
- [ ] Implement deterministic quality selection without user-agent sniffing.
- [ ] Build the Penang-centered globe, data paths, project signals, and neural preview using instancing and capped device pixel ratio.
- [ ] Add keyboard-operable HTML controls over the canvas and a complete fallback card grid.
- [ ] Run unit tests and a production build; expect no hydration warnings and no uncaught WebGL errors.
- [ ] Commit with `git commit -m "feat: build progressive AI Observatory scene"`.

### Task 4: Penang Pulse data pipeline and case study

**Files:**
- Create: `analysis/pyproject.toml`, `analysis/src/observatory/models.py`
- Create: `analysis/src/observatory/penang/sources.py`, `accessibility.py`, `export.py`
- Create: `analysis/tests/penang/test_accessibility.py`, `test_export.py`
- Create: `apps/web/src/components/studies/penang-map.tsx`

**Interfaces:**
- Produces: `public/artefacts/penang-pulse/manifest.json`, simplified service points, district aggregates, and accessibility summaries.

- [ ] Write fixture-based failing tests for source normalisation, missing coordinates, distance bands, zero-population districts, manifest citations, and deterministic export checksums.
- [ ] Run `uv run pytest analysis/tests/penang -q`; expect failures for unimplemented functions.
- [ ] Implement PeGIS GeoJSON ingestion, district/population joins, service-category mapping, and a documented accessibility-score calculation.
- [ ] Export bounded web artefacts and render category filters, source age, uncertainty, and limitations in the case study.
- [ ] Run Python tests, web tests, and the production build; expect all to pass using fixtures without network access.
- [ ] Commit with `git commit -m "feat: publish Penang Pulse analysis"`.

### Task 5: Forecasting pipeline and interactive lab

**Files:**
- Create: `analysis/src/observatory/forecasting/data.py`, `features.py`, `models.py`, `evaluate.py`, `export.py`
- Create: `analysis/tests/forecasting/test_splits.py`, `test_metrics.py`, `test_export.py`
- Create: `apps/web/src/components/studies/forecast-chart.tsx`, `model-comparison.tsx`, `neural-graph.tsx`

**Interfaces:**
- Produces: a leakage-safe chronological split; seasonal-naive, tree, and neural predictions; MAE/RMSE by sensor and horizon; versioned compact artefacts.

- [ ] Write failing tests proving chronological splits do not overlap, scalers fit training data only, the seasonal baseline uses past values, and exported metrics reproduce fixture calculations.
- [ ] Run `uv run pytest analysis/tests/forecasting -q`; expect failures before implementation.
- [ ] Implement UCI dataset 608 loading and feature extraction, then the seasonal-naive and histogram-gradient-boosting baselines.
- [ ] Add a compact spatial/temporal PyTorch model only after baselines pass; fix random seeds and record package/model versions.
- [ ] Export predictions and diagnostics; render sensor selection, forecast comparison, residuals, feature importance, and the model graph without browser-side training.
- [ ] Run Python tests, web tests, and the production build; expect all to pass.
- [ ] Commit with `git commit -m "feat: add reproducible Forecasting Lab"`.

### Task 6: Reproduction, discussion, and resilient refresh

**Files:**
- Create: `.github/workflows/ci.yml`, `.github/workflows/refresh-data.yml`
- Create: `apps/web/src/components/studies/reproduction-panel.tsx`
- Create: `analysis/scripts/refresh.py`, `analysis/tests/test_refresh.py`
- Modify: `README.md`

**Interfaces:**
- Produces: `refresh.py --check` exit code `0` for unchanged/valid sources, `2` for upstream/schema failure, and a reproduction panel linking commit, notebook, artefacts, citations, GitHub Discussion, and collaboration contact.

- [ ] Write failing tests that retain the last valid manifest when a mocked source times out or changes schema.
- [ ] Implement atomic staging and validation before replacing published artefacts.
- [ ] Add CI for web tests/build and Python tests; add a scheduled refresh workflow that uploads failure diagnostics but never commits invalid outputs.
- [ ] Add reproduction panels and configure discussion URLs for `SubaashNair/ai-observatory-portfolio`.
- [ ] Run all checks locally and validate the workflow YAML.
- [ ] Commit with `git commit -m "feat: add reproducible publishing workflow"`.

### Task 7: End-to-end accessibility, performance, and Vercel release

**Files:**
- Create: `apps/web/playwright.config.ts`, `apps/web/e2e/observatory.spec.ts`
- Create: `apps/web/vercel.json`, `apps/web/public/robots.txt`
- Modify: `apps/web/src/app/layout.tsx`, `README.md`

**Interfaces:**
- Produces: tested public routes `/`, `/work/penang-pulse`, `/work/forecasting-lab`, `/about`, and Vercel deployment configuration.

- [ ] Write end-to-end tests for keyboard navigation, reduced motion, fallback rendering, both case studies, source citations, and reproduction links.
- [ ] Run Playwright; verify tests fail for any missing route or inaccessible control.
- [ ] Complete responsive behavior, Open Graph metadata, sitemap, robots, loading boundaries, error boundaries, and dynamic-import boundaries for the canvas.
- [ ] Run unit tests, Python tests, Playwright, production build, and Lighthouse against the production build.
- [ ] Connect the GitHub repository to Vercel and verify preview plus production deployment.
- [ ] Commit with `git commit -m "feat: prepare AI Observatory for launch"`.

