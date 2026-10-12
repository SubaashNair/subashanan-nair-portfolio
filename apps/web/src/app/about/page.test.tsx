import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import About from "./page";

describe("About", () => {
  it("has a contact section and no placeholder buttons", () => {
    const { container } = render(<About />);
    expect(container.querySelector("#contact")).not.toBeNull();
    expect(container.querySelector("#main")).toContainElement(screen.getByRole("heading", { level: 1, name: "About" }));
    expect(screen.queryByRole("link", { name: "Email me" })).not.toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Find me on GitHub" })).toHaveAttribute("href", "https://github.com/SubaashNair");
    expect(screen.getByRole("heading", { level: 2, name: "Toolkit" })).toBeInTheDocument();
  });
});
