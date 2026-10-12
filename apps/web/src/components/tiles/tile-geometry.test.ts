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
