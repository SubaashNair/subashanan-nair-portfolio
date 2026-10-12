import { fireEvent, render, screen, within } from "@testing-library/react";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import { llmEvalFixture } from "@/content/fixtures/llm-eval";

import { LlmEvalFigure } from "./llm-eval-figure";

describe("LlmEvalFigure", () => {
  it("server-renders the default task's leaderboard and scatter", () => {
    const html = renderToStaticMarkup(<LlmEvalFigure data={llmEvalFixture} />);
    expect(html).toContain("Accuracy, with 95% interval");
    expect((html.match(/class="score-dot"/g) ?? []).length).toBe(4);
  });

  it("changes the table and the chart together when the task changes", () => {
    render(<LlmEvalFigure data={llmEvalFixture} />);
    fireEvent.click(screen.getByRole("tab", { name: "BM summaries" }));
    const table = screen.getByRole("table");
    expect(within(table).getByRole("columnheader", { name: /faithfulness/i })).toBeInTheDocument();
    expect(within(table).getByText("Extractive baseline")).toBeInTheDocument();
    expect(screen.getByRole("img", { name: /faithfulness against cost/i })).toBeInTheDocument();
  });

  it("labels every point on the scatter by name", () => {
    render(<LlmEvalFigure data={llmEvalFixture} />);
    const chart = screen.getByRole("img", { name: /accuracy against cost/i });
    for (const row of llmEvalFixture.tasks[0].rows) expect(chart).toHaveTextContent(row.model);
  });

  it("shows each error example with its verdict", () => {
    render(<LlmEvalFigure data={llmEvalFixture} />);
    expect(screen.getAllByText("Missed")).toHaveLength(2);
    expect(screen.getAllByText("Correct")).toHaveLength(1);
  });
});
