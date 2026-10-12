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
