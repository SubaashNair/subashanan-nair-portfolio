import { fireEvent, render, screen } from "@testing-library/react";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import { ExperimentList } from "./experiment-list";

describe("ExperimentList", () => {
  it("without JavaScript shows all 13 tools and no filter buttons", () => {
    const html = renderToStaticMarkup(<ExperimentList />);
    expect((html.match(/class="tool"/g) ?? []).length).toBe(13);
    expect(html).not.toContain("aria-pressed");
  });

  it("filters by category and reports the count", () => {
    render(<ExperimentList />);
    fireEvent.click(screen.getByRole("button", { name: "Libraries" }));
    expect(screen.getByRole("button", { name: "Libraries" })).toHaveAttribute("aria-pressed", "true");
    expect(screen.getAllByRole("listitem")).toHaveLength(5);
    expect(screen.getByText("Showing 5 of 13 tools")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "All" }));
    expect(screen.getAllByRole("listitem")).toHaveLength(13);
  });
});
