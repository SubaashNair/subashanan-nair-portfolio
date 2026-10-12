import { fireEvent, render, screen } from "@testing-library/react";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import { forecastFixture } from "@/content/fixtures/forecasting";

import { ForecastFigure } from "./forecast-figure";

describe("ForecastFigure", () => {
  it("server-renders both charts with every model line", () => {
    const html = renderToStaticMarkup(<ForecastFigure data={forecastFixture} />);
    expect(html).toContain("Traffic flow for Sensor 12");
    expect((html.match(/class="model-line"/g) ?? []).length).toBe(8); // 4 forecast lines and 4 horizon lines
  });

  it("switches sensor and updates the window error list", () => {
    render(<ForecastFigure data={forecastFixture} />);
    const before = screen.getByRole("list", { name: /mean absolute error in this window/i }).textContent;
    fireEvent.click(screen.getByRole("tab", { name: "Sensor 47" }));
    expect(screen.getByRole("img", { name: /sensor 47/i })).toBeInTheDocument();
    expect(screen.getByRole("list", { name: /mean absolute error in this window/i }).textContent).not.toBe(before);
  });

  it("hides a model from both charts", () => {
    const { container } = render(<ForecastFigure data={forecastFixture} />);
    fireEvent.click(screen.getByRole("button", { name: "Chronos, zero-shot" }));
    expect(container.querySelectorAll(".model-line")).toHaveLength(6);
  });

  it("bolds the lowest error in each horizon column", () => {
    render(<ForecastFigure data={forecastFixture} />);
    const bold = screen.getByRole("table").querySelectorAll("b");
    expect([...bold].map((b) => b.textContent)).toEqual(["6.1", "7.9", "10.1", "11.6", "13.4"]);
  });
});
