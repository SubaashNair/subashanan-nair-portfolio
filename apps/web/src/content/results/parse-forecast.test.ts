import { describe, expect, it } from "vitest";

import { forecastFixture } from "../fixtures/forecasting";
import { parseForecastResults } from "./parse-forecast";

// The fixture, as plain JSON, is a valid file. Each malformed case changes one thing in a copy.
const valid = JSON.parse(JSON.stringify(forecastFixture));
const sensor = valid.sensors[0];
const withSensor = (changes: object) => ({ ...valid, sensors: [{ ...sensor, ...changes }, ...valid.sensors.slice(1)] });

describe("parseForecastResults", () => {
  it("accepts a valid file and returns its data", () => {
    const parsed = parseForecastResults(valid);
    expect(parsed.models.map((m) => m.id)).toEqual(["persistence", "seasonal", "gb", "mlp", "chronos"]);
    expect(parsed.sensors[0].actual).toEqual(sensor.actual);
  });

  it.each([
    ["not an object", [], /file must be an object/],
    ["two key numbers", { ...valid, keyNumbers: valid.keyNumbers.slice(0, 2) }, /keyNumbers must have 3 items/],
    ["an empty caveat", { ...valid, keyNumbers: [{ ...valid.keyNumbers[0], caveat: "" }, ...valid.keyNumbers.slice(1)] }, /keyNumbers\[0\]\.caveat/],
    ["a run date that is not ISO", { ...valid, run: { ...valid.run, lastRun: "13 Oct 2026" } }, /run\.lastRun/],
    ["the old four models", { ...valid, models: valid.models.slice(1) }, /models must list each of/],
    ["a misspelt model id", { ...valid, models: [{ ...valid.models[0], id: "naive" }, ...valid.models.slice(1)] }, /models must list each of/],
    ["an MAE row of the wrong length", { ...valid, models: [{ ...valid.models[0], mae: [1, 2] }, ...valid.models.slice(1)] }, /models\[0\]\.mae must have 5 items/],
    ["a forecast that breaks the chart contract", withSensor({ forecasts: { ...sensor.forecasts, gb: sensor.forecasts.gb.slice(1) } }), /sensors\[0\]\.forecasts\.gb must have 9 items/],
    ["a missing window error", withSensor({ windowMae: { ...sensor.windowMae, chronos: undefined } }), /windowMae\.chronos/],
    ["a number stored as text", withSensor({ actual: ["12", ...sensor.actual.slice(1)] }), /actual\[0\] must be a finite number/],
    ["an origin past midnight", withSensor({ originMinutes: 1440 }), /originMinutes/],
    ["no sensors", { ...valid, sensors: [] }, /sensors must have at least one sensor/],
  ])("rejects %s", (_name, input, message) => {
    expect(() => parseForecastResults(input)).toThrow(message);
  });
});
