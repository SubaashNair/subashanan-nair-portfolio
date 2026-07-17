import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import Home from "./page";

describe("AI Observatory home", () => {
  it("introduces the observatory and both launch studies", () => {
    render(<Home />);

    expect(screen.getByRole("heading", { level: 1, name: /living intelligence/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /enter the observatory/i })).toHaveAttribute("href", "#signals");
    expect(screen.getByRole("link", { name: /explore penang pulse/i })).toHaveAttribute("href", "/work/penang-pulse");
    expect(screen.getByRole("link", { name: /enter forecasting lab/i })).toHaveAttribute("href", "/work/forecasting-lab");
    expect(screen.getByText(/NASA signal/i)).toHaveTextContent(/coming next/i);
  });
});

