import { fireEvent, render, screen, within } from "@testing-library/react";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import { llmEvalFixture } from "@/content/fixtures/llm-eval";

import { labelOffsets } from "./calls-score-chart";
import { LlmEvalFigure } from "./llm-eval-figure";

describe("LlmEvalFigure", () => {
  it("server-renders the first view's leaderboard and scatter", () => {
    const html = renderToStaticMarkup(<LlmEvalFigure data={llmEvalFixture} />);
    expect(html).toContain("% with the latest figure, with 95% interval");
    expect(html).toContain("Tool calls per answer");
    expect((html.match(/class="score-dot"/g) ?? []).length).toBe(3);
  });

  it("changes the table and the chart together when the view changes", () => {
    render(<LlmEvalFigure data={llmEvalFixture} />);
    fireEvent.click(screen.getByRole("tab", { name: "All series, from memory" }));
    const table = screen.getByRole("table");
    expect(within(table).getAllByRole("row")).toHaveLength(3); // the header and two cloud models: no baseline from memory
    expect(within(table).queryByText("Open data only")).not.toBeInTheDocument();
    expect(screen.getByRole("img", { name: /against tool calls per answer/i })).toBeInTheDocument();
  });

  it("labels every point on the scatter by name and names both roles in the legend", () => {
    render(<LlmEvalFigure data={llmEvalFixture} />);
    const chart = screen.getByRole("img", { name: /against tool calls per answer/i });
    for (const row of llmEvalFixture.tasks[0].rows) expect(chart).toHaveTextContent(row.model);
    expect(screen.getByText("Cloud model")).toBeInTheDocument();
    expect(screen.getByText("Open data baseline")).toBeInTheDocument();
  });

  it("shows each error example as missed", () => {
    render(<LlmEvalFigure data={llmEvalFixture} />);
    expect(screen.getAllByText("Missed")).toHaveLength(3);
    expect(screen.queryByText("Correct")).not.toBeInTheDocument();
  });
});

describe("labelOffsets", () => {
  it("keeps labels that are far apart where they are", () => {
    expect(labelOffsets([100, 40, 200])).toEqual([100, 40, 200]);
  });

  it("pushes a label down when two points share a score", () => {
    expect(labelOffsets([120, 120, 50])).toEqual([120, 136, 50]);
  });
});
