import { describe, expect, it, vi } from "vitest";

vi.mock("next/navigation", () => ({
  notFound: () => {
    throw new Error("NEXT_NOT_FOUND");
  },
}));

import StudyRoute, { dynamicParams, generateStaticParams } from "./page";

describe("/work/[slug]", () => {
  it("prerenders exactly the four studies and nothing else", async () => {
    expect(await generateStaticParams()).toEqual([{ slug: "penang-pulse" }, { slug: "forecasting-lab" }, { slug: "llm-eval-lab" }, { slug: "penang-ai-assistant" }]);
    expect(dynamicParams).toBe(false);
  });

  it("returns not found for an unknown slug", async () => {
    await expect(StudyRoute({ params: Promise.resolve({ slug: "foo" }) })).rejects.toThrow("NEXT_NOT_FOUND");
  });
});
