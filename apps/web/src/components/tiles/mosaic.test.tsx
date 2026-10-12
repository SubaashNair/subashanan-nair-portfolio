import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { Mosaic } from "./mosaic";
import { mixedTile } from "./tile-geometry";

describe("Mosaic", () => {
  it("turns only the clicked tile by 90 degrees each time", () => {
    render(<Mosaic tiles={[mixedTile(0), mixedTile(1)]} label="Decorative tiles" />);
    const first = screen.getByRole("button", { name: "Turn tile 1" });
    fireEvent.click(first);
    fireEvent.click(first);
    expect(first).toHaveStyle({ transform: "rotate(180deg)" });
    expect(screen.getByRole("button", { name: "Turn tile 2" })).toHaveStyle({ transform: "rotate(0deg)" });
    expect(screen.getByRole("group", { name: "Decorative tiles" })).toBeInTheDocument();
  });
});
