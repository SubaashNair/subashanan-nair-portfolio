import { fireEvent, render, screen } from "@testing-library/react";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import { penangFixture } from "@/content/fixtures/penang";

import { PenangFigure } from "./penang-figure";

describe("PenangFigure", () => {
  it("server-renders the map, points and the default district without JavaScript", () => {
    const html = renderToStaticMarkup(<PenangFigure data={penangFixture} />);
    expect(html).toContain("Public services across Penang");
    expect((html.match(/data-cat="/g) ?? []).length).toBe(penangFixture.points.length);
    expect(html).toContain("Seberang Perai Selatan");
  });

  it("selects a district and updates the panel and the map", () => {
    const { container } = render(<PenangFigure data={penangFixture} />);
    fireEvent.click(screen.getByRole("tab", { name: /timur laut/i }));
    expect(screen.getByRole("tabpanel")).toHaveTextContent("Timur Laut");
    expect(screen.getByRole("tabpanel")).toHaveTextContent("72%");
    expect(container.querySelector('.district.on[data-district="tl"]')).not.toBeNull();
  });

  it("hides a category of points", () => {
    const { container } = render(<PenangFigure data={penangFixture} />);
    fireEvent.click(screen.getByRole("button", { name: "Schools" }));
    const schools = container.querySelectorAll('.pt[data-cat="school"]');
    expect(schools.length).toBeGreaterThan(0);
    schools.forEach((p) => expect(p.parentElement?.getAttribute("class")).toBe("off"));
  });
});
