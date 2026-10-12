# Peranakan Tiles Redesign

> Date: 2026-10-12. Status: draft for review.
> Visual source of truth: `mockups/peranakan-tiles/` (approved by Subashanan on 2026-10-12).
> Content and fixture data: `docs/superpowers/specs/2026-10-12-peranakan-redesign-content.md`.

## 1. Purpose

Rebuild the `apps/web` site in the Peranakan Tiles direction so that it:

- tells a hiring team who Subashanan is in the first screen (name, role, place, contact);
- presents three case studies with provenance on every claim;
- shows the tools and experiments he has already shipped;
- fixes the problems found in the 2026-08-28 review: dead links, no mobile navigation, unloaded fonts, tiny metadata text, placeholder claims, and unused Three.js.

Success means: every nav link resolves, the site reads well from 360px to 1440px, Lighthouse meets the targets in section 10, and no number on the production site is invented.

## 2. What this supersedes

| Earlier decision | Where | Replaced by |
|---|---|---|
| Visual language: near-black space, cyan and violet, monospace metadata | Original spec, "Interaction and Visual Design" | Peranakan Tiles tokens (section 5) |
| Persistent React Three Fiber observatory scene | Original spec and implementation plan Task 3 | Tile mosaic hero and SVG figures. Remove `three`, `@react-three/fiber`, `@react-three/drei`, `@types/three` |
| Direction A "Cosmic Playground (FINALIZED)" | `docs/superpowers/plans/2026-08-28-design-research-and-redesign.md` | This spec |
| Journey "Observe, Discover, Dive, Understand" | Original spec | Four study chapters (section 7.3) |
| NASA as the upcoming third study | Original spec, implementation plan Task 2 | LLM Eval Lab, status "Planned" |
| Brand title "AI Observatory" | `layout.tsx` metadata | Wordmark "Subashanan Nair". Repository name is unchanged |

Unchanged from the original spec: provenance requirements, the `analysis/` Python workspace and artefact manifests, the last-valid-snapshot rule, Vercel as the target, and no auth, CMS, comments or runtime training.

## 3. Scope

**In scope**

- Design tokens, fonts and global styles.
- Tile system: generator, tile, mosaic, frieze and tile frame.
- Shell: header, footer, skip link, not-found page.
- Pages: home, work index, case study template, experiments, about.
- Typed content records for profile, studies and experiments.
- Figure components for all three studies, built against typed fixtures.
- Removal of the Three.js dependencies and of the old home components.
- Metadata, Open Graph image, sitemap and robots updated for the new routes.

**Out of scope** (each has its own plan)

- The Python pipelines that produce real results: Penang Pulse (implementation plan Task 4), Forecasting Lab with Chronos (Task 5, amended), LLM Eval Lab (new spec).
- The artefact manifest schema and its runtime validation (implementation plan Task 2). This spec defines the TypeScript shape the figures consume, so the manifest work has a target.
- The scheduled refresh workflow, Playwright E2E suite and Vercel launch (Tasks 6 and 7).

## 4. Honesty rule for figures

The prototype shows illustrative numbers. Production must not.

- Each study record has an optional `results` field. It is set only from a validated artefact.
- **Production build:** when `results` is missing, the study shows its question, planned method, sources and limitations. The key numbers and the main figure are replaced by one tile-framed panel that says what the figure will show and that the analysis is in progress. No number appears.
- **Development** (`next dev`): when `results` is missing, the figures render from typed fixtures inside a frame labelled "Preview with illustrative data". This lets the full design be reviewed locally without ever shipping fake results.
- The fixture switch is a single check on `process.env.NODE_ENV` in one place (`getStudyResults`). Nothing else branches on environment.

## 5. Design tokens

Defined once as CSS custom properties in `globals.css`.

**Colour**

| Token | Value | Use |
|---|---|---|
| `--peacock` | `#0f4c5c` | Hero and evidence bands |
| `--peacock-deep` | `#0a3843` | "Check it yourself" band, footer band |
| `--porcelain` | `#eef3f1` | Page ground |
| `--ink` | `#13262b` | Body text |
| `--ink-soft` | `#46595e` | Secondary text |
| `--rose`, `--mustard`, `--jade`, `--cobalt` | `#e58fa4`, `#d9a21b`, `#2e9c7a`, `#2b4c9b` | Tile fills, bands, tints |
| `--rose-deep`, `--mustard-deep`, `--jade-deep` | `#c4506e`, `#a87a0c`, `#24805f` | Chart lines and marks, at least 3:1 on porcelain |
| `--warm`, `--sky`, `--rose-tint` | `#f7e7d0`, `#e3eef4`, `#fbeef1` | Study grounds |

