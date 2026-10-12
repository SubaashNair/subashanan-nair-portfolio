import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { experiments } from "@/content/experiments";

import { ToolItem } from "./tool-item";

const find = (name: string) => experiments.find((e) => e.name === name)!;

describe("ToolItem", () => {
  it("links public repositories", () => {
    render(<ToolItem experiment={find("ml-review")} />);
    expect(screen.getByRole("link", { name: "ml-review" })).toHaveAttribute("href", "https://github.com/SubaashNair/ml-review");
  });

  it("shows private repositories as plain text, labelled private", () => {
    const { container } = render(<ToolItem experiment={find("matomari")} />);
    expect(screen.getByRole("heading", { name: "matomari" })).toBeInTheDocument();
    expect(screen.queryByRole("link")).not.toBeInTheDocument();
    expect(container.querySelector(".lang")).toHaveTextContent("macOS, agents and MCP, private repository");
  });
});
