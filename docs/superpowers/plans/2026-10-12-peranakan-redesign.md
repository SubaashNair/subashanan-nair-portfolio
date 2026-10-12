# Peranakan Tiles Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild `apps/web` in the approved Peranakan Tiles design, with five routes, typed content, and interactive figures that never show invented numbers in production.

**Architecture:** Next.js App Router with server components by default and small client islands for the mosaic, tabs, toggles and charts. The prototype stylesheet is ported as one global stylesheet so class names match the approved prototype exactly. Study results come through one function, `getStudyResults`. It returns published results, or illustrative fixtures outside production, or `null`.

**Tech Stack:** Next.js 16.3 (App Router), React 19.2, TypeScript 5.9, Vitest 4 with Testing Library and jsdom, `next/font/google` (Bricolage Grotesque), and `next/og`. No new runtime dependencies.

**Spec:** `docs/superpowers/specs/2026-10-12-peranakan-redesign-design.md`. Content and fixture data: `docs/superpowers/specs/2026-10-12-peranakan-redesign-content.md`. Visual source of truth: `mockups/peranakan-tiles/` (open `mockups/peranakan-tiles/index.html` in a browser).

## Global Constraints

- Brand and displayed name: **Subashanan Nair**. GitHub handle and URLs stay `SubaashNair` (for example `https://github.com/SubaashNair`).
- No invented numbers in a production build. Only `src/lib/study-results.ts` may branch on `NODE_ENV`.
- Remove `three`, `@react-three/fiber`, `@react-three/drei` and `@types/three`. Add no runtime dependencies.
- Font: Bricolage Grotesque only, via `next/font/google`, with `axes: ["opsz", "wdth"]` and CSS variable `--font-sans`.
- Minimum rendered text size is 12px everywhere, including SVG labels. Text contrast is at least 4.5:1. Chart lines and marks are at least 3:1 against their panel.
- Copy rules: sentence case, no all-caps labels, no "→" or "↗" in link text, no em or en dashes in prose (number ranges in tables like "84–90" are fine), no middle-dot meta strings.
- Motion only in response to the user, and none under `prefers-reduced-motion`.
- Files stay under 400 lines. Use immutable updates: never mutate props or state, return new arrays and sets.
- `apps/web/AGENTS.md` applies: read the relevant guide in `node_modules/next/dist/docs/` before using a Next.js API. In particular, `params` in pages and `generateMetadata` is a `Promise`.
- Commands run from the repository root: `npm test`, `npm run lint`, `npm run typecheck` and `npm run build`. To run one test file: `npm test --workspace web -- src/path/to/file.test.tsx`.

## Review Focus

1. **A production build with no published results shows no fixture numbers and no "Preview" label.** Test: Task 6, `study-page.test.tsx` "production mode".
2. **With JavaScript off, every figure still shows its default state.** Test: Tasks 7, 8 and 9 render each figure with `renderToStaticMarkup` and assert the SVG content exists.
3. **An unknown study URL such as `/work/foo` gives a 404, not a crash.** Test: Task 6, `page.test.tsx` for the `[slug]` route.
4. **With JavaScript off, the experiments page shows all 12 tools and no dead filter buttons.** Test: Task 10, `experiment-list.test.tsx` static markup.
5. **No horizontal page scroll and no text under 12px at 360px.** Check: Task 11, the layout script.

## Before you start

The branch `codebase-review-plan` has uncommitted work from 2026-08-28: `.github/`, `CONTRIBUTING.md`, the `apps/web` component split, `mockups/` and docs. Ask Subashanan whether to commit it as `chore: snapshot pre-redesign work` before Task 1. Do not discard it.

## File map

```
apps/web/
  package.json                                   remove Three.js deps (Task 1)
  public/robots.txt, public/sitemap.xml          delete (Task 11)
  src/styles/palette.ts, contrast.ts             colour source of truth (Task 1)
  src/app/globals.css                            tokens and base (Task 1)
  src/app/site.css                               ported prototype styles (Task 1)
  src/app/layout.tsx                             font, stylesheets, metadata (Tasks 1, 11)
  src/app/page.tsx                               home (Task 5)
  src/app/not-found.tsx                          (Task 5)
  src/app/work/page.tsx                          work index (Task 6)
  src/app/work/[slug]/page.tsx                   study route (Task 6)
  src/app/experiments/page.tsx                   (Task 10)
  src/app/about/page.tsx                         (Task 10)
  src/app/sitemap.ts, robots.ts, opengraph-image.tsx   (Task 11)
  src/components/tiles/tile-geometry.ts, tile.tsx, mosaic.tsx, frieze.tsx   (Task 2)
  src/components/ui/tab-list.tsx, toggle-group.tsx                          (Task 3)
  src/components/figures/chart-utils.ts, use-chart-width.ts                 (Task 3)
  src/content/types.ts, profile.ts, studies.ts, experiments.ts              (Task 4)
  src/content/fixtures/penang.ts, forecasting.ts, llm-eval.ts, index.ts     (Task 4)
  src/content/results/index.ts                                              (Task 4)
  src/lib/study-results.ts                                                  (Task 4)
  src/components/shell/site-header.tsx, site-footer.tsx                     (Task 5)
  src/components/home/hero.tsx, tools-preview.tsx, about-band.tsx           (Task 5)
  src/components/experiments/tool-item.tsx                                  (Task 5)
  src/components/study/study-card.tsx, study-run.tsx                        (Task 5)
  src/components/study/study-page.tsx, chapters.tsx, figure-pending.tsx, study-theme.ts   (Task 6)
  src/components/figures/registry.ts                                        (Task 6)
  src/components/figures/penang/*        (Task 7)
  src/components/figures/forecasting/*   (Task 8)
  src/components/figures/llm-eval/*      (Task 9)
  src/components/experiments/experiment-list.tsx                            (Task 10)
```

Delete in Task 5: `src/components/home/signals-section.tsx`, `src/components/home/study-card.tsx` and the old `src/components/home/hero.tsx`, which is rewritten.

---

### Task 1: Foundation: palette, contrast test, font, stylesheets, remove Three.js

**Files:**
- Create: `apps/web/src/styles/palette.ts`, `apps/web/src/styles/contrast.ts`, `apps/web/src/app/site.css`
- Replace: `apps/web/src/app/globals.css`, `apps/web/src/app/layout.tsx`
- Modify: `apps/web/package.json`, `package-lock.json`
- Test: `apps/web/src/styles/palette.test.ts`

**Interfaces:**
- Produces: `palette` (readonly record of hex strings), `type PaletteKey`, `contrastRatio(a: string, b: string): number`, and CSS custom properties named in kebab case (`peacockDeep` becomes `--peacock-deep`).

- [ ] **Step 1: Write the failing test**

`apps/web/src/styles/palette.test.ts`:

```ts
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

import { contrastRatio } from "./contrast";
import { palette, type PaletteKey } from "./palette";

const kebab = (key: string): string => key.replace(/[A-Z]/g, (c) => `-${c.toLowerCase()}`);

describe("palette", () => {
  it("matches the CSS custom properties in globals.css", () => {
    const css = readFileSync(resolve(__dirname, "../app/globals.css"), "utf8");
    for (const key of Object.keys(palette) as PaletteKey[]) {
      expect(css).toContain(`--${kebab(key)}: ${palette[key]};`);
    }
  });

  it.each([
    ["ink", "porcelain"], ["inkSoft", "porcelain"], ["inkSoft", "warm"], ["inkSoft", "sky"], ["inkSoft", "roseTint"],
    ["porcelain", "peacock"], ["onPeacock", "peacock"], ["onPeacockSoft", "peacock"], ["onPeacockSoft", "peacockDeep"],
    ["ink", "mustard"],
  ] as const)("text %s on %s is at least 4.5:1", (fg, bg) => {
    expect(contrastRatio(palette[fg], palette[bg])).toBeGreaterThanOrEqual(4.5);
  });

  it.each([
    ["roseDeep", "porcelain"], ["mustardDeep", "porcelain"], ["jadeDeep", "porcelain"], ["cobalt", "porcelain"],
    ["roseDeep", "sky"], ["mustardDeep", "sky"], ["jadeDeep", "sky"], ["cobalt", "sky"],
  ] as const)("chart glaze %s on %s is at least 3:1", (fg, bg) => {
    expect(contrastRatio(palette[fg], palette[bg])).toBeGreaterThanOrEqual(3);
  });

  it("computes the WCAG ratio for black on white", () => {
    expect(contrastRatio("#000000", "#ffffff")).toBeCloseTo(21, 5);
  });
});
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `npm test --workspace web -- src/styles/palette.test.ts`
Expected: FAIL with "Failed to resolve import ./contrast".

- [ ] **Step 3: Write the palette and contrast helpers**

`apps/web/src/styles/palette.ts`:

```ts
// The one source of truth for colour. globals.css mirrors these values; palette.test.ts keeps them in sync.
export const palette = {
  peacock: "#0f4c5c",
  peacockDeep: "#0a3843",
  porcelain: "#eef3f1",
  ink: "#13262b",
  inkSoft: "#46595e",
  rose: "#e58fa4",
  mustard: "#d9a21b",
  jade: "#2e9c7a",
  cobalt: "#2b4c9b",
  warm: "#f7e7d0",
  sky: "#e3eef4",
  roseTint: "#fbeef1",
  onPeacock: "#d6e4e1",
  onPeacockSoft: "#b9cfca",
  // Deeper glazes for chart lines and marks; the light colours above stay for fills.
  mustardDeep: "#a87a0c",
  roseDeep: "#c4506e",
  jadeDeep: "#24805f",
} as const;

export type PaletteKey = keyof typeof palette;
```

`apps/web/src/styles/contrast.ts`:

```ts
const channel = (value: number): number => {
  const c = value / 255;
  return c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4;
};

const luminance = (hex: string): number => {
  const h = hex.replace("#", "");
  const [r, g, b] = [0, 2, 4].map((i) => channel(parseInt(h.slice(i, i + 2), 16)));
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
};

/** WCAG 2 contrast ratio between two #rrggbb colours. */
export function contrastRatio(a: string, b: string): number {
  const [hi, lo] = [luminance(a), luminance(b)].sort((x, y) => y - x);
  return (hi + 0.05) / (lo + 0.05);
}
```

- [ ] **Step 4: Replace `globals.css` with the tokens and base styles**

Overwrite `apps/web/src/app/globals.css` with exactly:

```css
:root {
  --peacock: #0f4c5c;
  --peacock-deep: #0a3843;
  --porcelain: #eef3f1;
  --ink: #13262b;
  --ink-soft: #46595e;
  --rose: #e58fa4;
  --mustard: #d9a21b;
  --jade: #2e9c7a;
  --cobalt: #2b4c9b;
  --warm: #f7e7d0;
  --sky: #e3eef4;
  --rose-tint: #fbeef1;
  --on-peacock: #d6e4e1;
  --on-peacock-soft: #b9cfca;
  --mustard-deep: #a87a0c;
  --rose-deep: #c4506e;
  --jade-deep: #24805f;
  --line: rgba(19, 38, 43, .12);
}
* { box-sizing: border-box; }
html { -webkit-text-size-adjust: 100%; }
body {
  margin: 0; background: var(--porcelain); color: var(--ink);
  font: 17px/1.55 var(--font-sans), system-ui, sans-serif;
  font-variation-settings: "opsz" 14;
  overflow-x: hidden;
}
a { color: inherit; }
a:hover { color: var(--cobalt); }
.top a:hover, .about-band a:hover { color: var(--mustard); }
:focus-visible { outline: 3px solid var(--cobalt); outline-offset: 3px; }
.top :focus-visible, .about-band :focus-visible { outline-color: var(--mustard); }
.wrap { max-width: 1240px; margin: 0 auto; padding: 0 28px; }
.sr { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); white-space: nowrap; }
.skip { position: absolute; left: 12px; top: -80px; z-index: 30; background: var(--mustard); color: var(--ink); padding: 10px 18px; border-radius: 999px; font-weight: 650; text-decoration: none; }
.skip:focus { top: 12px; }
.preview-flag { display: inline-block; margin: 0 0 18px; padding: 6px 14px; border-radius: 999px; background: var(--mustard); color: var(--ink); font-size: 14px; font-weight: 650; }
```

- [ ] **Step 5: Port the prototype stylesheet to `site.css`**

Create `apps/web/src/app/site.css`. Copy `mockups/peranakan-tiles/style.css` from line 42 (`/* Header */`) to the end of the file, then make exactly these edits:
1. Delete the `.mock-note { position: fixed; ... }` rule.
2. Inside the `@media (max-width: 900px)` block, delete the `.mock-note { position: static; ... }` line.
3. Replace `#board #metric-head { width: 48%; }` with `.board-metric { width: 48%; }`.
4. Replace `.map .pt.off { opacity: 0; }` with `.map .off .pt { opacity: 0; }`. Points sit inside a wrapper `g`, so hiding them never overwrites a point's own class.

Do not rename any other class. Components in later tasks use these class names exactly.

- [ ] **Step 6: Load the font and both stylesheets in the layout**

Replace `apps/web/src/app/layout.tsx` with:

```tsx
import type { Metadata } from "next";
import { Bricolage_Grotesque } from "next/font/google";
import type { ReactNode } from "react";

import { SiteFooter } from "@/components/shell/site-footer";
import { SiteHeader } from "@/components/shell/site-header";

import "./globals.css";
import "./site.css";

const bricolage = Bricolage_Grotesque({
  subsets: ["latin"],
  axes: ["opsz", "wdth"],
  variable: "--font-sans",
  display: "swap",
});

export const metadata: Metadata = {
  title: "Subashanan Nair, data scientist in Penang",
  description: "Reproducible ML and LLM case studies on Malaysian public data, with sources, code and limits for every result.",
};

export default function RootLayout({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <html lang="en" className={bricolage.variable}>
      <body>
        <a className="skip" href="#main">Skip to content</a>
        <SiteHeader />
        {children}
        <SiteFooter />
      </body>
    </html>
  );
}
```

The old home page looks unstyled until Task 5. That is expected.

- [ ] **Step 7: Remove the Three.js packages**

Run: `npm uninstall three @react-three/fiber @react-three/drei @types/three --workspace web`
Then run `grep -rn "three\|react-three" apps/web/src`. Expected: no matches.

- [ ] **Step 8: Run the tests and checks**

Run: `npm test --workspace web -- src/styles/palette.test.ts`, then `npm run typecheck` and `npm run build`.
Expected: the palette tests PASS, the typecheck passes, and the build succeeds.

- [ ] **Step 9: Commit**

```bash
git add apps/web/src/styles apps/web/src/app/globals.css apps/web/src/app/site.css apps/web/src/app/layout.tsx apps/web/package.json package-lock.json
git commit -m "feat: add Peranakan palette, font and ported styles; drop Three.js"
```

---

### Task 2: Tile system

**Files:**
- Create: `apps/web/src/components/tiles/tile-geometry.ts`, `tile.tsx`, `mosaic.tsx`, `frieze.tsx`
- Test: `apps/web/src/components/tiles/tile-geometry.test.ts`, `apps/web/src/components/tiles/mosaic.test.tsx`

**Interfaces:**
- Consumes: `palette` from Task 1.
- Produces:
  - `type Motif = "flower" | "star" | "diamond" | "petals"`
  - `type TileColour = "rose" | "mustard" | "jade" | "cobalt" | "peacock"`
  - `type Ground = "porcelain" | "warm" | "sky" | "roseTint"`
  - `interface TileSpec { motif; a; b; ground }`
  - `tileMarkup(spec: TileSpec): string`, `mixedTile(i: number): TileSpec`
  - `friezeUri(markups: readonly string[]): string`, `borderTileMarkup(spec: TileSpec, tint: Ground): string`
  - `thinFriezeUri(spec: TileSpec, tint: Ground): string`, `stepTileUri(fill: TileColour, tint: Ground): string`
  - Components: `<Tile spec className? />`, `<Mosaic tiles label pair? />` (client), `<Frieze markups />`
  - The tile frame is the `.tile-frame` CSS class from `site.css`; it has no component.

- [ ] **Step 1: Write the failing tests**

`apps/web/src/components/tiles/tile-geometry.test.ts`:

```ts
import { describe, expect, it } from "vitest";

import { friezeUri, mixedTile, tileMarkup, type Motif } from "./tile-geometry";

describe("tile geometry", () => {
  it("is deterministic", () => {
    const spec = { motif: "diamond", a: "mustard", b: "jade", ground: "warm" } as const;
    expect(tileMarkup(spec)).toBe(tileMarkup(spec));
  });

  it("draws a different centre for every motif, with jade corners and a ground", () => {
    const motifs: Motif[] = ["flower", "star", "diamond", "petals"];
    const out = motifs.map((motif) => tileMarkup({ motif, a: "cobalt", b: "mustard", ground: "porcelain" }));
    expect(new Set(out).size).toBe(4);
    for (const svg of out) {
      expect(svg).toContain('fill="#2e9c7a"');
      expect(svg).toContain('<rect width="100" height="100" fill="#eef3f1"/>');
    }
  });

  it("reproduces the prototype home mosaic order", () => {
    expect(mixedTile(0)).toEqual({ motif: "star", a: "cobalt", b: "mustard", ground: "porcelain" });
    expect(mixedTile(3)).toEqual({ motif: "diamond", a: "mustard", b: "jade", ground: "warm" });
  });

  it("builds a CSS url() with one tile width per markup", () => {
    const uri = friezeUri(["<g/>", "<g/>"]);
    expect(uri.startsWith('url("data:image/svg+xml,')).toBe(true);
    expect(decodeURIComponent(uri)).toContain('viewBox="0 0 200 100"');
  });
});
```

`apps/web/src/components/tiles/mosaic.test.tsx`:

```tsx
import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { Mosaic } from "./mosaic";
import { mixedTile } from "./tile-geometry";

describe("Mosaic", () => {
  it("turns only the clicked tile by 90 degrees each time", () => {
    render(<Mosaic tiles={[mixedTile(0), mixedTile(1)]} label="Decorative tiles" />);
    const first = screen.getByRole("button", { name: "Turn tile 1" });
    fireEvent.click(first);
    fireEvent.click(first);
    expect(first).toHaveStyle({ transform: "rotate(180deg)" });
    expect(screen.getByRole("button", { name: "Turn tile 2" })).toHaveStyle({ transform: "rotate(0deg)" });
    expect(screen.getByRole("group", { name: "Decorative tiles" })).toBeInTheDocument();
  });
});
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `npm test --workspace web -- src/components/tiles`
Expected: FAIL with "Failed to resolve import ./tile-geometry".

- [ ] **Step 3: Write the geometry**

`apps/web/src/components/tiles/tile-geometry.ts`:

```ts
import { palette } from "@/styles/palette";

export type Motif = "flower" | "star" | "diamond" | "petals";
export type TileColour = "rose" | "mustard" | "jade" | "cobalt" | "peacock";
export type Ground = "porcelain" | "warm" | "sky" | "roseTint";

export interface TileSpec {
  motif: Motif;
  a: TileColour;
  b: TileColour;
  ground: Ground;
}

