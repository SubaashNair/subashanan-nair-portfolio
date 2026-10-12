# AI Observatory — Design Research & Redesign Plan

> Research date: 2026-08-28. Sources: Awwwards portfolio / 3D / colorful / microinteraction collections, frontend-patterns skill, and the existing design spec.

## 1. Why the current design feels off

The current landing page is competent but reads as "serious sci-fi instrument panel" rather than "fun and creative". Specific issues:

- **Monochrome + two accents.** Near-black `#05070c` with cyan `#63ebc8` and violet `#ad8bff` is a safe, common "AI/space" palette. It does not differentiate the portfolio from hundreds of similar dark-mode AI sites.
- **Static, flat hero.** The "observatory" is drawn with CSS borders and radial gradients. It is decorative, not interactive. Nothing responds to the cursor, scroll, or selection.
- **Uniform typography.** One sans-serif for everything plus monospace labels. There is no display typeface, no editorial contrast, no personality in the letterforms.
- **No microinteractions.** Links change color on hover and that is it. There is no sense of play, no reward for exploration.
- **The "fun" is told, not shown.** Copy says "living intelligence" and "active studies", but the UI does not feel alive.

## 2. What award-winning fun/creative portfolios do (research findings)

Across Awwwards portfolio, 3D, colorful, and microinteraction collections, the recurring patterns are:

1. **A single strong display typeface.** Big, expressive, often variable or condensed (Druk, Clash Display, Bebas Neue, Anton, Archivo Black, Dela Gothic One, Bungee, Fredoka, Baloo 2). Paired with a quiet body face and a mono for metadata.
2. **A bold, limited color story.** 3–5 colors max, but chosen for contrast and warmth, not just "dark + neon". Many winning sites use a warm paper/cream base with one or two saturated accents, or a saturated duotone.
3. **Motion that responds to the user.** Cursor-following elements, scroll-driven reveals, hover states that morph, magnetic buttons, marquees. Motion is the personality.
4. **Microinteractions everywhere.** Small, delightful feedback: a dot that pulses, a card that tilts on hover, a number that counts up, a link that underlines with a draw animation.
5. **Storytelling through scroll.** Sections reveal progressively; the "journey" (Observe → Discover → Dive → Understand) is felt, not just labeled.
6. **Playful, tactile details.** Grain/noise textures, hand-drawn or blob shapes, rounded corners, sticker-like badges, emoji or icon accents used sparingly.

## 3. Three design directions

### Direction A — "Cosmic Playground" (recommended, FINALIZED)

Keep the observatory concept but make it warm, tactile, and playful.

- **Base:** deep indigo `#1a1033` → `#241a45` gradient (space, but warmer than pure black).
- **Accents:** soft dusty rose `#e8a0a0` (both accents unified to a single muted rose) and a warm cream `#f7f3e8` for text. The original coral `#ff6b6b` and mint `#4ade80` were softened and merged into one subtle rose tone for a calmer, more understated look.
- **Type:** `Bricolage Grotesque` (display, has personality) + `Inter` (body) + `Space Mono` (metadata). All free on Google Fonts.
- **Motion:** cursor-following starfield, magnetic primary button, cards that tilt on hover, scroll-driven section reveals, a marquee "ticker" of study keywords.
- **Texture:** subtle grain overlay, blob-shaped study cards with rounded corners, sticker-style badges.
- **Nav:** header links (Work / Experiments / About) vertically centered with the GitHub pill.

### Direction B — "Editorial Lab Notebook"

Lean into the "reproducible science" angle with a warm paper aesthetic.

- **Base:** warm paper `#f6f1e7`, ink `#1c1c1c`.
- **Accents:** one saturated accent (e.g. `#e63946` red) + `#2a9d8f` teal.
- **Type:** `Fraunces` (serif display) + `Inter` + `IBM Plex Mono`.
- **Motion:** underline-draw links, stamp-style reveal animations, ruled-paper grid background.
- **Vibe:** credible, editorial, "scientist's notebook". Less "fun", more "charming".

### Direction C — "Neon Arcade"

Maximum fun, high energy.

- **Base:** near-black `#0a0a0a`.
- **Accents:** electric `#ffd60a` yellow, `#ff2d55` pink, `#00e5ff` cyan.
- **Type:** `Bungee` or `Dela Gothic One` (display) + `Space Grotesk` + `JetBrains Mono`.
- **Motion:** glitch reveals, scanline overlay, marquee tickers, hover glow.
- **Vibe:** bold and loud; risks feeling dated and can hurt readability/accessibility.

**Recommendation:** Direction A. It keeps the existing "observatory" narrative and Three.js investment, but injects warmth, play, and interactivity without sacrificing the accessibility and reduced-motion guarantees already in the codebase.

## 4. Concrete changes mapped to the current code

| Area | Current | Proposed |
|------|---------|----------|
| Design tokens (`globals.css:1-12`) | `--ink #05070c`, `--signal #63ebc8`, `--neural #ad8bff` | Replace with warm indigo base + soft dusty rose `#e8a0a0` + cream; add `--grain`, `--radius` tokens |
| Typography (`globals.css:22`) | single `Inter` stack | Add `Bricolage Grotesque` display + `Space Mono`; define `--font-display`, `--font-body`, `--font-mono` |
| Hero (`components/home/hero.tsx`) | static CSS globe | Add cursor-following starfield + magnetic CTA; keep `aria-hidden` decorative layer |
| Study cards (`components/home/study-card.tsx`) | flat cards | Tilt-on-hover, blob shapes, sticker badges, draw-underline links |
| Signals section | static grid | Scroll-reveal + keyword marquee ticker |
| Header/footer | static | Sticky header with blur, animated brand mark, vertically centered nav links |
| Motion | none | Framer Motion (or CSS-only) with `prefers-reduced-motion` fallback preserved |

## 5. Phased plan

### Phase 1 — Foundation (tokens + type)
- [ ] Add Google Fonts (`Bricolage Grotesque`, `Space Mono`) via `next/font`.
- [ ] Rewrite `:root` tokens in `globals.css` to the new palette and font variables.
- [ ] Add a grain/noise overlay and global radius tokens.
- [ ] Verify `npm run lint`, `typecheck`, `test`, `build` still pass.

### Phase 2 — Playful motion (no new heavy deps)
- [ ] Add a lightweight cursor-following starfield to the hero (CSS/JS, `aria-hidden`).
- [ ] Magnetic primary button and draw-underline link hover states.
- [ ] Card tilt-on-hover with `prefers-reduced-motion` fallback.
- [ ] Add a keyword marquee ticker in the signals section.

### Phase 3 — Component polish
- [ ] Restyle study cards with blob shapes, rounded corners, sticker badges.
- [ ] Animated brand mark and sticky blurred header.
- [ ] Scroll-driven section reveals (IntersectionObserver or Framer Motion).

### Phase 4 — Verify & ship
- [ ] Run full checks (lint, typecheck, test, build).
- [ ] Manual pass: keyboard nav, reduced-motion, no-JS, mobile.
- [ ] Lighthouse against production build (targets from spec: Perf 80+, A11y 95+, BP 90+, SEO 95+).

## 6. Guardrails (must preserve)

- Semantic HTML, skip link, `aria-labelledby`, and `aria-hidden` decorative layers stay.
- `prefers-reduced-motion` must disable all new animation (already scaffolded in `globals.css:147-150`).
- Content must remain fully readable without WebGL or JavaScript.
- No new heavy dependencies unless justified; prefer CSS and small utilities over a full animation library.