`src/styles/palette.ts` is the source of truth for these values; a test keeps `globals.css` in sync and checks contrast.

Per-study accent: each study page gets a theme class (`s-pulse`, `s-forecast`, `s-llm`) that sets `--study-a`, `--study-b` and `--study-ground` from its colour pair. Friezes, number tiles, method tiles, selected states and chart highlights read these variables.

| Study | Motif | `--study-a` | `--study-b` |
|---|---|---|---|
| Penang Pulse | Diamond | mustard | jade |
| Forecasting Lab | Four petals | cobalt | mustard |
| LLM Eval Lab | Flower | rose | cobalt |

**Type:** Bricolage Grotesque only, loaded with `next/font/google` using `axes: ["opsz", "wdth"]` and exposed as `--font-sans`. Headings use high optical size and `wdth` 85 to 92. Minimum rendered text size is 12px everywhere, including SVG labels. No all-caps labels.

**Shape:** tile frames have a 2px ink border, an inner line in `--study-a`, and jade quarter-circles in the four corners. Buttons are pills. No gradients and no soft drop shadows.

**Motion:** only in response to the user (tile turns, chart transitions, tab changes). All of it is disabled under `prefers-reduced-motion`.

## 6. Architecture

Next.js App Router, TypeScript, React Server Components by default. Client components only where there is interaction. Styling is `globals.css` for tokens and base, plus `site.css`, which ports the approved prototype stylesheet with its class names unchanged. Both are imported once in the root layout. This keeps the prototype's cascade intact and avoids renaming every class. No chart or animation library. Charts are hand-written SVG.

Before writing code, read the relevant guide in `node_modules/next/dist/docs/`, as `apps/web/AGENTS.md` requires. This Next.js version differs from older releases.

### 6.1 Routes

| Route | File | Notes |
|---|---|---|
| `/` | `app/page.tsx` | Home |
| `/work` | `app/work/page.tsx` | Work index |
| `/work/[slug]` | `app/work/[slug]/page.tsx` | `generateStaticParams` from the study records; unknown slugs call `notFound()` |
| `/experiments` | `app/experiments/page.tsx` | Filterable list |
| `/about` | `app/about/page.tsx` | Contains `#contact` |
| not found | `app/not-found.tsx` | Tile-framed message with links home and to Work |

Every route is statically generated. `generateMetadata` gives each study its own title and description.

### 6.2 Folder layout (by feature)

```
src/
  app/                      routes as above, plus globals.css, site.css, sitemap, robots and opengraph-image
  styles/                   palette.ts (colour source of truth) and contrast.ts
  content/
    profile.ts              name, role line, contact links
    studies.ts              three StudyRecord objects
    experiments.ts          tool records
    fixtures/               illustrative results per study, dev preview and tests only
    results/                published results; empty until the pipelines publish
  components/
    shell/                  site-header, site-footer
    tiles/                  tile-geometry.ts, tile.tsx, mosaic.tsx, frieze.tsx
    ui/                     tab-list.tsx, toggle-group.tsx
    home/                   hero, tools-preview, about-band
    study/                  study-card, study-run, study-page, chapters, figure-pending, study-theme
    figures/
      penang/               penang-map, district-tiles, district-panel
      forecasting/          forecast-chart, horizon-chart
      llm-eval/             leaderboard, cost-score-chart, error-examples
      chart-utils.ts        scales, ticks, useChartWidth
    experiments/            tool-item, experiment-list
  lib/
    study-results.ts        getStudyResults(slug): the only place the honesty rule lives
```

Files stay under 400 lines. The prototype's `app.js` (397 lines) splits across `tiles/`, `ui/` and `figures/`.

### 6.3 Content types

The full types are in the implementation plan (Task 4, `content/types.ts`). The shape that matters:

