# Repository-wide Codebase Review

## Table of Contents
- [Executive Summary](#executive-summary)
- [Security Findings](#security-findings)
- [Redundant / Incomplete Files](#redundant--incomplete-files)
- [SOLID-Principle Evaluation](#solid-principle-evaluation)
- [Improvement & Suggestion Recommendations](#improvement--suggestion-recommendations)
- [Prioritized Remediation](#prioritized-remediation)
- [Appendix – Tooling & Commands Used](#appendix)

## Executive Summary

The repository is an early-stage, well-structured monorepo for "AI Observatory", a Next.js + React Three Fiber data-science portfolio. Only the first of seven planned implementation tasks is complete: the repository foundation, design-system shell, and landing page are in place, with passing lint, typecheck, and unit tests. The code that exists is clean, idiomatic, and follows modern Next.js App Router conventions with good accessibility practices (skip link, semantic landmarks, `aria-labelledby`, reduced-motion support).

The primary concern is dependency security: `npm audit` reports 6 high-severity vulnerabilities, including a direct dependency on `next@16.2.10` that is affected by multiple advisories (middleware/proxy bypass, DoS, SSRF, cache confusion). No hard-coded secrets were found. The codebase is small enough that dead code and SOLID violations are minimal, but the landing page component and global stylesheet are beginning to accumulate responsibilities and would benefit from decomposition as the project grows. The remaining six implementation tasks (typed content contracts, the Three.js scene, both data pipelines, CI/CD, and E2E testing) are planned but not yet implemented.

## Security Findings

### Critical
- None identified.

### High
- `apps/web/package.json:16` — direct dependency `next@16.2.10` is affected by 9 advisories (middleware/proxy bypass in App Router with Turbopack, DoS via Server Actions, SSRF in Server Actions and rewrites, cache confusion of response bodies, unbounded Server Action payload, DoS in Image Optimization via SVGs, unauthenticated disclosure of internal Server Function endpoints). Fix available: `next@16.3.3` (outside the stated `16.2.10` range, requires `npm audit fix --force`).
- `package-lock.json` — transitive `postcss@<=8.5.22` (via `next` and `vite`) affected by XSS via unescaped `</style>` and arbitrary file read via attacker-controlled `sourceMappingURL`.
- `package-lock.json` — transitive `sharp@<0.35.0` (via `next`) inherits libvips CVEs (CVE-2026-33327, CVE-2026-33328, CVE-2026-35590, CVE-2026-35591).
- `package-lock.json` — transitive `brace-expansion@<=1.1.17 || 4.0.0-5.0.8` DoS via unbounded expansion length.
- `package-lock.json` — transitive `js-yaml@4.0.0-4.3.0` quadratic CPU consumption in `!!omap` resolution (CVE-2026-59870 not backported).
- `package-lock.json` — transitive `nanoid@<3.3.18` custom generators can loop indefinitely when size is zero.

### Medium
- None identified.

### Low
- None identified.

### Secret Detection
- No hard-coded secrets (API keys, passwords, tokens, private keys) were found in tracked source files or git history. The only matches were false positives in `package-lock.json` (package names such as `css-tokenizer` and `js-tokens`) and documentation prose. No `.env*` files are present in the working tree.

## Redundant / Incomplete Files

### Dead code
- None detected. All exported components (`Home`, `RootLayout`, `SiteHeader`, `SiteFooter`) are referenced by their consumers, and all imports resolve.

### Duplicate / unused files
- `apps/web/tsconfig.tsbuildinfo` — TypeScript incremental build cache present on disk but correctly gitignored (`.gitignore:5`); not tracked and safe to delete.
- `apps/web/.next/**` — Next.js build/dev output present on disk but gitignored; not tracked.

### Incomplete-task markers
- `apps/web/next-env.d.ts:5` — `NOTE: This file should not be edited` (generated file, expected and benign).
- `docs/superpowers/plans/2026-07-17-ai-observatory-implementation.md` — Tasks 2 through 7 remain unchecked (`- [ ]`), indicating planned but unimplemented work: typed story/artefact contracts, the Three.js observatory scene, the Penang Pulse and Forecasting pipelines, CI/CD + refresh workflow, and E2E/accessibility/Vercel release.
- No `TODO`, `FIXME`, `HACK`, `XXX`, or `WIP` markers exist in source code.

### Missing (planned but not created)
- `analysis/` Python workspace (referenced in README and design spec) does not exist.
- `.github/workflows/ci.yml` and `.github/workflows/refresh-data.yml` do not exist.
- `apps/web/vercel.json`, `apps/web/playwright.config.ts`, `apps/web/public/robots.txt` do not exist.

## SOLID-Principle Evaluation

The codebase is composed of React function components and a single global stylesheet rather than classes, so SOLID is evaluated at the module/component level.

- **`RootLayout` (`apps/web/src/app/layout.tsx`)** — Satisfies Single Responsibility (composition of shell + metadata only). No violations.
- **`SiteHeader` (`apps/web/src/components/shell/site-header.tsx`)** — Satisfies Single Responsibility and Open-Closed (navigation links are declarative data). No violations.
- **`SiteFooter` (`apps/web/src/components/shell/site-footer.tsx`)** — Satisfies Single Responsibility. No violations.
- **`Home` (`apps/web/src/app/page.tsx`)** — Single Responsibility is strained: the component mixes the hero section, the signals section, and two study cards in one 97-line function. Suggest extracting `Hero`, `StudyCard`, and `SignalsSection` into `src/components/` subcomponents.
- **`globals.css` (`apps/web/src/app/globals.css`)** — Single Responsibility is strained: one 150-line file holds tokens, layout, hero, cards, and responsive rules. Suggest splitting into CSS modules or co-located component styles as the app grows.
- **Dependency Inversion / Interface Segregation** — Not yet applicable: the typed content contracts (`Story`, `SourceCitation`, `ArtefactManifest`) and the `loadArtefactManifest` abstraction are specified in Task 2 but not yet implemented. Once added, they will provide the seams needed for Dependency Inversion.

## Improvement & Suggestion Recommendations

- **Critical**
  - Patch the direct `next` dependency from `16.2.10` to `16.3.3` (or the latest patched release) to resolve 9 high-severity advisories. Action: update `apps/web/package.json`, run `npm install`, then `npm audit`.
  - Remediate the 5 transitive high-severity advisories (`postcss`, `sharp`, `brace-expansion`, `js-yaml`, `nanoid`). Action: run `npm audit fix` and verify the lockfile updates without breaking the build.

- **High**
  - Add CI/CD. Action: create `.github/workflows/ci.yml` running `npm run lint`, `npm run typecheck`, `npm test`, and `npm run build` on every push/PR (Task 6 of the plan).
  - Add automated dependency and security scanning to CI. Action: add `npm audit --audit-level=high` as a CI gate and enable Dependabot/Renovate for weekly updates.
  - Complete the remaining implementation tasks (2–7), especially the typed content contracts and artefact manifest validation, which the design spec requires to "fail closed" in CI.
  - Add end-to-end tests. Action: introduce Playwright with coverage for keyboard navigation, reduced motion, fallback rendering, and both case-study routes (Task 7).

- **Medium**
  - Decompose `Home` into `Hero`, `StudyCard`, and `SignalsSection` subcomponents to restore single responsibility and enable reuse.
  - Modularize `globals.css` into CSS modules or co-located styles to keep the design system maintainable.
  - Add `robots.txt`, a sitemap, and Open Graph metadata (planned in Task 7) for SEO and social sharing.
  - Add a `CONTRIBUTING.md` and expand the README with the Python analysis workspace setup once it exists.

- **Low**
  - Adopt stricter lint rules (e.g., `eslint-plugin-jsx-a11y` is already included via `eslint-config-next`; consider enabling `@typescript-eslint` strict rules).
  - Add observability (Vercel Analytics / Web Vitals) once deployed.
  - Consider a `pre-commit` hook running lint and typecheck to catch issues before CI.

## Prioritized Remediation

1. **Critical** — Patch `next` to `16.3.3` and run `npm audit fix` to clear the 6 high-severity dependency vulnerabilities. No hard-coded credentials were found, so no secret rotation is required.
2. **High** — Add GitHub Actions CI (lint, typecheck, test, build, `npm audit`), enable Dependabot, and complete the typed content/artefact contracts plus the Python analysis workspace.
3. **Medium** — Decompose the `Home` component and `globals.css`, add `robots.txt`/sitemap/OG metadata, and add a `CONTRIBUTING.md`.
4. **Low** — Clear the remaining unchecked plan tasks, enrich documentation, and adopt optional linting rules and pre-commit hooks.

## Appendix – Tooling & Commands Used

- **Node.js** `v24.13.0` / **npm** `11.12.1` — runtime and package manager.
- **npm audit** — `npm audit` (and `npm audit --json`) — dependency vulnerability scan. Result: 6 high, 0 critical.
- **ESLint** `v9.39.5` — `npm run lint` (runs `eslint .` via `eslint-config-next`). Result: clean.
- **TypeScript** `5.9.3` — `npm run typecheck` (runs `tsc --noEmit`). Result: clean.
- **Vitest** `4.1.10` — `npm test` (runs `vitest run`). Result: 2 test files, 2 tests passed.
- **Ripgrep** — secret detection and marker search via regex patterns for API keys, passwords, tokens, private keys, and `TODO`/`FIXME`/`NOTE`/`HACK`/`XXX`/`WIP`. Result: no secrets, no source markers.
- **git** — `git ls-files`, `git log --all`, `git check-ignore` — tracked-file inventory, history scan, and ignore verification.

Note: Python-specific scanners (`bandit`, `safety`) were not run because the `analysis/` Python workspace does not yet exist. No Java manifests (`pom.xml`, `build.gradle`) are present.
