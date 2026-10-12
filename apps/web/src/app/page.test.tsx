import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import Home from "./page";

describe("Home", () => {
  it("introduces Subashanan and links the main journeys", () => {
    render(<Home />);
    expect(screen.getByRole("heading", { level: 1, name: "Subashanan Nair" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Read the case studies" })).toHaveAttribute("href", "/work");
    expect(screen.getByRole("link", { name: "Get in touch" })).toHaveAttribute("href", "/about#contact");
    expect(screen.getByRole("link", { name: "Penang Pulse" })).toHaveAttribute("href", "/work/penang-pulse");
    expect(screen.getByRole("link", { name: "See all tools and experiments" })).toHaveAttribute("href", "/experiments");
    expect(screen.queryByText(/NASA/)).not.toBeInTheDocument();
  });

  it("puts the title inside the main landmark and links only public tools", () => {
    const { container } = render(<Home />);
    expect(container.querySelectorAll("main")).toHaveLength(1);
    expect(container.querySelector("#main")).toContainElement(screen.getByRole("heading", { level: 1 }));
    expect(screen.queryByText("matomari")).not.toBeInTheDocument();
    for (const item of container.querySelectorAll("li.tool")) expect(item.querySelector("a")).not.toBeNull();
  });

  it("shows four tools", () => {
    const { container } = render(<Home />);
    expect(container.querySelectorAll("li.tool")).toHaveLength(4);
  });
});