- `StudyRecord` holds only what is true before any analysis runs: title, question, status, `plannedAnswer` (no numbers), `figurePlan`, tile and theme, sources (name, publisher, what was used, licence), method steps, limitations, reproduce commands and a discussion note.
- Everything that is a result lives in a per-study results type that extends `BaseResults { answer; keyNumbers (exactly three, each with a required caveat); run: RunInfo; retrieved (source name to ISO date) }`. The answer, key numbers, commit hash and retrieval dates therefore never appear before a real run exists.
- `PenangResults` adds districts, service points and map geometry. `ForecastResults` adds horizons, models with MAE by horizon, and sensor series. `LlmEvalResults` adds tasks with rows (score, interval, cost, latency) and error examples.

### 6.4 Tile system

- `tile-geometry.ts` holds pure functions: `tileMarkup(spec)` returns the tile's inner SVG markup as a string, and helpers build the frieze, thin frieze and method step tiles as CSS `url()` data URIs. The output is deterministic and built only from internal constants.
- `Tile` is a server component that renders an inline SVG with `aria-hidden`.
- `Mosaic` is a client component: a grid of tile buttons, each turning 90 degrees on click or Enter. It has `aria-label`s and a visible focus state. The home hero has 16 mixed tiles; each study hero has 4 of the study's tile.
- `Frieze` renders a repeating strip as a CSS background, from an SVG data URI generated at build time. It is decorative and used only at chapter thresholds.
- The tile frame (border, inner line and jade corners) is the `.tile-frame` CSS class. It needs no component.

### 6.5 Interactive primitives

- `TabList`: `role="tablist"` and `role="tab"` with `aria-selected`, a roving tabindex, and Arrow, Home and End keys. Used for task tabs and sensor tabs.
- `ToggleGroup`: buttons with `aria-pressed`. Used for map categories, model lines and experiment filters.
- `useChartWidth`: a `ResizeObserver` hook so charts draw at real pixel width and SVG text stays at least 12px. Server render uses a default width, so the figure is readable without JavaScript.

## 7. Pages

### 7.1 Shell

- **Header:** wordmark with a small tile on the left; Work, Experiments, About and GitHub on the right. The current page gets `aria-current="page"`. All links stay visible down to 420px; below that, GitHub moves to the footer.
- **Footer:** "Subashanan Nair, Penang", plus "Source for this site" and GitHub links.
- **Skip link:** kept.

### 7.2 Home

1. **Hero** (peacock band): h1 "Subashanan Nair", the role line, "Read the case studies" (to `/work`) and "Get in touch" (to `/about#contact`), and the 16-tile mosaic.
2. **Case studies:** the three study tiles as one joined run, each with status and question. A key number appears only when results exist.
3. **Tools and experiments:** four tools, each with its tile icon, and "See all tools and experiments".
4. **About band** (peacock-deep): two sentences and the contact buttons.

### 7.3 Case study template

The prototype's chapter structure, driven by one `StudyRecord`:

1. **Hero** (peacock): a link back to all case studies, the status pill, h1 title, the question, and a 4-tile mosaic of the study tile. A frieze follows.
2. **The answer** (porcelain): the results answer and the key numbers as three joined tiles when results exist. Otherwise `plannedAnswer` and no numbers. A frieze follows.
3. **The evidence** (peacock band, figures on porcelain panels in tile frames): the study's figures, or `FigurePending`. A frieze follows.
4. **How it was made** (porcelain): the sources table with a frieze header rule, the method as a run of tiles, and limitations with jade diamond bullets.
5. **Check it yourself** (peacock-deep): reproduce commands, plus `RunInfo` when results exist; the discuss link; previous and next study tiles in each study's own colours, wrapping around.

Heading order: h1 title, h2 per chapter, h3 per section, h4 for panel titles.

### 7.4 Figures

| Study | Figures | Interaction |
|---|---|---|
| Penang Pulse | Penang map (island and Seberang Perai, facility points by category) beside five district tiles whose bands encode the under 1 km, 1 to 3 km and over 3 km shares, and a district panel | Category toggles; district tiles work as a tab list and highlight the district on the map |
| Forecasting Lab | Forecast chart (actual plus four models over the next two hours), and error by horizon (chart plus table) | Sensor tabs; model toggles drive both charts |
| LLM Eval Lab | Leaderboard (score with 95% interval, cost per 1k items, median latency), cost against score on a log scale, and error examples | Task tabs drive the leaderboard and the scatter together |

