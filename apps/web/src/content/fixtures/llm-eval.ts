import type { LlmEvalResults } from "../types";

// Illustrative only. Never shown in a production build.
export const llmEvalFixture: LlmEvalResults = {
  answer:
    "On out-of-date series, gpt-oss 120B gave the latest official figure for 62% of questions with tools, against 0% for the open data alone.",
  keyNumbers: [
    { value: "62%", label: "of questions on out-of-date series answered with the latest figure by gpt-oss 120B, with tools.", caveat: "95% interval 41 to 80%, from a bootstrap over statistics." },
    { value: "47 points", label: "higher latest-figure share for gpt-oss 120B with tools than from memory, across all series.", caveat: "From 18% from memory to 65% with tools." },
    { value: "30", label: "statistics, asked 4 ways each: 120 questions verified against the official release.", caveat: "Snapshot of open data and releases taken on 1 October 2026; results describe that day." },
  ],
  run: { commit: "a1c9e04", manifest: "manifest.json", python: "3.12", lastRun: "2026-10-01" },
  retrieved: {
    "data.gov.my datasets": "2026-10-01", "DOSM releases": "2026-10-01", "Bank Negara Malaysia": "2026-10-01",
    MYNIC: "2026-10-01", "Ollama Cloud": "2026-10-02", "Question set": "2026-10-01",
  },
  tasks: [
    {
      id: "all-tools", label: "All series, with tools", metric: "% with the latest figure",
      rows: [
        { model: "gpt-oss 120B", role: "cloud", score: 65, low: 52, high: 77, callsPerAnswer: 3.4, callsLabel: "3.4", latency: "9.8 s" },
        { model: "DeepSeek V4.1 Flash", role: "cloud", score: 58, low: 45, high: 70, callsPerAnswer: 4.1, callsLabel: "4.1", latency: "12.5 s" },
        { model: "Open data only", role: "baseline", score: 52, low: 38, high: 66, callsPerAnswer: 0, callsLabel: "0", latency: "under 0.1 s" },
      ],
    },
    {
      id: "stale-tools", label: "Out-of-date series, with tools", metric: "% with the latest figure",
      rows: [
        { model: "gpt-oss 120B", role: "cloud", score: 62, low: 41, high: 80, callsPerAnswer: 4.2, callsLabel: "4.2", latency: "11.2 s" },
        { model: "DeepSeek V4.1 Flash", role: "cloud", score: 48, low: 29, high: 68, callsPerAnswer: 4.8, callsLabel: "4.8", latency: "14.0 s" },
        { model: "Open data only", role: "baseline", score: 0, low: 0, high: 0, callsPerAnswer: 0, callsLabel: "0", latency: "under 0.1 s" },
      ],
    },
    {
      id: "all-memory", label: "All series, from memory", metric: "% with the latest figure",
      rows: [
        { model: "gpt-oss 120B", role: "cloud", score: 18, low: 9, high: 28, callsPerAnswer: 0, callsLabel: "0", latency: "4.1 s" },
        { model: "DeepSeek V4.1 Flash", role: "cloud", score: 15, low: 7, high: 25, callsPerAnswer: 0, callsLabel: "0", latency: "3.6 s" },
      ],
    },
  ],
  errorExamples: [
    { input: "What is Malaysia's latest youth unemployment rate (15 to 24)?", expected: "10.1 per cent, August 2026", model: "DeepSeek V4.1 Flash", output: "10.2 per cent, June 2026", note: "Gave the open dataset's figure for June 2026, not the release for August 2026.", correct: false },
    { input: "Berapakah jumlah domain .my aktif terkini?", expected: "693,122 domains, September 2026", model: "gpt-oss 120B", output: "352,717 domains, January 2025", note: "Gave the open dataset's figure for January 2025, not the release for September 2026.", correct: false },
    { input: "What was Malaysia's latest net FDI inflow?", expected: "RM7.4 billion, Q2 2026", model: "gpt-oss 120B", output: "No final answer", note: "No final JSON answer could be read.", correct: false },
  ],
};
