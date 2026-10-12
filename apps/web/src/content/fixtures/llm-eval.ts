import type { LlmEvalResults } from "../types";

// Illustrative only. Never shown in a production build.
export const llmEvalFixture: LlmEvalResults = {
  answer:
    "On Manglish sentiment, a fine-tuned 1B model lands within 3 points of a frontier model at about a fiftieth of the cost. On summaries, the frontier model still leads clearly.",
  keyNumbers: [
    { value: "3 points", label: "gap between the fine-tuned 1B and the frontier model on sentiment.", caveat: "The 95% intervals overlap, so the gap could be smaller." },
    { value: "1/50th", label: "the cost per 1k items for the fine-tuned 1B.", caveat: "List prices on the run date; prices change." },
    { value: "1,200", label: "hand-labelled items per task.", caveat: "Inter-annotator agreement was 0.81 on a 20% overlap." },
  ],
  run: { commit: "a1c9e04", manifest: "manifest.json", python: "3.12", lastRun: "2026-10-01" },
  retrieved: { "Manglish and BM sets": "2026-09-30", "Malaysian news headlines": "2026-09-15", Models: "2026-10-01" },
  tasks: [
    {
      id: "sentiment", label: "Manglish sentiment", metric: "Accuracy",
      rows: [
        { model: "Frontier model", role: "frontier", score: 87, low: 84, high: 90, costPer1k: 2.1, costLabel: "$2.10", latency: "900 ms" },
        { model: "Fine-tuned 1B", role: "ft", score: 84, low: 81, high: 87, costPer1k: 0.04, costLabel: "$0.04", latency: "38 ms" },
        { model: "Open 8B, zero-shot", role: "open", score: 79, low: 75, high: 83, costPer1k: 0.12, costLabel: "$0.12", latency: "210 ms" },
        { model: "TF-IDF + logistic", role: "base", score: 71, low: 67, high: 75, costPer1k: 0.007, costLabel: "<$0.01", latency: "1 ms" },
      ],
    },
    {
      id: "entities", label: "BM entity extraction", metric: "F1",
      rows: [
        { model: "Frontier model", role: "frontier", score: 83, low: 80, high: 86, costPer1k: 2.4, costLabel: "$2.40", latency: "1.1 s" },
        { model: "Fine-tuned 1B", role: "ft", score: 78, low: 74, high: 81, costPer1k: 0.05, costLabel: "$0.05", latency: "45 ms" },
        { model: "Open 8B, zero-shot", role: "open", score: 70, low: 66, high: 74, costPer1k: 0.14, costLabel: "$0.14", latency: "260 ms" },
        { model: "CRF baseline", role: "base", score: 62, low: 58, high: 66, costPer1k: 0.007, costLabel: "<$0.01", latency: "3 ms" },
      ],
    },
    {
      id: "summaries", label: "BM summaries", metric: "Faithfulness",
      rows: [
        { model: "Frontier model", role: "frontier", score: 82, low: 79, high: 85, costPer1k: 4.8, costLabel: "$4.80", latency: "2.4 s" },
        { model: "Open 8B, zero-shot", role: "open", score: 71, low: 67, high: 75, costPer1k: 0.3, costLabel: "$0.30", latency: "640 ms" },
        { model: "Fine-tuned 1B", role: "ft", score: 66, low: 62, high: 70, costPer1k: 0.09, costLabel: "$0.09", latency: "120 ms" },
        { model: "Extractive baseline", role: "base", score: 58, low: 54, high: 62, costPer1k: 0.007, costLabel: "<$0.01", latency: "5 ms" },
      ],
    },
  ],
  errorExamples: [
    { input: "Wah this nasi lemak damn power lah", expected: "positive", model: "Fine-tuned 1B", output: "positive", note: "Reads \"damn power\" as praise", correct: true },
    { input: "Service ok la but wait so long sampai tak larat", expected: "negative", model: "Open 8B", output: "neutral", note: "Misses \"tak larat\" (exhausted)", correct: false },
    { input: "Boleh tahan, not bad for the price", expected: "positive", model: "TF-IDF", output: "negative", note: "\"Tahan\" read as a complaint", correct: false },
  ],
};