Each model keeps one glaze colour across every chart, legend and table on its page. Colour is never the only cue: every line and mark also has a text label.

The Penang map geometry comes from the Penang Pulse artefact (simplified district boundaries). Until it exists, the prototype's schematic outline is used only in the development preview.

### 7.5 Work index

The peacock hero shows the three study tiles, followed by a frieze. Below it are three large tile cards forming one run: motif, status, title, question, the key number (only with results), data used, and a link.

### 7.6 Experiments

Filter pills: All, Agents and MCP, Libraries, Apps, ML projects. Each tool shows its tile icon, name (linked to GitHub), language and a one-line description. A count line reads "Showing N of 12". With JavaScript off, all items show and the filters are hidden.

### 7.7 About

Intro, "What I work on", "How I work", a plain-text "Toolkit" list (no skill bars), and a contact block with `id="contact"`. No invented employers, degrees, dates or testimonials.

## 8. Content inputs needed from Subashanan

These are needed before launch. If a value is missing, the matching element is hidden rather than shown as a placeholder.

- Email address, LinkedIn URL and CV file (`public/cv.pdf`).
- One-line descriptions for OptimRL, GRPOptim and StatClean. The current ones are guessed from the repository names.
- Confirm the role line and the About copy.

## 9. Error handling and edge cases

- An unknown `/work/[slug]` returns the not-found page.
- A study with no results renders as described in section 4. The build never fails because results are missing.
- A study record missing sources, method steps or limitations fails a unit test and the build.
- An experiment without a description is excluded from the list, and a test reports it.
- Without JavaScript, all text, tables and the default state of every figure are server-rendered. Only toggling and tab switching need JavaScript.

## 10. Quality bar

- Semantic HTML, one h1 per page, visible focus, keyboard-operable tabs and toggles, `prefers-reduced-motion` respected.
- No horizontal page scroll at 360, 390 or 1440px. Wide tables scroll inside their own frame.
- Text contrast of at least 4.5:1, and at least 3:1 for chart lines and marks against their panel.
- Lighthouse on the production home page: Performance 80+, Accessibility 95+, Best Practices 90+, SEO 95+.
- `npm run lint`, `typecheck`, `test` and `build` pass in CI. The CI workflow is unchanged.

## 11. Testing

Unit and component tests use Vitest and Testing Library, as now. Tests are written first for each unit.

- **Tile geometry:** deterministic for the same inputs, and every motif renders shapes.
- **Tokens:** a contrast test computes the WCAG ratio of each glaze against porcelain (at least 3:1) and of text tokens against their grounds (at least 4.5:1).
- **Content:** slugs are unique, every study meets the required field counts, every source has an ISO date, and experiment links point to `github.com/SubaashNair/`.
- **Honesty rule:** `getStudyResults` returns fixtures only outside production. The study page renders no key numbers and shows `FigurePending` when results are missing in production mode.
- **Shell:** nav links by accessible name, and `aria-current` on the active route.
- **TabList and ToggleGroup:** arrow-key navigation, `aria-selected` and `aria-pressed` states.
- **Figures:** each renders from its fixture, the selected task or sensor changes the rendered values, and labels exist for every series.
- **Routes:** `generateStaticParams` returns exactly the three slugs.
- **Replaced tests:** `page.test.tsx` (which asserts the old hero and NASA copy) and `site-header.test.tsx` are rewritten for the new content.
- **Visual check before merging:** screenshots of every page at 390 and 1440px, compared side by side with the prototype.

The Playwright E2E suite stays in implementation plan Task 7.

## 12. Build order (outline for the implementation plan)

1. Tokens, fonts and base styles; remove the Three.js dependencies and the old home components.
2. Tile system and interactive primitives.
3. Content records, result types, fixtures and `getStudyResults`.
4. Shell, home and not-found.
5. Case study template with `FigurePending`, plus the work index.
6. Figures: Penang Pulse, Forecasting Lab, LLM Eval Lab.
7. Experiments and About.
8. Metadata, Open Graph image, sitemap and robots; final responsive and accessibility pass.
