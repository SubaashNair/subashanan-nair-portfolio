import { describe, expect, it } from "vitest";

import { contrastRatio } from "@/styles/contrast";
import { palette } from "@/styles/palette";

import { MODEL_STYLE } from "./model-style";

const styles = Object.entries(MODEL_STYLE);

describe("MODEL_STYLE", () => {
  it("styles exactly the five models", () => {
    expect(Object.keys(MODEL_STYLE)).toEqual(["persistence", "seasonal", "gb", "mlp", "chronos"]);
  });

  it("gives every model its own colour", () => {
    expect(new Set(styles.map(([, s]) => s.colour)).size).toBe(5);
  });

  it.each(styles)("%s is at least 3:1 on porcelain and sky", (_id, style) => {
    expect(contrastRatio(style.colour, palette.porcelain)).toBeGreaterThanOrEqual(3);
    expect(contrastRatio(style.colour, palette.sky)).toBeGreaterThanOrEqual(3);
  });

  it("dashes only the persistence baseline", () => {
    expect(styles.filter(([, s]) => s.dash).map(([id]) => id)).toEqual(["persistence"]);
  });
});
