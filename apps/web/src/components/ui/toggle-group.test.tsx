import { fireEvent, render, screen } from "@testing-library/react";
import { useState } from "react";
import { describe, expect, it } from "vitest";

import { ToggleGroup } from "./toggle-group";

const items = [{ id: "x", label: "Clinics" }, { id: "y", label: "Schools" }];

function Harness({ mode }: { mode: "multi" | "single" }) {
  const [pressed, setPressed] = useState<ReadonlySet<string>>(new Set(mode === "multi" ? ["x", "y"] : ["x"]));
  return <ToggleGroup label="Show" items={items} pressed={pressed} onChange={setPressed} mode={mode} />;
}

describe("ToggleGroup", () => {
  it("toggles each button independently in multi mode", () => {
    render(<Harness mode="multi" />);
    fireEvent.click(screen.getByRole("button", { name: "Clinics" }));
    expect(screen.getByRole("button", { name: "Clinics" })).toHaveAttribute("aria-pressed", "false");
    expect(screen.getByRole("button", { name: "Schools" })).toHaveAttribute("aria-pressed", "true");
    expect(screen.getByRole("group", { name: "Show" })).toBeInTheDocument();
  });

  it("keeps exactly one pressed in single mode", () => {
    render(<Harness mode="single" />);
    fireEvent.click(screen.getByRole("button", { name: "Schools" }));
    expect(screen.getByRole("button", { name: "Clinics" })).toHaveAttribute("aria-pressed", "false");
    expect(screen.getByRole("button", { name: "Schools" })).toHaveAttribute("aria-pressed", "true");
  });
});