const MOTIFS: Record<Motif, (a: string, b: string) => string> = {
  flower: (a, b) => `<g fill="${a}"><circle cx="50" cy="35" r="13"/><circle cx="50" cy="65" r="13"/><circle cx="35" cy="50" r="13"/><circle cx="65" cy="50" r="13"/></g><circle cx="50" cy="50" r="7" fill="${b}"/>`,
  star: (a, b) => `<g fill="${a}"><rect x="30" y="30" width="40" height="40"/><rect x="30" y="30" width="40" height="40" transform="rotate(45 50 50)"/></g><circle cx="50" cy="50" r="9" fill="${b}"/>`,
  diamond: (a, b) => `<path d="M50 18 L82 50 L50 82 L18 50Z" fill="${a}"/><path d="M50 34 L66 50 L50 66 L34 50Z" fill="${b}"/>`,
  petals: (a, b) => `<g fill="${a}"><ellipse cx="50" cy="32" rx="9" ry="17"/><ellipse cx="50" cy="68" rx="9" ry="17"/><ellipse cx="32" cy="50" rx="17" ry="9"/><ellipse cx="68" cy="50" rx="17" ry="9"/></g><circle cx="50" cy="50" r="8" fill="${b}"/>`,
};

// Corner quarter-circles share one colour, so neighbouring tiles join into a second pattern, as real Peranakan tiles do.
const corners = (fill: string): string =>
  `<g fill="${fill}"><path d="M0 0h18a18 18 0 0 1-18 18z"/><path d="M100 0v18a18 18 0 0 1-18-18z"/><path d="M0 100v-18a18 18 0 0 1 18 18z"/><path d="M100 100h-18a18 18 0 0 1 18-18z"/></g>`;
const frame = (stroke: string): string =>
  `<rect x="6" y="6" width="88" height="88" fill="none" stroke="${stroke}" stroke-width="1.5" opacity=".6"/>`;

/** Inner SVG markup for one 100x100 tile. Inputs are internal constants, never user text. */
export function tileMarkup(spec: TileSpec): string {
  const a = palette[spec.a];
  const b = palette[spec.b];
  return `<rect width="100" height="100" fill="${palette[spec.ground]}"/>${corners(palette.jade)}${frame(a)}${MOTIFS[spec.motif](a, b)}`;
}

const MIX_PAIRS: ReadonlyArray<readonly [TileColour, TileColour]> = [
  ["cobalt", "mustard"], ["jade", "rose"], ["rose", "cobalt"], ["mustard", "jade"], ["peacock", "rose"],
];
const MIX_MOTIFS: readonly Motif[] = ["flower", "star", "diamond", "petals"];
const MIX_GROUNDS: readonly Ground[] = ["porcelain", "warm", "porcelain", "sky"];

/** The i-th tile of the mixed home mosaic, matching the approved prototype. */
export function mixedTile(i: number): TileSpec {
  const [a, b] = MIX_PAIRS[i % MIX_PAIRS.length];
  return { motif: MIX_MOTIFS[(i * 7 + 1) % MIX_MOTIFS.length], a, b, ground: MIX_GROUNDS[(i * 3) % MIX_GROUNDS.length] };
}

const svgUri = (viewBox: string, body: string): string =>
  `url("data:image/svg+xml,${encodeURIComponent(`<svg xmlns="http://www.w3.org/2000/svg" viewBox="${viewBox}">${body}</svg>`)}")`;

/** A repeating strip of tiles laid side by side, for the chapter frieze. */
export function friezeUri(markups: readonly string[]): string {
  const body = markups.map((m, i) => `<g transform="translate(${i * 100} 0)">${m}</g>`).join("");
  return svgUri(`0 0 ${markups.length * 100} 100`, body);
}

/** The small border tile that alternates with a study's own tile in its frieze. */
export function borderTileMarkup(spec: TileSpec, tint: Ground): string {
  return `<rect width="100" height="100" fill="${palette[tint]}"/>${corners(palette.jade)}${frame(palette[spec.a])}<path d="M50 28L72 50L50 72L28 50Z" fill="${palette[spec.b]}"/><circle cx="50" cy="50" r="6" fill="${palette[spec.a]}"/>`;
}

/** The thin patterned rule used under table headers. */
export function thinFriezeUri(spec: TileSpec, tint: Ground): string {
  return svgUri(
    "0 0 40 10",
    `<rect width="40" height="10" fill="${palette[tint]}"/><path d="M10 1L14 5L10 9L6 5Z" fill="${palette[spec.a]}"/><path d="M30 1L34 5L30 9L26 5Z" fill="${palette[spec.b]}"/><g fill="${palette.jade}"><circle cx="0" cy="5" r="2.2"/><circle cx="20" cy="5" r="2.2"/><circle cx="40" cy="5" r="2.2"/></g>`,
  );
}

/** The diamond tile behind each numbered method step. */
export function stepTileUri(fill: TileColour, tint: Ground): string {
  return svgUri("0 0 100 100", `<rect width="100" height="100" fill="${palette[tint]}"/>${corners(palette.jade)}<path d="M50 13L87 50L50 87L13 50Z" fill="${palette[fill]}"/>`);
}
```

- [ ] **Step 4: Write the components**

`apps/web/src/components/tiles/tile.tsx`:

```tsx
import { tileMarkup, type TileSpec } from "./tile-geometry";

interface TileProps {
  spec: TileSpec;
  className?: string;
}

/** Decorative tile. The markup comes from internal constants only, so inner HTML is safe here. */
export function Tile({ spec, className }: TileProps) {
  return <svg className={className} viewBox="0 0 100 100" aria-hidden="true" dangerouslySetInnerHTML={{ __html: tileMarkup(spec) }} />;
}
```

`apps/web/src/components/tiles/mosaic.tsx`:

```tsx
"use client";

import { useState } from "react";

import { Tile } from "./tile";
import type { TileSpec } from "./tile-geometry";

interface MosaicProps {
  tiles: readonly TileSpec[];
  label: string;
  pair?: boolean;
}

export function Mosaic({ tiles, label, pair = false }: MosaicProps) {
  const [turns, setTurns] = useState<readonly number[]>(() => tiles.map(() => 0));
  const turn = (index: number) => setTurns((prev) => prev.map((n, i) => (i === index ? n + 1 : n)));

  return (
    <div className={pair ? "mosaic pair" : "mosaic"} role="group" aria-label={label}>
      {tiles.map((spec, i) => (
        <button key={i} type="button" aria-label={`Turn tile ${i + 1}`} style={{ transform: `rotate(${turns[i] * 90}deg)` }} onClick={() => turn(i)}>
          <Tile spec={spec} />
        </button>
      ))}
    </div>
  );
}
```

`apps/web/src/components/tiles/frieze.tsx`:

```tsx
import type { CSSProperties } from "react";

import { friezeUri } from "./tile-geometry";

interface FriezeProps {
  markups: readonly string[];
}

/** Decorative border strip, used only at chapter thresholds. */
export function Frieze({ markups }: FriezeProps) {
  return <div className="frieze" aria-hidden="true" style={{ "--frieze": friezeUri(markups) } as CSSProperties} />;
}
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `npm test --workspace web -- src/components/tiles`
Expected: PASS (5 tests).

- [ ] **Step 6: Commit**

```bash
git add apps/web/src/components/tiles
git commit -m "feat: add Peranakan tile generator, mosaic and frieze"
```

---

### Task 3: Interactive primitives and chart utilities

**Files:**
- Create: `apps/web/src/components/ui/tab-list.tsx`, `apps/web/src/components/ui/toggle-group.tsx`, `apps/web/src/components/figures/chart-utils.ts`, `apps/web/src/components/figures/use-chart-width.ts`
- Test: `apps/web/src/components/ui/tab-list.test.tsx`, `apps/web/src/components/ui/toggle-group.test.tsx`, `apps/web/src/components/figures/chart-utils.test.ts`

**Interfaces:**
- Produces:
  - `TabList`, with props `{ items: readonly TabItem[]; selected: string; onSelect: (id: string) => void; idPrefix: string; panelId: string; label?: string; labelledBy?: string; className?: string; tabClassName?: string }`
  - `interface TabItem { id: string; label: ReactNode }` and `tabId(prefix: string, id: string): string`
  - `ToggleGroup`, with props `{ label: string; items: readonly ToggleItem[]; pressed: ReadonlySet<string>; onChange: (next: ReadonlySet<string>) => void; mode?: "multi" | "single"; prefix?: string; className?: string }`
  - `interface ToggleItem { id: string; label: ReactNode }`
  - `scale(d0, d1, r0, r1): (v: number) => number`, `seeded(seed: number): () => number`, `gauss(rand: () => number): number`, `pathOf(points: ReadonlyArray<readonly [number, number]>): string`, `clock(minutes: number): string`
  - `useChartWidth(ref: RefObject<HTMLElement | null>, fallback?: number): number`

- [ ] **Step 1: Write the failing tests**

`apps/web/src/components/ui/tab-list.test.tsx`:

```tsx
import { fireEvent, render, screen } from "@testing-library/react";
import { useState } from "react";
import { describe, expect, it } from "vitest";

import { TabList } from "./tab-list";

function Harness() {
  const [selected, setSelected] = useState("a");
  return (
    <TabList
      label="Tasks"
      idPrefix="t"
      panelId="t-panel"
      selected={selected}
      onSelect={setSelected}
      items={[{ id: "a", label: "Alpha" }, { id: "b", label: "Beta" }, { id: "c", label: "Gamma" }]}
    />
  );
}

describe("TabList", () => {
  it("marks one tab selected and keeps only it in the tab order", () => {
    render(<Harness />);
    expect(screen.getByRole("tab", { name: "Alpha" })).toHaveAttribute("aria-selected", "true");
    expect(screen.getByRole("tab", { name: "Alpha" })).toHaveAttribute("tabindex", "0");
    expect(screen.getByRole("tab", { name: "Beta" })).toHaveAttribute("tabindex", "-1");
    expect(screen.getByRole("tab", { name: "Beta" })).toHaveAttribute("aria-controls", "t-panel");
  });

  it("moves with arrow keys, wraps around, and supports Home and End", () => {
    render(<Harness />);
    fireEvent.keyDown(screen.getByRole("tab", { name: "Alpha" }), { key: "ArrowLeft" });
    expect(screen.getByRole("tab", { name: "Gamma" })).toHaveAttribute("aria-selected", "true");
    expect(screen.getByRole("tab", { name: "Gamma" })).toHaveFocus();
    fireEvent.keyDown(screen.getByRole("tab", { name: "Gamma" }), { key: "Home" });
    expect(screen.getByRole("tab", { name: "Alpha" })).toHaveAttribute("aria-selected", "true");
    fireEvent.keyDown(screen.getByRole("tab", { name: "Alpha" }), { key: "End" });
    expect(screen.getByRole("tab", { name: "Gamma" })).toHaveAttribute("aria-selected", "true");
  });

  it("selects on click", () => {
    render(<Harness />);
    fireEvent.click(screen.getByRole("tab", { name: "Beta" }));
    expect(screen.getByRole("tab", { name: "Beta" })).toHaveAttribute("aria-selected", "true");
  });
});
```

`apps/web/src/components/ui/toggle-group.test.tsx`:

```tsx
import { fireEvent, render, screen } from "@testing-library/react";
import { useState } from "react";
import { describe, expect, it } from "vitest";

import { ToggleGroup } from "./toggle-group";

const items = [{ id: "x", label: "Clinics" }, { id: "y", label: "Schools" }];

function Harness({ mode }: { mode: "multi" | "single" }) {
  const [pressed, setPressed] = useState<ReadonlySet<string>>(new Set(mode === "multi" ? ["x", "y"] : ["x"]));
  return <ToggleGroup label="Show" items={items} pressed={pressed} onChange={setPressed} mode={mode} />;
}

describe("ToggleGroup", () => {
  it("toggles each button independently in multi mode", () => {
    render(<Harness mode="multi" />);
    fireEvent.click(screen.getByRole("button", { name: "Clinics" }));
    expect(screen.getByRole("button", { name: "Clinics" })).toHaveAttribute("aria-pressed", "false");
    expect(screen.getByRole("button", { name: "Schools" })).toHaveAttribute("aria-pressed", "true");
    expect(screen.getByRole("group", { name: "Show" })).toBeInTheDocument();
  });

  it("keeps exactly one pressed in single mode", () => {
    render(<Harness mode="single" />);
    fireEvent.click(screen.getByRole("button", { name: "Schools" }));
    expect(screen.getByRole("button", { name: "Clinics" })).toHaveAttribute("aria-pressed", "false");
    expect(screen.getByRole("button", { name: "Schools" })).toHaveAttribute("aria-pressed", "true");
  });
});
```

`apps/web/src/components/figures/chart-utils.test.ts`:

```ts
import { describe, expect, it } from "vitest";

import { clock, pathOf, scale, seeded } from "./chart-utils";

describe("chart utils", () => {
  it("maps a domain onto a range, including reversed ranges", () => {
    const y = scale(0, 10, 100, 0);
    expect(y(0)).toBe(100);
    expect(y(5)).toBe(50);
    expect(y(10)).toBe(0);
  });

  it("gives the same sequence for the same seed", () => {
    const a = seeded(7);
    const b = seeded(7);
    expect([a(), a(), a()]).toEqual([b(), b(), b()]);
  });

  it("builds an SVG path", () => {
    expect(pathOf([[0, 0], [10.04, 5]])).toBe("M0.0 0.0L10.0 5.0");
  });

  it("formats minutes after midnight as a clock", () => {
    expect(clock(17 * 60 + 5)).toBe("17:05");
  });
});
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `npm test --workspace web -- src/components/ui src/components/figures/chart-utils.test.ts`
Expected: FAIL with "Failed to resolve import".

- [ ] **Step 3: Write the implementations**

`apps/web/src/components/ui/tab-list.tsx`:

```tsx
"use client";

import { useRef, type KeyboardEvent, type ReactNode } from "react";

export interface TabItem {
  id: string;
  label: ReactNode;
}

interface TabListProps {
  items: readonly TabItem[];
  selected: string;
  onSelect: (id: string) => void;
  idPrefix: string;
  panelId: string;
  label?: string;
  labelledBy?: string;
  className?: string;
  tabClassName?: string;
}

export const tabId = (prefix: string, id: string): string => `${prefix}-tab-${id}`;

const STEP: Readonly<Record<string, number>> = { ArrowRight: 1, ArrowDown: 1, ArrowLeft: -1, ArrowUp: -1 };

export function TabList({ items, selected, onSelect, idPrefix, panelId, label, labelledBy, className = "controls", tabClassName = "pill" }: TabListProps) {
  const refs = useRef<Array<HTMLButtonElement | null>>([]);

  const moveTo = (index: number) => {
    const i = (index + items.length) % items.length;
    onSelect(items[i].id);
    refs.current[i]?.focus();
  };

  const onKeyDown = (event: KeyboardEvent<HTMLButtonElement>, index: number) => {
    if (event.key in STEP) moveTo(index + STEP[event.key]);
    else if (event.key === "Home") moveTo(0);
    else if (event.key === "End") moveTo(items.length - 1);
    else return;
    event.preventDefault();
  };

  return (
    <div role="tablist" aria-label={label} aria-labelledby={labelledBy} className={className}>
      {items.map((item, i) => {
        const on = item.id === selected;
        return (
          <button
            key={item.id}
            ref={(el) => {
              refs.current[i] = el;
            }}
            type="button"
            role="tab"
            id={tabId(idPrefix, item.id)}
            aria-controls={panelId}
            aria-selected={on}
            tabIndex={on ? 0 : -1}
            className={tabClassName}
            onClick={() => onSelect(item.id)}
            onKeyDown={(e) => onKeyDown(e, i)}
          >
            {item.label}
          </button>
        );
      })}
    </div>
  );
}
```

`apps/web/src/components/ui/toggle-group.tsx`:

```tsx
"use client";

import type { ReactNode } from "react";

export interface ToggleItem {
  id: string;
  label: ReactNode;
}

interface ToggleGroupProps {
  label: string;
  items: readonly ToggleItem[];
  pressed: ReadonlySet<string>;
  onChange: (next: ReadonlySet<string>) => void;
  mode?: "multi" | "single";
  prefix?: string;
  className?: string;
}

export function ToggleGroup({ label, items, pressed, onChange, mode = "multi", prefix, className = "controls" }: ToggleGroupProps) {
  const toggle = (id: string) => {
    if (mode === "single") return onChange(new Set([id]));
    onChange(new Set(pressed.has(id) ? [...pressed].filter((x) => x !== id) : [...pressed, id]));
  };

  return (
    <div role="group" aria-label={label} className={className}>
      {prefix && <span className="label">{prefix}</span>}
      {items.map((item) => (
        <button key={item.id} type="button" className={mode === "multi" ? "pill toggle" : "pill"} aria-pressed={pressed.has(item.id)} onClick={() => toggle(item.id)}>
          {item.label}
        </button>
      ))}
    </div>
  );
}
```

`apps/web/src/components/figures/chart-utils.ts`:

```ts
export const scale =
  (d0: number, d1: number, r0: number, r1: number) =>
  (v: number): number =>
    r0 + ((v - d0) / (d1 - d0)) * (r1 - r0);

/** Park-Miller generator, so illustrative data is stable between renders. */
export function seeded(seed: number): () => number {
  let s = seed;
  return () => {
    s = (s * 16807) % 2147483647;
    return s / 2147483647;
  };
}

/** Roughly normal noise with unit spread, from four uniform draws. */
export const gauss = (rand: () => number): number => (rand() + rand() + rand() + rand() - 2) * 1.73;

export const pathOf = (points: ReadonlyArray<readonly [number, number]>): string =>
  points.map(([x, y], i) => `${i ? "L" : "M"}${x.toFixed(1)} ${y.toFixed(1)}`).join("");

export const clock = (minutes: number): string =>
  `${String(Math.floor(minutes / 60)).padStart(2, "0")}:${String(minutes % 60).padStart(2, "0")}`;
```

`apps/web/src/components/figures/use-chart-width.ts`:

```ts
"use client";

import { useEffect, useState, type RefObject } from "react";

/** Width of the element in CSS pixels, so SVG text is drawn at its real size. The fallback is used for the server render. */
export function useChartWidth(ref: RefObject<HTMLElement | null>, fallback = 640): number {
  const [width, setWidth] = useState(fallback);
  useEffect(() => {
    const el = ref.current;
    if (!el || typeof ResizeObserver === "undefined") return;
    const observer = new ResizeObserver(() => {
      const w = Math.round(el.clientWidth);
      if (w > 0) setWidth(w);
    });
    observer.observe(el);
    return () => observer.disconnect();
  }, [ref]);
  return width;
}
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `npm test --workspace web -- src/components/ui src/components/figures/chart-utils.test.ts`
Expected: PASS (9 tests).

- [ ] **Step 5: Commit**

```bash
git add apps/web/src/components/ui apps/web/src/components/figures/chart-utils.ts apps/web/src/components/figures/chart-utils.test.ts apps/web/src/components/figures/use-chart-width.ts
git commit -m "feat: add accessible tab list, toggle group and chart utilities"
```

---

### Task 4: Content records, result types, fixtures and the honesty rule

**Files:**
- Create: `apps/web/src/content/types.ts`, `profile.ts`, `studies.ts`, `experiments.ts`
- Create: `apps/web/src/content/fixtures/penang.ts`, `forecasting.ts`, `llm-eval.ts`, `index.ts`
- Create: `apps/web/src/content/results/index.ts`, `apps/web/src/lib/study-results.ts`
- Test: `apps/web/src/content/content.test.ts`, `apps/web/src/lib/study-results.test.ts`

**Interfaces:**
- Consumes: `TileSpec`, `Ground` and `mixedTile` from Task 2; `seeded` and `gauss` from Task 3.
- Produces: everything exported from `content/types.ts` (below), plus:
  - `profile` and `type ContactLinks`
  - `studies: readonly StudyRecord[]`, `findStudy(slug: string): StudyRecord | undefined`, `neighbours(slug: StudySlug): { prev: StudyRecord; next: StudyRecord }`
  - `experiments: readonly ExperimentRecord[]`, `EXPERIMENT_CATEGORIES`, `experimentUrl(name: string): string`
  - `fixtures: StudyResultsBySlug`, `published: Partial<StudyResultsBySlug>`
  - `getStudyResults<S extends StudySlug>(slug: S, env?: string): LoadedResults<S> | null`

