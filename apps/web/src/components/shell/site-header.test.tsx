import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { SiteHeader } from "./site-header";

describe("SiteHeader", () => {
  it("exposes the observatory brand and primary destinations", () => {
    render(<SiteHeader />);

    expect(screen.getByRole("link", { name: /ai observatory/i })).toHaveAttribute("href", "/");
    expect(screen.getByRole("link", { name: "Work" })).toHaveAttribute("href", "/work");
    expect(screen.getByRole("link", { name: "Experiments" })).toHaveAttribute("href", "/experiments");
    expect(screen.getByRole("link", { name: "About" })).toHaveAttribute("href", "/about");
    expect(screen.getByRole("link", { name: /github/i })).toHaveAttribute("href", "https://github.com/SubaashNair");
  });
});

