import { describe, expect, it } from "vitest";

import sitemap from "./sitemap";

describe("sitemap", () => {
  it("lists every page", () => {
    expect(sitemap().map((e) => e.url)).toEqual([
      "https://subashanan-nair.vercel.app/",
      "https://subashanan-nair.vercel.app/work",
      "https://subashanan-nair.vercel.app/work/penang-pulse",
      "https://subashanan-nair.vercel.app/work/forecasting-lab",
      "https://subashanan-nair.vercel.app/work/llm-eval-lab",
      "https://subashanan-nair.vercel.app/experiments",
      "https://subashanan-nair.vercel.app/about",
    ]);
  });
});