- [ ] **Step 1: Write the types**

`apps/web/src/content/types.ts`:

```ts
import type { Ground, TileSpec } from "@/components/tiles/tile-geometry";

export type StudySlug = "penang-pulse" | "forecasting-lab" | "llm-eval-lab";
export type StudyStatus = "published" | "in-progress" | "planned";
export type ThemeClass = "s-pulse" | "s-forecast" | "s-llm";

export interface Source {
  name: string;
  publisher: string;
  used: string;
  licence: string;
}

export interface StudyRecord {
  slug: StudySlug;
  title: string;
  question: string;
  status: StudyStatus;
  plannedAnswer: string; // shown when no results exist; contains no numbers
  figurePlan: string; // what the evidence chapter will show
  data: string; // one line for cards
  tile: TileSpec;
  tint: Ground;
  themeClass: ThemeClass;
  sources: readonly Source[];
  method: readonly string[];
  limitations: readonly string[];
  reproduce: { commands: readonly string[]; note?: string };
  discussNote: string;
}

export interface KeyNumber {
  value: string;
  label: string;
  caveat: string;
}

export interface RunInfo {
  commit: string;
  manifest: string;
  python: string;
  lastRun: string; // ISO date
}

export interface BaseResults {
  answer: string;
  keyNumbers: readonly [KeyNumber, KeyNumber, KeyNumber];
  run: RunInfo;
  retrieved: Readonly<Record<string, string>>; // source name to ISO date
}

export type ServiceCategory = "clinic" | "school" | "transit";
export interface District {
  id: string;
  name: string;
  short: string;
  bands: readonly [number, number, number]; // % under 1 km, 1 to 3 km, over 3 km
  population: number;
}
export interface ServicePoint {
  category: ServiceCategory;
  x: number;
  y: number;
}
export interface MapLabel {
  text: string;
  x: number;
  y: number;
}
export interface PenangGeometry {
  island: string;
  mainland: string;
  districts: ReadonlyArray<{ id: string; d: string; land: "island" | "mainland" }>;
  boundaries: readonly string[];
  bridges: readonly string[];
  places: readonly MapLabel[];
  water: MapLabel;
}
export interface PenangResults extends BaseResults {
  districts: readonly District[];
  points: readonly ServicePoint[];
  geometry: PenangGeometry;
  pointsNote: string;
}

export type ForecastModelId = "naive" | "gb" | "gru" | "chronos";
export interface ForecastModel {
  id: ForecastModelId;
  name: string;
  mae: readonly number[]; // one value per horizon
}
export interface SensorSeries {
  id: string;
  label: string;
  originMinutes: number; // minutes after midnight at the forecast origin
  stepMinutes: number;
  pastSteps: number;
  actual: readonly number[]; // pastSteps + aheadSteps + 1 values, origin at index pastSteps
  forecasts: Readonly<Record<ForecastModelId, readonly number[]>>; // aheadSteps + 1 values, index 0 is the origin
  windowMae: Readonly<Record<ForecastModelId, number>>;
}
export interface ForecastResults extends BaseResults {
  horizons: readonly number[];
  models: readonly ForecastModel[];
  sensors: readonly SensorSeries[];
}

export type ModelRole = "frontier" | "ft" | "open" | "base";
export interface EvalRow {
  model: string;
  role: ModelRole;
  score: number;
  low: number;
  high: number;
  costPer1k: number;
  costLabel: string;
  latency: string;
}
export interface EvalTask {
  id: string;
  label: string;
  metric: string;
  rows: readonly EvalRow[];
}
export interface ErrorExample {
  input: string;
  expected: string;
  model: string;
  output: string;
  note: string;
  correct: boolean;
}
export interface LlmEvalResults extends BaseResults {
  tasks: readonly EvalTask[];
  errorExamples: readonly ErrorExample[];
}

export interface StudyResultsBySlug {
  "penang-pulse": PenangResults;
  "forecasting-lab": ForecastResults;
  "llm-eval-lab": LlmEvalResults;
}

export type ExperimentCategory = "agents" | "libraries" | "apps" | "ml";
export interface ExperimentRecord {
  name: string;
  category: ExperimentCategory;
  language: string;
  description: string;
  tile: number; // index for mixedTile
}
```

- [ ] **Step 2: Write the failing tests**

`apps/web/src/content/content.test.ts`:

```ts
import { describe, expect, it } from "vitest";

import { experimentUrl, experiments } from "./experiments";
import { fixtures } from "./fixtures";
import { profile } from "./profile";
import { findStudy, neighbours, studies } from "./studies";

const ISO = /^\d{4}-\d{2}-\d{2}$/;
const DIGIT = /\d/;

describe("study records", () => {
  it("has three unique slugs in a fixed order", () => {
    expect(studies.map((s) => s.slug)).toEqual(["penang-pulse", "forecasting-lab", "llm-eval-lab"]);
  });

  it.each(studies.map((s) => [s.slug, s] as const))("%s meets the provenance minimums", (_slug, study) => {
    expect(study.sources.length).toBeGreaterThanOrEqual(1);
    expect(study.method.length).toBeGreaterThanOrEqual(4);
    expect(study.method.length).toBeLessThanOrEqual(5);
    expect(study.limitations.length).toBeGreaterThanOrEqual(3);
  });

  it.each(studies.map((s) => [s.slug, s] as const))("%s planned copy has no numbers except model sizes", (_slug, study) => {
    expect(DIGIT.test(study.plannedAnswer.replace(/\b\d+B\b/g, ""))).toBe(false);
  });

  it("finds studies and wraps previous and next", () => {
    expect(findStudy("nope")).toBeUndefined();
    expect(neighbours("penang-pulse").prev.slug).toBe("llm-eval-lab");
    expect(neighbours("llm-eval-lab").next.slug).toBe("penang-pulse");
  });
});

describe("fixtures", () => {
  it.each(Object.entries(fixtures))("%s dates its run and its sources", (slug, data) => {
    expect(data.run.lastRun).toMatch(ISO);
    for (const source of findStudy(slug)?.sources ?? []) {
      expect(data.retrieved[source.name]).toMatch(ISO);
    }
  });

  it("gives every forecast series the right length", () => {
    const f = fixtures["forecasting-lab"];
    for (const s of f.sensors) {
      expect(s.actual.length).toBe(s.pastSteps + 25);
      for (const m of f.models) expect(s.forecasts[m.id].length).toBe(25);
    }
  });

  it("keeps the seasonal baseline worst in every sensor window", () => {
    for (const s of fixtures["forecasting-lab"].sensors) {
      const others = (["gb", "gru", "chronos"] as const).map((id) => s.windowMae[id]);
      expect(s.windowMae.naive).toBeGreaterThan(Math.max(...others));
    }
  });
});

describe("experiments and profile", () => {
  it("lists 12 tools, each with a description and a GitHub link", () => {
    expect(experiments).toHaveLength(12);
    for (const e of experiments) {
      expect(e.description.length).toBeGreaterThan(0);
      expect(experimentUrl(e.name)).toBe(`https://github.com/SubaashNair/${e.name}`);
    }
  });

  it("uses the chosen brand name", () => {
    expect(profile.name).toBe("Subashanan Nair");
  });
});
```

`apps/web/src/lib/study-results.test.ts`:

```ts
import { describe, expect, it } from "vitest";

import { getStudyResults } from "./study-results";

describe("getStudyResults", () => {
  it("returns nothing in production when no results are published", () => {
    expect(getStudyResults("penang-pulse", "production")).toBeNull();
    expect(getStudyResults("forecasting-lab", "production")).toBeNull();
    expect(getStudyResults("llm-eval-lab", "production")).toBeNull();
  });

  it("returns illustrative fixtures, flagged as a preview, outside production", () => {
    const loaded = getStudyResults("llm-eval-lab", "development");
    expect(loaded?.preview).toBe(true);
    expect(loaded?.data.tasks).toHaveLength(3);
  });
});
```

- [ ] **Step 3: Run the tests to verify they fail**

Run: `npm test --workspace web -- src/content src/lib`
Expected: FAIL with "Failed to resolve import ./experiments".

- [ ] **Step 4: Write `profile.ts`**

`apps/web/src/content/profile.ts`:

```ts
export interface ContactLinks {
  email?: string;
  linkedin?: string;
  cv?: string;
}

// Contact values are filled in by Subashanan before launch (spec, section 8). Missing values hide their buttons.
const contact: ContactLinks = {};

export const profile = {
  name: "Subashanan Nair",
  place: "Penang",
  roleLine:
    "Data scientist in Penang. I build reproducible ML and LLM systems on Malaysian public data, and publish the sources, code and limits behind every result.",
  githubUrl: "https://github.com/SubaashNair",
  sourceUrl: "https://github.com/SubaashNair/ai-observatory-portfolio",
  discussUrl: "https://github.com/SubaashNair/ai-observatory-portfolio/discussions",
  siteUrl: "https://ai-observatory.vercel.app",
  contact,
  intro:
    "I am a data scientist based in Penang, Malaysia. I like questions that matter locally and answers that hold up when someone else reruns them.",
  openTo: "I am open to data science and ML engineering roles, and to collaborations on Malaysian open data.",
  workOn: [
    "Spatial analysis of public services",
    "Forecasting",
    "Evaluating language models on Malaysian languages",
    "Small tools and agents that make data work faster",
  ],
  howIWork: [
    "Every result ships with its sources, code, model versions and limits.",
    "I prefer a strong baseline before a complex model.",
    "I report uncertainty, not just a single number.",
  ],
  toolkit: ["Python", "pandas", "scikit-learn", "PyTorch", "MLflow", "GeoPandas", "TypeScript", "Next.js", "Go", "Swift"],
} as const;
```

- [ ] **Step 5: Write `studies.ts`**

`apps/web/src/content/studies.ts`:

```ts
import type { StudyRecord, StudySlug } from "./types";

export const studies: readonly StudyRecord[] = [
  {
    slug: "penang-pulse",
    title: "Penang Pulse",
    question: "How evenly are clinics, schools and transit stops spread across Penang?",
    status: "in-progress",
    plannedAnswer:
      "This study will measure how far residents in each of Penang's districts live from the nearest public clinic, school and transit stop, and show where the gaps are widest.",
    figurePlan:
      "a map of public clinics, schools and transit stops, and one tile per district showing the share of residents under 1 km, 1 to 3 km and over 3 km from the nearest clinic.",
    data: "PeGIS facility layers, DOSM Census 2020, OpenStreetMap roads.",
    tile: { motif: "diamond", a: "mustard", b: "jade", ground: "warm" },
    tint: "warm",
    themeClass: "s-pulse",
    sources: [
      { name: "PeGIS", publisher: "Penang state GIS portal", used: "Facility layers for clinics, schools and transit stops", licence: "CC BY 4.0" },
      { name: "Census 2020", publisher: "DOSM", used: "Population by mukim", licence: "Open government licence" },
      { name: "OpenStreetMap", publisher: "OpenStreetMap contributors", used: "Road network for travel distances", licence: "ODbL" },
    ],
    method: [
      "Collect facility points for clinics, schools and transit stops from PeGIS.",
      "Join each mukim to its 2020 census population.",
      "Compute road network distance from each population-weighted mukim centroid to the nearest facility.",
      "Band distances into under 1 km, 1 to 3 km and over 3 km, and sum residents per band.",
      "Bootstrap mukims to get intervals for each district share.",
    ],
    limitations: [
      "Centroids hide within-mukim variation, so some residents are closer or further than their band says.",
      "Private clinics are excluded, which overstates the distance to any clinic.",
      "OpenStreetMap road coverage is thinner in rural Seberang Perai.",
      "The 2020 census population is six years old.",
    ],
    reproduce: { commands: ["uv sync", "uv run python -m analysis.penang.build --from-cache", "npm run dev"] },
    discussNote: "Spotted a missing clinic or a better boundary file? Questions and corrections are welcome.",
  },
  {
    slug: "forecasting-lab",
    title: "Forecasting Lab",
    question: "Can a pre-trained time-series model beat a tuned baseline on traffic sensors?",
    status: "in-progress",
    plannedAnswer:
      "This study will test whether Chronos, a pre-trained time-series model used without tuning, can beat a seasonal baseline, a tuned gradient boosting model and a small neural net on traffic forecasts up to two hours ahead.",
    figurePlan: "forecasts for the next two hours on three sensors, and each model's error by horizon from 15 minutes to 2 hours.",
    data: "UCI dataset 608, Chronos weights from Hugging Face.",
    tile: { motif: "petals", a: "cobalt", b: "mustard", ground: "sky" },
    tint: "sky",
    themeClass: "s-forecast",
    sources: [
      { name: "Dataset 608", publisher: "UCI Machine Learning Repository", used: "Traffic sensor network flows", licence: "CC BY 4.0" },
      { name: "chronos-t5-small", publisher: "Amazon, via Hugging Face", used: "Pre-trained model weights", licence: "Apache 2.0" },
    ],
    method: [
      "Split the data into chronological train, validation and test windows with no overlap, and fit scalers on training data only.",
      "Build the seasonal naive baseline from the same weekday last week.",
      "Tune gradient boosting and the GRU on the validation window only.",
      "Run Chronos zero-shot, with no tuning.",
      "Score every model on the same test window at each horizon.",
    ],
    limitations: [
      "One dataset from one city.",
      "Chronos context length caps how much history it sees.",
      "No outside features like weather or holidays.",
      "MAE hides rare congestion spikes, which matter most to drivers.",
    ],
    reproduce: { commands: ["uv sync", "uv run python -m analysis.forecasting.run --seed 42", "npm run dev"] },
    discussNote: "Have a model you think should be on this chart? Suggestions and corrections are welcome.",
  },
  {
    slug: "llm-eval-lab",
    title: "LLM Eval Lab",
    question: "How well do small and frontier models handle Bahasa Malaysia and Manglish?",
    status: "planned",
    plannedAnswer:
      "This study will compare a classical baseline, a fine-tuned 1B model, an open 8B model and a frontier model on Manglish sentiment, Bahasa Malaysia entity extraction and Bahasa Malaysia summaries, reporting accuracy with intervals, cost and latency.",
    figurePlan: "a leaderboard per task with 95% intervals, cost per 1,000 items and latency, a cost against score chart, and examples of where models go wrong.",
    data: "Hand-labelled Manglish and BM sets, Malaysian news headlines.",
    tile: { motif: "flower", a: "rose", b: "cobalt", ground: "porcelain" },
    tint: "roseTint",
    themeClass: "s-llm",
    sources: [
      { name: "Manglish and BM sets", publisher: "This project", used: "Hand-labelled items for sentiment and entities", licence: "CC BY 4.0" },
      { name: "Malaysian news headlines", publisher: "Public news sites", used: "Articles for the summary task", licence: "Public, research use" },
      { name: "Models", publisher: "Model APIs and open weights", used: "Every model, listed with its version", licence: "Per provider" },
    ],
    method: [
      "Write and freeze the labelling guidelines.",
      "Label 1,200 items per task, with a second annotator on 20%.",
      "Version prompts (v1 to v3) in the repo.",
      "Run each model 3 times at temperature 0, recording cost and latency per call.",
      "Bootstrap 95% intervals for every score.",
    ],
    limitations: [
      "Manglish varies by region and age; one set cannot cover it.",
      "Inter-annotator agreement is not perfect.",
      "Frontier model versions change, so results are dated.",
      "Costs use list prices on the run date.",
    ],
    reproduce: {
      commands: ["uv sync", "uv run python -m analysis.llm_eval.run --task all --prompts v3", "npm run dev"],
      note: "Hosted models need API keys; open models run locally.",
    },
    discussNote: "Speak Manglish and disagree with a label? That is exactly the feedback this needs.",
  },
];

export function findStudy(slug: string): StudyRecord | undefined {
  return studies.find((s) => s.slug === slug);
}

/** Previous and next studies, wrapping around so no slot is empty. */
export function neighbours(slug: StudySlug): { prev: StudyRecord; next: StudyRecord } {
  const i = studies.findIndex((s) => s.slug === slug);
  return { prev: studies[(i - 1 + studies.length) % studies.length], next: studies[(i + 1) % studies.length] };
}
```

Method steps describe the plan, not results, so they may contain numbers. The no-numbers test covers only `plannedAnswer`.

- [ ] **Step 6: Write `experiments.ts`**

`apps/web/src/content/experiments.ts`:

```ts
import type { ExperimentCategory, ExperimentRecord } from "./types";

// `inline` is the lower-case form used after the language, for example "Python, libraries".
export const EXPERIMENT_CATEGORIES: ReadonlyArray<{ id: ExperimentCategory; label: string; inline: string }> = [
  { id: "agents", label: "Agents and MCP", inline: "agents and MCP" },
  { id: "libraries", label: "Libraries", inline: "libraries" },
  { id: "apps", label: "Apps", inline: "apps" },
  { id: "ml", label: "ML projects", inline: "ML projects" },
];

export const experimentUrl = (name: string): string => `https://github.com/SubaashNair/${name}`;

export const experiments: readonly ExperimentRecord[] = [
  { name: "documentation-mcp-server", category: "agents", language: "JavaScript", tile: 5, description: "An MCP server that gives coding agents up-to-date documentation for popular libraries." },
  { name: "matomari", category: "agents", language: "macOS", tile: 6, description: "A native file explorer with an agent inside, and an importance score for every file built from how you actually use it." },
  { name: "exam-monitor-app", category: "apps", language: "Go", tile: 7, description: "Real-time classroom exam monitoring: teachers see live student screens over LAN, with session tokens, lock-all, messaging and CSV audit export." },
  { name: "CU5_project_dashboard", category: "apps", language: "Python", tile: 8, description: "Monitors student repositories with GitHub activity, file evidence and requirement-based completion estimates." },
  { name: "ml-review", category: "libraries", language: "Python", tile: 9, description: "Extended evaluation metrics for scikit-learn models." },
  { name: "OutlierCleaner", category: "libraries", language: "Python", tile: 10, description: "Detects and removes outliers using several statistical methods." },
  { name: "StatClean", category: "libraries", language: "Python", tile: 11, description: "Statistical data cleaning and outlier handling." },
  { name: "OptimRL", category: "libraries", language: "Python", tile: 12, description: "Reinforcement learning optimisation experiments." },
  { name: "GRPOptim", category: "libraries", language: "Python", tile: 13, description: "GRPO training experiments." },
  { name: "pima-diabetes-mlflow", category: "ml", language: "Python", tile: 14, description: "Train, register, serve and ship a classifier end to end with MLflow, Docker and Streamlit." },
  { name: "Land-subsidence-Prediction", category: "ml", language: "Python", tile: 15, description: "Forecasts land subsidence in the Klang Valley from geospatial and temporal data." },
  { name: "Taiwan-Real-Estate-Price-Prediction-App", category: "ml", language: "Python", tile: 16, description: "Predicts property prices with a scikit-learn model behind a Gradio app." },
];
```

- [ ] **Step 7: Write the fixtures**

`apps/web/src/content/fixtures/penang.ts`:

```ts
import { seeded } from "@/components/figures/chart-utils";

import type { PenangResults, ServiceCategory, ServicePoint } from "../types";

// Illustrative only. Never shown in a production build (see lib/study-results.ts).
const CATEGORIES: readonly ServiceCategory[] = ["clinic", "school", "transit"];
const CLUSTERS: ReadonlyArray<readonly [number, number, number, number]> = [
  [300, 175, 18, 14], [180, 125, 24, 5], [298, 335, 14, 8], [215, 405, 18, 4], [120, 300, 16, 4],
  [425, 165, 24, 10], [540, 110, 30, 4], [500, 260, 34, 9], [470, 420, 40, 6],
];

