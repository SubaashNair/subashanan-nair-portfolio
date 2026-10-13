import { fireEvent, render, screen } from "@testing-library/react";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import { forecastFixture } from "@/content/fixtures/forecasting";
import type { ForecastModelId } from "@/content/types";

import { ForecastFigure } from "./forecast-figure";
import { HorizonChart } from "./horizon-chart";

describe("ForecastFigure", () => {
  it("server-renders both charts with every model line", () => {
    const html = renderToStaticMarkup(<ForecastFigure data={forecastFixture} />);
    expect(html).toContain("Traffic flow for Sensor 12");
    expect((html.match(/class="model-line"/g) ?? []).length).toBe(10); // 5 forecast lines and 5 horizon lines
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
    expect(container.querySelectorAll(".model-line")).toHaveLength(8);
  });

  it("bolds the lowest error in each horizon column", () => {
    render(<ForecastFigure data={forecastFixture} />);
    const bold = screen.getByRole("table").querySelectorAll("b");
    expect([...bold].map((b) => b.textContent)).toEqual(["2.4", "3.4", "6.4", "4.9", "5.8"]); // row order: gb, mlp, chronos
  });

  it("labels the time axis every hour for 15 minute steps, across midnight", () => {
    const sensor = { ...forecastFixture.sensors[0], originMinutes: 60 };
    const html = renderToStaticMarkup(<ForecastFigure data={{ ...forecastFixture, sensors: [sensor] }} />);
    expect(html).toContain(">16:00<");
    expect(html).toContain(">00:00<");
    expect(html).toContain(">03:00<");
  });

  it("starts the flow axis at zero for a quiet sensor", () => {
    const s = forecastFixture.sensors[0];
    const quiet = (values: readonly number[]): number[] => values.map((v) => v / 10);
    const forecasts = Object.fromEntries(Object.entries(s.forecasts).map(([id, values]) => [id, quiet(values)])) as Record<ForecastModelId, number[]>;
    const html = renderToStaticMarkup(<ForecastFigure data={{ ...forecastFixture, sensors: [{ ...s, actual: quiet(s.actual), forecasts }] }} />);
    expect(html).not.toContain(">-25<");
    expect(html).toContain('text-anchor="end">0<');
  });

  it("scales the error axis to the largest error", () => {
    const models = [{ id: "gb" as const, name: "Gradient boosting", mae: [12, 18, 24, 31, 38] }];
    const html = renderToStaticMarkup(<HorizonChart horizons={forecastFixture.horizons} models={models} visible={new Set(["gb"])} />);
    expect([...html.matchAll(/text-anchor="end">([\d.]+)</g)].map((m) => m[1])).toEqual(["0", "20", "40"]);
  });
});
