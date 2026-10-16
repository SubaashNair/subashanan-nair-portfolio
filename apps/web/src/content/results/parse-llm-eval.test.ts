import { describe, expect, it } from "vitest";

import { llmEvalFixture } from "../fixtures/llm-eval";
import { parseLlmEvalResults } from "./parse-llm-eval";

// The fixture, as plain JSON, is a valid file. Each malformed case changes one thing in a copy.
const valid = JSON.parse(JSON.stringify(llmEvalFixture));
const [tools, stale, memory] = valid.tasks;
const withRow = (task: number, changes: object) => ({
  ...valid,
  tasks: valid.tasks.map((t: { rows: object[] }, i: number) => (i === task ? { ...t, rows: [{ ...t.rows[0], ...changes }, ...t.rows.slice(1)] } : t)),
});
const withTask = (task: number, changes: object) => ({ ...valid, tasks: valid.tasks.map((t: object, i: number) => (i === task ? { ...t, ...changes } : t)) });

describe("parseLlmEvalResults", () => {
  it("accepts a valid file and returns its data", () => {
    const parsed = parseLlmEvalResults(valid);
    expect(parsed.tasks.map((t) => t.id)).toEqual(["all-tools", "stale-tools", "all-memory"]);
    expect(parsed.tasks[2].rows.every((r) => r.role === "cloud")).toBe(true);
    expect(parsed.errorExamples).toHaveLength(3);
  });

  it.each([
    ["not an object", null, /file must be an object/],
    ["two key numbers", { ...valid, keyNumbers: valid.keyNumbers.slice(1) }, /keyNumbers must have 3 items/],
    ["two views", { ...valid, tasks: [tools, stale] }, /tasks must have 3 items/],
    ["views out of order", { ...valid, tasks: [stale, tools, memory] }, /tasks\[0\]\.id must be all-tools/],
    ["an old role", withRow(0, { role: "frontier" }), /tasks\[0\]\.rows\[0\]\.role must be one of cloud, baseline/],
    ["a score outside its interval", withRow(0, { score: 90 }), /tasks\[0\]\.rows\[0\]\.score must lie inside its interval/],
    ["a fractional score", withRow(0, { score: 64.5 }), /tasks\[0\]\.rows\[0\]\.score must be a whole number/],
    ["a share over 100", withRow(0, { high: 101 }), /tasks\[0\]\.rows\[0\]\.high must be a whole number from 0 to 100/],
    ["the old cost field instead of tool calls", withRow(0, { callsPerAnswer: undefined, costPer1k: 2.1 }), /callsPerAnswer must be a finite number/],
    ["more tool calls than the cap", withRow(0, { callsPerAnswer: 7 }), /callsPerAnswer must be from 0 to 6/],
    ["a missing latency", withRow(1, { latency: "" }), /tasks\[1\]\.rows\[0\]\.latency/],
    ["a baseline from memory", withTask(2, { rows: [...memory.rows, tools.rows[2]] }), /tasks\[2\]\.rows must have 0 baseline rows, found 1/],
    ["no baseline with tools", withTask(1, { rows: stale.rows.slice(0, 2) }), /tasks\[1\]\.rows must have 1 baseline row, found 0/],
    ["only the baseline", withTask(0, { rows: [tools.rows[2]] }), /tasks\[0\]\.rows must have at least one cloud model/],
    ["a model listed twice", withTask(2, { rows: [memory.rows[0], memory.rows[0]] }), /must name each model once/],
    ["seven error examples", { ...valid, errorExamples: Array(7).fill(valid.errorExamples[0]) }, /errorExamples must have at most 6 items/],
    ["an error example without a verdict", { ...valid, errorExamples: [{ ...valid.errorExamples[0], correct: "no" }] }, /errorExamples\[0\]\.correct must be true or false/],
  ])("rejects %s", (_name, input, message) => {
    expect(() => parseLlmEvalResults(input)).toThrow(message);
  });
});