function points(): readonly ServicePoint[] {
  const rand = seeded(7);
  return CLUSTERS.flatMap(([cx, cy, spread, n]) =>
    Array.from({ length: n }, () => {
      const category = CATEGORIES[Math.floor(rand() * 3)];
      return { category, x: +(cx + (rand() - 0.5) * spread * 2).toFixed(1), y: +(cy + (rand() - 0.5) * spread * 2).toFixed(1) };
    }),
  );
}

export const penangFixture: PenangResults = {
  answer:
    "Most residents of Timur Laut live within a kilometre of a public clinic. In Seberang Perai Selatan, about 1 in 5 live more than 3 km away, and the gap is widest for clinics rather than schools.",
  keyNumbers: [
    { value: "21%", label: "of Seberang Perai Selatan residents live over 3 km from a public clinic.", caveat: "95% interval 18 to 24%, from a mukim bootstrap." },
    { value: "412", label: "public service points mapped across clinics, schools and transit stops.", caveat: "Public facilities only. Private clinics are not included." },
    { value: "5", label: "districts compared on the same distance bands.", caveat: "District averages hide variation inside each mukim." },
  ],
  run: { commit: "a1c9e04", manifest: "manifest.json", python: "3.12", lastRun: "2026-10-01" },
  retrieved: { PeGIS: "2026-09-28", "Census 2020": "2026-09-28", OpenStreetMap: "2026-09-29" },
  districts: [
    { id: "tl", name: "Timur Laut", short: "Timur Laut", bands: [72, 24, 4], population: 545000 },
    { id: "bd", name: "Barat Daya", short: "Barat Daya", bands: [48, 34, 18], population: 236000 },
    { id: "spu", name: "Seberang Perai Utara", short: "SP Utara", bands: [55, 33, 12], population: 330000 },
    { id: "spt", name: "Seberang Perai Tengah", short: "SP Tengah", bands: [61, 30, 9], population: 402000 },
    { id: "sps", name: "Seberang Perai Selatan", short: "SP Selatan", bands: [41, 38, 21], population: 205000 },
  ],
  points: points(),
  pointsNote: "Schematic, not to scale. Points are an illustrative sample of the 412 public service points mapped. Dashed lines mark district boundaries.",
  geometry: {
    island:
      "M95 120 C130 95 175 100 205 105 C235 110 255 100 280 115 C300 125 318 140 322 160 C326 185 312 205 318 230 C324 260 315 290 322 320 C330 345 318 370 300 395 C285 415 262 432 240 438 C210 445 180 430 160 420 C130 405 110 385 100 360 C85 330 78 300 80 270 C82 240 70 210 75 180 C78 155 82 135 95 120 Z",
    mainland:
      "M380 0 L600 0 L600 500 L395 500 C400 470 385 440 392 410 C398 380 385 350 390 320 C395 290 378 260 385 230 C390 200 375 170 382 140 C388 110 372 80 378 50 C380 30 378 15 380 0 Z",
    districts: [
      { id: "tl", d: "M0 0H345V301L0 215Z", land: "island" },
      { id: "bd", d: "M0 215L345 301V500H0Z", land: "island" },
      { id: "spu", d: "M370 0H600V190H370Z", land: "mainland" },
      { id: "spt", d: "M370 190H600V340H370Z", land: "mainland" },
      { id: "sps", d: "M370 340H600V500H370Z", land: "mainland" },
    ],
    boundaries: ["M0 215L345 301", "M370 190H600", "M370 340H600"],
    bridges: ["M322 300L390 290", "M303 398L393 430"],
    places: [
      { text: "George Town", x: 240, y: 92 }, { text: "Bayan Lepas", x: 200, y: 462 }, { text: "Balik Pulau", x: 150, y: 350 },
      { text: "Butterworth", x: 490, y: 52 }, { text: "Bukit Mertajam", x: 495, y: 320 }, { text: "Nibong Tebal", x: 495, y: 480 },
    ],
    water: { text: "Selat Melaka", x: 22, y: 52 },
  },
};
```

`apps/web/src/content/fixtures/forecasting.ts`:

```ts
import { gauss, seeded } from "@/components/figures/chart-utils";

import type { ForecastModel, ForecastModelId, ForecastResults, SensorSeries } from "../types";

// Illustrative only. Each forecast is the actual series plus smooth seeded error whose size follows the MAE table,
// so relative accuracy matches it. Never shown in a production build.
const HORIZONS = [15, 30, 60, 90, 120] as const;
const ORIGIN = 17 * 60;
const STEP = 5;
const PAST = 36;
const AHEAD = 24;

const MODELS: readonly ForecastModel[] = [
  { id: "naive", name: "Seasonal naive", mae: [9.8, 11.2, 13.5, 15.1, 16.4] },
  { id: "gb", name: "Gradient boosting", mae: [6.1, 7.9, 10.6, 12.4, 14.0] },
  { id: "gru", name: "Small neural net (GRU)", mae: [6.4, 8.1, 10.4, 12.0, 13.6] },
  { id: "chronos", name: "Chronos, zero-shot", mae: [7.0, 8.3, 10.1, 11.6, 13.4] },
];
const MODEL_SEEDS: Readonly<Record<ForecastModelId, number>> = { naive: 11, gb: 23, gru: 37, chronos: 53 };
const SENSORS = [
  { id: "s12", label: "Sensor 12", seed: 12, base: 96, peak: 82, peakAt: 17 * 60 + 50, k: 1 },
  { id: "s47", label: "Sensor 47", seed: 47, base: 64, peak: 58, peakAt: 18 * 60 + 5, k: 0.8 },
  { id: "s103", label: "Sensor 103", seed: 103, base: 128, peak: 64, peakAt: 17 * 60 + 35, k: 1.2 },
] as const;

/** MAE at any horizon in minutes, linear between the published horizons. */
function maeAt(model: ForecastModel, minutes: number): number {
  const xs = [0, ...HORIZONS];
  const ys = [model.mae[0] * 0.4, ...model.mae];
  for (let i = 1; i < xs.length; i++) {
    if (minutes <= xs[i]) return ys[i - 1] + ((ys[i] - ys[i - 1]) * (minutes - xs[i - 1])) / (xs[i] - xs[i - 1]);
  }
  return ys[ys.length - 1];
}

function sensorSeries(s: (typeof SENSORS)[number]): SensorSeries {
  const r = seeded(s.seed * 97);
  const actual = Array.from({ length: PAST + AHEAD + 1 }, (_, i) => {
    const m = ORIGIN + (i - PAST) * STEP;
    return s.base + s.peak * Math.exp(-(((m - s.peakAt) / 58) ** 2)) + 6 * Math.sin(m / 37 + s.seed) * s.k + gauss(r) * 3.2 * s.k;
  });
  const at = (t: number): number => actual[t + PAST];

  // Normalising by the weighted |z| makes each window's MAE equal k times the mean target error, so the table's ranking holds.
  const build = (model: ForecastModel): { values: readonly number[]; mae: number } => {
    const rr = seeded(MODEL_SEEDS[model.id] * 131 + s.seed);
    const zs = Array.from({ length: AHEAD }).reduce<number[]>((acc) => [...acc, 0.85 * (acc.at(-1) ?? 0) + 0.5 * gauss(rr)], []);
    const target = zs.map((_, i) => maeAt(model, (i + 1) * STEP));
    const norm = zs.reduce((a, z, i) => a + Math.abs(z) * target[i], 0) / target.reduce((a, b) => a + b, 0);
    const values = [at(0), ...zs.map((z, i) => at(i + 1) + target[i] * s.k * (z / norm))];
    const mae = values.slice(1).reduce((a, v, i) => a + Math.abs(v - at(i + 1)), 0) / AHEAD;
    return { values, mae };
  };

  const built = Object.fromEntries(MODELS.map((m) => [m.id, build(m)])) as Record<ForecastModelId, { values: readonly number[]; mae: number }>;
  return {
    id: s.id,
    label: s.label,
    originMinutes: ORIGIN,
    stepMinutes: STEP,
    pastSteps: PAST,
    actual,
    forecasts: { naive: built.naive.values, gb: built.gb.values, gru: built.gru.values, chronos: built.chronos.values },
    windowMae: { naive: built.naive.mae, gb: built.gb.mae, gru: built.gru.mae, chronos: built.chronos.mae },
  };
}

export const forecastFixture: ForecastResults = {
  answer:
    "At short horizons a tuned gradient boosting model is hard to beat. Past one hour, Chronos, used with no tuning at all, has the lowest error, about 18% below the seasonal baseline at two hours.",
  keyNumbers: [
    { value: "18%", label: "lower error for Chronos than the seasonal baseline at 2 hours.", caveat: "Interval 12 to 23%, from a bootstrap over test days." },
    { value: "4", label: "models compared on the same chronological splits.", caveat: "One dataset from one city, so treat the ranking as local." },
    { value: "0", label: "hours of tuning for Chronos.", caveat: "Its context length still caps how much history it sees." },
  ],
  run: { commit: "a1c9e04", manifest: "manifest.json", python: "3.12", lastRun: "2026-10-01" },
  retrieved: { "Dataset 608": "2026-09-20", "chronos-t5-small": "2026-09-21" },
  horizons: HORIZONS,
  models: MODELS,
  sensors: SENSORS.map(sensorSeries),
};
```

`apps/web/src/content/fixtures/llm-eval.ts`:

```ts
import type { LlmEvalResults } from "../types";

// Illustrative only. Never shown in a production build.
export const llmEvalFixture: LlmEvalResults = {
  answer:
    "On Manglish sentiment, a fine-tuned 1B model lands within 3 points of a frontier model at about a fiftieth of the cost. On summaries, the frontier model still leads clearly.",
  keyNumbers: [
    { value: "3 points", label: "gap between the fine-tuned 1B and the frontier model on sentiment.", caveat: "The 95% intervals overlap, so the gap could be smaller." },
    { value: "1/50th", label: "the cost per 1k items for the fine-tuned 1B.", caveat: "List prices on the run date; prices change." },
    { value: "1,200", label: "hand-labelled items per task.", caveat: "Inter-annotator agreement was 0.81 on a 20% overlap." },
  ],
  run: { commit: "a1c9e04", manifest: "manifest.json", python: "3.12", lastRun: "2026-10-01" },
  retrieved: { "Manglish and BM sets": "2026-09-30", "Malaysian news headlines": "2026-09-15", Models: "2026-10-01" },
  tasks: [
    {
      id: "sentiment", label: "Manglish sentiment", metric: "Accuracy",
      rows: [
        { model: "Frontier model", role: "frontier", score: 87, low: 84, high: 90, costPer1k: 2.1, costLabel: "$2.10", latency: "900 ms" },
        { model: "Fine-tuned 1B", role: "ft", score: 84, low: 81, high: 87, costPer1k: 0.04, costLabel: "$0.04", latency: "38 ms" },
        { model: "Open 8B, zero-shot", role: "open", score: 79, low: 75, high: 83, costPer1k: 0.12, costLabel: "$0.12", latency: "210 ms" },
        { model: "TF-IDF + logistic", role: "base", score: 71, low: 67, high: 75, costPer1k: 0.007, costLabel: "<$0.01", latency: "1 ms" },
      ],
    },
    {
      id: "entities", label: "BM entity extraction", metric: "F1",
      rows: [
        { model: "Frontier model", role: "frontier", score: 83, low: 80, high: 86, costPer1k: 2.4, costLabel: "$2.40", latency: "1.1 s" },
        { model: "Fine-tuned 1B", role: "ft", score: 78, low: 74, high: 81, costPer1k: 0.05, costLabel: "$0.05", latency: "45 ms" },
        { model: "Open 8B, zero-shot", role: "open", score: 70, low: 66, high: 74, costPer1k: 0.14, costLabel: "$0.14", latency: "260 ms" },
        { model: "CRF baseline", role: "base", score: 62, low: 58, high: 66, costPer1k: 0.007, costLabel: "<$0.01", latency: "3 ms" },
      ],
    },
    {
      id: "summaries", label: "BM summaries", metric: "Faithfulness",
      rows: [
        { model: "Frontier model", role: "frontier", score: 82, low: 79, high: 85, costPer1k: 4.8, costLabel: "$4.80", latency: "2.4 s" },
        { model: "Open 8B, zero-shot", role: "open", score: 71, low: 67, high: 75, costPer1k: 0.3, costLabel: "$0.30", latency: "640 ms" },
        { model: "Fine-tuned 1B", role: "ft", score: 66, low: 62, high: 70, costPer1k: 0.09, costLabel: "$0.09", latency: "120 ms" },
        { model: "Extractive baseline", role: "base", score: 58, low: 54, high: 62, costPer1k: 0.007, costLabel: "<$0.01", latency: "5 ms" },
      ],
    },
  ],
  errorExamples: [
    { input: "Wah this nasi lemak damn power lah", expected: "positive", model: "Fine-tuned 1B", output: "positive", note: "Reads \"damn power\" as praise", correct: true },
    { input: "Service ok la but wait so long sampai tak larat", expected: "negative", model: "Open 8B", output: "neutral", note: "Misses \"tak larat\" (exhausted)", correct: false },
    { input: "Boleh tahan, not bad for the price", expected: "positive", model: "TF-IDF", output: "negative", note: "\"Tahan\" read as a complaint", correct: false },
  ],
};
```

`apps/web/src/content/fixtures/index.ts`:

```ts
import type { StudyResultsBySlug } from "../types";
import { forecastFixture } from "./forecasting";
import { llmEvalFixture } from "./llm-eval";
import { penangFixture } from "./penang";

export const fixtures: StudyResultsBySlug = {
  "penang-pulse": penangFixture,
  "forecasting-lab": forecastFixture,
  "llm-eval-lab": llmEvalFixture,
};
```

`apps/web/src/content/results/index.ts`:

```ts
import type { StudyResultsBySlug } from "../types";

// Real, validated results are added here by the pipeline work (original implementation plan Tasks 4 to 6, and the LLM Eval Lab plan).
// Until then this stays empty, and production pages show their planned state.
export const published: Partial<StudyResultsBySlug> = {};
```

- [ ] **Step 8: Write the honesty rule**

`apps/web/src/lib/study-results.ts`:

```ts
import { fixtures } from "@/content/fixtures";
import { published } from "@/content/results";
import type { StudyResultsBySlug, StudySlug } from "@/content/types";

export interface LoadedResults<S extends StudySlug> {
  data: StudyResultsBySlug[S];
  preview: boolean;
}

/**
 * The only place that decides what a study may show.
 * Published results always win. Outside production, illustrative fixtures fill the gap and are flagged as a preview.
 * In production with nothing published, the answer is null and pages show their planned state.
 * Pages call this at build time on the server; fixture data reaches the browser only in development.
 */
export function getStudyResults<S extends StudySlug>(slug: S, env: string | undefined = process.env.NODE_ENV): LoadedResults<S> | null {
  const real = published[slug];
  if (real) return { data: real, preview: false };
  if (env === "production") return null;
  return { data: fixtures[slug], preview: true };
}
```

- [ ] **Step 9: Run the tests to verify they pass**

Run: `npm test --workspace web -- src/content src/lib`, then `npm run typecheck`.
Expected: PASS, with no type errors.

- [ ] **Step 10: Commit**

```bash
git add apps/web/src/content apps/web/src/lib
git commit -m "feat: add typed content, illustrative fixtures and the results honesty rule"
```

---

### Task 5: Shell, home and not-found

**Files:**
- Replace: `apps/web/src/components/shell/site-header.tsx`, `site-footer.tsx`, `site-header.test.tsx`, `apps/web/src/components/home/hero.tsx`, `apps/web/src/app/page.tsx`, `apps/web/src/app/page.test.tsx`
- Create: `apps/web/src/components/home/tools-preview.tsx`, `apps/web/src/components/home/about-band.tsx`, `apps/web/src/components/study/study-card.tsx`, `apps/web/src/components/study/study-run.tsx`, `apps/web/src/components/experiments/tool-item.tsx`, `apps/web/src/app/not-found.tsx`
- Delete: `apps/web/src/components/home/signals-section.tsx`, `apps/web/src/components/home/study-card.tsx`

**Interfaces:**
- Consumes: `Tile`, `Mosaic` and `mixedTile` (Task 2); `profile`, `studies`, `experiments` and `EXPERIMENT_CATEGORIES` (Task 4); `getStudyResults` and `LoadedResults` (Task 4).
- Produces:
  - `<StudyCard study results headingLevel />`, with `results: LoadedResults<StudySlug> | null` and `headingLevel: 2 | 3`
  - `STATUS_LABEL: Record<StudyStatus, string>` (exported from `study-card.tsx`)
  - `<StudyRun headingLevel />`, `<ToolItem experiment />`
  - `<ContactButtons tone="dark" | "light" />` (from `home/about-band.tsx`)

- [ ] **Step 1: Write the failing tests**

`apps/web/src/components/shell/site-header.test.tsx`:

```tsx
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

vi.mock("next/navigation", () => ({ usePathname: () => "/work/penang-pulse" }));

import { SiteHeader } from "./site-header";

describe("SiteHeader", () => {
  it("names the brand and links every destination", () => {
    render(<SiteHeader />);
    expect(screen.getByRole("link", { name: "Subashanan Nair" })).toHaveAttribute("href", "/");
    expect(screen.getByRole("link", { name: "Experiments" })).toHaveAttribute("href", "/experiments");
    expect(screen.getByRole("link", { name: "About" })).toHaveAttribute("href", "/about");
    expect(screen.getByRole("link", { name: "GitHub" })).toHaveAttribute("href", "https://github.com/SubaashNair");
  });

  it("marks Work as current on a case study page", () => {
    render(<SiteHeader />);
    expect(screen.getByRole("link", { name: "Work" })).toHaveAttribute("aria-current", "page");
    expect(screen.getByRole("link", { name: "About" })).not.toHaveAttribute("aria-current");
  });
});
```

`apps/web/src/app/page.test.tsx`:

```tsx
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import Home from "./page";

