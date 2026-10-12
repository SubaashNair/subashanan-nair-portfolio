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
