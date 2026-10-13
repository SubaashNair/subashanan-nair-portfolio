import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import About from "./page";

describe("About", () => {
  it("has a contact section with email, LinkedIn, CV and GitHub", () => {
    const { container } = render(<About />);
    expect(container.querySelector("#contact")).not.toBeNull();
    expect(container.querySelector("#main")).toContainElement(screen.getByRole("heading", { level: 1, name: "About" }));
    expect(screen.getByRole("link", { name: "Email me" })).toHaveAttribute("href", "mailto:subaashnair12@gmail.com");
    expect(screen.getByRole("link", { name: "LinkedIn" })).toHaveAttribute("href", "https://www.linkedin.com/in/subashanan-nair/");
    expect(screen.getByRole("link", { name: "Download CV" })).toHaveAttribute("href", "/subashanan-nair-cv.pdf");
    expect(screen.getByRole("link", { name: "Find me on GitHub" })).toHaveAttribute("href", "https://github.com/SubaashNair");
    expect(screen.getByRole("heading", { level: 2, name: "Toolkit" })).toBeInTheDocument();
  });
});