describe("Home", () => {
  it("introduces Subashanan and links the main journeys", () => {
    render(<Home />);
    expect(screen.getByRole("heading", { level: 1, name: "Subashanan Nair" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Read the case studies" })).toHaveAttribute("href", "/work");
    expect(screen.getByRole("link", { name: "Get in touch" })).toHaveAttribute("href", "/about#contact");
    expect(screen.getByRole("link", { name: "Penang Pulse" })).toHaveAttribute("href", "/work/penang-pulse");
    expect(screen.getByRole("link", { name: "See all tools and experiments" })).toHaveAttribute("href", "/experiments");
    expect(screen.queryByText(/NASA/)).not.toBeInTheDocument();
  });

  it("shows four tools", () => {
    const { container } = render(<Home />);
    expect(container.querySelectorAll("li.tool")).toHaveLength(4);
  });
});
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `npm test --workspace web -- src/components/shell src/app/page.test.tsx`
Expected: FAIL. The brand link is still named "AI Observatory home" and the hero text is the old one.

- [ ] **Step 3: Write the shell**

`apps/web/src/components/shell/site-header.tsx`:

```tsx
"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { Tile } from "@/components/tiles/tile";
import { mixedTile } from "@/components/tiles/tile-geometry";
import { profile } from "@/content/profile";

const LINKS = [
  { href: "/work", label: "Work" },
  { href: "/experiments", label: "Experiments" },
  { href: "/about", label: "About" },
] as const;

export function SiteHeader() {
  const pathname = usePathname() ?? "/";
  const isCurrent = (href: string): boolean => pathname === href || pathname.startsWith(`${href}/`);

  return (
    <div className="top">
      <div className="wrap">
        <header className="site">
          <Link className="wordmark" href="/" aria-current={pathname === "/" ? "page" : undefined}>
            <Tile spec={mixedTile(0)} />
            {profile.name}
          </Link>
          <nav className="primary" aria-label="Primary">
            {LINKS.map((link) => (
              <Link key={link.href} href={link.href} aria-current={isCurrent(link.href) ? "page" : undefined}>
                {link.label}
              </Link>
            ))}
            <a className="gh" href={profile.githubUrl}>GitHub</a>
          </nav>
        </header>
      </div>
    </div>
  );
}
```

`apps/web/src/components/shell/site-footer.tsx`:

```tsx
import { profile } from "@/content/profile";

export function SiteFooter() {
  return (
    <div className="about-band foot-only">
      <div className="wrap">
        <footer className="site">
          <span>{profile.name}, {profile.place}</span>
          <span className="actions">
            <a href={profile.githubUrl}>GitHub</a>
            <a href={profile.sourceUrl}>Source for this site</a>
          </span>
        </footer>
      </div>
    </div>
  );
}
```

The header and footer render their own peacock bands, so `layout.tsx` from Task 1 needs no change.

- [ ] **Step 4: Write the study card and run (shared by home and work index)**

`apps/web/src/components/study/study-card.tsx`:

```tsx
import Link from "next/link";

import { Tile } from "@/components/tiles/tile";
import type { StudyRecord, StudySlug, StudyStatus } from "@/content/types";
import type { LoadedResults } from "@/lib/study-results";

export const STATUS_LABEL: Readonly<Record<StudyStatus, string>> = { published: "Published", "in-progress": "In progress", planned: "Planned" };

interface StudyCardProps {
  study: StudyRecord;
  results: LoadedResults<StudySlug> | null;
  headingLevel: 2 | 3;
}

export function StudyCard({ study, results, headingLevel }: StudyCardProps) {
  const Heading = headingLevel === 2 ? "h2" : "h3";
  const href = `/work/${study.slug}`;
  const key = results?.data.keyNumbers[0];

  return (
    <article className={`tile-frame study-card ${study.themeClass}`}>
      <div className="card-marks" aria-hidden="true">
        {[0, 1, 2, 3].map((i) => <Tile key={i} spec={study.tile} />)}
      </div>
      <span className={study.status === "planned" ? "tag plan" : "tag"}>{STATUS_LABEL[study.status]}</span>
      <Heading><Link href={href}>{study.title}</Link></Heading>
      <p className="q">{study.question}</p>
      {key && (
        <p className="key">
          <strong>{key.value}</strong>
          {key.label}
          {results?.preview && <span className="sr"> (illustrative preview)</span>}
        </p>
      )}
      <p className="data">Data: {study.data}</p>
      <Link className="btn ink" href={href}>{study.status === "planned" ? "Read the plan" : `Open ${study.title}`}</Link>
    </article>
  );
}
```

`apps/web/src/components/study/study-run.tsx`:

```tsx
import { studies } from "@/content/studies";
import { getStudyResults } from "@/lib/study-results";

import { StudyCard } from "./study-card";

export function StudyRun({ headingLevel }: { headingLevel: 2 | 3 }) {
  return (
    <div className="tile-run">
      {studies.map((study) => (
        <StudyCard key={study.slug} study={study} results={getStudyResults(study.slug)} headingLevel={headingLevel} />
      ))}
    </div>
  );
}
```

- [ ] **Step 5: Write the tool item, home sections, page and not-found**

`apps/web/src/components/experiments/tool-item.tsx`:

```tsx
import { Tile } from "@/components/tiles/tile";
import { mixedTile } from "@/components/tiles/tile-geometry";
import { EXPERIMENT_CATEGORIES, experimentUrl } from "@/content/experiments";
import type { ExperimentRecord } from "@/content/types";

export function ToolItem({ experiment }: { experiment: ExperimentRecord }) {
  const category = EXPERIMENT_CATEGORIES.find((c) => c.id === experiment.category)?.inline ?? "";
  return (
    <li className="tool">
      <Tile spec={mixedTile(experiment.tile)} />
      <div>
        <h3><a href={experimentUrl(experiment.name)}>{experiment.name}</a></h3>
        <div className="lang">{experiment.language}, {category}</div>
        <p>{experiment.description}</p>
      </div>
    </li>
  );
}
```

`apps/web/src/components/home/hero.tsx`:

```tsx
import Link from "next/link";

import { Mosaic } from "@/components/tiles/mosaic";
import { mixedTile } from "@/components/tiles/tile-geometry";
import { profile } from "@/content/profile";

const TILES = Array.from({ length: 16 }, (_, i) => mixedTile(i));
const [first, last] = profile.name.split(" ");

export function Hero() {
  return (
    <div className="top">
      <div className="wrap">
        <div className="hero">
          <div>
            <h1>{first}<br />{" "}{last}</h1>
            <p className="lede">{profile.roleLine}</p>
            <div className="actions">
              <Link className="btn primary" href="/work">Read the case studies</Link>
              <Link className="btn quiet" href="/about#contact">Get in touch</Link>
            </div>
          </div>
          <div>
            <Mosaic tiles={TILES} label="Decorative tile mosaic. Select a tile to turn it." />
            <p className="mosaic-note">Patterns drawn from George Town&apos;s Peranakan floor tiles. Tap a tile to turn it.</p>
          </div>
        </div>
      </div>
    </div>
  );
}
```

The `{" "}` after `<br />` keeps the accessible name "Subashanan Nair" with a space, and is invisible on screen.

`apps/web/src/components/home/tools-preview.tsx`:

```tsx
import Link from "next/link";

import { ToolItem } from "@/components/experiments/tool-item";
import { experiments } from "@/content/experiments";

const PREVIEW = ["documentation-mcp-server", "matomari", "exam-monitor-app", "pima-diabetes-mlflow"];

export function ToolsPreview() {
  const shown = experiments.filter((e) => PREVIEW.includes(e.name));
  return (
    <section className="block" aria-labelledby="exp-h" style={{ paddingTop: 0 }}>
      <div className="wrap">
        <h2 id="exp-h">Tools and experiments</h2>
        <p className="intro">Smaller things I have shipped. Each gets its own tile.</p>
        <ul className="tools">{shown.map((e) => <ToolItem key={e.name} experiment={e} />)}</ul>
        <p className="more"><Link className="btn ink" href="/experiments">See all tools and experiments</Link></p>
      </div>
    </section>
  );
}
```

`apps/web/src/components/home/about-band.tsx`:

```tsx
import Link from "next/link";

import { profile } from "@/content/profile";

/** Contact buttons. A missing contact value hides its button; GitHub is always available. */
export function ContactButtons({ tone }: { tone: "dark" | "light" }) {
  const quiet = tone === "dark" ? "btn quiet" : "btn ink";
  const { email, linkedin, cv } = profile.contact;
  return (
    <div className="actions">
      {email && <a className="btn primary" href={`mailto:${email}`}>Email me</a>}
      {linkedin && <a className={quiet} href={linkedin}>LinkedIn</a>}
      {cv && <a className={quiet} href={cv}>Download CV</a>}
      <a className={email ? quiet : "btn primary"} href={profile.githubUrl}>Find me on GitHub</a>
    </div>
  );
}

export function AboutBand() {
  return (
    <div className="about-band">
      <section className="block wrap about" aria-labelledby="about-h">
        <h2 id="about-h">About</h2>
        <div>
          <p>{profile.intro}</p>
          <p>{profile.openTo}</p>
          <ContactButtons tone="dark" />
          <p style={{ marginTop: 16 }}><Link href="/about">More about me</Link></p>
        </div>
      </section>
    </div>
  );
}
```

`apps/web/src/app/page.tsx`:

```tsx
import { AboutBand } from "@/components/home/about-band";
import { Hero } from "@/components/home/hero";
import { ToolsPreview } from "@/components/home/tools-preview";
import { StudyRun } from "@/components/study/study-run";

export default function Home() {
  return (
    <>
      <Hero />
      <main id="main">
        <section className="block" aria-labelledby="work-h">
          <div className="wrap">
            <h2 id="work-h">Case studies</h2>
            <p className="intro">Three questions about Malaysia, answered with public data. Each one links its sources, code, model versions and known limits.</p>
            <StudyRun headingLevel={3} />
          </div>
        </section>
        <ToolsPreview />
      </main>
      <AboutBand />
    </>
  );
}
```

`apps/web/src/app/not-found.tsx`:

```tsx
import Link from "next/link";

export default function NotFound() {
  return (
    <main id="main" className="chapter">
      <div className="wrap">
        <div className="tile-frame" style={{ maxWidth: 640 }}>
          <h1 className="chapter-title">Page not found</h1>
          <p>This page does not exist. It may have moved when the site was redesigned.</p>
          <div className="actions">
            <Link className="btn ink" href="/">Go to the home page</Link>
            <Link className="btn ink" href="/work">See the case studies</Link>
          </div>
        </div>
      </div>
    </main>
  );
}
```

Delete `apps/web/src/components/home/signals-section.tsx` and `apps/web/src/components/home/study-card.tsx`.

- [ ] **Step 6: Run the tests and the build**

Run: `npm test --workspace web`, then `npm run lint` and `npm run build`.
Expected: all tests PASS and the build succeeds. `/work`, `/experiments` and `/about` still 404 until Tasks 6 and 10. That is expected.

- [ ] **Step 7: Compare with the prototype**

Run `npm run dev`. Open `http://localhost:3000` beside `mockups/peranakan-tiles/index.html` at 1440px and 390px wide. The hero, mosaic, study run, tools and about band should match. The study cards show key numbers here because `next dev` uses the preview fixtures.

- [ ] **Step 8: Commit**

```bash
git add -A apps/web/src
git commit -m "feat: rebuild shell and home in the Peranakan design"
```

---

### Task 6: Case study template, work index and the `[slug]` route

**Files:**
- Create: `apps/web/src/components/study/study-page.tsx`, `chapters.tsx`, `figure-pending.tsx`, `study-theme.ts`
- Create: `apps/web/src/components/figures/registry.ts`
- Create: `apps/web/src/app/work/page.tsx`, `apps/web/src/app/work/[slug]/page.tsx`
- Test: `apps/web/src/components/study/study-page.test.tsx`, `apps/web/src/app/work/[slug]/page.test.tsx`

**Interfaces:**
- Consumes: Tasks 2 to 5.
- Produces:
  - `<StudyPage study results />`, with `results: LoadedResults<StudySlug> | null`
  - `figures`: a registry typed `{ [S in StudySlug]?: ComponentType<{ data: StudyResultsBySlug[S] }> }`. Tasks 7 to 9 add their entries here.
  - `studyThemeStyle(study: StudyRecord): CSSProperties`

- [ ] **Step 1: Write the failing tests**

`apps/web/src/components/study/study-page.test.tsx`:

```tsx
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { findStudy } from "@/content/studies";
import { getStudyResults } from "@/lib/study-results";

import { StudyPage } from "./study-page";

const pulse = findStudy("penang-pulse")!;

describe("StudyPage", () => {
  it("production mode with no results shows the plan and no numbers", () => {
    const { container } = render(<StudyPage study={pulse} results={getStudyResults("penang-pulse", "production")} />);
    expect(screen.getByRole("heading", { level: 1, name: "Penang Pulse" })).toBeInTheDocument();
    expect(screen.getByText(pulse.plannedAnswer)).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /the analysis is in progress/i })).toBeInTheDocument();
    expect(screen.queryAllByText("21%")).toHaveLength(0);
    expect(screen.queryByText(/preview with illustrative data/i)).not.toBeInTheDocument();
    expect(screen.queryByText("a1c9e04")).not.toBeInTheDocument();
    expect(container.querySelectorAll(".num-tile")).toHaveLength(0);
    expect(screen.getAllByText("Not yet retrieved")).toHaveLength(pulse.sources.length);
  });

  it("preview mode shows fixture numbers under a visible preview label", () => {
    render(<StudyPage study={pulse} results={getStudyResults("penang-pulse", "development")} />);
    expect(screen.getAllByText("21%").length).toBeGreaterThan(0);
    expect(screen.getAllByText(/preview with illustrative data/i).length).toBeGreaterThan(0);
  });

  it("always shows the provenance chapters and wraps the pager", () => {
    render(<StudyPage study={pulse} results={null} />);
    for (const name of ["The answer", "The evidence", "How it was made", "Check it yourself"]) {
      expect(screen.getByRole("heading", { level: 2, name })).toBeInTheDocument();
    }
    expect(screen.getByRole("table")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /previous study llm eval lab/i })).toHaveAttribute("href", "/work/llm-eval-lab");
    expect(screen.getByRole("link", { name: /next study forecasting lab/i })).toHaveAttribute("href", "/work/forecasting-lab");
  });
});
```

`apps/web/src/app/work/[slug]/page.test.tsx`:

```tsx
import { describe, expect, it, vi } from "vitest";

vi.mock("next/navigation", () => ({
  notFound: () => {
    throw new Error("NEXT_NOT_FOUND");
  },
}));

import StudyRoute, { dynamicParams, generateStaticParams } from "./page";

describe("/work/[slug]", () => {
  it("prerenders exactly the three studies and nothing else", async () => {
    expect(await generateStaticParams()).toEqual([{ slug: "penang-pulse" }, { slug: "forecasting-lab" }, { slug: "llm-eval-lab" }]);
    expect(dynamicParams).toBe(false);
  });

  it("returns not found for an unknown slug", async () => {
    await expect(StudyRoute({ params: Promise.resolve({ slug: "foo" }) })).rejects.toThrow("NEXT_NOT_FOUND");
  });
});
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `npm test --workspace web -- src/components/study/study-page.test.tsx src/app/work`
Expected: FAIL with "Failed to resolve import ./study-page".

- [ ] **Step 3: Write the theme helper, registry and pending panel**

`apps/web/src/components/study/study-theme.ts`:

```ts
import type { CSSProperties } from "react";

import { stepTileUri, thinFriezeUri } from "@/components/tiles/tile-geometry";
import type { StudyRecord } from "@/content/types";

/** CSS variables for a study's thin table frieze and method step tiles. Its other colours come from its theme class. */
export function studyThemeStyle(study: StudyRecord): CSSProperties {
  return {
    "--frieze-thin": thinFriezeUri(study.tile, study.tint),
    "--step-a": stepTileUri(study.tile.a, study.tint),
    "--step-b": stepTileUri(study.tile.b, study.tint),
  } as CSSProperties;
}
```

`apps/web/src/components/figures/registry.ts`:

```ts
import type { ComponentType } from "react";

import type { StudyResultsBySlug, StudySlug } from "@/content/types";

export type FigureRegistry = { [S in StudySlug]?: ComponentType<{ data: StudyResultsBySlug[S] }> };

// Tasks 7 to 9 register each study's figure here. An unregistered study shows the pending panel.
export const figures: FigureRegistry = {};
```

`apps/web/src/components/study/figure-pending.tsx`:

```tsx
import type { StudyRecord } from "@/content/types";

export function FigurePending({ study }: { study: StudyRecord }) {
  return (
    <div className="tile-frame">
      <h3 className="panel-title">The analysis is in progress</h3>
      <p>When the first run is published, this chapter will show {study.figurePlan}</p>
      <p className="note">Nothing here is estimated or illustrative. Results appear only after the pipeline publishes them with their sources.</p>
    </div>
  );
}
```

- [ ] **Step 4: Write the chapters**

`apps/web/src/components/study/chapters.tsx`:

```tsx
import Link from "next/link";
import type { ComponentType } from "react";

import { figures } from "@/components/figures/registry";
import { Tile } from "@/components/tiles/tile";
import { profile } from "@/content/profile";
import { neighbours } from "@/content/studies";
import type { StudyRecord, StudyResultsBySlug, StudySlug } from "@/content/types";
import type { LoadedResults } from "@/lib/study-results";

import { FigurePending } from "./figure-pending";

type Results = LoadedResults<StudySlug> | null;

function ChapterTitle({ id, study, children }: { id: string; study: StudyRecord; children: string }) {
  return (
    <h2 className="chapter-title" id={id}>
      <Tile spec={study.tile} />
      {children}
    </h2>
  );
}

function PreviewFlag({ results }: { results: Results }) {
  return results?.preview ? <p className="preview-flag">Preview with illustrative data. These are not results.</p> : null;
}

export function AnswerChapter({ study, results }: { study: StudyRecord; results: Results }) {
  return (
    <section className="chapter" aria-labelledby="ch-answer">
      <div className="wrap">
        <ChapterTitle id="ch-answer" study={study}>The answer</ChapterTitle>
        <PreviewFlag results={results} />
        <p className="short-answer">{results ? results.data.answer : study.plannedAnswer}</p>
        {results && (
          <>
            <h3 className="sub">Key numbers</h3>
            <div className="num-run">
              {results.data.keyNumbers.map((n) => (
                <div key={n.value} className="tile-frame num-tile">
                  <strong>{n.value}</strong>
                  <p>{n.label}</p>
                  <p className="caveat">{n.caveat}</p>
                </div>
              ))}
            </div>
          </>
        )}
      </div>
    </section>
  );
}

export function EvidenceChapter({ study, results }: { study: StudyRecord; results: Results }) {
  const Figure = figures[study.slug] as ComponentType<{ data: StudyResultsBySlug[StudySlug] }> | undefined;
  return (
    <section className="chapter dark" aria-labelledby="ch-evidence">
      <div className="wrap">
        <ChapterTitle id="ch-evidence" study={study}>The evidence</ChapterTitle>
        <PreviewFlag results={results} />
        {results && Figure ? <Figure data={results.data} /> : <FigurePending study={study} />}
      </div>
    </section>
  );
}

export function MadeChapter({ study, results }: { study: StudyRecord; results: Results }) {
  return (
    <section className="chapter" aria-labelledby="ch-made">
      <div className="wrap">
        <ChapterTitle id="ch-made" study={study}>How it was made</ChapterTitle>
        <div>
          <h3 className="sub" id="sources-h">Data sources</h3>
          <div className="table-wrap" role="region" aria-labelledby="sources-h" tabIndex={0}>
            <table>
              <thead>
                <tr><th scope="col">Source</th><th scope="col">Publisher</th><th scope="col">What we used</th><th scope="col">Licence</th><th scope="col">Retrieved</th></tr>
              </thead>
              <tbody>
                {study.sources.map((s) => (
                  <tr key={s.name}>
                    <th scope="row">{s.name}</th>
                    <td>{s.publisher}</td>
                    <td>{s.used}</td>
                    <td>{s.licence}</td>
                    <td>{results?.data.retrieved[s.name] ?? "Not yet retrieved"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
        <div>
          <h3 className="sub">Method</h3>
          <ol className="steps">{study.method.map((step) => <li key={step}><span>{step}</span></li>)}</ol>
        </div>
        <div>
          <h3 className="sub">Limitations</h3>
          <ul className="limits">{study.limitations.map((l) => <li key={l}>{l}</li>)}</ul>
        </div>
      </div>
    </section>
  );
}

export function CheckChapter({ study, results }: { study: StudyRecord; results: Results }) {
  const { prev, next } = neighbours(study.slug);
  const run = results?.data.run;
  return (
    <section className="chapter deep" aria-labelledby="ch-check">
      <div className="wrap">
        <ChapterTitle id="ch-check" study={study}>Check it yourself</ChapterTitle>
        <div className="check-grid">
          <div>
            <h3 className="sub">Reproduce</h3>
            {run ? (
              <>
                <pre className="code" tabIndex={0}><code>{study.reproduce.commands.join("\n")}</code></pre>
                <dl className="run-meta">
                  <div><dt>Commit</dt><dd><code>{run.commit}</code></dd></div>
                  <div><dt>Manifest</dt><dd><code>{run.manifest}</code></dd></div>
                  <div><dt>Python</dt><dd>{run.python}</dd></div>
                  <div><dt>Last run</dt><dd>{run.lastRun}</dd></div>
                </dl>
                {study.reproduce.note && <p className="note">{study.reproduce.note}</p>}
              </>
            ) : (
              <p className="note">Reproduction steps appear here with the first published run.</p>
            )}
          </div>
          <div>
            <h3 className="sub">Discuss</h3>
            <p className="note">{study.discussNote}</p>
            <p><a className="btn quiet" href={profile.discussUrl}>Discuss this study on GitHub</a></p>
          </div>
        </div>
        <nav className="pager" aria-label="More case studies">
          <Link className={`tile-frame ${prev.themeClass}`} href={`/work/${prev.slug}`}>
            <Tile spec={prev.tile} />
            <span><small>Previous study</small> <b>{prev.title}</b></span>
          </Link>
          <Link className={`tile-frame next ${next.themeClass}`} href={`/work/${next.slug}`}>
            <span><small>Next study</small> <b>{next.title}</b></span>
            <Tile spec={next.tile} />
          </Link>
        </nav>
      </div>
    </section>
  );
}
```

- [ ] **Step 5: Write the study page and routes**

`apps/web/src/components/study/study-page.tsx`:

```tsx
import Link from "next/link";

import { Frieze } from "@/components/tiles/frieze";
import { Mosaic } from "@/components/tiles/mosaic";
import { borderTileMarkup, tileMarkup } from "@/components/tiles/tile-geometry";
import type { StudyRecord, StudySlug } from "@/content/types";
import type { LoadedResults } from "@/lib/study-results";

import { AnswerChapter, CheckChapter, EvidenceChapter, MadeChapter } from "./chapters";
import { STATUS_LABEL } from "./study-card";
import { studyThemeStyle } from "./study-theme";

interface StudyPageProps {
  study: StudyRecord;
  results: LoadedResults<StudySlug> | null;
}

export function StudyPage({ study, results }: StudyPageProps) {
  const frieze = [tileMarkup(study.tile), borderTileMarkup(study.tile, study.tint)];
  return (
    <div className={`study-page ${study.themeClass}`} style={studyThemeStyle(study)}>
      <div className="top">
        <div className="wrap">
          <div className="page-hero">
            <div>
              <Link className="crumb" href="/work">All case studies</Link>
              <br />
              <span className={study.status === "planned" ? "tag plan" : "tag"}>{STATUS_LABEL[study.status]}</span>
              <h1>{study.title}</h1>
              <p className="lede">{study.question}</p>
            </div>
            <Mosaic pair tiles={[study.tile, study.tile, study.tile, study.tile]} label={`${study.title} tiles. Select a tile to turn it.`} />
          </div>
        </div>
      </div>
      <Frieze markups={frieze} />
      <main id="main">
        <AnswerChapter study={study} results={results} />
        <Frieze markups={frieze} />
        <EvidenceChapter study={study} results={results} />
        <Frieze markups={frieze} />
        <MadeChapter study={study} results={results} />
        <Frieze markups={frieze} />
        <CheckChapter study={study} results={results} />
      </main>
    </div>
  );
}
```

`apps/web/src/app/work/[slug]/page.tsx`:

```tsx
import type { Metadata } from "next";
import { notFound } from "next/navigation";

import { StudyPage } from "@/components/study/study-page";
import { findStudy, studies } from "@/content/studies";
import { getStudyResults } from "@/lib/study-results";

export const dynamicParams = false;

export async function generateStaticParams(): Promise<Array<{ slug: string }>> {
  return studies.map((s) => ({ slug: s.slug }));
}

interface RouteProps {
  params: Promise<{ slug: string }>;
}

export async function generateMetadata({ params }: RouteProps): Promise<Metadata> {
  const study = findStudy((await params).slug);
  return study ? { title: `${study.title}, a case study`, description: study.question } : {};
}

export default async function StudyRoute({ params }: RouteProps) {
  const study = findStudy((await params).slug);
  if (!study) notFound();
  return <StudyPage study={study} results={getStudyResults(study.slug)} />;
}
```

`apps/web/src/app/work/page.tsx`:

```tsx
import type { Metadata } from "next";

import { StudyRun } from "@/components/study/study-run";
import { Frieze } from "@/components/tiles/frieze";
import { Tile } from "@/components/tiles/tile";
import { tileMarkup } from "@/components/tiles/tile-geometry";
import { studies } from "@/content/studies";

export const metadata: Metadata = { title: "Case studies", description: "Three questions about Malaysia, answered with public data." };

export default function WorkIndex() {
  return (
    <>
      <div className="top">
        <div className="wrap">
          <div className="page-hero">
            <div>
              <h1>Case studies</h1>
              <p className="lede">Three questions about Malaysia, answered with public data. Each one links its sources, code, model versions and known limits.</p>
            </div>
            <div className="hero-side">
              <div className="marks-row" aria-hidden="true">{studies.map((s) => <Tile key={s.slug} spec={s.tile} />)}</div>
              <p className="mosaic-note">One tile per study. You will find it on every page of that study.</p>
            </div>
          </div>
        </div>
      </div>
      <Frieze markups={studies.map((s) => tileMarkup(s.tile))} />
      <main id="main" className="chapter">
        <div className="wrap"><StudyRun headingLevel={2} /></div>
      </main>
    </>
  );
}
```

- [ ] **Step 6: Run the tests and the build**

Run: `npm test --workspace web`, then `npm run lint`, `npm run typecheck` and `npm run build`.
Expected: PASS. The build lists `/work`, `/work/penang-pulse`, `/work/forecasting-lab` and `/work/llm-eval-lab` as static pages.

- [ ] **Step 7: Check both modes by eye**

From `apps/web`, run `npm run build && npx next start --port 3001`. Open `http://localhost:3001/work/penang-pulse`: it shows the planned answer, the pending panel and "Not yet retrieved", with no numbers. Then run `npm run dev` and open the same page: it shows the preview flag and fixture numbers. The evidence chapter shows the pending panel until Task 7 registers the figure.

- [ ] **Step 8: Commit**

```bash
git add apps/web/src/components/study apps/web/src/components/figures/registry.ts apps/web/src/app/work
git commit -m "feat: add case study template, work index and study routes"
```

---

### Task 7: Penang Pulse figure

**Files:**
- Create: `apps/web/src/components/figures/penang/penang-figure.tsx`, `penang-map.tsx`, `district-tiles.tsx`, `district-panel.tsx`
- Modify: `apps/web/src/components/figures/registry.ts`
- Test: `apps/web/src/components/figures/penang/penang-figure.test.tsx`

**Interfaces:**
- Consumes: `PenangResults`, `PenangGeometry`, `District`, `ServicePoint` and `ServiceCategory` (Task 4); `TabList`, `tabId`, `ToggleGroup` and `useChartWidth` (Task 3); `palette` (Task 1).
- Produces: `<PenangFigure data: PenangResults />`, registered as `figures["penang-pulse"]`.

- [ ] **Step 1: Write the failing test**

`apps/web/src/components/figures/penang/penang-figure.test.tsx`:

```tsx
import { fireEvent, render, screen } from "@testing-library/react";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import { penangFixture } from "@/content/fixtures/penang";

import { PenangFigure } from "./penang-figure";

describe("PenangFigure", () => {
  it("server-renders the map, points and the default district without JavaScript", () => {
    const html = renderToStaticMarkup(<PenangFigure data={penangFixture} />);
    expect(html).toContain("Public services across Penang");
    expect((html.match(/data-cat="/g) ?? []).length).toBe(penangFixture.points.length);
    expect(html).toContain("Seberang Perai Selatan");
  });

  it("selects a district and updates the panel and the map", () => {
    const { container } = render(<PenangFigure data={penangFixture} />);
    fireEvent.click(screen.getByRole("tab", { name: /timur laut/i }));
    expect(screen.getByRole("tabpanel")).toHaveTextContent("Timur Laut");
    expect(screen.getByRole("tabpanel")).toHaveTextContent("72%");
    expect(container.querySelector('.district.on[data-district="tl"]')).not.toBeNull();
  });

  it("hides a category of points", () => {
    const { container } = render(<PenangFigure data={penangFixture} />);
    fireEvent.click(screen.getByRole("button", { name: "Schools" }));
    const schools = container.querySelectorAll('.pt[data-cat="school"]');
    expect(schools.length).toBeGreaterThan(0);
    schools.forEach((p) => expect(p.parentElement?.getAttribute("class")).toBe("off"));
  });
});
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `npm test --workspace web -- src/components/figures/penang`
Expected: FAIL with "Failed to resolve import ./penang-figure".

- [ ] **Step 3: Write the map**

`apps/web/src/components/figures/penang/penang-map.tsx`:

```tsx
"use client";

import { useRef, type CSSProperties } from "react";

import type { PenangGeometry, ServiceCategory, ServicePoint } from "@/content/types";
import { palette } from "@/styles/palette";

import { useChartWidth } from "../use-chart-width";

export const CATEGORY_COLOUR: Readonly<Record<ServiceCategory, string>> = { clinic: palette.cobalt, school: palette.roseDeep, transit: palette.peacock };

function Point({ point }: { point: ServicePoint }) {
  const { x, y, category } = point;
  const fill = CATEGORY_COLOUR[category];
  if (category === "clinic") return <circle className="pt" data-cat={category} cx={x} cy={y} r={5.2} fill={fill} stroke="#fff" strokeWidth={1.4} />;
  if (category === "school") return <rect className="pt" data-cat={category} x={x - 4.6} y={y - 4.6} width={9.2} height={9.2} fill={fill} stroke="#fff" strokeWidth={1.4} />;
  return <path className="pt" data-cat={category} d={`M${x} ${y - 6.2}L${x + 6.2} ${y}L${x} ${y + 6.2}L${x - 6.2} ${y}Z`} fill={fill} stroke="#fff" strokeWidth={1.4} />;
}

interface PenangMapProps {
  geometry: PenangGeometry;
  points: readonly ServicePoint[];
  visible: ReadonlySet<string>;
  selected: string;
}

export function PenangMap({ geometry, points, visible, selected }: PenangMapProps) {
  const ref = useRef<HTMLDivElement>(null);
  const width = useChartWidth(ref, 600);
  // Map labels keep a fixed on-screen size however wide the map renders.
  const style = { "--u": (600 / width).toFixed(3) } as CSSProperties;

  return (
    <div ref={ref} style={style}>
      <svg viewBox="0 0 600 500" role="img" aria-labelledby="map-title map-desc">
        <title id="map-title">Public services across Penang</title>
        <desc id="map-desc">Map of Penang Island and Seberang Perai with clinics, schools and transit stops plotted as points. The selected district is shaded.</desc>
        <defs>
          <clipPath id="island-clip"><path d={geometry.island} /></clipPath>
          <clipPath id="mainland-clip"><path d={geometry.mainland} /></clipPath>
        </defs>
        <rect width="600" height="500" fill="#d4e6e4" />
        <path d={geometry.mainland} fill="#fff" />
        <path d={geometry.island} fill="#fff" />
        {geometry.districts.map((d) => (
          <path key={d.id} className={d.id === selected ? "district on" : "district"} data-district={d.id} d={d.d} clipPath={`url(#${d.land}-clip)`} />
        ))}
        <g stroke={palette.inkSoft} strokeWidth={1.5} strokeDasharray="6 5" fill="none">
          {geometry.boundaries.map((b) => <path key={b} d={b} />)}
        </g>
        <path d={geometry.mainland} fill="none" stroke={palette.ink} strokeWidth={1.6} />
        <path d={geometry.island} fill="none" stroke={palette.ink} strokeWidth={1.6} />
        <g stroke={palette.ink} strokeWidth={2.5}>{geometry.bridges.map((b) => <path key={b} d={b} />)}</g>
        <text className="water" x={geometry.water.x} y={geometry.water.y}>{geometry.water.text}</text>
        <g>
          {points.map((p, i) => (
            <g key={i} className={visible.has(p.category) ? undefined : "off"}>
              <Point point={p} />
            </g>
          ))}
        </g>
        {geometry.places.map((p) => <text key={p.text} className="place" x={p.x} y={p.y}>{p.text}</text>)}
      </svg>
    </div>
  );
}
```

- [ ] **Step 4: Write the district tiles and panel**

`apps/web/src/components/figures/penang/district-tiles.tsx`:

```tsx
"use client";

import { TabList } from "@/components/ui/tab-list";
import type { District } from "@/content/types";
import { palette } from "@/styles/palette";

export const BAND_COLOURS = [palette.jade, palette.mustard, palette.rose] as const;
export const BAND_NAMES = ["Under 1 km", "1 to 3 km", "Over 3 km"] as const;

// A district tile: three bands stacked from the floor up (jade near, mustard middle, rose far).
function BandTile({ district }: { district: District }) {
  const tops = district.bands.reduce<number[]>((acc, p) => [...acc, (acc.at(-1) ?? 94) - p * 0.88], []);
  return (
    <svg viewBox="0 0 100 100" aria-hidden="true">
      <rect width="100" height="100" fill={palette.porcelain} />
      {district.bands.map((p, i) => <rect key={i} x="6" y={tops[i].toFixed(2)} width="88" height={(p * 0.88).toFixed(2)} fill={BAND_COLOURS[i]} />)}
      <path d="M50 20 L80 50 L50 80 L20 50Z" fill="none" stroke={palette.porcelain} strokeWidth="3" opacity=".85" />
      <circle cx="50" cy="50" r="5" fill={palette.porcelain} />
      <rect x="6" y="6" width="88" height="88" fill="none" stroke={palette.ink} strokeWidth="1.5" opacity=".6" />
    </svg>
  );
}

interface DistrictTilesProps {
  districts: readonly District[];
  selected: string;
  onSelect: (id: string) => void;
}

export function DistrictTiles({ districts, selected, onSelect }: DistrictTilesProps) {
  return (
    <TabList
      label="Districts"
      idPrefix="district"
      panelId="district-panel"
      className="district-tiles"
      tabClassName=""
      selected={selected}
      onSelect={onSelect}
      items={districts.map((d) => ({
        id: d.id,
        label: (
          <>
            <span className="tile-wrap"><BandTile district={d} /></span>
            <span className="name">{d.short.startsWith("SP ") ? <><abbr title="Seberang Perai">SP</abbr>{d.short.slice(2)}</> : d.short}</span>
            <span className="stat">{d.bands[2]}% over 3 km</span>
          </>
        ),
      }))}
    />
  );
}
```

`apps/web/src/components/figures/penang/district-panel.tsx`:

```tsx
import { tabId } from "@/components/ui/tab-list";
import type { District } from "@/content/types";
import { palette } from "@/styles/palette";

import { BAND_COLOURS, BAND_NAMES } from "./district-tiles";

const fmt = (n: number): string => n.toLocaleString("en-GB");

export function DistrictPanel({ district }: { district: District }) {
  const lefts = district.bands.map((_, i) => district.bands.slice(0, i).reduce((a, b) => a + b, 0));
  const far = Math.round((district.population * district.bands[2]) / 100 / 500) * 500;
  return (
    <div className="tile-frame panel" id="district-panel" role="tabpanel" tabIndex={0} aria-labelledby={tabId("district", district.id)}>
      <h4>{district.name}</h4>
      <p className="pop">Population {fmt(district.population)}, share of residents by road distance to the nearest public clinic</p>
      <div className="band-bar" aria-hidden="true">
        {district.bands.map((p, i) => <span key={i} className="band-seg" style={{ left: `${lefts[i]}%`, width: `${p}%`, background: BAND_COLOURS[i] }} />)}
      </div>
      <ul className="band-legend">
        {district.bands.map((p, i) => (
          <li key={i}><span className="sw sq" style={{ background: BAND_COLOURS[i], borderColor: palette.ink }} />{BAND_NAMES[i]}<strong>{p}%</strong></li>
        ))}
      </ul>
      <p className="callout"><strong>About {fmt(far)} residents</strong>live more than 3 km from a public clinic.</p>
    </div>
  );
}
```

- [ ] **Step 5: Write the figure and register it**

`apps/web/src/components/figures/penang/penang-figure.tsx`:

```tsx
"use client";

import { useState } from "react";

import { ToggleGroup } from "@/components/ui/toggle-group";
import type { PenangResults } from "@/content/types";
import { palette } from "@/styles/palette";

import { DistrictPanel } from "./district-panel";
import { DistrictTiles } from "./district-tiles";
import { CATEGORY_COLOUR, PenangMap } from "./penang-map";

const CATEGORIES = [
  { id: "clinic", label: "Clinics", shape: "sw" },
  { id: "school", label: "Schools", shape: "sw sq" },
  { id: "transit", label: "Transit stops", shape: "sw dia" },
] as const;

export function PenangFigure({ data }: { data: PenangResults }) {
  const [visible, setVisible] = useState<ReadonlySet<string>>(new Set(CATEGORIES.map((c) => c.id)));
  const [selected, setSelected] = useState(data.districts.at(-1)?.id ?? "");
  const district = data.districts.find((d) => d.id === selected) ?? data.districts[0];

  return (
    <div>
      <h3 className="sub">Distance to the nearest clinic, by district</h3>
      <p className="intro">Each tile is a district. Its bands fill from the floor up: jade for residents under 1 km from a public clinic, mustard for 1 to 3 km, rose for over 3 km. Pick a tile to see its numbers and find it on the map.</p>
      <div className="figure-grid">
        <figure className="tile-frame map">
          <PenangMap geometry={data.geometry} points={data.points} visible={visible} selected={selected} />
          <ToggleGroup
            label="Show or hide service types"
            pressed={visible}
            onChange={setVisible}
            items={CATEGORIES.map((c) => ({
              id: c.id,
              label: <><span className={c.shape} style={{ background: CATEGORY_COLOUR[c.id], borderColor: c.id === "school" ? palette.roseDeep : CATEGORY_COLOUR[c.id] }} />{c.label}</>,
            }))}
          />
          <figcaption className="figcap">{data.pointsNote}</figcaption>
        </figure>
        <div>
          <DistrictTiles districts={data.districts} selected={selected} onSelect={setSelected} />
          <DistrictPanel district={district} />
          <p className="figcap"><abbr title="Seberang Perai">SP</abbr> is Seberang Perai. Shares are of residents, by road distance from population-weighted mukim centroids.</p>
        </div>
      </div>
    </div>
  );
}
```

Replace the contents of `apps/web/src/components/figures/registry.ts` with:

```ts
import type { ComponentType } from "react";

import type { StudyResultsBySlug, StudySlug } from "@/content/types";

import { PenangFigure } from "./penang/penang-figure";

export type FigureRegistry = { [S in StudySlug]?: ComponentType<{ data: StudyResultsBySlug[S] }> };

// An unregistered study shows the pending panel.
export const figures: FigureRegistry = {
  "penang-pulse": PenangFigure,
};
```

- [ ] **Step 6: Run the tests to verify they pass**

Run: `npm test --workspace web`, then `npm run lint` and `npm run typecheck`.
Expected: PASS.

- [ ] **Step 7: Compare with the prototype**

Run `npm run dev`. Open `/work/penang-pulse` beside `mockups/peranakan-tiles/work/penang-pulse.html` at 1440px and 390px. Check that:
- the district tiles, the panel and the map shading change together;
- the toggles hide their points;
- map labels stay readable on mobile.

- [ ] **Step 8: Commit**

```bash
git add apps/web/src/components/figures
git commit -m "feat: add Penang Pulse map and district tiles figure"
```

---

### Task 8: Forecasting Lab figure

**Files:**
- Create: `apps/web/src/components/figures/forecasting/forecast-figure.tsx`, `forecast-chart.tsx`, `horizon-chart.tsx`, `model-style.ts`
- Modify: `apps/web/src/components/figures/registry.ts`
- Test: `apps/web/src/components/figures/forecasting/forecast-figure.test.tsx`

**Interfaces:**
- Consumes: `ForecastResults`, `ForecastModel`, `ForecastModelId` and `SensorSeries` (Task 4); `TabList`, `tabId`, `ToggleGroup`, `useChartWidth`, `scale`, `pathOf` and `clock` (Task 3).
- Produces: `<ForecastFigure data: ForecastResults />`, registered as `figures["forecasting-lab"]`; `MODEL_STYLE: Record<ForecastModelId, { colour: string; dash?: string }>`.

- [ ] **Step 1: Write the failing test**

`apps/web/src/components/figures/forecasting/forecast-figure.test.tsx`:

```tsx
import { fireEvent, render, screen } from "@testing-library/react";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import { forecastFixture } from "@/content/fixtures/forecasting";

import { ForecastFigure } from "./forecast-figure";

describe("ForecastFigure", () => {
  it("server-renders both charts with every model line", () => {
    const html = renderToStaticMarkup(<ForecastFigure data={forecastFixture} />);
    expect(html).toContain("Traffic flow for Sensor 12");
    expect((html.match(/class="model-line"/g) ?? []).length).toBe(8); // 4 forecast lines and 4 horizon lines
  });

  it("switches sensor and updates the window error list", () => {
    render(<ForecastFigure data={forecastFixture} />);
    const before = screen.getByRole("list", { name: /mean absolute error in this window/i }).textContent;
    fireEvent.click(screen.getByRole("tab", { name: "Sensor 47" }));
    expect(screen.getByRole("img", { name: /sensor 47/i })).toBeInTheDocument();
    expect(screen.getByRole("list", { name: /mean absolute error in this window/i }).textContent).not.toBe(before);
  });

  it("hides a model from both charts", () => {
    const { container } = render(<ForecastFigure data={forecastFixture} />);
    fireEvent.click(screen.getByRole("button", { name: "Chronos, zero-shot" }));
    expect(container.querySelectorAll(".model-line")).toHaveLength(6);
  });

  it("bolds the lowest error in each horizon column", () => {
    render(<ForecastFigure data={forecastFixture} />);
    const bold = screen.getByRole("table").querySelectorAll("b");
    expect([...bold].map((b) => b.textContent)).toEqual(["6.1", "7.9", "10.1", "11.6", "13.4"]);
  });
});
```

The bold cells come out in row order: gradient boosting first (6.1 and 7.9), then Chronos (10.1, 11.6 and 13.4).

- [ ] **Step 2: Run the test to verify it fails**

Run: `npm test --workspace web -- src/components/figures/forecasting`
Expected: FAIL with "Failed to resolve import ./forecast-figure".

- [ ] **Step 3: Write the model styles and charts**

`apps/web/src/components/figures/forecasting/model-style.ts`:

```ts
import type { ForecastModelId } from "@/content/types";
import { palette } from "@/styles/palette";

// One colour per model across both charts, the toggles and the table. All are at least 3:1 on porcelain and sky.
export const MODEL_STYLE: Readonly<Record<ForecastModelId, { colour: string; dash?: string }>> = {
  naive: { colour: palette.inkSoft, dash: "7 5" },
  gb: { colour: palette.mustardDeep },
  gru: { colour: palette.cobalt },
  chronos: { colour: palette.jadeDeep },
};
```

`apps/web/src/components/figures/forecasting/forecast-chart.tsx`:

```tsx
"use client";

import { useRef } from "react";

import type { ForecastModel, SensorSeries } from "@/content/types";
import { palette } from "@/styles/palette";

import { clock, pathOf, scale } from "../chart-utils";
import { useChartWidth } from "../use-chart-width";
import { MODEL_STYLE } from "./model-style";

interface ForecastChartProps {
  sensor: SensorSeries;
  models: readonly ForecastModel[];
  visible: ReadonlySet<string>;
}

export function ForecastChart({ sensor, models, visible }: ForecastChartProps) {
  const ref = useRef<HTMLDivElement>(null);
  const w = useChartWidth(ref);
  const h = Math.round(Math.min(420, Math.max(300, w * 0.52)));
  const pad = { l: 46, r: 14, t: 34, b: 38 };
  const past = sensor.pastSteps;
  const ahead = sensor.actual.length - past - 1;
  const shown = models.filter((m) => visible.has(m.id));
  const values = [...sensor.actual, ...shown.flatMap((m) => sensor.forecasts[m.id])];
  const lo = Math.floor((Math.min(...values) - 5) / 25) * 25;
  const hi = Math.ceil((Math.max(...values) + 5) / 25) * 25;
  const x = scale(-past, ahead, pad.l, w - pad.r);
  const y = scale(lo, hi, h - pad.b, pad.t);
  const yTicks = Array.from({ length: (hi - lo) / 25 + 1 }, (_, i) => lo + i * 25);
  const hourStep = w < 520 ? 24 : 12;
  const xTicks = Array.from({ length: Math.floor((past + ahead) / hourStep) + 1 }, (_, i) => -past + i * hourStep);

  return (
    <div className="chart" ref={ref}>
      <svg viewBox={`0 0 ${w} ${h}`} role="img" aria-label={`Traffic flow for ${sensor.label}, actual and forecast, vehicles per 5 minutes`}>
        <rect x={x(0)} y={pad.t} width={x(ahead) - x(0)} height={h - pad.b - pad.t} fill={palette.sky} />
        <text className="strong" x={x(0) + 8} y={pad.t - 12}>Next 2 hours</text>
        {yTicks.map((v) => (
          <g key={v}>
            <line x1={pad.l} x2={w - pad.r} y1={y(v)} y2={y(v)} stroke={palette.ink} strokeOpacity={0.1} />
            <text x={pad.l - 8} y={y(v) + 4} textAnchor="end">{v}</text>
          </g>
        ))}
        {xTicks.map((t) => <text key={t} x={x(t)} y={h - pad.b + 22} textAnchor="middle">{clock(sensor.originMinutes + t * sensor.stepMinutes)}</text>)}
        <line x1={x(0)} x2={x(0)} y1={pad.t} y2={h - pad.b} stroke={palette.ink} strokeWidth={1.5} />
        <line x1={pad.l} x2={w - pad.r} y1={h - pad.b} y2={h - pad.b} stroke={palette.ink} strokeWidth={1.5} />
        <path d={pathOf(sensor.actual.map((v, i) => [x(i - past), y(v)] as const))} fill="none" stroke={palette.ink} strokeWidth={2.5} strokeLinejoin="round" />
        {shown.map((m) => (
          <path
            key={m.id}
            className="model-line"
            d={pathOf(sensor.forecasts[m.id].map((v, i) => [x(i), y(v)] as const))}
            fill="none"
            stroke={MODEL_STYLE[m.id].colour}
            strokeWidth={2.75}
            strokeLinejoin="round"
            strokeDasharray={MODEL_STYLE[m.id].dash}
          />
        ))}
      </svg>
    </div>
  );
}
```

`apps/web/src/components/figures/forecasting/horizon-chart.tsx`:

```tsx
"use client";

import { useRef } from "react";

import type { ForecastModel } from "@/content/types";
import { palette } from "@/styles/palette";

import { pathOf, scale } from "../chart-utils";
import { useChartWidth } from "../use-chart-width";
import { MODEL_STYLE } from "./model-style";

interface HorizonChartProps {
  horizons: readonly number[];
  models: readonly ForecastModel[];
  visible: ReadonlySet<string>;
}

export function HorizonChart({ horizons, models, visible }: HorizonChartProps) {
  const ref = useRef<HTMLDivElement>(null);
  const w = useChartWidth(ref);
  const h = Math.round(Math.min(340, Math.max(260, w * 0.42)));
  const pad = { l: 40, r: 18, t: 18, b: 40 };
  const x = (i: number): number => pad.l + 20 + i * ((w - pad.l - pad.r - 40) / (horizons.length - 1));
  const y = scale(0, 18, h - pad.b, pad.t);

  return (
    <div className="chart" ref={ref}>
      <svg viewBox={`0 0 ${w} ${h}`} role="img" aria-label="Mean absolute error by forecast horizon for each model">
        {[0, 6, 12, 18].map((v) => (
          <g key={v}>
            <line x1={pad.l} x2={w - pad.r} y1={y(v)} y2={y(v)} stroke={palette.ink} strokeOpacity={v ? 0.1 : 1} strokeWidth={v ? 1 : 1.5} />
            <text x={pad.l - 8} y={y(v) + 4} textAnchor="end">{v}</text>
          </g>
        ))}
        {horizons.map((hz, i) => <text key={hz} x={x(i)} y={h - pad.b + 22} textAnchor="middle">{hz} min</text>)}
        {models.filter((m) => visible.has(m.id)).map((m) => (
          <g key={m.id}>
            <path className="model-line" d={pathOf(m.mae.map((v, i) => [x(i), y(v)] as const))} fill="none" stroke={MODEL_STYLE[m.id].colour} strokeWidth={2.75} strokeDasharray={MODEL_STYLE[m.id].dash} />
            {m.mae.map((v, i) => <circle key={i} cx={x(i)} cy={y(v)} r={4.5} fill={MODEL_STYLE[m.id].colour} stroke="#fff" strokeWidth={1.5} />)}
          </g>
        ))}
      </svg>
    </div>
  );
}
```

- [ ] **Step 4: Write the figure and register it**

`apps/web/src/components/figures/forecasting/forecast-figure.tsx`:

```tsx
"use client";

import { useState } from "react";

import { TabList, tabId } from "@/components/ui/tab-list";
import { ToggleGroup } from "@/components/ui/toggle-group";
import type { ForecastModelId, ForecastResults } from "@/content/types";

import { ForecastChart } from "./forecast-chart";
import { HorizonChart } from "./horizon-chart";
import { MODEL_STYLE } from "./model-style";

const Swatch = ({ id }: { id: ForecastModelId }) => <span className="sw line" style={{ background: MODEL_STYLE[id].colour }} />;

export function ForecastFigure({ data }: { data: ForecastResults }) {
  const [sensorId, setSensorId] = useState(data.sensors[0].id);
  const [visible, setVisible] = useState<ReadonlySet<string>>(new Set(data.models.map((m) => m.id)));
  const sensor = data.sensors.find((s) => s.id === sensorId) ?? data.sensors[0];
  const best = data.horizons.map((_, i) => Math.min(...data.models.map((m) => m.mae[i])));

  return (
    <div>
      <h3 className="sub">Forecasts for the next two hours</h3>
      <p className="intro">Pick a sensor, then switch models on and off. The black line is the traffic that actually arrived. The model toggles also drive the error chart below.</p>
      <div className="controls">
        <span className="label" id="sensor-label">Sensor</span>
        <TabList labelledBy="sensor-label" idPrefix="sensor" panelId="forecast-panel" selected={sensorId} onSelect={setSensorId} items={data.sensors.map((s) => ({ id: s.id, label: s.label }))} />
      </div>
      <ToggleGroup label="Show or hide models" prefix="Models" pressed={visible} onChange={setVisible} items={data.models.map((m) => ({ id: m.id, label: <><Swatch id={m.id} />{m.name}</> }))} />
      <div className="stack">
        <figure className="tile-frame" id="forecast-panel" role="tabpanel" aria-labelledby={tabId("sensor", sensorId)}>
          <ForecastChart sensor={sensor} models={data.models} visible={visible} />
          <figcaption className="figcap">Vehicles per 5 minutes. The shaded window is the forecast; the seasonal naive line is dashed.</figcaption>
          <h4 className="panel-title" id="window-mae-h" style={{ marginTop: 20, fontSize: 17 }}>Mean absolute error in this window</h4>
          <ul className="band-legend mae-list" aria-labelledby="window-mae-h">
            {data.models.map((m) => <li key={m.id}><Swatch id={m.id} />{m.name}<strong>{sensor.windowMae[m.id].toFixed(1)}</strong></li>)}
          </ul>
        </figure>
        <figure className="tile-frame">
          <h4 className="panel-title">Error by horizon</h4>
          <p className="figcap" style={{ margin: "0 0 14px" }}>Mean absolute error on the test window, all sensors, vehicles per 5 minutes. Lower is better.</p>
          <HorizonChart horizons={data.horizons} models={data.models} visible={visible} />
          <div className="table-wrap" role="region" aria-label="Mean absolute error by horizon" tabIndex={0} style={{ marginTop: 18 }}>
            <table>
              <thead>
                <tr><th scope="col">Model</th>{data.horizons.map((hz) => <th key={hz} scope="col" className="num">{hz} min</th>)}</tr>
              </thead>
              <tbody>
                {data.models.map((m) => (
                  <tr key={m.id}>
                    <th scope="row"><span className="model-name"><Swatch id={m.id} />{m.name}</span></th>
                    {m.mae.map((v, i) => <td key={i} className="num">{v === best[i] ? <b>{v.toFixed(1)}</b> : v.toFixed(1)}</td>)}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </figure>
      </div>
    </div>
  );
}
```

In `apps/web/src/components/figures/registry.ts`, add `import { ForecastFigure } from "./forecasting/forecast-figure";` under the Penang import, and add the entry `"forecasting-lab": ForecastFigure,` inside `figures`.

- [ ] **Step 5: Run the tests to verify they pass**

Run: `npm test --workspace web`, then `npm run lint` and `npm run typecheck`.
Expected: PASS.

- [ ] **Step 6: Compare with the prototype**

Open `/work/forecasting-lab` in `npm run dev` beside `mockups/peranakan-tiles/work/forecasting-lab.html` at 1440px and 390px. Check that sensor tabs work with arrow keys, that the toggles drive both charts, and that axis text stays readable at 390px.

- [ ] **Step 7: Commit**

```bash
git add apps/web/src/components/figures
git commit -m "feat: add Forecasting Lab forecast and horizon charts"
```

---

### Task 9: LLM Eval Lab figure

**Files:**
- Create: `apps/web/src/components/figures/llm-eval/llm-eval-figure.tsx`, `leaderboard.tsx`, `cost-score-chart.tsx`, `error-examples.tsx`, `role-style.ts`
- Modify: `apps/web/src/components/figures/registry.ts`
- Test: `apps/web/src/components/figures/llm-eval/llm-eval-figure.test.tsx`

**Interfaces:**
- Consumes: `LlmEvalResults`, `EvalTask`, `ErrorExample` and `ModelRole` (Task 4); `TabList`, `tabId`, `useChartWidth` and `scale` (Task 3).
- Produces: `<LlmEvalFigure data: LlmEvalResults />`, registered as `figures["llm-eval-lab"]`.

- [ ] **Step 1: Write the failing test**

`apps/web/src/components/figures/llm-eval/llm-eval-figure.test.tsx`:

```tsx
import { fireEvent, render, screen, within } from "@testing-library/react";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import { llmEvalFixture } from "@/content/fixtures/llm-eval";

import { LlmEvalFigure } from "./llm-eval-figure";

describe("LlmEvalFigure", () => {
  it("server-renders the default task's leaderboard and scatter", () => {
    const html = renderToStaticMarkup(<LlmEvalFigure data={llmEvalFixture} />);
    expect(html).toContain("Accuracy, with 95% interval");
    expect((html.match(/class="score-dot"/g) ?? []).length).toBe(4);
  });

  it("changes the table and the chart together when the task changes", () => {
    render(<LlmEvalFigure data={llmEvalFixture} />);
    fireEvent.click(screen.getByRole("tab", { name: "BM summaries" }));
    const table = screen.getByRole("table");
    expect(within(table).getByRole("columnheader", { name: /faithfulness/i })).toBeInTheDocument();
    expect(within(table).getByText("Extractive baseline")).toBeInTheDocument();
    expect(screen.getByRole("img", { name: /faithfulness against cost/i })).toBeInTheDocument();
  });

  it("labels every point on the scatter by name", () => {
    render(<LlmEvalFigure data={llmEvalFixture} />);
    const chart = screen.getByRole("img", { name: /accuracy against cost/i });
    for (const row of llmEvalFixture.tasks[0].rows) expect(chart).toHaveTextContent(row.model);
  });

  it("shows each error example with its verdict", () => {
    render(<LlmEvalFigure data={llmEvalFixture} />);
    expect(screen.getAllByText("Missed")).toHaveLength(2);
    expect(screen.getAllByText("Correct")).toHaveLength(1);
  });
});
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `npm test --workspace web -- src/components/figures/llm-eval`
Expected: FAIL with "Failed to resolve import ./llm-eval-figure".

- [ ] **Step 3: Write the parts**

`apps/web/src/components/figures/llm-eval/role-style.ts`:

```ts
import type { ModelRole } from "@/content/types";
import { palette } from "@/styles/palette";

// Marks use the deep glaze (at least 3:1); interval bands use the light tint.
export const ROLE_COLOUR: Readonly<Record<ModelRole, string>> = { frontier: palette.cobalt, ft: palette.jadeDeep, open: palette.mustardDeep, base: palette.roseDeep };
export const ROLE_TINT: Readonly<Record<ModelRole, string>> = { frontier: palette.cobalt, ft: palette.jade, open: palette.mustard, base: palette.rose };
```

`apps/web/src/components/figures/llm-eval/leaderboard.tsx`:

```tsx
import type { EvalTask } from "@/content/types";
import { palette } from "@/styles/palette";

import { scale } from "../chart-utils";
import { ROLE_COLOUR, ROLE_TINT } from "./role-style";

const pct = scale(50, 100, 0, 100);

export function Leaderboard({ task }: { task: EvalTask }) {
  return (
    <div className="tile-frame">
      <div className="table-wrap" role="region" aria-label="Leaderboard for the selected task" tabIndex={0}>
        <table>
          <thead>
            <tr>
              <th scope="col">Model</th>
              <th scope="col" className="board-metric">{task.metric}, with 95% interval</th>
              <th scope="col" className="num">Cost per 1k items</th>
              <th scope="col" className="num">Median latency</th>
            </tr>
          </thead>
          <tbody>
            {task.rows.map((r) => (
              <tr key={r.model}>
                <th scope="row"><span className="model-name"><span className="sw" style={{ background: ROLE_COLOUR[r.role], borderColor: palette.ink }} />{r.model}</span></th>
                <td>
                  <div className="ci">
                    <b>{r.score}<small>{r.low} to {r.high}</small></b>
                    <span className="ci-track" aria-hidden="true">
                      <span className="ci-range" style={{ left: `${pct(r.low)}%`, width: `${pct(r.high) - pct(r.low)}%`, background: ROLE_TINT[r.role] }} />
                      <span className="ci-dot" style={{ left: `${pct(r.score)}%`, background: ROLE_COLOUR[r.role] }} />
                    </span>
                  </div>
                </td>
                <td className="num">{r.costLabel}</td>
                <td className="num">{r.latency}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
```

`apps/web/src/components/figures/llm-eval/cost-score-chart.tsx`:

```tsx
"use client";

import { useRef } from "react";

import type { EvalTask } from "@/content/types";
import { palette } from "@/styles/palette";

import { scale } from "../chart-utils";
import { useChartWidth } from "../use-chart-width";
import { ROLE_COLOUR } from "./role-style";

const COST_TICKS = [[0.01, "$0.01"], [0.1, "$0.10"], [1, "$1"], [10, "$10"]] as const;

export function CostScoreChart({ task }: { task: EvalTask }) {
  const ref = useRef<HTMLDivElement>(null);
  const w = useChartWidth(ref);
  const h = Math.round(Math.min(380, Math.max(300, w * 0.5)));
  const pad = { l: 44, r: 16, t: 18, b: 32 };
  const lx = scale(Math.log10(0.005), Math.log10(10), pad.l, w - pad.r);
  const x = (v: number): number => lx(Math.log10(v));
  const y = scale(50, 95, h - pad.b, pad.t);

  return (
    <div className="chart" ref={ref}>
      <svg viewBox={`0 0 ${w} ${h}`} role="img" aria-label={`${task.metric} against cost per 1k items for each model`}>
        {[50, 60, 70, 80, 90].map((v) => (
          <g key={v}>
            <line x1={pad.l} x2={w - pad.r} y1={y(v)} y2={y(v)} stroke={palette.ink} strokeOpacity={0.1} />
            <text x={pad.l - 8} y={y(v) + 4} textAnchor="end">{v}</text>
          </g>
        ))}
        {COST_TICKS.map(([v, label]) => (
          <g key={label}>
            <line x1={x(v)} x2={x(v)} y1={pad.t} y2={h - pad.b} stroke={palette.ink} strokeOpacity={0.1} />
            <text x={x(v)} y={h - pad.b + 20} textAnchor={v === 10 ? "end" : "middle"}>{label}</text>
          </g>
        ))}
        <line x1={pad.l} x2={w - pad.r} y1={h - pad.b} y2={h - pad.b} stroke={palette.ink} strokeWidth={1.5} />
        {task.rows.map((r) => {
          const px = x(r.costPer1k);
          const py = y(r.score);
          const right = px > w * 0.62;
          return (
            <g key={r.model}>
              <line x1={px} x2={px} y1={y(r.low)} y2={y(r.high)} stroke={ROLE_COLOUR[r.role]} strokeWidth={2.5} strokeLinecap="round" />
              <circle className="score-dot" cx={px} cy={py} r={7.5} fill={ROLE_COLOUR[r.role]} stroke={palette.ink} strokeWidth={2} />
              <text className="strong" x={right ? px + 9 : px + 13} y={right ? py - 15 : py + 4.5} textAnchor={right ? "end" : "start"}>{r.model}</text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}
```

`apps/web/src/components/figures/llm-eval/error-examples.tsx`:

```tsx
import type { ErrorExample } from "@/content/types";

export function ErrorExamples({ examples }: { examples: readonly ErrorExample[] }) {
  return (
    <>
      <h3 className="sub">Error examples</h3>
      <p className="intro">Three items from the Manglish sentiment set, picked to show where models slip.</p>
      <div className="examples">
        {examples.map((e) => (
          <article key={e.input} className="tile-frame">
            <span className={e.correct ? "verdict ok" : "verdict miss"}>{e.correct ? "Correct" : "Missed"}</span>
            <blockquote>&ldquo;{e.input}&rdquo;</blockquote>
            <dl>
              <dt>Expected</dt><dd>{e.expected}</dd>
              <dt>Model</dt><dd>{e.model}</dd>
              <dt>Output</dt><dd>{e.output}</dd>
              <dt>Note</dt><dd>{e.note}</dd>
            </dl>
          </article>
        ))}
      </div>
    </>
  );
}
```

- [ ] **Step 4: Write the figure and register it**

`apps/web/src/components/figures/llm-eval/llm-eval-figure.tsx`:

```tsx
"use client";

import { useState } from "react";

import { TabList, tabId } from "@/components/ui/tab-list";
import type { LlmEvalResults } from "@/content/types";

import { CostScoreChart } from "./cost-score-chart";
import { ErrorExamples } from "./error-examples";
import { Leaderboard } from "./leaderboard";

export function LlmEvalFigure({ data }: { data: LlmEvalResults }) {
  const [taskId, setTaskId] = useState(data.tasks[0].id);
  const task = data.tasks.find((t) => t.id === taskId) ?? data.tasks[0];

  return (
    <div>
      <h3 className="sub">Leaderboard</h3>
      <p className="intro">Pick a task. Each model keeps its colour across the table and the chart. Bars show the 95% interval on a 50 to 100 scale.</p>
      <TabList label="Tasks" idPrefix="task" panelId="task-panel" selected={taskId} onSelect={setTaskId} items={data.tasks.map((t) => ({ id: t.id, label: t.label }))} />
      <div className="stack" id="task-panel" role="tabpanel" aria-labelledby={tabId("task", taskId)}>
        <Leaderboard task={task} />
        <figure className="tile-frame">
          <h4 className="panel-title">Cost against score</h4>
          <p className="figcap" style={{ margin: "0 0 14px" }}>One point per model for the selected task. Vertical lines are 95% intervals. Up and to the left is better value.</p>
          <CostScoreChart task={task} />
          <p className="figcap">Score on the vertical axis. Cost per 1k items on a log scale; baselines cost under $0.01 and sit at the left edge.</p>
        </figure>
      </div>
      <ErrorExamples examples={data.errorExamples} />
    </div>
  );
}
```

In `apps/web/src/components/figures/registry.ts`, add `import { LlmEvalFigure } from "./llm-eval/llm-eval-figure";` and the entry `"llm-eval-lab": LlmEvalFigure,`.

- [ ] **Step 5: Run the tests to verify they pass**

Run: `npm test --workspace web`, then `npm run lint` and `npm run typecheck`.
Expected: PASS.

- [ ] **Step 6: Compare with the prototype and commit**

Open `/work/llm-eval-lab` in `npm run dev` beside `mockups/peranakan-tiles/work/llm-eval-lab.html` at 1440px and 390px.

```bash
git add apps/web/src/components/figures
git commit -m "feat: add LLM Eval Lab leaderboard, cost chart and error examples"
```

---

### Task 10: Experiments and About pages

**Files:**
- Create: `apps/web/src/components/experiments/experiment-list.tsx`, `apps/web/src/app/experiments/page.tsx`, `apps/web/src/app/about/page.tsx`
- Test: `apps/web/src/components/experiments/experiment-list.test.tsx`, `apps/web/src/app/about/page.test.tsx`

**Interfaces:**
- Consumes: `experiments`, `EXPERIMENT_CATEGORIES`, `ToolItem`, `ToggleGroup`, `ContactButtons` and `profile`.
- Produces: the `/experiments` and `/about` routes.

- [ ] **Step 1: Write the failing tests**

`apps/web/src/components/experiments/experiment-list.test.tsx`:

```tsx
import { fireEvent, render, screen } from "@testing-library/react";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import { ExperimentList } from "./experiment-list";

describe("ExperimentList", () => {
  it("without JavaScript shows all 12 tools and no filter buttons", () => {
    const html = renderToStaticMarkup(<ExperimentList />);
    expect((html.match(/class="tool"/g) ?? []).length).toBe(12);
    expect(html).not.toContain("aria-pressed");
  });

  it("filters by category and reports the count", () => {
    render(<ExperimentList />);
    fireEvent.click(screen.getByRole("button", { name: "Libraries" }));
    expect(screen.getByRole("button", { name: "Libraries" })).toHaveAttribute("aria-pressed", "true");
    expect(screen.getAllByRole("listitem")).toHaveLength(5);
    expect(screen.getByText("Showing 5 of 12 tools")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "All" }));
    expect(screen.getAllByRole("listitem")).toHaveLength(12);
  });
});
```

`apps/web/src/app/about/page.test.tsx`:

```tsx
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import About from "./page";

describe("About", () => {
  it("has a contact section and no placeholder buttons", () => {
    const { container } = render(<About />);
    expect(container.querySelector("#contact")).not.toBeNull();
    expect(screen.queryByRole("link", { name: "Email me" })).not.toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Find me on GitHub" })).toHaveAttribute("href", "https://github.com/SubaashNair");
    expect(screen.getByRole("heading", { level: 2, name: "Toolkit" })).toBeInTheDocument();
  });
});
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `npm test --workspace web -- src/components/experiments src/app/about`
Expected: FAIL with "Failed to resolve import".

- [ ] **Step 3: Write the experiment list**

`apps/web/src/components/experiments/experiment-list.tsx`:

```tsx
"use client";

import { useState, useSyncExternalStore } from "react";

import { ToggleGroup } from "@/components/ui/toggle-group";
import { EXPERIMENT_CATEGORIES, experiments } from "@/content/experiments";

import { ToolItem } from "./tool-item";

const ALL = "all";
const noop = () => () => {};

export function ExperimentList() {
  // False on the server and true in the browser, so a no-JavaScript visitor sees every tool and no dead buttons.
  const hydrated = useSyncExternalStore(noop, () => true, () => false);
  const [filter, setFilter] = useState<ReadonlySet<string>>(new Set([ALL]));

  const active = [...filter][0] ?? ALL;
  const shown = active === ALL ? experiments : experiments.filter((e) => e.category === active);

  return (
    <>
      {hydrated && (
        <>
          <ToggleGroup
            label="Filter by category"
            mode="single"
            className="filters"
            pressed={filter}
            onChange={setFilter}
            items={[{ id: ALL, label: "All" }, ...EXPERIMENT_CATEGORIES.map((c) => ({ id: c.id, label: c.label }))]}
          />
          <p className="count" aria-live="polite">Showing {shown.length} of {experiments.length} tools</p>
        </>
      )}
      <ul className="tools">{shown.map((e) => <ToolItem key={e.name} experiment={e} />)}</ul>
    </>
  );
}
```

- [ ] **Step 4: Write the pages**

`apps/web/src/app/experiments/page.tsx`:

```tsx
import type { Metadata } from "next";

import { ExperimentList } from "@/components/experiments/experiment-list";

export const metadata: Metadata = { title: "Tools and experiments", description: "Libraries, agents and apps Subashanan Nair has shipped. All open source." };

export default function ExperimentsPage() {
  return (
    <>
      <div className="top">
        <div className="wrap">
          <div className="page-hero solo">
            <div>
              <h1>Tools and experiments</h1>
              <p className="lede">Smaller things I have shipped: libraries, agents and apps. All open source, each with its own tile.</p>
            </div>
          </div>
        </div>
      </div>
      <main id="main">
        <div className="wrap page-end">
          <section className="part" aria-labelledby="list-h">
            <h2 id="list-h" className="sr">All tools</h2>
            <ExperimentList />
          </section>
        </div>
      </main>
    </>
  );
}
```

`apps/web/src/app/about/page.tsx`:

```tsx
import type { Metadata } from "next";

import { ContactButtons } from "@/components/home/about-band";
import { profile } from "@/content/profile";

export const metadata: Metadata = { title: "About", description: profile.intro };

export default function About() {
  return (
    <>
      <div className="top">
        <div className="wrap">
          <div className="page-hero solo">
            <div>
              <h1>About</h1>
              <p className="lede">{profile.intro}</p>
            </div>
          </div>
        </div>
      </div>
      <main id="main">
        <div className="wrap">
          <div className="cols part">
            <section className="frame" aria-labelledby="what-h">
              <h2 id="what-h">What I work on</h2>
              <ul>{profile.workOn.map((x) => <li key={x}>{x}</li>)}</ul>
            </section>
            <section className="frame" aria-labelledby="how-h">
              <h2 id="how-h">How I work</h2>
              <ul>{profile.howIWork.map((x) => <li key={x}>{x}</li>)}</ul>
            </section>
          </div>
          <section className="part" aria-labelledby="kit-h">
            <h2 id="kit-h">Toolkit</h2>
            <ul className="toolkit">{profile.toolkit.map((x) => <li key={x}>{x}</li>)}</ul>
          </section>
          <section className="part page-end" id="contact" aria-labelledby="contact-h">
            <h2 id="contact-h">Contact</h2>
            <p className="intro">{profile.openTo}</p>
            <ContactButtons tone="light" />
          </section>
        </div>
      </main>
    </>
  );
}
```

- [ ] **Step 5: Run the tests and the build**

Run: `npm test --workspace web`, then `npm run lint` and `npm run build`.
Expected: PASS. Every nav link now resolves.

- [ ] **Step 6: Commit**

```bash
git add apps/web/src/components/experiments apps/web/src/app/experiments apps/web/src/app/about
git commit -m "feat: add experiments and about pages"
```

---

### Task 11: Metadata, Open Graph image, sitemap, robots and the final pass

**Files:**
- Create: `apps/web/src/app/sitemap.ts`, `apps/web/src/app/robots.ts`, `apps/web/src/app/opengraph-image.tsx`
- Delete: `apps/web/public/sitemap.xml`, `apps/web/public/robots.txt`
- Modify: `apps/web/src/app/layout.tsx` (metadata only)
- Test: `apps/web/src/app/sitemap.test.ts`

**Interfaces:**
- Consumes: `profile` and `studies`.

- [ ] **Step 1: Write the failing test**

`apps/web/src/app/sitemap.test.ts`:

```ts
import { describe, expect, it } from "vitest";

import sitemap from "./sitemap";

describe("sitemap", () => {
  it("lists every page", () => {
    expect(sitemap().map((e) => e.url)).toEqual([
      "https://ai-observatory.vercel.app/",
      "https://ai-observatory.vercel.app/work",
      "https://ai-observatory.vercel.app/work/penang-pulse",
      "https://ai-observatory.vercel.app/work/forecasting-lab",
      "https://ai-observatory.vercel.app/work/llm-eval-lab",
      "https://ai-observatory.vercel.app/experiments",
      "https://ai-observatory.vercel.app/about",
    ]);
  });
});
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `npm test --workspace web -- src/app/sitemap.test.ts`
Expected: FAIL with "Failed to resolve import ./sitemap".

- [ ] **Step 3: Write the metadata routes**

`apps/web/src/app/sitemap.ts`:

```ts
import type { MetadataRoute } from "next";

import { profile } from "@/content/profile";
import { studies } from "@/content/studies";

export default function sitemap(): MetadataRoute.Sitemap {
  const paths = ["/", "/work", ...studies.map((s) => `/work/${s.slug}`), "/experiments", "/about"];
  return paths.map((path) => ({ url: `${profile.siteUrl}${path}`, changeFrequency: "monthly" }));
}
```

`apps/web/src/app/robots.ts`:

```ts
import type { MetadataRoute } from "next";

import { profile } from "@/content/profile";

export default function robots(): MetadataRoute.Robots {
  return { rules: { userAgent: "*", allow: "/" }, sitemap: `${profile.siteUrl}/sitemap.xml` };
}
```

`apps/web/src/app/opengraph-image.tsx`:

```tsx
import { ImageResponse } from "next/og";

import { profile } from "@/content/profile";
import { palette } from "@/styles/palette";

export const alt = `${profile.name}, data scientist in Penang`;
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

const SWATCHES = [palette.mustard, palette.jade, palette.cobalt, palette.rose];

export default function OpengraphImage() {
  return new ImageResponse(
    (
      <div style={{ width: "100%", height: "100%", display: "flex", flexDirection: "column", justifyContent: "space-between", padding: 72, background: palette.peacock, color: palette.porcelain }}>
        <div style={{ display: "flex" }}>
          {SWATCHES.map((c) => <div key={c} style={{ width: 72, height: 72, background: c, border: `4px solid ${palette.porcelain}` }} />)}
        </div>
        <div style={{ display: "flex", flexDirection: "column" }}>
          <div style={{ fontSize: 96, fontWeight: 800, lineHeight: 1 }}>{profile.name}</div>
          <div style={{ fontSize: 36, marginTop: 24, color: palette.onPeacock, maxWidth: 980 }}>{profile.roleLine}</div>
        </div>
      </div>
    ),
    size,
  );
}
```

Delete `apps/web/public/sitemap.xml` and `apps/web/public/robots.txt`.

In `apps/web/src/app/layout.tsx`, replace the `metadata` export with:

```tsx
export const metadata: Metadata = {
  metadataBase: new URL("https://ai-observatory.vercel.app"),
  title: { default: "Subashanan Nair, data scientist in Penang", template: "%s | Subashanan Nair" },
  description: "Reproducible ML and LLM case studies on Malaysian public data, with sources, code and limits for every result.",
  openGraph: { type: "website", siteName: "Subashanan Nair" },
  twitter: { card: "summary_large_image" },
};
```

- [ ] **Step 4: Run every check**

Run: `npm test`, then `npm run lint`, `npm run typecheck` and `npm run build`.
Expected: everything passes. The build output lists `/sitemap.xml`, `/robots.txt` and `/opengraph-image`.

- [ ] **Step 5: Check overflow and text size at 360, 390 and 1440px (Review Focus 5)**

From `apps/web`, start the production server in the background: `npx next start --port 3001`. Then set up a scratch checker outside the repo:

```bash
mkdir -p /tmp/layout-check && cd /tmp/layout-check && npm init -y >/dev/null && npm i --no-save playwright@1.59
```

Save this as `/tmp/layout-check/check.mjs`:

```js
import { chromium } from "playwright";

const pages = ["/", "/work", "/work/penang-pulse", "/work/forecasting-lab", "/work/llm-eval-lab", "/experiments", "/about"];
const browser = await chromium.launch();
let failed = false;
for (const width of [360, 390, 1440]) {
  const page = await browser.newPage({ viewport: { width, height: 800 } });
  for (const path of pages) {
    await page.goto(`http://localhost:3001${path}`);
    const result = await page.evaluate(() => {
      const overflow = document.documentElement.scrollWidth - window.innerWidth;
      const tooSmall = [...document.querySelectorAll("body *")].filter((el) => {
        const hasText = [...el.childNodes].some((n) => n.nodeType === Node.TEXT_NODE && n.textContent.trim());
        if (!hasText || el.getBoundingClientRect().width === 0) return false;
        const size = parseFloat(getComputedStyle(el).fontSize);
        const svg = el.closest("svg");
        // SVG text scales with its viewBox, so measure it at its rendered size.
        const ratio = svg && svg.viewBox.baseVal.width ? svg.getBoundingClientRect().width / svg.viewBox.baseVal.width : 1;
        return size * ratio < 11.95;
      }).length;
      return { overflow, tooSmall };
    });
    if (result.overflow > 0 || result.tooSmall > 0) failed = true;
    console.log(`${width}px ${path}: overflow ${result.overflow}px, text under 12px: ${result.tooSmall}`);
  }
  await page.close();
}
await browser.close();
process.exit(failed ? 1 : 0);
```

Run: `node /tmp/layout-check/check.mjs`
Expected: every line reads `overflow 0px, text under 12px: 0`, and the exit code is 0. If any line fails, fix the CSS in `site.css` (or the SVG label size) and rerun.

- [ ] **Step 6: Accessibility and Lighthouse**

With the production server still running:
- Tab through `/work/penang-pulse` using only the keyboard. Check that the mosaic, district tiles (arrow keys), toggles and pager can be reached and operated, and that focus is visible on every band.
- Turn on reduced motion in the OS settings and check that tiles turn without animation.
- Disable JavaScript in DevTools and reload `/experiments`. Check that all 12 tools show and no filter buttons appear.
- Run `npx -y lighthouse http://localhost:3001/ --only-categories=performance,accessibility,best-practices,seo --chrome-flags="--headless" --quiet --output=json --output-path=/tmp/lh.json` and read the four scores. Expected: Performance 80+, Accessibility 95+, Best Practices 90+, SEO 95+.

- [ ] **Step 7: Screenshot every page against the prototype**

For each route, at 1440x900 and 390x844, run `npx -y playwright@1.59 screenshot --full-page --wait-for-timeout=1500 --viewport-size=W,H http://localhost:3001<path> .context/build-<name>-<W>.png`. Compare each screenshot with the matching page in `mockups/peranakan-tiles/`. The production build shows pending panels where the prototype shows charts. That difference is the honesty rule working as designed.

- [ ] **Step 8: Commit**

```bash
git add -A apps/web
git commit -m "feat: add sitemap, robots and Open Graph image for the redesign"
```
