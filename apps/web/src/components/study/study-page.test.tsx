import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { findStudy } from "@/content/studies";
import { getStudyResults } from "@/lib/study-results";

import { StudyPage } from "./study-page";

const pulse = findStudy("penang-pulse")!;
const llm = findStudy("llm-eval-lab")!;

describe("StudyPage", () => {
  it("production mode with no results shows the plan and no numbers", () => {
    const { container } = render(<StudyPage study={llm} results={getStudyResults("llm-eval-lab", "production")} />);
    expect(screen.getByRole("heading", { level: 1, name: "LLM Eval Lab" })).toBeInTheDocument();
    expect(screen.getByText(llm.plannedAnswer)).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /the analysis is in progress/i })).toBeInTheDocument();
    expect(screen.queryAllByText("3 points")).toHaveLength(0);
    expect(screen.queryByText(/preview with illustrative data/i)).not.toBeInTheDocument();
    expect(screen.queryByText("a1c9e04")).not.toBeInTheDocument();
    expect(container.querySelectorAll(".num-tile")).toHaveLength(0);
    expect(screen.getAllByText("Not yet retrieved")).toHaveLength(llm.sources.length);
  });

  it("production mode shows published Penang Pulse results, the service table and no preview label", () => {
    const loaded = getStudyResults("penang-pulse", "production")!;
    const { container } = render(<StudyPage study={pulse} results={loaded} />);
    expect(screen.getByText(loaded.data.answer)).toBeInTheDocument();
    expect(container.querySelectorAll(".num-tile")).toHaveLength(3);
    expect(screen.getByRole("table", { name: /more than 3 km by road from the nearest service/i })).toBeInTheDocument();
    expect(screen.queryByText(/preview with illustrative data/i)).not.toBeInTheDocument();
    expect(screen.queryAllByText("Not yet retrieved")).toHaveLength(0);
  });

  it("puts the title inside the single main landmark", () => {
    const { container } = render(<StudyPage study={pulse} results={null} />);
    expect(container.querySelectorAll("main")).toHaveLength(1);
    expect(container.querySelector("#main")).toContainElement(screen.getByRole("heading", { level: 1, name: "Penang Pulse" }));
  });

  it("preview mode shows fixture numbers under a visible preview label", () => {
    render(<StudyPage study={llm} results={getStudyResults("llm-eval-lab", "development")} />);
    expect(screen.getAllByText("3 points").length).toBeGreaterThan(0);
    expect(screen.getAllByText(/preview with illustrative data/i).length).toBeGreaterThan(0);
  });

  it("shows the new assistant study's plan, pending evidence and no preview in development", () => {
    const assist = findStudy("penang-ai-assistant")!;
    const { container } = render(<StudyPage study={assist} results={getStudyResults("penang-ai-assistant", "development")} />);
    expect(screen.getByText(assist.plannedAnswer)).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /the analysis is in progress/i })).toBeInTheDocument();
    expect(container.querySelectorAll(".num-tile")).toHaveLength(0);
    expect(screen.queryByText(/preview with illustrative data/i)).not.toBeInTheDocument();
  });

  it("always shows the provenance chapters and wraps the pager", () => {
    render(<StudyPage study={pulse} results={null} />);
    for (const name of ["The answer", "The evidence", "How it was made", "Check it yourself"]) {
      expect(screen.getByRole("heading", { level: 2, name })).toBeInTheDocument();
    }
    expect(screen.getByRole("table")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /previous study penang ai assistant/i })).toHaveAttribute("href", "/work/penang-ai-assistant");
    expect(screen.getByRole("link", { name: /next study forecasting lab/i })).toHaveAttribute("href", "/work/forecasting-lab");
  });
});
