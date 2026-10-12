import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

vi.mock("next/navigation", () => ({ usePathname: () => "/work/penang-pulse" }));

import { SiteHeader } from "./site-header";

describe("SiteHeader", () => {
  it("names the brand and links every destination", () => {
    render(<SiteHeader />);
    expect(screen.getByRole("link", { name: "Subashanan Nair" })).toHaveAttribute("href", "/");
    expect(screen.getByRole("link", { name: "Experiments" })).toHaveAttribute("href", "/experiments");
    expect(screen.getByRole("link", { name: "About" })).toHaveAttribute("href", "/about");
    expect(screen.getByRole("link", { name: "GitHub" })).toHaveAttribute("href", "https://github.com/SubaashNair");
  });

  it("marks Work as current on a case study page", () => {
    render(<SiteHeader />);
    expect(screen.getByRole("link", { name: "Work" })).toHaveAttribute("aria-current", "page");
    expect(screen.getByRole("link", { name: "About" })).not.toHaveAttribute("aria-current");
  });
});
