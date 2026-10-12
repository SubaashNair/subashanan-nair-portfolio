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
