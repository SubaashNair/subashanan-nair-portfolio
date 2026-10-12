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
