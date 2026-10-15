# LLM Eval Lab Freshness Study Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the LLM Eval Lab's Manglish plan with a published study of whether two Ollama Cloud models, with read-only tools over a frozen snapshot and from memory, find the latest official figure for 30 Malaysian statistics when the open dataset is out of date, against a baseline that trusts the open data; the site shows the validated results and the CV quotes them.

**Architecture:** A new package `analysis/evallab/` in the existing uv workspace: `statistics` (the 30 statistics and where each lives), `sources` (reading PDFs, BNM tables and MYNIC charts on disk), `snapshot` (fetch once, checksum, verify on every later run), `store` (the frozen snapshot read back), `tools` (the four tools and the baseline), `questions` (drafted answers, the review sheet, the verified set), `ollama` (a stdlib HTTP client), `runner` (tool loop, pacing, retries, resumable JSONL logs), `scoring` (answer parsing, unit and period normalisation, bootstrap over statistics), `export` (templated prose and the results JSON) and `cli` (`snapshot`, `draft`, `run`). A human verification stop sits between drafting and the runner, and a 20-question pilot runs before the full run. The site validates `apps/web/src/content/results/llm-eval-lab.json` with a hand-written guard at import time, so a bad file fails `next build`.

**Tech Stack:** Python 3.12, uv 0.11.4, numpy, pyarrow 26.0.0, PyMuPDF 1.28.2, openpyxl 3.1.5, stdlib `urllib` for Ollama, pytest. Ollama 0.40.4 (local server, cloud models `gpt-oss:120b-cloud` and `deepseek-v4.1-flash:cloud`). Next.js 16.4, React 19.2, TypeScript 5.9, Vitest 4. PyMuPDF 1.26.7 for the CV, run with `uv run --no-project --with` as before.

**Spec:** `docs/superpowers/specs/2026-10-15-llm-eval-lab-freshness-design.md` (approved 2026-10-15). Brief: `.context/evallab-planning-brief.md`. Evidence: `.context/dgm-freshness-report.md`. Conventions follow `docs/superpowers/plans/2026-10-14-penang-pulse-pipeline.md`.

## Global Constraints

- Honesty rule: no hand-typed numbers in site or CV copy that come from results. Every result on the site and in the CV comes from `apps/web/src/content/results/llm-eval-lab.json`, which only the pipeline writes; prose comes from templates in `analysis/evallab/export.py`. Only `apps/web/src/lib/study-results.ts` branches on `NODE_ENV`.
- Copy rules: sentence case, no em or en dashes in prose, no arrows, no all-caps labels.
- Files under 400 lines. Immutable patterns in TypeScript. Python is typed, with small functions, and reports progress with stdlib `logging`.
- Never commit raw data (`analysis/data/raw/`, which holds the snapshot `analysis/data/raw/evallab/`, the MYNIC responses and the run logs in `analysis/data/raw/evallab/runs/`), `.env*`, `.vercel/`, `.context/`, `.superpowers/`, `apps/web/next-env.d.ts` or the full CV.
- Spec section 15 is binding: MYNIC is the third agency, its figures are used under attribution and its raw data is never committed or republished; questions target headline figures only; the bootstrap resamples statistics, not questions; the memory view has no baseline row; temperature 0 with one run per question per mode.
- Models and settings: `gpt-oss:120b-cloud` and `deepseek-v4.1-flash:cloud` through the local Ollama server at `http://localhost:11434`; options `{"temperature": 0, "seed": 42}`; at most 6 tool calls per question; bootstrap of 2,000 resamples with seed 42.
- Dependency pins, verified on 2026-10-15 with Python 3.12 (macOS arm64; the lock also carries manylinux x86_64 wheels, so CI installs from wheels): `pymupdf==1.28.2`, `openpyxl==3.1.5`. The Ollama client uses stdlib `urllib`; no Ollama package is added.
- Python tests run offline on a synthetic world written into pytest's temporary directories, with a scripted fake model and, for the HTTP client, a local `http.server`. No test reads `analysis/data/raw/`, `/tmp/dgm`, `/tmp/evallab` or the network.
- Cloud requests are rationed: the only real cloud calls are the pilot (Task 7) and the full run (Task 10). Never delete or edit `analysis/data/raw/evallab/runs/` to repeat questions that already have answers.
- Commit every code change before a real run (Tasks 7 and 10), so the manifest records a clean tree.
- Web checks from the repository root: `npm test`, `npm run lint`, `npm run typecheck`, `npm run build`. One web test file: `npm test --workspace web -- src/path/to/file.test.ts`. Python checks from `analysis/`: `uv run pytest` (CI runs `uv sync --locked` first).
- `apps/web/AGENTS.md` applies to web code: read the relevant guide in `node_modules/next/dist/docs/` before using a Next.js API.
- Every test is written first and seen to fail before the code that makes it pass.
- Work on branch `llm-eval-lab-pipeline`, a git worktree: never run a bare `git stash`. One conventional commit per task. The last task stops before push and pull request; the controller opens it.

## Review Focus

The five input conditions the spec implies but does not test that are most likely to bite, most likely first. Each has a test in the task that owns the code.

1. **Several tool calls in one message, and a model that keeps calling tools.** On 2026-10-15 `deepseek-v4.1-flash:cloud` answered a single question with two `search_datasets` calls in one message. Expected: each call counts toward the cap of 6, calls past the cap are refused with a note instead of run, the next request offers no tools so the model must answer, and the question is scored on that answer. Test: Task 7, `test_parallel_tool_calls_count_one_by_one_and_the_cap_forces_an_answer`.
2. **Final answers that bend the requested format.** Seen on 2026-10-15: the JSON came inside a ```` ```json ```` fence after prose. Also likely: `"RM2.64 trillion"` for a statistic kept in RM billion, `"Ogos 2026"`, `"2Q 2026"`, `"suku kedua 2026"`, a percentage as `"10.1%"`. Expected: the last complete JSON answer is read, its value converted to the statistic's unit and its period to `YYYY-MM` or `YYYY-Qn` before comparing; a reply with no JSON answer is unreadable and scored wrong. Tests: Task 8, `test_parse_answer_takes_the_last_complete_json_answer`, `test_values_are_converted_to_the_statistics_unit`, `test_periods_are_read_in_english_and_malay`.
3. **An Ollama Cloud usage limit or an interruption in the middle of the run.** Expected: HTTP 429 stops the run with a message to run the same command later; the next run asks only what is missing, never repeats a finished question, and skips a log line cut short by the interruption. Tests: Task 7, `test_a_usage_limit_stops_the_run_and_the_next_run_resumes`, `test_a_line_cut_short_by_an_interruption_is_skipped`, `test_a_usage_limit_is_its_own_error`.
4. **Running `draft` again after verification has started.** Expected: the review sheet is never overwritten without `--force`, so Subashanan's checked rows survive. Test: Task 5, `test_drafting_again_never_overwrites_the_sheet_by_accident`.
5. **A release whose wording no longer matches its pattern, or a dataset newer than the newest indexed release.** Expected: the draft leaves the value blank with evidence telling the reviewer to read the release, or marks the dataset as newer for a hand check; the runner refuses a verified row whose value is blank or whose period is malformed. Tests: Task 5, `test_a_release_without_the_headline_leaves_the_value_for_the_reviewer`, `test_a_dataset_newer_than_the_release_is_flagged_and_counts_as_current`, `test_a_malformed_verified_row_stops_the_run`.

## Decisions this plan makes where the spec is silent or needs a correction

- **The score axis runs from 0 to 100.** The spec changes only the chart's x axis, but the old 50 to 100 score scale would push a share below 50 off the chart; the leaderboard's interval track and the chart's y axis both become 0 to 100 (Task 1).
- **`read_release` pages are PDF pages, and `search_releases` returns the best matching pages.** The tool signatures stay as in spec section 7; without `matching_pages` a model would have to guess which of 155 CPI pages holds the headline (Task 4). Releases with text in the snapshot rank above index-only entries.
- **The catalogue commit is the repository's HEAD on the snapshot day.** The audit's commit `4ba675a3` was already superseded by `59900ec1` on 2026-10-15; the commit used is recorded in `snapshot.json` and the manifest (Task 3).
- **The 30 statistics** are 21 DOSM headline figures, 6 BNM figures (money supply M1 and M3 from table 1.3; the 12-month fixed deposit, base, base lending and average lending rates of commercial banks from table 2.1) and 3 MYNIC totals (active, IPv6 and DNSSEC `.my` domains). A dry run on 2026-10-15 found all 30 values in the releases; 16 statistics were out of date and 14 current (Task 5).
- **BNM release text** is written from the XLSX rows of the newest Monthly Highlights and Statistics edition; BNM prints no release date, so BNM and MYNIC releases have `release_date: null`.
- **"Source given"** counts any dataset id in the snapshot and the URL of any file or page of a release in the snapshot (the PDF, the OpenDOSM page, the BNM XLSX or edition page, the MYNIC endpoint or statistics page). It is reported per model and view in the manifest; the site's views show the latest-figure share, as spec section 8 makes it the main score.
- **Quarterly answers given as a month** count as that month's quarter; monthly answers given as a quarter are wrong.
- **The CV label** beside the LLM Eval Lab heading changes from "In Progress" to "LLM Evaluation" with the bullet and tech line (Task 12). This goes beyond spec section 12; drop that one call if Subashanan prefers.
- **Unverified on 2026-10-15:** that Ollama Cloud signals a usage limit with HTTP 429 (no limit was hit; other errors are retried and then scored as no answer), and that cloud models honour `temperature` and `seed` (both were accepted without error). The second is covered by the limitation that run-to-run variation is not measured.

## Before you start

- The spec is committed (`748068d`, `241a33f`, `00f85f5`), and this plan is committed after it.
- `apps/web/next-env.d.ts` flips between `./.next/dev/types/...` and `./.next/types/...` whenever `next dev` or `next build` runs. Never stage it. Restore it with `git checkout -- apps/web/next-env.d.ts` before Tasks 7 and 10, which need a clean tree.
- uv 0.11.4 is installed and `analysis/.venv` exists. Python 3.12 comes from `requires-python`.
- Ollama 0.40.4 runs at `http://localhost:11434` and Subashanan is signed in to Ollama Cloud; both cloud models are pulled. The local `gpt-oss:20b` fails to load (its blob comes from LM Studio), so do not use it for checks.
- Checked on 2026-10-15 during planning (3 real cloud calls): `/api/chat` with `tools` returns `message.tool_calls[].function.{name, arguments}` with `arguments` as an object; tool results go back as `{"role": "tool", "tool_name": ..., "content": ...}`; `message.thinking` carries the reasoning; cloud responses report `total_duration`, `prompt_eval_count` and `eval_count` but no `eval_duration`, and name the model without the `-cloud` or `:cloud` suffix.
- Checked on 2026-10-15: a full snapshot took 90 seconds and 301 MB (95 files, 38 releases); every DOSM headline pattern matched its newest release; PyMuPDF extracted the 155-page CPI release in 0.7 s with numbers intact, while pypdf took 6.8 s and split numbers such as `292. 5`.

## File map

```
.github/workflows/ci.yml                               unchanged: the analysis job already runs uv sync --locked and uv run pytest
analysis/
  pyproject.toml, uv.lock                              pymupdf and openpyxl pinned; a PyMuPDF warning filter (Task 3)
  evallab/__init__.py                                  empty (Task 3)
  evallab/statistics.py                                the 30 statistics, release patterns and periods (Task 3)
  evallab/sources.py                                   release periods, PDF pages, BNM tables, MYNIC charts (Task 3)
  evallab/snapshot.py                                  fetch once, snapshot.json, verify on every later run (Task 3)
  evallab/store.py                                     the frozen snapshot read back; latest dataset values (Task 4)
  evallab/tools.py                                     search_datasets, read_dataset, search_releases, read_release, baseline (Task 4)
  evallab/questions.py                                 drafted answers, the review sheet, the verified question set (Task 5)
  evallab/questions.csv                                drafted (Task 5), verified by Subashanan (Task 6)
  evallab/cli.py                                       snapshot and draft (Task 5), run and the pilot (Task 7), scoring and outputs (Task 9)
  evallab/ollama.py                                    stdlib client for the Ollama HTTP API (Task 7)
  evallab/runner.py                                    tool loop, cap, retries, pacing, resumable logs (Task 7)
  evallab/scoring.py                                   answer parsing, units, periods, bootstrap, views (Task 8)
  evallab/export.py                                    prose templates, rows, error examples, results JSON (Task 9)
  tests/evallab/__init__.py                            empty (Task 3)
  tests/evallab/world.py                               the synthetic data.gov.my, DOSM, BNM and MYNIC (Task 3)
  tests/evallab/conftest.py                            store (Task 4), questions (Task 5), answered run (Task 7)
  tests/evallab/test_statistics.py, test_snapshot.py   (Task 3)
  tests/evallab/test_tools.py                          (Task 4)
  tests/evallab/test_questions.py                      (Task 5)
  tests/evallab/fake_ollama.py, test_ollama.py, test_runner.py, test_cli.py   (Task 7)
  tests/evallab/test_scoring.py                        (Task 8)
  tests/evallab/contract.py, test_export.py, test_pipeline.py                  (Task 9)
  tools/update_cv.py, tests/test_update_cv.py          LLM Eval Lab bullet, tech line and label (Task 12)
  outputs/llm-eval-lab-manifest.json                   written by the full run (Task 10)
apps/web/
  public/subashanan-nair-cv.pdf                        updated (Task 12)
  src/content/types.ts                                 ModelRole and EvalRow (Task 1)
  src/content/fixtures/llm-eval.ts                     the new shape, illustrative (Task 1)
  src/content/studies.ts                               LLM Eval Lab sources (Task 1), the full record (Task 11)
  src/components/figures/llm-eval/calls-score-chart.tsx   replaces cost-score-chart.tsx (Task 1)
  src/components/figures/llm-eval/leaderboard.tsx, role-style.ts, error-examples.tsx, llm-eval-figure.tsx, llm-eval-figure.test.tsx   (Task 1)
  src/components/study/study-page.test.tsx             fixture number (Task 1), unpublished example moved (Task 11)
  src/content/results/parse-llm-eval.ts, parse-llm-eval.test.ts                (Task 2)
  src/content/results/llm-eval-lab.json                written by the full run (Task 10)
  src/content/results/index.ts, index.test.ts          publish the validated file (Task 11)
  src/lib/study-results.test.ts, src/components/study/study-card.test.tsx      unpublished examples move to penang-ai-assistant (Task 11)
```

Not committed: `analysis/data/raw/` (including `analysis/data/raw/evallab/` and its `runs/` logs), `analysis/.venv/`, `.context/resume/`.

---

### Task 1: Web: cloud and baseline roles, tool calls on the x axis, the new fixture

**Files:**
- Create: `apps/web/src/components/figures/llm-eval/calls-score-chart.tsx`
- Delete: `apps/web/src/components/figures/llm-eval/cost-score-chart.tsx`
- Modify: `apps/web/src/content/types.ts`, `apps/web/src/content/fixtures/llm-eval.ts`, `apps/web/src/content/studies.ts` (LLM Eval Lab sources only), `apps/web/src/components/figures/llm-eval/role-style.ts`, `leaderboard.tsx`, `error-examples.tsx`, `llm-eval-figure.tsx`
- Test: `apps/web/src/components/figures/llm-eval/llm-eval-figure.test.tsx` (replace), `apps/web/src/components/study/study-page.test.tsx` (modify)

**Interfaces:**
- Consumes: `EvalTask`, `LlmEvalResults`, `ModelRole` (`@/content/types`); `scale` (`../chart-utils`); `useChartWidth` (`../use-chart-width`); `palette` (`@/styles/palette`); `TabList`, `tabId` (`@/components/ui/tab-list`).
- Produces: `ModelRole = "cloud" | "baseline"`; `EvalRow { model, role, score, low, high, callsPerAnswer: number, callsLabel: string, latency: string }` (`costPer1k` and `costLabel` are gone); `ROLE_COLOUR`, `ROLE_TINT` and `ROLE_LABEL` keyed by role (`ROLE_LABEL` reads "Cloud model" and "Open data baseline"); `CallsScoreChart({ task }: { task: EvalTask })` with x from 0 to 6 tool calls and y from 0 to 100, and `labelOffsets(ys: readonly number[]): number[]`, which pushes labels at least 16 px apart; `llmEvalFixture` in the new shape with views `all-tools`, `stale-tools` and `all-memory` (no baseline row in `all-memory`) and `retrieved` keyed by the six new source names; the LLM Eval Lab study's six `sources` (`data.gov.my datasets`, `DOSM releases`, `Bank Negara Malaysia`, `MYNIC`, `Ollama Cloud`, `Question set`). Task 2 uses the fixture as its valid input; Task 9 writes rows in this shape; Task 11 replaces the rest of the study record.

- [ ] **Step 1: Write the failing tests**

Replace `apps/web/src/components/figures/llm-eval/llm-eval-figure.test.tsx` with:

```tsx
import { fireEvent, render, screen, within } from "@testing-library/react";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import { llmEvalFixture } from "@/content/fixtures/llm-eval";

import { labelOffsets } from "./calls-score-chart";
import { LlmEvalFigure } from "./llm-eval-figure";

describe("LlmEvalFigure", () => {
  it("server-renders the first view's leaderboard and scatter", () => {
    const html = renderToStaticMarkup(<LlmEvalFigure data={llmEvalFixture} />);
    expect(html).toContain("% with the latest figure, with 95% interval");
    expect(html).toContain("Tool calls per answer");
    expect((html.match(/class="score-dot"/g) ?? []).length).toBe(3);
  });

  it("changes the table and the chart together when the view changes", () => {
    render(<LlmEvalFigure data={llmEvalFixture} />);
    fireEvent.click(screen.getByRole("tab", { name: "All series, from memory" }));
    const table = screen.getByRole("table");
    expect(within(table).getAllByRole("row")).toHaveLength(3); // the header and two cloud models: no baseline from memory
    expect(within(table).queryByText("Open data only")).not.toBeInTheDocument();
    expect(screen.getByRole("img", { name: /against tool calls per answer/i })).toBeInTheDocument();
  });

  it("labels every point on the scatter by name and names both roles in the legend", () => {
    render(<LlmEvalFigure data={llmEvalFixture} />);
    const chart = screen.getByRole("img", { name: /against tool calls per answer/i });
    for (const row of llmEvalFixture.tasks[0].rows) expect(chart).toHaveTextContent(row.model);
    expect(screen.getByText("Cloud model")).toBeInTheDocument();
    expect(screen.getByText("Open data baseline")).toBeInTheDocument();
  });

  it("shows each error example as missed", () => {
    render(<LlmEvalFigure data={llmEvalFixture} />);
    expect(screen.getAllByText("Missed")).toHaveLength(3);
    expect(screen.queryByText("Correct")).not.toBeInTheDocument();
  });
});

describe("labelOffsets", () => {
  it("keeps labels that are far apart where they are", () => {
    expect(labelOffsets([100, 40, 200])).toEqual([100, 40, 200]);
  });

  it("pushes a label down when two points share a score", () => {
    expect(labelOffsets([120, 120, 50])).toEqual([120, 136, 50]);
  });
});
```

The preview test in `apps/web/src/components/study/study-page.test.tsx` checks a number from the fixture. In that file, replace both occurrences of `"3 points"` with `"47 points"` (one in `production mode with no results shows the plan and no numbers`, one in `preview mode shows fixture numbers under a visible preview label`).

- [ ] **Step 2: Run the tests to verify they fail**

Run: `npm test --workspace web -- src/components/figures/llm-eval src/components/study/study-page.test.tsx`
Expected: FAIL. `llm-eval-figure.test.tsx` fails with `Failed to resolve import "./calls-score-chart"`; `study-page.test.tsx` fails `preview mode shows fixture numbers under a visible preview label` with `Unable to find an element with the text: 47 points`.

- [ ] **Step 3: Implement**

In `apps/web/src/content/types.ts`, replace:

```ts
export type ModelRole = "frontier" | "ft" | "open" | "base";
export interface EvalRow {
  model: string;
  role: ModelRole;
  score: number;
  low: number;
  high: number;
  costPer1k: number;
  costLabel: string;
  latency: string;
}
```

with:

```ts
export type ModelRole = "cloud" | "baseline";
export interface EvalRow {
  model: string;
  role: ModelRole;
  score: number; // % of questions answered with the latest official figure
  low: number; // 95% interval
  high: number;
  callsPerAnswer: number; // mean tool calls per answer
  callsLabel: string;
  latency: string; // median seconds per answer, as text
}
```

The fixture stays illustrative and dev-only. Replace `apps/web/src/content/fixtures/llm-eval.ts` with:

```ts
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
```

`content.test.ts` checks that a fixture dates every source its study lists, so the study's sources change now. In `apps/web/src/content/studies.ts`, in the `llm-eval-lab` record, replace:

```ts
    sources: [
      { name: "Manglish and BM sets", publisher: "This project", used: "Hand-labelled items for sentiment and entities", licence: "CC BY 4.0" },
      { name: "Malaysian news headlines", publisher: "Public news sites", used: "Articles for the summary task", licence: "Public, research use" },
      { name: "Models", publisher: "Model APIs and open weights", used: "Every model, listed with its version", licence: "Per provider" },
    ],
```

with:

```ts
    sources: [
      { name: "data.gov.my datasets", publisher: "Government of Malaysia, via data.gov.my", used: "Catalogue metadata and the latest value of each series", licence: "CC BY 4.0" },
      { name: "DOSM releases", publisher: "Department of Statistics Malaysia, via OpenDOSM", used: "Release text for the latest official figures; cited, not republished", licence: "DOSM terms" },
      { name: "Bank Negara Malaysia", publisher: "Bank Negara Malaysia", used: "Money supply and interest rate tables. Source: Bank Negara Malaysia", licence: "Terms of Use for BNM Datasets" },
      { name: "MYNIC", publisher: "MYNIC Berhad", used: "Domain statistics; single figures cited, raw data not republished", licence: "All rights reserved" },
      { name: "Ollama Cloud", publisher: "Ollama", used: "gpt-oss:120b-cloud and deepseek-v4.1-flash:cloud, with their versions in the manifest", licence: "Provider terms" },
      { name: "Question set", publisher: "This project", used: "Every question, with its answer verified against the official release", licence: "CC BY 4.0" },
    ],
```

Replace `apps/web/src/components/figures/llm-eval/role-style.ts` with:

```ts
import type { ModelRole } from "@/content/types";
import { palette } from "@/styles/palette";

// Marks use the deep glaze (at least 3:1); interval bands use the light tint.
export const ROLE_COLOUR: Readonly<Record<ModelRole, string>> = { cloud: palette.cobalt, baseline: palette.roseDeep };
export const ROLE_TINT: Readonly<Record<ModelRole, string>> = { cloud: palette.cobalt, baseline: palette.rose };
export const ROLE_LABEL: Readonly<Record<ModelRole, string>> = { cloud: "Cloud model", baseline: "Open data baseline" };
```

Delete the old chart with `git rm apps/web/src/components/figures/llm-eval/cost-score-chart.tsx` and create `apps/web/src/components/figures/llm-eval/calls-score-chart.tsx`. Every answer from memory and every baseline answer sits at x = 0, so labels that would collide are pushed apart:

```tsx
"use client";

import { useRef } from "react";

import type { EvalTask } from "@/content/types";
import { palette } from "@/styles/palette";

import { scale } from "../chart-utils";
import { useChartWidth } from "../use-chart-width";
import { ROLE_COLOUR } from "./role-style";

const MAX_CALLS = 6; // the runner's cap on tool calls per question
const SCORE_TICKS = [0, 20, 40, 60, 80, 100];
const LABEL_GAP = 16; // px between stacked labels

/** Label baselines for points sorted top to bottom, pushed down so no two sit closer than LABEL_GAP. */
export function labelOffsets(ys: readonly number[]): number[] {
  const order = ys.map((y, i) => ({ y, i })).sort((a, b) => a.y - b.y);
  const placed = new Array<number>(ys.length);
  let last = -Infinity;
  for (const { y, i } of order) {
    last = Math.max(y, last + LABEL_GAP);
    placed[i] = last;
  }
  return placed;
}

export function CallsScoreChart({ task }: { task: EvalTask }) {
  const ref = useRef<HTMLDivElement>(null);
  const w = useChartWidth(ref);
  const h = Math.round(Math.min(380, Math.max(300, w * 0.5)));
  const pad = { l: 44, r: 16, t: 18, b: 32 };
  const x = scale(0, MAX_CALLS, pad.l + 10, w - pad.r);
  const y = scale(0, 100, h - pad.b, pad.t);
  const labelY = labelOffsets(task.rows.map((r) => y(r.score) + 4.5));

  return (
    <div className="chart" ref={ref}>
      <svg viewBox={`0 0 ${w} ${h}`} role="img" aria-label={`${task.metric} against tool calls per answer for each model`}>
        {SCORE_TICKS.map((v) => (
          <g key={v}>
            <line x1={pad.l} x2={w - pad.r} y1={y(v)} y2={y(v)} stroke={palette.ink} strokeOpacity={0.1} />
            <text x={pad.l - 8} y={y(v) + 4} textAnchor="end">{v}</text>
          </g>
        ))}
        {Array.from({ length: MAX_CALLS + 1 }, (_, v) => (
          <g key={`x${v}`}>
            <line x1={x(v)} x2={x(v)} y1={pad.t} y2={h - pad.b} stroke={palette.ink} strokeOpacity={0.1} />
            <text x={x(v)} y={h - pad.b + 20} textAnchor="middle">{v}</text>
          </g>
        ))}
        <line x1={pad.l} x2={w - pad.r} y1={h - pad.b} y2={h - pad.b} stroke={palette.ink} strokeWidth={1.5} />
        {task.rows.map((r, i) => {
          const px = x(Math.min(r.callsPerAnswer, MAX_CALLS));
          const right = px > w * 0.62;
          return (
            <g key={r.model}>
              <line x1={px} x2={px} y1={y(r.low)} y2={y(r.high)} stroke={ROLE_COLOUR[r.role]} strokeWidth={2.5} strokeLinecap="round" />
              <circle className="score-dot" cx={px} cy={y(r.score)} r={7.5} fill={ROLE_COLOUR[r.role]} stroke={palette.ink} strokeWidth={2} />
              <text className="strong" x={right ? px - 13 : px + 13} y={labelY[i]} textAnchor={right ? "end" : "start"}>{r.model}</text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}
```

Replace `apps/web/src/components/figures/llm-eval/leaderboard.tsx` with:

```tsx
import type { EvalTask } from "@/content/types";
import { palette } from "@/styles/palette";

import { ROLE_COLOUR, ROLE_TINT } from "./role-style";

// Interval bars sit on a 0 to 100 track, the share of questions answered with the latest figure.
export function Leaderboard({ task }: { task: EvalTask }) {
  return (
    <div className="tile-frame">
      <div className="table-wrap" role="region" aria-label="Leaderboard for the selected task" tabIndex={0}>
        <table>
          <thead>
            <tr>
              <th scope="col">Model</th>
              <th scope="col" className="board-metric">{task.metric}, with 95% interval</th>
              <th scope="col" className="num">Tool calls per answer</th>
              <th scope="col" className="num">Median time per answer</th>
            </tr>
          </thead>
          <tbody>
            {task.rows.map((r) => (
              <tr key={r.model}>
                <th scope="row"><span className="model-name"><span className="sw" style={{ background: ROLE_COLOUR[r.role], borderColor: palette.ink }} />{r.model}</span></th>
                <td>
                  <div className="ci">
                    <b>{r.score}<small>{r.low} to {r.high}</small></b>
                    <span className="ci-track" aria-hidden="true">
                      <span className="ci-range" style={{ left: `${r.low}%`, width: `${r.high - r.low}%`, background: ROLE_TINT[r.role] }} />
                      <span className="ci-dot" style={{ left: `${r.score}%`, background: ROLE_COLOUR[r.role] }} />
                    </span>
                  </div>
                </td>
                <td className="num">{r.callsLabel}</td>
                <td className="num">{r.latency}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
```

In `apps/web/src/components/figures/llm-eval/error-examples.tsx`, replace:

```tsx
      <p className="intro">Three items from the Manglish sentiment set, picked to show where models slip.</p>
```

with:

```tsx
      <p className="intro">Real failures from the run, chosen by rule: an out-of-date figure quoted, the wrong period, or no answer that could be read.</p>
```

and, because two models can fail the same question, replace `<article key={e.input} className="tile-frame">` with ``<article key={`${e.model} ${e.input}`} className="tile-frame">``.

Replace `apps/web/src/components/figures/llm-eval/llm-eval-figure.tsx` with:

```tsx
"use client";

import { useState } from "react";

import { TabList, tabId } from "@/components/ui/tab-list";
import type { LlmEvalResults, ModelRole } from "@/content/types";
import { palette } from "@/styles/palette";

import { CallsScoreChart } from "./calls-score-chart";
import { ErrorExamples } from "./error-examples";
import { Leaderboard } from "./leaderboard";
import { ROLE_COLOUR, ROLE_LABEL } from "./role-style";

const ROLES: readonly ModelRole[] = ["cloud", "baseline"];

export function LlmEvalFigure({ data }: { data: LlmEvalResults }) {
  const [taskId, setTaskId] = useState(data.tasks[0].id);
  const task = data.tasks.find((t) => t.id === taskId) ?? data.tasks[0];

  return (
    <div>
      <h3 className="sub">Leaderboard</h3>
      <p className="intro">Pick a view. Cloud models and the open data baseline keep their colours across the table and the chart. Bars show the 95% interval on a 0 to 100 scale.</p>
      <TabList label="Views" idPrefix="task" panelId="task-panel" selected={taskId} onSelect={setTaskId} items={data.tasks.map((t) => ({ id: t.id, label: t.label }))} />
      <div className="stack" id="task-panel" role="tabpanel" aria-labelledby={tabId("task", taskId)}>
        <Leaderboard task={task} />
        <figure className="tile-frame">
          <h4 className="panel-title">Tool calls against score</h4>
          <p className="figcap" style={{ margin: "0 0 14px" }}>One point per model for the selected view. Vertical lines are 95% intervals. Up and to the left is a right answer found with fewer lookups.</p>
          <CallsScoreChart task={task} />
          <ul className="band-legend">
            {ROLES.map((role) => <li key={role}><span className="sw" style={{ background: ROLE_COLOUR[role], borderColor: palette.ink }} />{ROLE_LABEL[role]}</li>)}
          </ul>
          <p className="figcap">Share answered with the latest figure on the vertical axis. Mean tool calls per answer on the horizontal axis, capped at 6; the baseline and answers from memory make none.</p>
        </figure>
      </div>
      <ErrorExamples examples={data.errorExamples} />
    </div>
  );
}
```

- [ ] **Step 4: Run the tests and checks**

Run: `npm test --workspace web -- src/components/figures/llm-eval`, then `npm test`, `npm run typecheck` and `npm run lint`.
Expected: `Tests  6 passed (6)` for the figure; overall `Tests  147 passed (147)`; no type or lint errors. `grep -rn "costPer1k\|costLabel\|frontier\|CostScoreChart" apps/web/src` prints nothing.

- [ ] **Step 5: Commit**

```bash
git add apps/web/src/content/types.ts apps/web/src/content/fixtures/llm-eval.ts apps/web/src/content/studies.ts \
  apps/web/src/components/figures/llm-eval apps/web/src/components/study/study-page.test.tsx
git commit -m "feat: show tool calls and cloud and baseline roles in the LLM Eval Lab figure"
```

---

### Task 2: Web: validate LLM Eval Lab results files

**Files:**
- Create: `apps/web/src/content/results/parse-llm-eval.ts`
- Test: `apps/web/src/content/results/parse-llm-eval.test.ts`

**Interfaces:**
- Consumes: `checks(study)` from `./parse-checks` (`fail`, `object`, `text`, `finite`, `whole`, `list`, `base`); `LlmEvalResults`, `ModelRole` (`../types`); `llmEvalFixture` (Task 1) as the valid example.
- Produces: `parseLlmEvalResults(json: unknown): LlmEvalResults`, which returns its input typed when every check passes and otherwise throws `Error("llm-eval-lab results: <path> <problem>")`. It enforces: the base fields; exactly the views `all-tools`, `stale-tools`, `all-memory` in that order, each with a label and metric; rows with a model name, a role of `cloud` or `baseline`, whole `low`, `score` and `high` from 0 to 100 with `low <= score <= high`, `callsPerAnswer` from 0 to 6, a `callsLabel` and a `latency`; one baseline row in each view with tools and none from memory, at least one cloud model per view and no model twice; at most 6 error examples, each with text fields and a boolean `correct`. Task 11 calls it on the committed JSON; Task 9's `tests/evallab/contract.py` mirrors these rules in Python.

- [ ] **Step 1: Write the failing test**

Create `apps/web/src/content/results/parse-llm-eval.test.ts`:

```ts
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
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `npm test --workspace web -- src/content/results/parse-llm-eval.test.ts`
Expected: FAIL with `Failed to resolve import "./parse-llm-eval"`.

- [ ] **Step 3: Write the validator**

Create `apps/web/src/content/results/parse-llm-eval.ts`:

```ts
import type { LlmEvalResults, ModelRole } from "../types";
import { checks, type Json } from "./parse-checks";

// Checks a results file against the LlmEvalResults shape before the site uses it.
const TASK_IDS = ["all-tools", "stale-tools", "all-memory"] as const;
const ROLES: readonly ModelRole[] = ["cloud", "baseline"];
const MAX_CALLS = 6;
const MAX_EXAMPLES = 6;
const { fail, object, text, finite, whole, list, base } = checks("llm-eval-lab");

function checkRow(value: unknown, path: string): Json {
  const r = object(value, path);
  text(r.model, `${path}.model`);
  if (!ROLES.includes(r.role as ModelRole)) fail(`${path}.role`, `must be one of ${ROLES.join(", ")}`);
  const [low, score, high] = (["low", "score", "high"] as const).map((k) => whole(r[k], `${path}.${k}`, 0, 100));
  if (low > score || score > high) fail(`${path}.score`, "must lie inside its interval");
  const calls = finite(r.callsPerAnswer, `${path}.callsPerAnswer`);
  if (calls < 0 || calls > MAX_CALLS) fail(`${path}.callsPerAnswer`, `must be from 0 to ${MAX_CALLS}`);
  text(r.callsLabel, `${path}.callsLabel`);
  text(r.latency, `${path}.latency`);
  return r;
}

function checkTask(value: unknown, i: number): void {
  const path = `tasks[${i}]`;
  const t = object(value, path);
  if (t.id !== TASK_IDS[i]) fail(`${path}.id`, `must be ${TASK_IDS[i]}, the fixed view order is ${TASK_IDS.join(", ")}`);
  text(t.label, `${path}.label`);
  text(t.metric, `${path}.metric`);
  const rows = list(t.rows, `${path}.rows`).map((r, j) => checkRow(r, `${path}.rows[${j}]`));
  const baselines = rows.filter((r) => r.role === "baseline").length;
  const wanted = t.id === "all-memory" ? 0 : 1;
  if (baselines !== wanted) fail(`${path}.rows`, `must have ${wanted} baseline row${wanted === 1 ? "" : "s"}, found ${baselines}`);
  if (rows.length === baselines) fail(`${path}.rows`, "must have at least one cloud model");
  if (new Set(rows.map((r) => r.model)).size !== rows.length) fail(`${path}.rows`, "must name each model once");
}

function checkExample(value: unknown, i: number): void {
  const path = `errorExamples[${i}]`;
  const e = object(value, path);
  for (const field of ["input", "expected", "model", "output", "note"]) text(e[field], `${path}.${field}`);
  if (typeof e.correct !== "boolean") fail(`${path}.correct`, "must be true or false");
}

export function parseLlmEvalResults(json: unknown): LlmEvalResults {
  const root = object(json, "file");
  base(root);
  list(root.tasks, "tasks", TASK_IDS.length).forEach(checkTask);
  const examples = list(root.errorExamples, "errorExamples");
  if (examples.length > MAX_EXAMPLES) fail("errorExamples", `must have at most ${MAX_EXAMPLES} items`);
  examples.forEach(checkExample);
  return root as unknown as LlmEvalResults;
}
```

- [ ] **Step 4: Run the tests and checks**

Run: `npm test --workspace web -- src/content/results`, then `npm test`, `npm run typecheck` and `npm run lint`.
Expected: `parse-llm-eval.test.ts` 18 passed and the other results tests unchanged (`Tests  53 passed (53)` for the folder); overall `Tests  165 passed (165)`; no type or lint errors.

- [ ] **Step 5: Commit**

```bash
git add apps/web/src/content/results/parse-llm-eval.ts apps/web/src/content/results/parse-llm-eval.test.ts
git commit -m "feat: validate LLM Eval Lab results files"
```

---

### Task 3: Python: dependencies, the statistics and the snapshot

**Files:**
- Modify: `analysis/pyproject.toml`, `analysis/uv.lock` (generated)
- Create: `analysis/evallab/__init__.py` (empty), `analysis/evallab/statistics.py`, `analysis/evallab/sources.py`, `analysis/evallab/snapshot.py`, `analysis/tests/evallab/__init__.py` (empty), `analysis/tests/evallab/world.py`
- Test: `analysis/tests/evallab/test_statistics.py`, `analysis/tests/evallab/test_snapshot.py`

**Interfaces:**
- Consumes: `forecasting.data.sha256_of(path: Path) -> str`.
- Produces, in `evallab.statistics`: `NUMBER` (the regex group that captures a figure); `Series(dataset, column, where: tuple[tuple[str, str], ...] = (), scale: float = 1.0)` (frozen); `Statistic(id, agency, name_en, name_ms, unit, decimals, quarterly, series, release, pattern="", release_scale=1.0)` (frozen; `release` is a regex over DOSM release ids, `"<table>:<column index>"` for BNM, or the MYNIC chart type); `STATISTICS` (30, in a fixed order); `period_of(day: date, quarterly: bool) -> str` (`2026-08` or `2026-Q2`).
- Produces, in `evallab.sources`: `dosm_period(release_id) -> str`; `pdf_pages(path) -> list[str]` (whitespace collapsed per page); `latest_edition(listing_html) -> tuple[str, str]` (edition URL and `YYYY-MM`); `table_link(edition_html, table) -> str`; `bnm_rows(path) -> tuple[str, list[tuple[str, tuple]]]`; `bnm_latest(path, column) -> tuple[float, str] | None`; `bnm_text(path, table, columns: dict[int, str]) -> str`; `mynic_points(path) -> list[tuple[str, int]]`; `mynic_text(path, chart) -> str`.
- Produces, in `evallab.snapshot`: `Get = Callable[[str], bytes]`; `http_get(url) -> bytes`; constants `USER_AGENT`, `HEAD_URL`, `TARBALL_URL`, `BNM_LISTING`, `MYNIC_URL`, `MYNIC_PAGE`, `OPENDOSM_PAGE`, `RELEASES_PER_SERIES = 3`, `SNAPSHOT = "snapshot.json"`; `read_catalogue(tarball) -> tuple[dict[str, dict], list[dict]]` (dataset metadata by id, and the DOSM release records); `freeze(raw_dir, statistics, today, get=http_get) -> dict` (takes the snapshot unless `snapshot.json` exists, then verifies every file; returns the snapshot record with `taken`, `catalogue`, `files` and `releases`); `verify(raw_dir) -> dict`. Each release entry has `id, agency, title, date, period, summary, url, page, raw, pages`.
- Produces, in `tests/evallab/world.py`: `TODAY`, `COMMIT`, `STATS` (the real `unemployment_rate`, `youth_rate_15_24`, `m3` and `domains_active`), `STORAGE`, `remote() -> dict[str, bytes]`, `serve(files, asked=None)`, `take_snapshot(raw_dir) -> dict`. Tasks 4, 5, 7 and 9 build on this world.

The snapshot lives in `analysis/data/raw/evallab/` (already ignored by `analysis/data/raw/`): `catalogue.tar.gz` (the `datagovmy-meta` repository at one commit), `datasets/<id>.parquet`, `releases/<id>.pdf|.xlsx|.json` with `releases/<id>.pages.json` beside each, and `snapshot.json`, which records every file's URL, retrieval time, size and SHA-256. Once `snapshot.json` exists no command touches the network for data again, and a changed or missing file stops the run.

- [ ] **Step 1: Add the dependencies and the packages**

In `analysis/pyproject.toml`, replace:

```toml
  "networkx==3.7",
  "osmium==4.3.1",
  "pyarrow==26.0.0",
  "rasterio==1.5.2",
```

with:

```toml
  "networkx==3.7",
  "openpyxl==3.1.5",
  "osmium==4.3.1",
  "pyarrow==26.0.0",
  "pymupdf==1.28.2",
  "rasterio==1.5.2",
```

and replace:

```toml
filterwarnings = ["ignore::sklearn.exceptions.ConvergenceWarning"]
```

with:

```toml
filterwarnings = [
  "ignore::sklearn.exceptions.ConvergenceWarning",
  "ignore:builtin type .* has no __module__ attribute:DeprecationWarning",  # PyMuPDF's SWIG bindings on Python 3.12
]
```

Create the empty files `analysis/evallab/__init__.py` and `analysis/tests/evallab/__init__.py`.

Run (in `analysis/`): `uv lock`, then `uv sync --locked`, then `uv run python -c "import openpyxl, pymupdf; print(openpyxl.__version__, pymupdf.VersionBind)"`.
Expected: `uv lock` adds `et-xmlfile v2.0.0`, `openpyxl v3.1.5` and `pymupdf v1.28.2` and changes nothing else; `uv sync --locked` exits 0; the last command prints `3.1.5 1.28.2`.

- [ ] **Step 2: Write the failing tests**

Create `analysis/tests/evallab/world.py`:

```python
"""A tiny synthetic data.gov.my, DOSM, BNM and MYNIC, served from memory, and the snapshot taken from it.

Four real statistics are asked about: the unemployment rate (dataset current), youth unemployment (dataset two months
behind), money supply M3 (BNM, behind) and active .my domains (MYNIC, far behind).
"""

from __future__ import annotations

import io
import json
import tarfile
from collections.abc import Callable
from datetime import date, datetime
from pathlib import Path
from typing import Any

import openpyxl
import pyarrow as pa
import pyarrow.parquet as pq
import pymupdf

from evallab.snapshot import BNM_LISTING, HEAD_URL, MYNIC_URL, TARBALL_URL, freeze
from evallab.statistics import STATISTICS

TODAY = date(2026, 10, 15)
COMMIT = "4ba675a3fc39ee8f1119ef7bc83a588826fe1a65"
STATS = [s for s in STATISTICS if s.id in ("unemployment_rate", "youth_rate_15_24", "m3", "domains_active")]
STORAGE = "https://storage.example/"
EDITION = "https://www.bnm.gov.my/-/monthly-highlights-statistics-in-august-2026-1"
M3_TABLE = "https://www.bnm.gov.my/documents/20124/999/1.3.xlsx"
LFS_TEXT = {  # release period: (unemployment rate, youth rate)
    "2026-08": ("August 2026 eased to 2.9", "10.1"),
    "2026-07": ("July 2026 remained at 3.0", "10.2"),
    "2026-06": ("June 2026 remained at 3.0", "10.2"),
}


def pdf(*pages: str) -> bytes:
    doc = pymupdf.open()
    for text in pages:
        doc.new_page().insert_textbox(pymupdf.Rect(50, 50, 550, 800), text, fontsize=10)
    return doc.tobytes()


def parquet(rows: list[dict[str, Any]]) -> bytes:
    buffer = io.BytesIO()
    pq.write_table(pa.Table.from_pylist(rows), buffer)
    return buffer.getvalue()


def tarball(files: dict[str, Any]) -> bytes:
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w:gz") as archive:
        for name, content in files.items():
            data = json.dumps(content).encode()
            info = tarfile.TarInfo(f"datagovmy-meta-{COMMIT}/{name}")
            info.size = len(data)
            archive.addfile(info, io.BytesIO(data))
    return buffer.getvalue()


def bnm_table() -> bytes:
    book = openpyxl.Workbook()
    sheet = book.active
    sheet.append([1.3, None, "Agregat Kewangan: M1, M2 dan M3"])
    sheet.append([None, None, "Monetary Aggregates: M1, M2 and M3"])
    sheet.append(["End of period", None, None, "Total", "Total", "Total"])
    sheet.append([2025, 12, None, 2600000.0, 2590000.0, 730000.0])
    sheet.append([2026, 1, None, 2610000.0, 2600000.0, 731000.0])
    for month, m3 in ((6, 2670359.957), (7, 2659386.335), (8, 2636548.767)):
        sheet.append([None, month, None, m3, m3 - 5000, 740000.0])
    sheet.append([None, "Source: Bank Negara Malaysia"])
    buffer = io.BytesIO()
    book.save(buffer)
    return buffer.getvalue()


def dataset(id: str, title: str, file: str) -> dict[str, Any]:
    return {"title_en": title, "title_ms": "", "description_en": title, "frequency": "MONTHLY", "data_as_of": "2026-06", "link_parquet": STORAGE + file}


def release(publication: str, day: str) -> dict[str, Any]:
    period = publication[-7:]
    return {
        "publication": publication, "release_date": day,
        "en": {"title": f"[{period}] Labour Force", "description": "Monthly labour force report, covering statistics on unemployment.",
               "resources": [{"resource_type": "excel", "resource_link": f"{STORAGE}lfs_{period}.xlsx"},
                             {"resource_type": "pdf", "resource_link": f"{STORAGE}lfs_{period}_en.pdf"}]},
    }


def catalogue() -> bytes:
    return tarball({
        "data-catalogue/lfs_month.json": dataset("lfs_month", "Monthly Principal Labour Force Statistics", "lfs_month.parquet"),
        "data-catalogue/lfs_month_youth.json": dataset("lfs_month_youth", "Monthly Youth Unemployment", "lfs_month_youth.parquet"),
        "data-catalogue/monetary_aggregates.json": dataset("monetary_aggregates", "Monetary Aggregates", "money_aggregates.parquet"),
        "data-catalogue/domains.json": dataset("domains", "Domain Registrations", "domains.parquet"),
        "data-catalogue/cpi_headline.json": dataset("cpi_headline", "Consumer Price Index", "cpi_2d.parquet"),  # listed, never downloaded
        "data-catalogue/openapi/lfs_month.json": {"not": "a dataset"},
        "pub-dosm/publications/lfs_2026-08.json": release("labour_month_2026-08", "2026-10-09"),
        "pub-dosm/publications/lfs_2026-07.json": release("labour_month_2026-07", "2026-09-11"),
        "pub-dosm/publications/lfs_2026-06.json": release("labour_month_2026-06", "2026-08-11"),
        "pub-dosm/publications/lfs_2026-05.json": release("labour_month_2026-05", "2026-07-10"),  # older than the newest three, never downloaded
    })


def mynic(year: int, totals: dict[int, int]) -> bytes:
    return json.dumps({"year": str(year), "chartData": {str(m): totals.get(m) for m in range(1, 13)}}).encode()


def remote() -> dict[str, bytes]:
    lfs = {f"{STORAGE}lfs_{p}_en.pdf": pdf(f"LABOUR FORCE STATISTICS {p}", f"The unemployment rate for {rate} per cent. The youth unemployment rate for "
                                         f"those aged 15 to 24 years decreased by 0.1 percentage point to {youth} per cent, with 291.3 thousand unemployed persons.")
           for p, (rate, youth) in LFS_TEXT.items()}
    return {
        HEAD_URL: (COMMIT + "\n").encode(),
        TARBALL_URL.format(commit=COMMIT): catalogue(),
        STORAGE + "lfs_month.parquet": parquet([{"date": date(2026, m, 1), "u_rate": r} for m, r in ((6, 3.0), (7, 3.0), (8, 2.9))]),
        STORAGE + "lfs_month_youth.parquet": parquet([{"date": date(2026, m, 1), "u_rate_15_24": 10.2} for m in (5, 6)]),
        STORAGE + "money_aggregates.parquet": parquet([{"date": datetime(2026, 6, 1), "measure": m, "value": v} for m, v in (("m3_total", 2670359.957), ("m1_total", 742082.1))]),
        STORAGE + "domains.parquet": parquet([
            {"series": "cumulative", "date": date(2025, 1, 1), "domain": "overall", "registrations": 352717},
            {"series": "cumulative", "date": date(2025, 1, 1), "domain": ".my", "registrations": 189813},
            {"series": "new_net", "date": date(2025, 1, 1), "domain": "overall", "registrations": 10391},
        ]),
        **lfs,
        BNM_LISTING: f'<a href="https://www.bnm.gov.my/-/monthly-highlights-statistics-in-july-2026">July</a><a href="{EDITION}">Aug</a>'.encode(),
        EDITION: b'<a href="/documents/20124/999/1.3.xlsx">1.3</a><a href="/documents/20124/999/2.1.xlsx">2.1</a>',
        M3_TABLE: bnm_table(),
        MYNIC_URL.format(chart="active", year=2026): mynic(2026, {1: 821903, 8: 826384, 9: 693122}),
        MYNIC_URL.format(chart="active", year=2025): mynic(2025, {1: 352717, 12: 815000}),
    }


def serve(files: dict[str, bytes], asked: list[str] | None = None) -> Callable[[str], bytes]:
    """A stand-in for http_get. Asking for any URL the world does not hold fails the test."""
    def get(url: str) -> bytes:
        if asked is not None:
            asked.append(url)
        return files[url]
    return get


def take_snapshot(raw_dir: Path) -> dict[str, Any]:
    return freeze(raw_dir, STATS, TODAY, serve(remote()))
```

Create `analysis/tests/evallab/test_statistics.py`. The sentences are the real headline sentences from the newest releases on 2026-10-15, so a pattern that drifts from DOSM's wording fails here, offline:

```python
import re
from datetime import date

import pytest

from evallab.statistics import STATISTICS, period_of

# Headline sentences from the real releases, checked on 2026-10-15 (whitespace collapsed as pdf_pages does), with the figure each pattern must find.
REAL_SENTENCES = {
    "cpi_inflation": ("Malaysia's inflation increased 1.9 per cent in August 2026 as compared to 1.8 per cent in the previous month", "1.9"),
    "cpi_index": ("with the index points increased to 137.5 from 134.9 (August 2025)", "137.5"),
    "unemployment_rate": ("The unemployment rate for August 2026 eased to 2.9 per cent", "2.9"),
    "unemployed_persons": ("The number of unemployed in August 2026 declined by 8.7 thousand persons (-1.7%) to 511.6 thousand persons, compared to", "511.6"),
    "employed_persons": ("the number of employed persons grew modestly by 0.2 per cent (+28.8 thousand persons) to 16.87 million persons, up from", "16.87"),
    "lfpr": ("The labour force participation rate (LFPR) edged up by 0.1 percentage point to 71.0 per cent (July 2026: 70.9%)", "71.0"),
    "youth_rate_15_24": ("The youth unemployment rate for those aged 15 to 24 years decreased by 0.1 percentage point to 10.1 per cent, with 291.3 thousand unemployed persons", "10.1"),
    "youth_unemployed_15_24": ("The youth unemployment rate for those aged 15 to 24 years decreased by 0.1 percentage point to 10.1 per cent, with 291.3 thousand unemployed persons", "291.3"),
    "youth_rate_15_30": ("the unemployment rate among youth aged 15 to 30 years also decreased by 0.1 percentage point to 6.3 per cent, corresponding to 394.6 thousand", "6.3"),
    "youth_unemployed_15_30": ("the unemployment rate among youth aged 15 to 30 years also decreased by 0.1 percentage point to 6.3 per cent, corresponding to 394.6 thousand", "394.6"),
    "exports": ("Malaysia's exports surged by 45.5 per cent y-o-y to RM191.0 billion in August 2026.", "191.0"),
    "imports": ("Imports recorded double-digit growth of 41.1 per cent or RM47.5 billion, rising from RM115.5 billion to RM163.0 billion in August 2026.", "163.0"),
    "ipi_growth": ("The Industrial Production Index (IPI) increased by 5.0 per cent year-on-year in August 2026", "5.0"),
    "ppi_growth": ("Malaysia's Producer Price Index increased by 10.7 per cent in August 2026", "10.7"),
    "wrt_sales": ("Wholesale & retail trade sales value recorded RM173.0 billion in August 2026", "173.0"),
    "leading_index": ("The annual growth of the LI increased by 1.1 per cent in July 2026, recording 115.3 points compared to 114.0 points", "115.3"),
    "coincident_index": ("the CI recorded a year-on-year growth of 1.7 per cent to reach 131.5 points in July 2026", "131.5"),
    "gdp_growth": ("in the second quarter of 2026, expanding by 6.0 per cent as compared to 5.4 per cent in the preceding quarter", "6.0"),
    "fdi_net": ("Foreign Direct Investment (FDI) registered a lower net inflow of RM7.4 billion in the second quarter of 2026", "7.4"),
    "current_account": ("Malaysia's Current Account Balance (CAB) recorded a surplus of RM10.8 billion in the second quarter of 2026", "10.8"),
    "productivity_hour": ("recorded a growth of 5.5 per cent with value RM46.5 per hour compared to the preceding quarter", "46.5"),
}


def test_there_are_thirty_statistics_from_three_agencies() -> None:
    assert len(STATISTICS) == 30
    assert len({s.id for s in STATISTICS}) == 30
    assert {a: sum(s.agency == a for s in STATISTICS) for a in ("DOSM", "BNM", "MYNIC")} == {"DOSM": 21, "BNM": 6, "MYNIC": 3}


@pytest.mark.parametrize("statistic", [s for s in STATISTICS if s.agency == "DOSM"], ids=lambda s: s.id)
def test_each_dosm_pattern_finds_its_headline_figure(statistic) -> None:
    sentence, figure = REAL_SENTENCES[statistic.id]
    match = re.search(statistic.pattern, sentence)
    assert match is not None and match["value"] == figure


def test_bnm_and_mynic_name_a_table_column_or_a_chart() -> None:
    assert all(re.fullmatch(r"\d\.\d:\d+", s.release) and s.release_scale > 0 for s in STATISTICS if s.agency == "BNM")
    assert {s.release for s in STATISTICS if s.agency == "MYNIC"} == {"active", "ipv6", "dnssec"}


def test_periods_are_months_or_quarters() -> None:
    assert period_of(date(2026, 8, 1), quarterly=False) == "2026-08"
    assert period_of(date(2026, 4, 1), quarterly=True) == "2026-Q2"
    assert period_of(date(2026, 12, 1), quarterly=True) == "2026-Q4"
```

Create `analysis/tests/evallab/test_snapshot.py`:

```python
import json
from pathlib import Path

import pytest

from evallab.snapshot import freeze
from evallab.sources import bnm_latest, dosm_period, latest_edition, mynic_points
from forecasting.data import sha256_of

from .world import COMMIT, STATS, TODAY, remote, serve, take_snapshot


def test_a_snapshot_records_every_file_and_release(tmp_path: Path) -> None:
    asked: list[str] = []
    snapshot = freeze(tmp_path, STATS, TODAY, serve(remote(), asked))

    assert snapshot["taken"] == "2026-10-15"
    assert snapshot["catalogue"] == {"repository": "data-gov-my/datagovmy-meta", "commit": COMMIT}
    assert all(sha256_of(tmp_path / f["path"]) == f["sha256"] and f["bytes"] == (tmp_path / f["path"]).stat().st_size for f in snapshot["files"])
    assert {f["path"] for f in snapshot["files"] if f["path"].startswith("datasets/")} == {
        "datasets/domains.parquet", "datasets/lfs_month.parquet", "datasets/lfs_month_youth.parquet", "datasets/monetary_aggregates.parquet"}
    assert [r["id"] for r in snapshot["releases"]] == [
        "labour_month_2026-08", "labour_month_2026-07", "labour_month_2026-06", "bnm_mhs_2026-08_table_1.3", "mynic_active_2026", "mynic_active_2025"]
    assert not any("2026-05" in url or url.endswith("2.1.xlsx") for url in asked)  # only the newest three releases, only the tables used
    assert not list(tmp_path.rglob("*.part"))


def test_release_text_is_kept_page_by_page(tmp_path: Path) -> None:
    snapshot = take_snapshot(tmp_path)
    august = next(r for r in snapshot["releases"] if r["id"] == "labour_month_2026-08")
    pages = json.loads((tmp_path / august["pages"]).read_text())
    assert august["period"] == "2026-08" and august["page"] == "https://open.dosm.gov.my/publications/labour_month_2026-08"
    assert len(pages) == 2 and "The unemployment rate for August 2026 eased to 2.9 per cent." in pages[1]


def test_bnm_uses_the_newest_edition_and_the_year_on_january_rows(tmp_path: Path) -> None:
    snapshot = take_snapshot(tmp_path)
    table = next(r for r in snapshot["releases"] if r["agency"] == "BNM")
    assert table["page"].endswith("august-2026-1") and table["url"] == "https://www.bnm.gov.my/documents/20124/999/1.3.xlsx"
    assert bnm_latest(tmp_path / table["raw"], 3) == (2636548.767, "2026-08")
    text = json.loads((tmp_path / table["pages"]).read_text())[0]
    assert "Source: Bank Negara Malaysia." in text and "2026-08: money supply M3 2,636,548.7670" in text


def test_a_second_freeze_reads_only_the_disk(tmp_path: Path) -> None:
    first = take_snapshot(tmp_path)
    assert freeze(tmp_path, STATS, TODAY, serve({})) == first  # serve({}) fails on any request


def test_a_changed_file_stops_the_run(tmp_path: Path) -> None:
    take_snapshot(tmp_path)
    (tmp_path / "datasets/lfs_month.parquet").write_bytes(b"edited")
    with pytest.raises(ValueError, match="datasets/lfs_month.parquet changed"):
        freeze(tmp_path, STATS, TODAY, serve({}))


def test_a_commit_that_is_not_a_sha_stops_the_snapshot(tmp_path: Path) -> None:
    files = {**remote(), "https://api.github.com/repos/data-gov-my/datagovmy-meta/commits/HEAD": b'{"message": "API rate limit exceeded"}'}
    with pytest.raises(ValueError, match="unexpected commit"):
        freeze(tmp_path, STATS, TODAY, serve(files))
    assert not (tmp_path / "snapshot.json").exists()


def test_release_periods_come_from_the_release_id() -> None:
    assert dosm_period("labour_month_2026-08") == "2026-08"
    assert dosm_period("bop_2026-q2") == "2026-Q2"
    with pytest.raises(ValueError, match="cannot tell the period"):
        dosm_period("tourism_2025")


def test_the_newest_bnm_edition_wins_whatever_the_link_order() -> None:
    html = ('<a href="https://www.bnm.gov.my/-/monthly-highlights-statistics-in-august-2026-1"></a>'
            '<a href="https://www.bnm.gov.my/-/monthly-highlights-statistics-in-december-2025"></a>'
            '<a href="https://www.bnm.gov.my/-/monthly-highlights-statistics-in-september-2026"></a>')
    assert latest_edition(html) == ("https://www.bnm.gov.my/-/monthly-highlights-statistics-in-september-2026", "2026-09")
    with pytest.raises(ValueError, match="no Monthly Highlights"):
        latest_edition("<html></html>")


def test_mynic_months_without_data_are_left_out(tmp_path: Path) -> None:
    path = tmp_path / "mynic.json"
    path.write_text(json.dumps({"year": "2026", "chartData": {"10": None, "9": 693122, "1": 821903, "2": None}}))
    assert mynic_points(path) == [("2026-01", 821903), ("2026-09", 693122)]
```

- [ ] **Step 3: Run the tests to verify they fail**

Run (in `analysis/`): `uv run pytest tests/evallab`
Expected: FAIL with `ModuleNotFoundError: No module named 'evallab.snapshot'` (from `test_snapshot.py`) and `No module named 'evallab.statistics'` (from `test_statistics.py`).

- [ ] **Step 4: Write the statistics**

Each DOSM pattern was matched against the newest release on 2026-10-15. Units are the statistic's own; `Series.scale` turns the dataset's unit into it (for example trade values in RM to RM billion), and `release_scale` does the same for a BNM table in RM million.

Create `analysis/evallab/statistics.py`:

```python
"""The statistics the study asks about: where each one's open dataset lives and where its latest official figure is published."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

NUMBER = r"(?P<value>-?\d[\d,]*(?:\.\d+)?)"  # a figure in release text, commas allowed


@dataclass(frozen=True)
class Series:
    """Where data.gov.my keeps a statistic: one column of one dataset, filtered to one series."""

    dataset: str  # data.gov.my catalogue id
    column: str
    where: tuple[tuple[str, str], ...] = ()  # (column, value) pairs every row must match
    scale: float = 1.0  # dataset value times scale is the statistic in its own unit


@dataclass(frozen=True)
class Statistic:
    id: str
    agency: str  # "DOSM", "BNM" or "MYNIC"
    name_en: str
    name_ms: str
    unit: str
    decimals: int  # the publication's rounding
    quarterly: bool
    series: Series
    release: str  # DOSM: regex over release ids; BNM: "<table>:<column index>"; MYNIC: the statistics chart type
    pattern: str = ""  # DOSM: regex with a `value` group, searched in the release's English text
    release_scale: float = 1.0  # BNM: table value times release_scale is the statistic in its own unit


def _dosm(id: str, en: str, ms: str, unit: str, decimals: int, series: Series, release: str, pattern: str, quarterly: bool = False) -> Statistic:
    return Statistic(id, "DOSM", en, ms, unit, decimals, quarterly, series, release, pattern.replace("{N}", NUMBER))


def _bnm(id: str, en: str, ms: str, unit: str, decimals: int, series: Series, release: str, release_scale: float = 1.0) -> Statistic:
    return Statistic(id, "BNM", en, ms, unit, decimals, False, series, release, release_scale=release_scale)


def _mynic(id: str, en: str, ms: str, dataset: str, chart: str) -> Statistic:
    return Statistic(id, "MYNIC", en, ms, "domains", 0, False, Series(dataset, "registrations", (("series", "cumulative"), ("domain", "overall"))), chart)


LFS = r"^labour_month_\d{4}-\d{2}$"
TRADE = r"^trade_(?:headline_)?\d{4}-\d{2}$"
MEI = r"^mei_\d{4}-\d{2}$"
BOP = r"^bop_\d{4}-q\d$"
YOUTH = "lfs_month_youth"
COMMERCIAL = ("bank", "commercial")

STATISTICS: tuple[Statistic, ...] = (
    _dosm("cpi_inflation", "consumer price inflation (year on year)", "kadar inflasi harga pengguna (tahun ke tahun)", "per cent", 1,
          Series("cpi_headline_inflation", "inflation_yoy", (("division", "overall"),)), r"^cpi_\d{4}-\d{2}$",
          r"[Ii]nflation (?:increased|decreased|rose|fell|eased|remained|was|stood at|moderated)(?: by| at| to)? {N} per cent in"),
    _dosm("cpi_index", "consumer price index", "indeks harga pengguna", "index points", 1,
          Series("cpi_headline", "index", (("division", "overall"),)), r"^cpi_\d{4}-\d{2}$", r"index points (?:\w+ )?(?:to|at) {N}"),
    _dosm("unemployment_rate", "unemployment rate", "kadar pengangguran", "per cent", 1, Series("lfs_month", "u_rate"), LFS,
          r"[Uu]nemployment rate for \w+ \d{4} (?:\w+ ){1,3}{N} per cent"),
    _dosm("unemployed_persons", "number of unemployed persons", "bilangan penganggur", "thousand persons", 1, Series("lfs_month", "lf_unemployed"), LFS,
          r"number of unemployed in \w+ \d{4} .{0,80}?to {N} thousand persons"),
    _dosm("employed_persons", "number of employed persons", "bilangan penduduk bekerja", "million persons", 2, Series("lfs_month", "lf_employed", scale=0.001), LFS,
          r"number of employed persons .{0,80}?to {N} million persons"),
    _dosm("lfpr", "labour force participation rate", "kadar penyertaan tenaga buruh", "per cent", 1, Series("lfs_month", "p_rate"), LFS,
          r"participation rate \(LFPR\) .{0,60}?to {N} per cent"),
    _dosm("youth_rate_15_24", "youth unemployment rate for ages 15 to 24", "kadar pengangguran belia berumur 15 hingga 24 tahun", "per cent", 1,
          Series(YOUTH, "u_rate_15_24"), LFS, r"youth unemployment rate for those aged 15 to 24 years .{0,60}?to {N} per cent"),
    _dosm("youth_unemployed_15_24", "number of unemployed youth aged 15 to 24", "bilangan belia menganggur berumur 15 hingga 24 tahun", "thousand persons", 1,
          Series(YOUTH, "unemployed_15_24"), LFS, r"youth unemployment rate for those aged 15 to 24 years .{0,80}?with {N} thousand unemployed"),
    _dosm("youth_rate_15_30", "youth unemployment rate for ages 15 to 30", "kadar pengangguran belia berumur 15 hingga 30 tahun", "per cent", 1,
          Series(YOUTH, "u_rate_15_30"), LFS, r"unemployment rate among youth aged 15 to 30 years .{0,60}?to {N} per cent"),
    _dosm("youth_unemployed_15_30", "number of unemployed youth aged 15 to 30", "bilangan belia menganggur berumur 15 hingga 30 tahun", "thousand persons", 1,
          Series(YOUTH, "unemployed_15_30"), LFS, r"unemployment rate among youth aged 15 to 30 years .{0,120}?{N} thousand"),
    _dosm("exports", "value of exports for the month", "nilai eksport bulanan", "RM billion", 1,
          Series("trade_sitc_1d", "exports", (("section", "overall"),), scale=1e-9), TRADE, r"[Ee]xports .{0,60}?to RM{N} billion in \w+ \d{4}"),
    _dosm("imports", "value of imports for the month", "nilai import bulanan", "RM billion", 1,
          Series("trade_sitc_1d", "imports", (("section", "overall"),), scale=1e-9), TRADE, r"Imports .{0,140}?to RM{N} billion in \w+ \d{4}"),
    _dosm("ipi_growth", "industrial production index growth (year on year)", "pertumbuhan indeks pengeluaran perindustrian (tahun ke tahun)", "per cent", 1,
          Series("ipi", "index", (("series", "growth_yoy"),)), r"^ipi_\d{4}-\d{2}$",
          r"Industrial Production Index \(IPI\) (?:increased|decreased|rose|fell|grew|declined|contracted) by {N} per cent year-on-year"),
    _dosm("ppi_growth", "producer price index growth (year on year)", "pertumbuhan indeks harga pengeluar (tahun ke tahun)", "per cent", 1,
          Series("ppi", "index", (("series", "growth_yoy"),)), r"^ppi_\d{4}-\d{2}$",
          r"Producer Price Index (?:increased|decreased|rose|fell|declined) by {N} per cent"),
    _dosm("wrt_sales", "wholesale and retail trade sales value for the month", "nilai jualan perdagangan borong dan runcit bulanan", "RM billion", 1,
          Series("iowrt", "sales", (("series", "abs"),), scale=1e-3), r"^iowrt_\d{4}-\d{2}$", r"[Ww]holesale & retail trade sales value recorded RM{N} billion"),
    _dosm("leading_index", "leading index", "indeks pelopor", "index points", 1, Series("economic_indicators", "leading"), MEI,
          r"LI (?:increased|decreased|rose|fell|declined) by -?\d+(?:\.\d+)? per cent in \w+ \d{4}, recording {N} points"),
    _dosm("coincident_index", "coincident index", "indeks serentak", "index points", 1, Series("economic_indicators", "coincident"), MEI,
          r"the CI recorded .{0,80}?to reach {N} points"),
    _dosm("gdp_growth", "GDP growth (year on year)", "pertumbuhan KDNK (tahun ke tahun)", "per cent", 1,
          Series("gdp_qtr_real", "value", (("series", "growth_yoy"),)), r"^gdp_\d{4}-q\d$", r"quarter of \d{4}, expanding by {N} per cent", quarterly=True),
    _dosm("fdi_net", "net foreign direct investment inflow for the quarter", "aliran masuk bersih pelaburan langsung asing bagi suku tahun", "RM billion", 1,
          Series("fdi_flows", "net"), BOP, r"Foreign Direct Investment \(FDI\) .{0,40}?net inflow of RM{N} billion", quarterly=True),
    _dosm("current_account", "current account balance for the quarter", "imbangan akaun semasa bagi suku tahun", "RM billion", 1,
          Series("bop_balance", "balance", (("account", "ca"),), scale=1e-3), BOP,
          r"Current Account Balance \(CAB\) recorded a (?:surplus|deficit) of RM{N} billion", quarterly=True),
    _dosm("productivity_hour", "labour productivity as value added per hour worked", "produktiviti buruh sebagai nilai ditambah per jam bekerja", "RM per hour", 1,
          Series("productivity_qtr", "output_hour", (("series", "abs"), ("sector", "p0"))), r"^productivity_\d{4}-q\d$", r"value RM{N} per hour", quarterly=True),
    _bnm("m3", "money supply M3", "penawaran wang M3", "RM billion", 1, Series("monetary_aggregates", "value", (("measure", "m3_total"),), scale=1e-3), "1.3:3", 1e-3),
    _bnm("m1", "money supply M1", "penawaran wang M1", "RM billion", 1, Series("monetary_aggregates", "value", (("measure", "m1_total"),), scale=1e-3), "1.3:5", 1e-3),
    _bnm("fd_12mo", "12-month fixed deposit rate at commercial banks", "kadar deposit tetap 12 bulan di bank perdagangan", "per cent", 2,
         Series("interestrates", "value", (COMMERCIAL, ("rate", "fdr_12mo"))), "2.1:7"),
    _bnm("base_rate", "base rate of commercial banks", "kadar asas bank perdagangan", "per cent", 2, Series("interestrates", "value", (COMMERCIAL, ("rate", "br"))), "2.1:15"),
    _bnm("blr", "base lending rate of commercial banks", "kadar pinjaman asas bank perdagangan", "per cent", 2, Series("interestrates", "value", (COMMERCIAL, ("rate", "blr"))), "2.1:17"),
    _bnm("alr", "average lending rate of commercial banks", "kadar pinjaman purata bank perdagangan", "per cent", 2, Series("interestrates", "value", (COMMERCIAL, ("rate", "alr"))), "2.1:19"),
    _mynic("domains_active", "number of active .my domains", "bilangan domain .my yang aktif", "domains", "active"),
    _mynic("domains_ipv6", "number of .my domains with IPv6", "bilangan domain .my dengan IPv6", "domains_ipv6", "ipv6"),
    _mynic("domains_dnssec", "number of .my domains signed with DNSSEC", "bilangan domain .my yang ditandatangani dengan DNSSEC", "domains_dnssec", "dnssec"),
)


def period_of(day: date, quarterly: bool) -> str:
    """The period a dataset row covers: 2026-08 for a month, 2026-Q2 for a quarter."""
    return f"{day.year}-Q{(day.month - 1) // 3 + 1}" if quarterly else f"{day.year}-{day.month:02d}"


def find(statistic_id: str) -> Statistic:
    return next(s for s in STATISTICS if s.id == statistic_id)
```

- [ ] **Step 5: Write the readers**

BNM prints the year only on each January row and the month on every row, so `bnm_rows` carries the year down. The BNM column indices in `STATISTICS` were read from the August 2026 tables: in 1.3, column 3 is M3 and column 5 is M1 (RM million); in 2.1, columns 7, 15, 17 and 19 are the commercial banks' 12-month fixed deposit, base, base lending and average lending rates. MYNIC's `chartData` maps month numbers to totals, with `null` for months still to come.

Create `analysis/evallab/sources.py`:

```python
"""Reading each publisher's files once they are on disk: release periods, PDF pages, BNM tables and MYNIC charts. No network."""

from __future__ import annotations

import json
import re
from pathlib import Path

import openpyxl
import pymupdf

MONTHS = ("january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december")
BNM_EDITION = re.compile(r"https://www\.bnm\.gov\.my/-/monthly-highlights-statistics-in-([a-z]+)-(\d{4})(?:-\d+)?")
BNM_ROWS_IN_TEXT = 24  # months of each table written into the release text


def dosm_period(release_id: str) -> str:
    """The period a DOSM release covers, from its id: labour_month_2026-08 is 2026-08, bop_2026-q2 is 2026-Q2."""
    month = re.search(r"(\d{4})-(\d{2})$", release_id)
    if month:
        return f"{month[1]}-{month[2]}"
    quarter = re.search(r"(\d{4})-q([1-4])$", release_id)
    if quarter:
        return f"{quarter[1]}-Q{quarter[2]}"
    raise ValueError(f"cannot tell the period of release {release_id!r}")


def pdf_pages(path: Path) -> list[str]:
    """The text of every page, with runs of whitespace collapsed to one space."""
    with pymupdf.open(path) as doc:
        return [re.sub(r"\s+", " ", page.get_text()).strip() for page in doc]


def latest_edition(listing_html: str) -> tuple[str, str]:
    """The newest Monthly Highlights and Statistics edition linked from BNM's listing page: its URL and period."""
    editions = {}
    for match in BNM_EDITION.finditer(listing_html):
        month, year = match[1], match[2]
        if month in MONTHS:
            editions[f"{year}-{MONTHS.index(month) + 1:02d}"] = match[0]
    if not editions:
        raise ValueError("no Monthly Highlights and Statistics edition found on the BNM listing page")
    period = max(editions)
    return editions[period], period


def table_link(edition_html: str, table: str) -> str:
    """The XLSX link for one numbered table on an edition page, such as 1.3."""
    match = re.search(rf"/documents/20124/\d+/{re.escape(table)}\.xlsx", edition_html)
    if match is None:
        raise ValueError(f"table {table} not found on the BNM edition page")
    return "https://www.bnm.gov.my" + match[0]


def bnm_rows(path: Path) -> tuple[str, list[tuple[str, tuple[object, ...]]]]:
    """A BNM table's English title and its monthly rows as (YYYY-MM, cells). The year is printed only on January rows."""
    book = openpyxl.load_workbook(path, read_only=True, data_only=True)
    try:
        cells = list(book.worksheets[0].iter_rows(values_only=True))
    finally:
        book.close()
    title = str(cells[1][2]).strip()
    rows, year = [], None
    for row in cells:
        if len(row) > 1 and isinstance(row[1], int) and 1 <= row[1] <= 12:
            year = row[0] if isinstance(row[0], int) else year
            if year is not None:
                rows.append((f"{year}-{row[1]:02d}", row))
    return title, rows


def bnm_latest(path: Path, column: int) -> tuple[float, str] | None:
    """The newest month with a number in this column, as (value, YYYY-MM)."""
    _, rows = bnm_rows(path)
    found = [(float(row[column]), period) for period, row in rows if isinstance(row[column], int | float)]
    return found[-1] if found else None


def bnm_text(path: Path, table: str, columns: dict[int, str]) -> str:
    """The release text for a BNM table: its title and the named columns for the last BNM_ROWS_IN_TEXT months."""
    title, rows = bnm_rows(path)
    lines = [f"Bank Negara Malaysia, Monthly Highlights and Statistics, table {table}: {title}. Source: Bank Negara Malaysia."]
    for period, row in rows[-BNM_ROWS_IN_TEXT:]:
        values = [f"{name} {row[i]:,.4f}" for i, name in sorted(columns.items()) if isinstance(row[i], int | float)]
        lines.append(f"{period}: " + "; ".join(values))
    return "\n".join(lines)


def mynic_points(path: Path) -> list[tuple[str, int]]:
    """Monthly totals from one MYNIC statistics response, as (YYYY-MM, total), months without data left out."""
    data = json.loads(path.read_text())
    year = int(data["year"])
    return [(f"{year}-{int(month):02d}", int(total)) for month, total in sorted(data["chartData"].items(), key=lambda kv: int(kv[0])) if total is not None]


def mynic_text(path: Path, chart: str) -> str:
    lines = [f"MYNIC domain statistics, {chart} domains: monthly totals for all .my domains. Source: MYNIC."]
    lines += [f"{period}: {total:,} domains" for period, total in mynic_points(path)]
    return "\n".join(lines)
```

- [ ] **Step 6: Write the snapshot**

The catalogue comes from the `datagovmy-meta` repository as one tarball at the commit GitHub reports for `HEAD` that day (the data.gov.my API has no list endpoint and allows 4 requests a minute). Datasets come from the parquet links in the catalogue; DOSM releases from the release index in the same tarball, the newest three per series, English PDF; BNM from the newest Monthly Highlights and Statistics edition; MYNIC from its statistics endpoint for this year and last. Every file is written through a `.part` file, so an interrupted download never looks complete, and `snapshot.json` is written last.

Create `analysis/evallab/snapshot.py`:

```python
"""Take the study's snapshot once: catalogue, datasets, DOSM releases, BNM tables and MYNIC charts, each with its checksum.

Later runs only verify the files against snapshot.json, so every run after the first reads exactly the same bytes.
"""

from __future__ import annotations

import json
import logging
import re
import tarfile
import time
import urllib.request
from collections.abc import Callable, Iterable
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

from forecasting.data import sha256_of

from .sources import bnm_text, dosm_period, latest_edition, mynic_text, pdf_pages, table_link
from .statistics import Statistic

log = logging.getLogger(__name__)

Get = Callable[[str], bytes]

USER_AGENT = "observatory-analysis/0.1 (LLM Eval Lab study)"
POLITE_SECONDS = 0.5  # pause before every request
REPO = "data-gov-my/datagovmy-meta"
HEAD_URL = f"https://api.github.com/repos/{REPO}/commits/HEAD"
TARBALL_URL = "https://codeload.github.com/" + REPO + "/tar.gz/{commit}"
BNM_LISTING = "https://www.bnm.gov.my/publications/mhs"
MYNIC_URL = "https://mynic.my/ajax/statistics?type={chart}&year={year}"
MYNIC_PAGE = "https://mynic.my/media/statistics"
OPENDOSM_PAGE = "https://open.dosm.gov.my/publications/{id}"
RELEASES_PER_SERIES = 3  # the newest DOSM releases kept for each release series
SNAPSHOT = "snapshot.json"


def http_get(url: str) -> bytes:
    time.sleep(POLITE_SECONDS)
    headers = {"User-Agent": USER_AGENT}
    if url == HEAD_URL:
        headers["Accept"] = "application/vnd.github.sha"  # the commit SHA as plain text
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=300) as response:
        return response.read()


def now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


class Freezer:
    """Writes files into the raw directory and remembers what each one is, for snapshot.json."""

    def __init__(self, raw_dir: Path, get: Get) -> None:
        self.raw_dir, self.get, self.files = raw_dir, get, []

    def fetch(self, url: str, name: str) -> Path:
        log.info("fetching %s", url)
        return self.save(name, self.get(url), url)

    def save(self, name: str, data: bytes, url: str | None) -> Path:
        path = self.raw_dir / name
        path.parent.mkdir(parents=True, exist_ok=True)
        partial = path.with_name(path.name + ".part")
        partial.write_bytes(data)
        partial.replace(path)
        self.files.append({"path": name, "url": url, "retrieved": now(), "bytes": len(data), "sha256": sha256_of(path)})
        return path

    def pages(self, release_id: str, pages: list[str]) -> str:
        name = f"releases/{release_id}.pages.json"
        self.save(name, json.dumps(pages, ensure_ascii=False, indent=0).encode(), None)
        return name


def read_catalogue(tarball: Path) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    """Dataset metadata by id, and every DOSM release record, from the metadata repository's tarball."""
    datasets, releases = {}, []
    with tarfile.open(tarball) as archive:
        for member in archive.getmembers():
            parts = member.name.split("/")
            if not member.isfile() or not member.name.endswith(".json"):
                continue
            if parts[1:2] == ["data-catalogue"] and len(parts) == 3:
                datasets[parts[2][:-5]] = json.load(archive.extractfile(member))
            elif parts[1:3] == ["pub-dosm", "publications"] and len(parts) == 4:
                releases.append(json.load(archive.extractfile(member)))
    return datasets, releases


def newest_releases(index: list[dict[str, Any]], pattern: str) -> list[dict[str, Any]]:
    chosen = [r for r in index if re.match(pattern, r["publication"])]
    if not chosen:
        raise ValueError(f"no DOSM release matches {pattern}")
    return sorted(chosen, key=lambda r: (r["release_date"], r["publication"]), reverse=True)[:RELEASES_PER_SERIES]


def english_pdf(record: dict[str, Any]) -> str:
    return next(r["resource_link"] for r in record["en"]["resources"] if r["resource_type"] == "pdf")


def freeze_dosm(f: Freezer, index: list[dict[str, Any]], patterns: Iterable[str]) -> list[dict[str, Any]]:
    entries = []
    for record in [r for p in sorted(set(patterns)) for r in newest_releases(index, p)]:
        rid, url = record["publication"], english_pdf(record)
        raw = f.fetch(url, f"releases/{rid}.pdf")
        entries.append({"id": rid, "agency": "DOSM", "title": record["en"]["title"], "date": record["release_date"], "period": dosm_period(rid),
                        "summary": record["en"].get("description", ""), "url": url, "page": OPENDOSM_PAGE.format(id=rid), "raw": str(raw.relative_to(f.raw_dir)), "pages": f.pages(rid, pdf_pages(raw))})
    return entries


def freeze_bnm(f: Freezer, statistics: list[Statistic]) -> list[dict[str, Any]]:
    edition_url, period = latest_edition(f.get(BNM_LISTING).decode())
    edition = f.get(edition_url).decode()
    entries = []
    for table in sorted({s.release.split(":")[0] for s in statistics}):
        columns = {int(s.release.split(":")[1]): s.name_en for s in statistics if s.release.startswith(table + ":")}
        rid, url = f"bnm_mhs_{period}_table_{table}", table_link(edition, table)
        raw = f.fetch(url, f"releases/{rid}.xlsx")
        title = f"Bank Negara Malaysia, Monthly Highlights and Statistics for {period}, table {table}"
        entries.append({"id": rid, "agency": "BNM", "title": title, "date": None, "period": period, "summary": "; ".join(columns.values()), "url": url, "page": edition_url,
                        "raw": str(raw.relative_to(f.raw_dir)), "pages": f.pages(rid, [bnm_text(raw, table, columns)])})
    return entries


def freeze_mynic(f: Freezer, statistics: list[Statistic], today: date) -> list[dict[str, Any]]:
    entries = []
    for chart in sorted({s.release for s in statistics}):
        summary = "; ".join(s.name_en for s in statistics if s.release == chart)
        for year in (today.year, today.year - 1):  # last year too, so January still has a latest month
            rid, url = f"mynic_{chart}_{year}", MYNIC_URL.format(chart=chart, year=year)
            raw = f.fetch(url, f"releases/{rid}.json")
            entries.append({"id": rid, "agency": "MYNIC", "title": f"MYNIC domain statistics, {chart} domains, {year}", "date": None, "period": str(year),
                            "summary": summary, "url": url, "page": MYNIC_PAGE, "raw": str(raw.relative_to(f.raw_dir)), "pages": f.pages(rid, [mynic_text(raw, chart)])})
    return entries


def take(raw_dir: Path, statistics: list[Statistic], today: date, get: Get) -> dict[str, Any]:
    f = Freezer(raw_dir, get)
    commit = get(HEAD_URL).decode().strip()
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ValueError(f"unexpected commit from GitHub: {commit[:80]!r}")
    tarball = f.fetch(TARBALL_URL.format(commit=commit), "catalogue.tar.gz")
    catalogue, index = read_catalogue(tarball)
    for dataset in sorted({s.series.dataset for s in statistics}):
        f.fetch(catalogue[dataset]["link_parquet"], f"datasets/{dataset}.parquet")
    by_agency = {a: [s for s in statistics if s.agency == a] for a in ("DOSM", "BNM", "MYNIC")}
    releases = freeze_dosm(f, index, [s.release for s in by_agency["DOSM"]])
    releases += freeze_bnm(f, by_agency["BNM"]) if by_agency["BNM"] else []
    releases += freeze_mynic(f, by_agency["MYNIC"], today) if by_agency["MYNIC"] else []
    return {"taken": today.isoformat(), "catalogue": {"repository": REPO, "commit": commit}, "files": f.files, "releases": releases}


def verify(raw_dir: Path) -> dict[str, Any]:
    """The frozen snapshot, after checking every file against its recorded SHA-256."""
    snapshot = json.loads((raw_dir / SNAPSHOT).read_text())
    for entry in snapshot["files"]:
        path = raw_dir / entry["path"]
        if not path.exists():
            raise ValueError(f"snapshot file {entry['path']} is missing")
        if sha256_of(path) != entry["sha256"]:
            raise ValueError(f"snapshot file {entry['path']} changed: SHA-256 differs from {entry['sha256']}")
    return snapshot


def freeze(raw_dir: Path, statistics: list[Statistic], today: date, get: Get = http_get) -> dict[str, Any]:
    """Take the snapshot unless one exists, then verify it. Only the first call touches the network."""
    if not (raw_dir / SNAPSHOT).exists():
        snapshot = take(raw_dir, statistics, today, get)
        (raw_dir / SNAPSHOT).write_text(json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n")
    return verify(raw_dir)
```

- [ ] **Step 7: Run the tests**

Run (in `analysis/`): `uv run pytest tests/evallab`, then `uv run pytest`.
Expected: `33 passed`, then `159 passed`.

- [ ] **Step 8: Commit**

```bash
git add analysis/pyproject.toml analysis/uv.lock analysis/evallab analysis/tests/evallab
git commit -m "feat: freeze the LLM Eval Lab snapshot with checksums"
```

---

### Task 4: Python: the frozen store, the four tools and the baseline

**Files:**
- Create: `analysis/evallab/store.py`, `analysis/evallab/tools.py`, `analysis/tests/evallab/conftest.py`
- Test: `analysis/tests/evallab/test_tools.py`

**Interfaces:**
- Consumes: `read_catalogue`, `verify`, `OPENDOSM_PAGE` (`evallab.snapshot`); `Series`, `Statistic`, `period_of` (`evallab.statistics`); `take_snapshot` (`tests/evallab/world.py`).
- Produces, in `evallab.store`: `Dataset(id, title, title_ms, description, frequency, data_as_of, url, in_snapshot)`; `Release(id, agency, title, date, period, summary, url, page, raw, pages)` (`raw` and `pages` are `None` for releases known only from the DOSM index); `Store(root, taken, commit, datasets, releases)` with `rows(dataset_id) -> list[dict]` (oldest first, `date` as `datetime.date`), `pages(release_id) -> list[str]` and `sources() -> frozenset[str]` (every dataset id and release URL an answer may cite); `load(root) -> Store` (verifies checksums first); `latest(store, series, quarterly) -> tuple[float, str] | None`.
- Produces, in `evallab.tools`: `search_datasets(store, query)`, `read_dataset(store, id, last_n=3)`, `search_releases(store, query, after=None)`, `read_release(store, id, page=1)`, each returning JSON-ready data or `{"error": ...}`; `TOOLS` (the four Ollama tool schemas, in that order); `call_tool(store, name, arguments) -> str` (JSON text, never raises for a bad call); `baseline_answer(store, statistic) -> str` (a final answer as JSON text: the dataset's newest value rounded to the statistic's decimals, its unit, period and dataset id; raises `ValueError` when the dataset has no value). Task 5 drafts from `latest`; Task 7 calls `TOOLS` and `call_tool`; Task 9 scores `baseline_answer` and checks sources with `Store.sources()`.
- Produces, in `tests/evallab/conftest.py`: the session fixture `store`.

Tool results are what the model sees, so they are small: at most 8 search results, 12 dates of dataset rows (120 rows at most) and 6,000 characters of a release page. `search_releases` returns, for each release with text, the pages whose words match the query best, so a model can open the headline page of a 155-page release instead of guessing.

- [ ] **Step 1: Write the failing tests**

Create `analysis/tests/evallab/conftest.py`:

```python
from pathlib import Path

import pytest

from evallab.store import Store, load

from .world import take_snapshot


@pytest.fixture(scope="session")
def store(tmp_path_factory: pytest.TempPathFactory) -> Store:
    """The synthetic snapshot, taken once and shared by every test that only reads it."""
    root: Path = tmp_path_factory.mktemp("snapshot")
    take_snapshot(root)
    return load(root)
```

Create `analysis/tests/evallab/test_tools.py`:

```python
import json

import pytest

from evallab.statistics import STATISTICS
from evallab.store import Store, latest
from evallab.tools import TOOLS, baseline_answer, call_tool, read_dataset, read_release, search_datasets, search_releases

BY_ID = {s.id: s for s in STATISTICS}


def test_the_store_lists_the_whole_catalogue_and_marks_what_was_downloaded(store: Store) -> None:
    assert store.taken == "2026-10-15"
    assert store.datasets["lfs_month_youth"].in_snapshot and not store.datasets["cpi_headline"].in_snapshot
    assert store.releases["labour_month_2026-05"].pages is None and store.releases["labour_month_2026-08"].pages is not None


@pytest.mark.parametrize(("statistic", "expected"), [
    ("youth_rate_15_24", (10.2, "2026-06")),
    ("m3", (pytest.approx(2670.359957), "2026-06")),  # timestamp dates, scaled from RM million to RM billion
    ("domains_active", (352717.0, "2025-01")),  # the overall cumulative row, not .my alone or the net new count
])
def test_latest_reads_the_newest_value_of_one_series(store: Store, statistic: str, expected: tuple) -> None:
    s = BY_ID[statistic]
    assert latest(store, s.series, s.quarterly) == expected


def test_search_datasets_ranks_by_matching_words(store: Store) -> None:
    found = search_datasets(store, "youth unemployment")
    assert found[0] == {"id": "lfs_month_youth", "title": "Monthly Youth Unemployment", "frequency": "MONTHLY", "data_as_of": "2026-06", "in_snapshot": True}
    assert search_datasets(store, "the latest") == []  # only stop words


def test_read_dataset_returns_the_newest_dates(store: Store) -> None:
    newest = read_dataset(store, "lfs_month", 1)
    assert newest["rows"] == [{"date": "2026-08-01", "u_rate": 2.9}] and newest["columns"] == ["date", "u_rate"]
    assert len(read_dataset(store, "lfs_month", "two")["rows"]) == 3  # an unreadable count falls back to 3
    assert "not in this snapshot" in read_dataset(store, "cpi_headline")["error"]
    assert "no dataset" in read_dataset(store, "nope")["error"]


def test_search_releases_puts_the_newest_matching_release_first(store: Store) -> None:
    found = search_releases(store, "labour force unemployment rate")
    assert [r["id"] for r in found[:4]] == ["labour_month_2026-08", "labour_month_2026-07", "labour_month_2026-06", "labour_month_2026-05"]
    assert found[3]["in_snapshot"] is False
    assert search_releases(store, "youth unemployment rate")[0]["matching_pages"] == [2]
    assert [r["id"] for r in search_releases(store, "labour force", after="2026-09-01")] == ["labour_month_2026-08", "labour_month_2026-07"]
    assert search_releases(store, "money supply M3")[0]["id"] == "bnm_mhs_2026-08_table_1.3"
    assert [r["id"] for r in search_releases(store, "active .my domains")] == ["mynic_active_2026", "mynic_active_2025"]  # undated: newest year first
    assert "YYYY-MM-DD" in search_releases(store, "labour", after="last month")["error"]


def test_read_release_returns_one_page(store: Store) -> None:
    page = read_release(store, "labour_month_2026-08", 2)
    assert page["pages"] == 2 and "eased to 2.9 per cent" in page["text"] and page["url"].endswith("lfs_2026-08_en.pdf")
    assert read_release(store, "labour_month_2026-08", 3)["error"] == "page must be from 1 to 2"
    assert "not in this snapshot" in read_release(store, "labour_month_2026-05")["error"]


def test_call_tool_turns_bad_calls_into_errors_the_model_can_read(store: Store) -> None:
    assert json.loads(call_tool(store, "read_release", {"id": "mynic_active_2026"}))["text"].startswith("MYNIC domain statistics")
    assert json.loads(call_tool(store, "delete_everything", {})) == {"error": "unknown tool 'delete_everything'"}
    assert "bad arguments for search_datasets" in json.loads(call_tool(store, "search_datasets", {"q": "cpi"}))["error"]
    assert "bad arguments" in json.loads(call_tool(store, "read_dataset", "lfs_month"))["error"]
    assert [t["function"]["name"] for t in TOOLS] == ["search_datasets", "read_dataset", "search_releases", "read_release"]


def test_the_baseline_trusts_the_open_dataset(store: Store) -> None:
    assert json.loads(baseline_answer(store, BY_ID["youth_rate_15_24"])) == {"value": 10.2, "unit": "per cent", "period": "2026-06", "source": "lfs_month_youth"}
    assert json.loads(baseline_answer(store, BY_ID["m3"]))["value"] == 2670.4


def test_an_answer_may_cite_any_dataset_or_release_in_the_snapshot(store: Store) -> None:
    sources = store.sources()
    assert {"lfs_month_youth", "https://open.dosm.gov.my/publications/labour_month_2026-08", "https://www.bnm.gov.my/documents/20124/999/1.3.xlsx"} <= sources
    assert "cpi_headline" not in sources and "https://open.dosm.gov.my/publications/labour_month_2026-05" not in sources
```

- [ ] **Step 2: Run the tests to verify they fail**

Run (in `analysis/`): `uv run pytest tests/evallab/test_tools.py`
Expected: FAIL with `ImportError while loading conftest` and `ModuleNotFoundError: No module named 'evallab.store'`.

- [ ] **Step 3: Write the store**

Parquet dates arrive as `date32` in some files and `timestamp[ns]` in others (checked on 2026-10-15: `lfs_month` and `fdi_flows` use dates, `cpi_2d` and `ipi` use timestamps), so `read_rows` turns both into `datetime.date`.

Create `analysis/evallab/store.py`:

```python
"""The frozen snapshot, read back for the tools, the baseline and the answer drafts. Nothing here touches the network."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from functools import cache
from pathlib import Path
from typing import Any

import pyarrow.parquet as pq

from .snapshot import OPENDOSM_PAGE, read_catalogue, verify
from .statistics import Series, period_of


@dataclass(frozen=True)
class Dataset:
    id: str
    title: str
    title_ms: str
    description: str
    frequency: str
    data_as_of: str
    url: str  # the parquet file on data.gov.my storage
    in_snapshot: bool


@dataclass(frozen=True)
class Release:
    id: str
    agency: str
    title: str
    date: str | None  # release date, when the publisher gives one
    period: str
    summary: str  # what the release covers, searched with the title
    url: str  # the file the figures come from
    page: str  # the web page that lists it
    raw: str | None  # the downloaded file in the snapshot, None when only the index entry is known
    pages: str | None  # its text, page by page


@dataclass(frozen=True)
class Store:
    root: Path
    taken: str
    commit: str
    datasets: dict[str, Dataset]
    releases: dict[str, Release]  # every DOSM release in the index, plus the BNM and MYNIC ones in the snapshot

    def rows(self, dataset_id: str) -> list[dict[str, Any]]:
        """Every row of a dataset in the snapshot, oldest first, with dates as datetime.date."""
        return read_rows(self.root / f"datasets/{dataset_id}.parquet")

    def pages(self, release_id: str) -> list[str]:
        release = self.releases[release_id]
        if release.pages is None:
            raise KeyError(f"{release_id} is listed in the release index but its text is not in the snapshot")
        return json.loads((self.root / release.pages).read_text())

    def sources(self) -> frozenset[str]:
        """Every dataset id and URL an answer may cite."""
        urls = {u for r in self.releases.values() if r.pages is not None for u in (r.url, r.page)}
        return frozenset({d.id for d in self.datasets.values() if d.in_snapshot} | {d.url for d in self.datasets.values() if d.in_snapshot} | urls)


@cache
def read_rows(path: Path) -> list[dict[str, Any]]:
    """Parquet dates arrive as date or as timestamp depending on the file; both become datetime.date."""
    as_date = lambda d: d.date() if isinstance(d, datetime) else d  # noqa: E731
    return sorted(({**row, "date": as_date(row["date"])} for row in pq.read_table(path).to_pylist()), key=lambda r: r["date"])


def load(root: Path) -> Store:
    snapshot = verify(root)
    catalogue, index = read_catalogue(root / "catalogue.tar.gz")
    saved = {p.stem for p in (root / "datasets").glob("*.parquet")}
    datasets = {
        key: Dataset(key, m.get("title_en", key), m.get("title_ms", ""), m.get("description_en", ""), m.get("frequency", ""), str(m.get("data_as_of", "")),
                     m.get("link_parquet", ""), key in saved)
        for key, m in catalogue.items()
    }
    frozen = {r["id"]: Release(r["id"], r["agency"], r["title"], r["date"], r["period"], r["summary"], r["url"], r["page"], r["raw"], r["pages"])
              for r in snapshot["releases"]}
    listed = {
        r["publication"]: Release(r["publication"], "DOSM", r["en"]["title"], r["release_date"], "", r["en"].get("description", ""),
                                  r["en"]["resources"][0]["resource_link"], OPENDOSM_PAGE.format(id=r["publication"]), None, None)
        for r in index
    }
    return Store(root, snapshot["taken"], snapshot["catalogue"]["commit"], datasets, {**listed, **frozen})


def latest(store: Store, series: Series, quarterly: bool) -> tuple[float, str] | None:
    """The newest value of a series in its dataset, scaled to the statistic's unit, with its period."""
    rows = [r for r in store.rows(series.dataset) if all(str(r.get(k)) == v for k, v in series.where) and r.get(series.column) is not None]
    if not rows:
        return None
    row = rows[-1]
    return float(row[series.column]) * series.scale, period_of(row["date"], quarterly)
```

- [ ] **Step 4: Write the tools and the baseline**

Create `analysis/evallab/tools.py`:

```python
"""The four tools a model may call, each reading only the frozen snapshot, and the baseline that trusts the open data."""

from __future__ import annotations

import inspect
import json
import re
from datetime import date
from functools import cache
from pathlib import Path
from typing import Any

from .statistics import Statistic
from .store import Release, Store, latest

MAX_RESULTS = 8
MAX_DATES = 12  # dates read_dataset returns at most
MAX_ROWS = 120
PAGE_CHARS = 6000  # text read_release returns from one page at most
STOPWORDS = frozenset("a an and the of for in on at to by with what is was are latest most recent malaysia malaysian berapakah terkini bagi di dan yang".split())


def tokens(text: str) -> frozenset[str]:
    return frozenset(t for t in re.findall(r"[a-z0-9]+", text.lower()) if len(t) > 1 and t not in STOPWORDS)


@cache
def page_tokens(path: Path) -> tuple[frozenset[str], ...]:
    return tuple(tokens(page) for page in json.loads(path.read_text()))


def as_int(value: Any, default: int) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def search_datasets(store: Store, query: str) -> list[dict[str, Any]]:
    wanted = tokens(query)
    scored = [(len(wanted & tokens(f"{d.id} {d.title} {d.title_ms} {d.description}")), d) for d in store.datasets.values()]
    best = sorted((s for s in scored if s[0] > 0), key=lambda s: (-s[0], not s[1].in_snapshot, s[1].id))[:MAX_RESULTS]
    return [{"id": d.id, "title": d.title, "frequency": d.frequency, "data_as_of": d.data_as_of, "in_snapshot": d.in_snapshot} for _, d in best]


def read_dataset(store: Store, id: str, last_n: Any = 3) -> dict[str, Any]:
    dataset = store.datasets.get(id)
    if dataset is None:
        return {"error": f"no dataset with id {id!r}; use search_datasets to find one"}
    if not dataset.in_snapshot:
        return {"error": f"dataset {id!r} is in the catalogue but not in this snapshot"}
    rows = store.rows(id)
    dates = sorted({r["date"] for r in rows})[-min(max(as_int(last_n, 3), 1), MAX_DATES):]
    chosen = [{**r, "date": r["date"].isoformat()} for r in rows if r["date"] in dates][-MAX_ROWS:]
    return {"id": id, "title": dataset.title, "frequency": dataset.frequency, "url": dataset.url, "columns": list(chosen[0]), "rows": chosen}


def release_score(store: Store, release: Release, wanted: frozenset[str]) -> tuple[int, list[int]]:
    """Twice the words matched in the title and summary, plus the best page; and the pages that match best."""
    head = len(wanted & tokens(f"{release.id} {release.title} {release.summary}"))
    if release.pages is None:
        return 2 * head, []
    per_page = [len(wanted & page) for page in page_tokens(store.root / release.pages)]
    best = max(per_page, default=0)
    return 2 * head + best, [i + 1 for i, n in enumerate(per_page) if n == best and n > 0][:3]


def search_releases(store: Store, query: str, after: str | None = None) -> list[dict[str, Any]] | dict[str, str]:
    if after:
        try:
            date.fromisoformat(after)
        except ValueError:
            return {"error": f"after must be a YYYY-MM-DD date, not {after!r}"}
    wanted = tokens(query)
    candidates = [r for r in store.releases.values() if not after or r.date is None or r.date >= after]
    scored = [(release_score(store, r, wanted), r) for r in candidates]
    matched = sorted((s for s in scored if s[0][0] > 0), key=lambda s: s[1].id)
    newest_first = sorted(matched, key=lambda s: s[1].date or s[1].period, reverse=True)  # stable sorts: id, then recency, then the rank below
    best = sorted(newest_first, key=lambda s: (s[1].pages is None, -s[0][0]))  # releases with text in the snapshot come first
    return [{"id": r.id, "title": r.title, "agency": r.agency, "release_date": r.date, "in_snapshot": r.pages is not None, "matching_pages": pages}
            for (_, pages), r in best[:MAX_RESULTS]]


def read_release(store: Store, id: str, page: Any = 1) -> dict[str, Any]:
    release = store.releases.get(id)
    if release is None:
        return {"error": f"no release with id {id!r}; use search_releases to find one"}
    if release.pages is None:
        return {"error": f"release {id!r} is in the index but its text is not in this snapshot"}
    pages = store.pages(id)
    number = as_int(page, 1)
    if not 1 <= number <= len(pages):
        return {"error": f"page must be from 1 to {len(pages)}"}
    return {"id": id, "title": release.title, "release_date": release.date, "url": release.url, "page": number, "pages": len(pages), "text": pages[number - 1][:PAGE_CHARS]}


def _schema(name: str, description: str, properties: dict[str, Any], required: list[str]) -> dict[str, Any]:
    return {"type": "function", "function": {"name": name, "description": description, "parameters": {"type": "object", "properties": properties, "required": required}}}


TOOLS = [
    _schema("search_datasets", "Search the data.gov.my catalogue. Returns dataset ids, titles, frequency and the latest period each dataset claims to cover.",
            {"query": {"type": "string", "description": "Words to look for, in English or Bahasa Malaysia"}}, ["query"]),
    _schema("read_dataset", "Read the newest rows of a data.gov.my dataset.",
            {"id": {"type": "string"}, "last_n": {"type": "integer", "description": f"How many of the newest dates to return, 1 to {MAX_DATES}"}}, ["id"]),
    _schema("search_releases", "Search official releases from DOSM, Bank Negara Malaysia and MYNIC. Returns release ids, dates and the pages that match best.",
            {"query": {"type": "string"}, "after": {"type": "string", "description": "Only releases on or after this YYYY-MM-DD date"}}, ["query"]),
    _schema("read_release", "Read one page of an official release's text.",
            {"id": {"type": "string"}, "page": {"type": "integer", "description": "Page number, starting at 1"}}, ["id"]),
]
HANDLERS = {"search_datasets": search_datasets, "read_dataset": read_dataset, "search_releases": search_releases, "read_release": read_release}


def call_tool(store: Store, name: str, arguments: Any) -> str:
    """Run one tool call and return its result as JSON text. Bad calls come back as an error the model can read."""
    handler = HANDLERS.get(name)
    if handler is None:
        return json.dumps({"error": f"unknown tool {name!r}"})
    kwargs = arguments if isinstance(arguments, dict) else {}
    try:
        inspect.signature(handler).bind(store, **kwargs)
    except TypeError as err:
        return json.dumps({"error": f"bad arguments for {name}: {err}"})
    return json.dumps(handler(store, **kwargs), ensure_ascii=False, default=str)


def baseline_answer(store: Store, statistic: Statistic) -> str:
    """What a user gets by trusting the open data: the dataset's newest value and period, as a final answer."""
    found = latest(store, statistic.series, statistic.quarterly)
    if found is None:
        raise ValueError(f"{statistic.id}: dataset {statistic.series.dataset} has no value for this series")
    value, period = found
    return json.dumps({"value": round(value, statistic.decimals), "unit": statistic.unit, "period": period, "source": statistic.series.dataset})
```

- [ ] **Step 5: Run the tests**

Run (in `analysis/`): `uv run pytest tests/evallab`, then `uv run pytest`.
Expected: `44 passed`, then `170 passed`.

- [ ] **Step 6: Commit**

```bash
git add analysis/evallab/store.py analysis/evallab/tools.py analysis/tests/evallab/conftest.py analysis/tests/evallab/test_tools.py
git commit -m "feat: add the LLM Eval Lab tools and the open data baseline"
```

---

### Task 5: Python: draft the answers into the review sheet, from the real snapshot

**Files:**
- Create: `analysis/evallab/questions.py`, `analysis/evallab/cli.py`, `analysis/evallab/questions.csv` (written by `draft`)
- Modify: `analysis/tests/evallab/conftest.py`
- Test: `analysis/tests/evallab/test_questions.py`
- Not committed: `analysis/data/raw/evallab/` (the snapshot)

**Interfaces:**
- Consumes: `bnm_latest`, `mynic_points` (`evallab.sources`); `Statistic`, `STATISTICS` (`evallab.statistics`); `Release`, `Store`, `latest`, `load` (`evallab.store`); `freeze` (`evallab.snapshot`).
- Produces, in `evallab.questions`: `QUESTIONS_PATH` (`analysis/evallab/questions.csv`); `FIELDS` (the sheet's columns: `id, statistic, agency, language, question, value, unit, period, release_id, release_url, dataset_id, dataset_value, dataset_period, status, evidence, verified`); `TEMPLATES` (two English and two Bahasa Malaysia phrasings); `CURRENT = "current"`, `OUT_OF_DATE = "out of date"`; `Draft(statistic, value: float | None, period, release, dataset_value, dataset_period, evidence)` with `status`; `Question(id, statistic, language, text, value: float, unit, period, release_url, dataset_value: float, dataset_period, status)`; `draft(store, statistic) -> Draft`; `draft_all(store, statistics) -> list[Draft]` (raises unless both current and out-of-date statistics exist); `sheet_rows(drafts) -> list[dict[str, str]]` (ids `q001` upward, four per statistic); `write_sheet(path, rows, force=False)` (raises `FileExistsError` rather than overwrite); `read_questions(path, statistics) -> list[Question]` (raises `ValueError` while any row is unverified or malformed).
- Produces, in `evallab.cli`: `python -m evallab.cli [--raw-dir DIR] [--questions CSV] snapshot|draft [--force]`. Task 7 adds `run`.
- Produces, in `tests/evallab/conftest.py`: the session fixture `questions` (the synthetic world's 16 questions, verified).

A statistic is out of date when its dataset's newest period is earlier than the newest release's period. The draft never guesses: a release whose text does not match the pattern leaves the value blank, and a dataset newer than the newest indexed release is flagged for a hand check. The four questions of a statistic share one answer.

- [ ] **Step 1: Write the failing tests**

Replace `analysis/tests/evallab/conftest.py` with:

```python
from pathlib import Path

import pytest

from evallab.questions import Question, draft_all, read_questions, sheet_rows, write_sheet
from evallab.store import Store, load

from .world import STATS, take_snapshot


@pytest.fixture(scope="session")
def store(tmp_path_factory: pytest.TempPathFactory) -> Store:
    """The synthetic snapshot, taken once and shared by every test that only reads it."""
    root: Path = tmp_path_factory.mktemp("snapshot")
    take_snapshot(root)
    return load(root)


@pytest.fixture(scope="session")
def questions(store: Store, tmp_path_factory: pytest.TempPathFactory) -> list[Question]:
    """The synthetic world's 16 questions, drafted and marked verified as Subashanan would."""
    path = tmp_path_factory.mktemp("questions") / "questions.csv"
    write_sheet(path, [{**row, "verified": "yes"} for row in sheet_rows(draft_all(store, STATS))])
    return read_questions(path, STATS)
```

Create `analysis/tests/evallab/test_questions.py`:

```python
import csv
from dataclasses import replace
from pathlib import Path

import pytest

from evallab.questions import CURRENT, OUT_OF_DATE, draft, draft_all, read_questions, sheet_rows, write_sheet
from evallab.store import Store

from .world import STATS

BY_ID = {s.id: s for s in STATS}


def test_drafts_come_from_the_newest_release_and_are_compared_with_the_dataset(store: Store) -> None:
    drafts = {d.statistic.id: d for d in draft_all(store, STATS)}
    summary = {k: (d.value, d.period, d.release.id, d.dataset_period, d.status) for k, d in drafts.items()}
    assert summary == {
        "unemployment_rate": (2.9, "2026-08", "labour_month_2026-08", "2026-08", CURRENT),
        "youth_rate_15_24": (10.1, "2026-08", "labour_month_2026-08", "2026-06", OUT_OF_DATE),
        "m3": (pytest.approx(2636.548767), "2026-08", "bnm_mhs_2026-08_table_1.3", "2026-06", OUT_OF_DATE),
        "domains_active": (693122.0, "2026-09", "mynic_active_2026", "2025-01", OUT_OF_DATE),
    }
    assert drafts["unemployment_rate"].evidence == "unemployment rate for August 2026 eased to 2.9 per cent"


def test_the_review_sheet_has_four_questions_per_statistic(store: Store) -> None:
    rows = sheet_rows(draft_all(store, STATS))
    assert [r["id"] for r in rows] == [f"q{i:03d}" for i in range(1, 17)]
    assert [r["language"] for r in rows[:4]] == ["en", "en", "ms", "ms"]
    assert rows[0]["question"] == "What is Malaysia's latest unemployment rate?"
    assert rows[10]["question"] == "Berapakah penawaran wang M3 terkini bagi Malaysia?"
    m3 = rows[8]
    assert (m3["value"], m3["unit"], m3["dataset_value"], m3["release_url"]) == ("2636.5", "RM billion", "2670.4", "https://www.bnm.gov.my/documents/20124/999/1.3.xlsx")
    assert all(r["verified"] == "" for r in rows)


def test_a_release_without_the_headline_leaves_the_value_for_the_reviewer(store: Store) -> None:
    blind = replace(BY_ID["unemployment_rate"], pattern=r"nothing like this (?P<value>\d+)")
    d = draft(store, blind)
    assert d.value is None and d.evidence == "No match in the release text; read the release."
    assert sheet_rows([d])[0]["value"] == ""


def test_a_dataset_newer_than_the_release_is_flagged_and_counts_as_current(store: Store) -> None:
    d = draft(store, replace(BY_ID["unemployment_rate"], release=r"^labour_month_2026-06$"))
    assert (d.period, d.dataset_period, d.status) == ("2026-06", "2026-08", CURRENT)
    assert d.evidence.startswith("Dataset is newer than the latest release; check by hand.")


def test_a_set_with_nothing_out_of_date_is_refused(store: Store) -> None:
    with pytest.raises(ValueError, match="needs both current and out-of-date series; 0 of 1"):
        draft_all(store, [BY_ID["unemployment_rate"]])


def test_drafting_again_never_overwrites_the_sheet_by_accident(tmp_path: Path, store: Store) -> None:
    path = tmp_path / "questions.csv"
    rows = sheet_rows(draft_all(store, STATS))
    write_sheet(path, rows)
    path.write_text(path.read_text().replace(",\n", ",yes\n", 1))  # the reviewer has verified the first row
    with pytest.raises(FileExistsError, match="may hold verified answers"):
        write_sheet(path, rows)
    assert ",yes\n" in path.read_text()
    write_sheet(path, rows, force=True)
    assert ",yes\n" not in path.read_text()


def verified(tmp_path: Path, store: Store, edit: dict[str, str] | None = None) -> Path:
    rows = [{**r, "verified": "Yes "} for r in sheet_rows(draft_all(store, STATS))]
    rows[0] = {**rows[0], **(edit or {})}
    path = tmp_path / "questions.csv"
    write_sheet(path, rows, force=True)
    return path


def test_the_runner_reads_only_a_fully_verified_sheet(tmp_path: Path, store: Store) -> None:
    questions = read_questions(verified(tmp_path, store), STATS)
    assert len(questions) == 16 and (questions[4].value, questions[4].period, questions[4].status) == (10.1, "2026-08", OUT_OF_DATE)
    with pytest.raises(ValueError, match=r"1 of 16 questions are not verified yet \(q001\)"):
        read_questions(verified(tmp_path, store, {"verified": ""}), STATS)


@pytest.mark.parametrize(("edit", "message"), [
    ({"value": ""}, "q001: value '' is not a number"),
    ({"period": "August 2026"}, "q001: period 'August 2026' must look like 2026-08"),
    ({"statistic": "gdp"}, "q001: unknown statistic 'gdp'"),
])
def test_a_malformed_verified_row_stops_the_run(tmp_path: Path, store: Store, edit: dict[str, str], message: str) -> None:
    with pytest.raises(ValueError, match=message):
        read_questions(verified(tmp_path, store, edit), STATS)


def test_values_with_thousands_separators_are_read(tmp_path: Path, store: Store) -> None:
    path = verified(tmp_path, store)
    rows = list(csv.DictReader(path.open()))
    rows[12]["value"] = "693,122"
    write_sheet(path, rows, force=True)
    assert read_questions(path, STATS)[12].value == 693122.0
```

- [ ] **Step 2: Run the tests to verify they fail**

Run (in `analysis/`): `uv run pytest tests/evallab/test_questions.py`
Expected: FAIL with `ImportError while loading conftest` and `ModuleNotFoundError: No module named 'evallab.questions'`.

- [ ] **Step 3: Write the drafting and the review sheet**

The sheet is written with `\n` line endings so its diffs stay readable.

Create `analysis/evallab/questions.py`:

```python
"""Draft each statistic's correct answer from its latest release, write the review sheet, and read it back once verified."""

from __future__ import annotations

import csv
import logging
import re
from dataclasses import dataclass
from pathlib import Path

from .sources import bnm_latest, mynic_points
from .statistics import Statistic
from .store import Release, Store, latest

log = logging.getLogger(__name__)

QUESTIONS_PATH = Path(__file__).with_name("questions.csv")
FIELDS = ["id", "statistic", "agency", "language", "question", "value", "unit", "period", "release_id", "release_url",
          "dataset_id", "dataset_value", "dataset_period", "status", "evidence", "verified"]
TEMPLATES = (
    ("en", "What is Malaysia's latest {en}?"),
    ("en", "According to the most recent official figures, what was the {en} in Malaysia, and for which period?"),
    ("ms", "Berapakah {ms} terkini bagi Malaysia?"),
    ("ms", "Menurut angka rasmi terbaru, berapakah {ms} di Malaysia, dan bagi tempoh mana?"),
)
CURRENT, OUT_OF_DATE = "current", "out of date"
FEW_OUT_OF_DATE = 6  # fewer out-of-date statistics than this makes the headline view thin
PERIOD = {False: re.compile(r"^\d{4}-(0[1-9]|1[0-2])$"), True: re.compile(r"^\d{4}-Q[1-4]$")}


@dataclass(frozen=True)
class Draft:
    statistic: Statistic
    value: float | None  # None when the release text did not give it up; the reviewer fills it in
    period: str
    release: Release
    dataset_value: float
    dataset_period: str
    evidence: str

    @property
    def status(self) -> str:
        return OUT_OF_DATE if self.dataset_period < self.period else CURRENT


@dataclass(frozen=True)
class Question:
    id: str
    statistic: str
    language: str
    text: str
    value: float
    unit: str
    period: str
    release_url: str
    dataset_value: float
    dataset_period: str
    status: str


def frozen_releases(store: Store, s: Statistic, test: str) -> list[Release]:
    """Releases with text in the snapshot whose id matches, newest first."""
    chosen = [r for r in store.releases.values() if r.agency == s.agency and r.pages is not None and re.search(test, r.id)]
    if not chosen:
        raise ValueError(f"{s.id}: no {s.agency} release in the snapshot matches {test}")
    return sorted(chosen, key=lambda r: (r.date or "", r.period, r.id), reverse=True)


def from_release(store: Store, s: Statistic) -> tuple[float | None, str, Release, str]:
    """The figure, its period, the release it comes from and the evidence for the reviewer."""
    if s.agency == "DOSM":
        release = frozen_releases(store, s, s.release)[0]
        match = re.search(s.pattern, " ".join(store.pages(release.id)))
        evidence = match[0][:300] if match else "No match in the release text; read the release."
        return (float(match["value"].replace(",", "")) if match else None), release.period, release, evidence
    if s.agency == "BNM":
        table, column = s.release.split(":")
        release = frozen_releases(store, s, rf"_table_{re.escape(table)}$")[0]
        found = bnm_latest(store.root / str(release.raw), int(column))
        if found is None:
            raise ValueError(f"{s.id}: table {table} has no value in column {column}")
        return found[0] * s.release_scale, found[1], release, f"Table {table}, column {column}, row {found[1]}"
    points = [(period, total, r) for r in frozen_releases(store, s, rf"^mynic_{s.release}_\d{{4}}$") for period, total in mynic_points(store.root / str(r.raw))]
    if not points:
        raise ValueError(f"{s.id}: the MYNIC {s.release} chart has no months with data")
    period, total, release = max(points, key=lambda p: p[0])
    return float(total), period, release, f"MYNIC {s.release} domains chart, {period}"


def draft(store: Store, s: Statistic) -> Draft:
    in_dataset = latest(store, s.series, s.quarterly)
    if in_dataset is None:
        raise ValueError(f"{s.id}: dataset {s.series.dataset} has no value for this series")
    value, period, release, evidence = from_release(store, s)
    if in_dataset[1] > period:
        evidence = f"Dataset is newer than the latest release; check by hand. {evidence}"
    return Draft(s, value, period, release, in_dataset[0], in_dataset[1], evidence)


def draft_all(store: Store, statistics: list[Statistic]) -> list[Draft]:
    drafts = [draft(store, s) for s in statistics]
    stale = sum(d.status == OUT_OF_DATE for d in drafts)
    if stale == 0 or stale == len(drafts):
        raise ValueError(f"the question set needs both current and out-of-date series; {stale} of {len(drafts)} statistics are out of date")
    if stale < FEW_OUT_OF_DATE:
        log.warning("only %d statistics are out of date; the headline view will be thin", stale)
    return drafts


def fixed(value: float | None, decimals: int) -> str:
    return "" if value is None else f"{value:.{decimals}f}"


def sheet_rows(drafts: list[Draft]) -> list[dict[str, str]]:
    rows = []
    for d in drafts:
        s = d.statistic
        for language, template in TEMPLATES:
            rows.append({
                "id": f"q{len(rows) + 1:03d}", "statistic": s.id, "agency": s.agency, "language": language,
                "question": template.format(en=s.name_en, ms=s.name_ms), "value": fixed(d.value, s.decimals), "unit": s.unit, "period": d.period,
                "release_id": d.release.id, "release_url": d.release.url, "dataset_id": s.series.dataset,
                "dataset_value": fixed(d.dataset_value, s.decimals), "dataset_period": d.dataset_period, "status": d.status, "evidence": d.evidence, "verified": "",
            })
    return rows


def write_sheet(path: Path, rows: list[dict[str, str]], force: bool = False) -> None:
    if path.exists() and not force:
        raise FileExistsError(f"{path} already exists and may hold verified answers; pass --force to replace it")
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def parse_row(row: dict[str, str], statistics: dict[str, Statistic]) -> Question:
    s = statistics.get(row["statistic"])
    if s is None:
        raise ValueError(f"{row['id']}: unknown statistic {row['statistic']!r}")
    if not PERIOD[s.quarterly].match(row["period"]):
        raise ValueError(f"{row['id']}: period {row['period']!r} must look like {'2026-Q2' if s.quarterly else '2026-08'}")
    try:
        value = float(row["value"].replace(",", ""))
    except ValueError:
        raise ValueError(f"{row['id']}: value {row['value']!r} is not a number") from None
    return Question(row["id"], s.id, row["language"], row["question"], value, s.unit, row["period"], row["release_url"],
                    float(row["dataset_value"]), row["dataset_period"], row["status"])


def read_questions(path: Path, statistics: list[Statistic]) -> list[Question]:
    """The verified question set. Refuses to return anything while a single row is unverified or malformed."""
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    waiting = [r["id"] for r in rows if r["verified"].strip().lower() != "yes"]
    if waiting:
        raise ValueError(f"{len(waiting)} of {len(rows)} questions are not verified yet ({', '.join(waiting[:5])}); check each against its release and set verified to yes")
    by_id = {s.id: s for s in statistics}
    return [parse_row(r, by_id) for r in rows]
```

- [ ] **Step 4: Write the command line**

Create `analysis/evallab/cli.py`:

```python
"""Entry point, run from analysis/:

  uv run python -m evallab.cli snapshot      take the snapshot once; later commands only verify it
  uv run python -m evallab.cli draft         draft every answer into evallab/questions.csv for review
"""

from __future__ import annotations

import argparse
import logging
from datetime import UTC, datetime
from pathlib import Path

from .questions import OUT_OF_DATE, QUESTIONS_PATH, draft_all, sheet_rows, write_sheet
from .snapshot import freeze
from .statistics import STATISTICS
from .store import load

ANALYSIS_DIR = Path(__file__).resolve().parents[1]
REPO_DIR = ANALYSIS_DIR.parent
RAW_DIR = ANALYSIS_DIR / "data/raw/evallab"


def cmd_snapshot(args: argparse.Namespace) -> None:
    snapshot = freeze(args.raw_dir, list(STATISTICS), datetime.now(UTC).date())
    print(f"snapshot of {snapshot['taken']}: {len(snapshot['files'])} files, {len(snapshot['releases'])} releases, catalogue at {snapshot['catalogue']['commit'][:8]}")


def cmd_draft(args: argparse.Namespace) -> None:
    drafts = draft_all(load(args.raw_dir), list(STATISTICS))
    write_sheet(args.questions, sheet_rows(drafts), force=args.force)
    stale, blank = sum(d.status == OUT_OF_DATE for d in drafts), [d.statistic.id for d in drafts if d.value is None]
    print(f"wrote {len(drafts) * 4} questions on {len(drafts)} statistics ({stale} out of date) to {args.questions}")
    if blank:
        print(f"no value found in the release text for: {', '.join(blank)}; fill these in by hand")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="python -m evallab.cli", description="Run the LLM Eval Lab freshness study.")
    parser.add_argument("--raw-dir", type=Path, default=RAW_DIR)
    parser.add_argument("--questions", type=Path, default=QUESTIONS_PATH)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("snapshot", help="take the snapshot, or verify the one already taken").set_defaults(handler=cmd_snapshot)
    draft = commands.add_parser("draft", help="draft the answers into the review sheet")
    draft.add_argument("--force", action="store_true", help="replace an existing review sheet")
    draft.set_defaults(handler=cmd_draft)
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%H:%M:%S")
    args.handler(args)


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Run the tests**

Run (in `analysis/`): `uv run pytest tests/evallab`, then `uv run pytest`, then `uv run python -m evallab.cli --help`.
Expected: `55 passed`, then `181 passed`, then a usage line listing `{snapshot,draft}`.

- [ ] **Step 6: Take the real snapshot**

Run (in `analysis/`): `uv run python -m evallab.cli snapshot`
This downloads about 300 MB into `analysis/data/raw/evallab/` (each DOSM release PDF is 3 to 22 MB) and takes one to two minutes. Expected log lines: one `fetching ...` line per file, ending with six MYNIC lines, then `snapshot of <today>: 95 files, 38 releases, catalogue at <8 characters>`. On 2026-10-15 the counts were 95 files (the catalogue, 18 datasets, 30 DOSM releases, 2 BNM tables and 6 MYNIC charts, plus a pages file for each of the 38 releases).

Run the same command again.
Expected: no `fetching` lines and the same summary line, because the snapshot is only verified now.

If it stops:
- `unexpected commit from GitHub`: the GitHub API refused (60 unauthenticated requests an hour); wait and rerun.
- `no DOSM release matches ...`, `no Monthly Highlights and Statistics edition found`, `table ... not found on the BNM edition page`: a publisher changed its layout. Stop and report; do not loosen a pattern without telling Subashanan.
- Any HTTP error: rerun; files already written are fetched again, because `snapshot.json` is written only at the end.

- [ ] **Step 7: Draft the answers**

Run (in `analysis/`): `uv run python -m evallab.cli draft`
Expected: `wrote 120 questions on 30 statistics (N out of date) to .../analysis/evallab/questions.csv` and no `no value found` line. On 2026-10-15, N was 16. A warning `only N statistics are out of date` (N below 6) or a `ValueError` saying the set needs both kinds means the open data has caught up; stop and tell Subashanan before going on, because the headline view depends on out-of-date series.

Run (in `analysis/`):

```bash
uv run python - <<'EOF'
import csv
rows = list(csv.DictReader(open("evallab/questions.csv")))
for r in rows[::4]:
    print(f"{r['statistic']:24} {r['value']:>10} {r['period']}  dataset {r['dataset_value']:>10} {r['dataset_period']}  {r['status']:11} {r['release_id']}")
EOF
```

Expected: 30 lines. On 2026-10-15 they read, for example, `youth_rate_15_24 10.1 2026-08 dataset 10.2 2026-06 out of date labour_month_2026-08`, `fdi_net 7.4 2026-Q2 dataset 8.5 2025-Q3 out of date bop_2026-q2`, `m3 2636.5 2026-08 dataset 2670.4 2026-06 out of date bnm_mhs_2026-08_table_1.3` and `domains_active 693122 2026-09 dataset 352717 2025-01 out of date mynic_active_2026`. Show this table to Subashanan with Task 6.

- [ ] **Step 8: Commit**

The drafted sheet is committed now, so the verification in Task 6 shows up as its own diff.

```bash
git add analysis/evallab/questions.py analysis/evallab/cli.py analysis/evallab/questions.csv \
  analysis/tests/evallab/conftest.py analysis/tests/evallab/test_questions.py
git commit -m "feat: draft the LLM Eval Lab answers for review"
```

---

### Task 6: Stop: Subashanan verifies the 120 answers

This task is done by Subashanan, not by an agent. The controller stops here, sends Subashanan the Task 5 table and the instructions below, and waits. Nothing after this task may start until Step 3 passes.

**Files:**
- Modify (by Subashanan): `analysis/evallab/questions.csv`

**Interfaces:**
- Consumes: the drafted sheet (Task 5).
- Produces: a sheet with `verified` set to `yes` on all 120 rows, which `read_questions` accepts; Task 7 refuses to start without it.

- [ ] **Step 1: Check every statistic against its release**

For each statistic (four rows that share `statistic`), open `release_url` and find the figure for `period`. The `evidence` column quotes the sentence or table cell the draft used. If the value, unit or period is wrong, correct `value` and `period` on all four rows (the unit is fixed per statistic; tell the controller if it is wrong). Then set `verified` to `yes` on all four rows. Leave the question wording, `status`, `dataset_value` and `dataset_period` as they are.

Edit the CSV in a text editor, or import it into a spreadsheet with every column as text: spreadsheets turn `2026-08` into a date and drop trailing zeros such as `2.20`. Keep UTF-8, the header row and the column order.

- [ ] **Step 2: Look at the diff**

Run: `git diff --stat analysis/evallab/questions.csv` and `git diff analysis/evallab/questions.csv | head -40`
Expected: one file changed with 120 lines replaced; periods still look like `2026-08` or `2026-Q2`; only `value`, `period` and `verified` differ.

- [ ] **Step 3: Check that the runner accepts it**

Run (in `analysis/`):

```bash
uv run python -c "from evallab.questions import QUESTIONS_PATH, read_questions; from evallab.statistics import STATISTICS; print(len(read_questions(QUESTIONS_PATH, list(STATISTICS))), 'verified')"
```

Expected: `120 verified`. Otherwise the error names the rows to fix, for example `3 of 120 questions are not verified yet (q041, q042, q043)` or `q009: period '08/2026' must look like 2026-08`.

- [ ] **Step 4: Commit**

```bash
git add analysis/evallab/questions.csv
git commit -m "feat: verify the LLM Eval Lab question set"
```

---

### Task 7: Python: the Ollama client, the runner and the 20-question pilot

**Files:**
- Create: `analysis/evallab/ollama.py`, `analysis/evallab/runner.py`, `analysis/tests/evallab/fake_ollama.py`
- Modify: `analysis/evallab/cli.py`, `analysis/tests/evallab/conftest.py`
- Test: `analysis/tests/evallab/test_ollama.py`, `analysis/tests/evallab/test_runner.py`, `analysis/tests/evallab/test_cli.py`
- Not committed: `analysis/data/raw/evallab/runs/calls.jsonl`, `answers.jsonl` (written by the pilot)

**Interfaces:**
- Consumes: `Question`, `read_questions` (Task 5); `Store`, `load` (Task 4); `TOOLS`, `call_tool`, `baseline_answer` (Task 4).
- Produces, in `evallab.ollama`: `OllamaError`; `UsageLimit(OllamaError)` for HTTP 429; the `Chat` protocol with `chat(model, messages, tools, options) -> dict`; `OllamaClient(base_url="http://localhost:11434", timeout=300)` with `version() -> str`, `show(model) -> dict` and `chat(...)`, which sends `{"model", "messages", "stream": false, "options"}` plus `tools` only when given.
- Produces, in `evallab.runner`: `MODES = ("tools", "memory")`, `MAX_TOOL_CALLS = 6`, `MAX_TURNS = 10`, `RETRIES = 2`, `BACKOFF_SECONDS = 5.0`, `SEED = 42`, `OPTIONS`, `CAP_NOTE`, `SYSTEM` (one system prompt per mode, with `{today}` replaced by the snapshot date); `Outcome(content, tool_calls, seconds, status)` with `status` one of `ok`, `cap`, `error`; `RunLog(folder)` with `call(record)`, `answer(record)`, `calls()`, `answers()` over `calls.jsonl` and `answers.jsonl`; `Asker(client, store, run_log, today, pace, sleep).ask(model, mode, question) -> Outcome`; `run(client, store, questions, models, run_log, today, pace, only=None, sleep=time.sleep) -> int`, which answers every (question, model, mode) missing from the log and lets `UsageLimit` stop it. An answer record is `{"time", "question", "model", "mode", "content", "tool_calls", "seconds", "status"}`; a call record is `{"time", "model", "mode", "question", "attempt", "seconds", "status", "prompt_tokens", "output_tokens"}` or, on failure, `"error"` instead of the token counts.
- Produces, in `evallab.cli`: `MODELS = ("gpt-oss:120b-cloud", "deepseek-v4.1-flash:cloud")`, `PILOT = 20`, `BY_ID`, `pilot_ids(questions) -> set[str]` (every sixth question of 120), `usage(calls)`, `timing(answers)`, `pilot_summary(answers, calls)`; and `python -m evallab.cli run [--pilot] [--pace SECONDS]`. Task 9 extends `run` to score and write the outputs.
- Produces, in `tests/evallab/fake_ollama.py`: `Script`, `tool_call(name, **arguments)`, `final(value, unit, period, source, prose=...)`, `FakeChat(script)` recording `requests`; in `tests/evallab/conftest.py`: `scripted(questions)` and the session fixture `answered` (every question asked of both models in both modes). Task 9 scores `answered`.

The runner asks one question at a time and logs every chat call before moving on, so stopping it at any point loses at most the question in progress. A question with tools may take several calls: the model asks for tools, the runner runs at most 6 of them in total and replies to each, and once the cap is reached the next request carries no tools so the model must answer. A failed call is retried twice after 5 and 10 seconds and then the question is recorded with no answer; HTTP 429 stops the whole run instead, to be resumed later. The runner pauses `--pace` seconds after every call (2 by default).

- [ ] **Step 1: Write the failing tests**

Create `analysis/tests/evallab/fake_ollama.py`:

```python
"""A scripted stand-in for the Ollama chat API: each reply is decided by a function of the conversation so far."""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

Script = Callable[[str, list[dict[str, Any]], list[dict[str, Any]] | None], dict[str, Any] | Exception]


def tool_call(name: str, **arguments: Any) -> dict[str, Any]:
    return {"function": {"name": name, "arguments": arguments}}


def final(value: Any, unit: str, period: str, source: str, prose: str = "Here is the figure.") -> dict[str, Any]:
    answer = json.dumps({"value": value, "unit": unit, "period": period, "source": source})
    return {"role": "assistant", "content": f"{prose}\n```json\n{answer}\n```"}


class FakeChat:
    def __init__(self, script: Script) -> None:
        self.script, self.requests = script, []

    def chat(self, model: str, messages: list[dict[str, Any]], tools: list[dict[str, Any]] | None, options: dict[str, Any]) -> dict[str, Any]:
        self.requests.append({"model": model, "messages": list(messages), "tools": tools, "options": options})
        reply = self.script(model, messages, tools)
        if isinstance(reply, Exception):
            raise reply
        return {"model": model, "message": reply, "done": True, "prompt_eval_count": 100, "eval_count": 20}
```

Replace `analysis/tests/evallab/conftest.py` with:

```python
from pathlib import Path
from typing import Any

import pytest

from evallab.cli import MODELS
from evallab.questions import Question, draft_all, read_questions, sheet_rows, write_sheet
from evallab.runner import RunLog, run
from evallab.store import Store, load

from .fake_ollama import FakeChat, Script, final, tool_call
from .world import STATS, take_snapshot


@pytest.fixture(scope="session")
def store(tmp_path_factory: pytest.TempPathFactory) -> Store:
    """The synthetic snapshot, taken once and shared by every test that only reads it."""
    root: Path = tmp_path_factory.mktemp("snapshot")
    take_snapshot(root)
    return load(root)


@pytest.fixture(scope="session")
def questions(store: Store, tmp_path_factory: pytest.TempPathFactory) -> list[Question]:
    """The synthetic world's 16 questions, drafted and marked verified as Subashanan would."""
    path = tmp_path_factory.mktemp("questions") / "questions.csv"
    write_sheet(path, [{**row, "verified": "yes"} for row in sheet_rows(draft_all(store, STATS))])
    return read_questions(path, STATS)


def scripted(questions: list[Question]) -> Script:
    """gpt-oss looks the figure up and is always right; DeepSeek reads the dataset and quotes it. From memory, gpt-oss
    names last year's period and DeepSeek gives no JSON at all."""
    by_text = {q.text: q for q in questions}

    def reply(model: str, messages: list[dict[str, Any]], tools: list[dict[str, Any]] | None) -> dict[str, Any]:
        q = by_text[messages[1]["content"]]
        if tools and not any(m["role"] == "tool" for m in messages):
            return {"role": "assistant", "content": "", "tool_calls": [tool_call("search_releases", query=q.text)]}
        if tools and model == MODELS[0]:
            return final(q.value, q.unit, q.period, q.release_url)
        if tools:
            return final(q.dataset_value, q.unit, q.dataset_period, "lfs_month")
        return final(q.value, q.unit, "2025-08", "memory") if model == MODELS[0] else {"role": "assistant", "content": "I am not sure."}
    return reply


@pytest.fixture(scope="session")
def answered(store: Store, questions: list[Question], tmp_path_factory: pytest.TempPathFactory) -> RunLog:
    """Every question asked of both models in both modes through the scripted fake, logged as a real run would be."""
    run_log = RunLog(tmp_path_factory.mktemp("runs"))
    run(FakeChat(scripted(questions)), store, questions, MODELS, run_log, store.taken, 0, sleep=lambda s: None)
    return run_log
```

Create `analysis/tests/evallab/test_ollama.py`. Its fake server answers in the shapes Ollama 0.40.4 returned on 2026-10-15; the usage limit message is illustrative, since no limit was hit during planning:

```python
import json
import threading
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from evallab.ollama import OllamaClient, OllamaError, UsageLimit

SEEN: list[dict] = []


class FakeOllama(BaseHTTPRequestHandler):
    """Answers like the Ollama server did on 2026-10-15 (version 0.40.4), and with an error for models named after one."""

    def reply(self, status: int, body: dict) -> None:
        data = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:  # noqa: N802
        self.reply(200, {"version": "0.40.4"})

    def do_POST(self) -> None:  # noqa: N802
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        SEEN.append({"path": self.path, **body})
        if body["model"] == "limited":
            return self.reply(429, {"error": "you have reached your weekly usage limit"})
        if body["model"] == "broken":
            return self.reply(500, {"error": "internal error"})
        if self.path == "/api/show":
            return self.reply(200, {"capabilities": ["completion", "tools", "thinking"], "details": {"parent_model": "gpt-oss:120b"}})
        message = {"role": "assistant", "content": "", "thinking": "Search first.", "tool_calls": [{"id": "call_1", "function": {"index": 0, "name": "search_datasets", "arguments": {"query": "CPI"}}}]}
        self.reply(200, {"model": "gpt-oss:120b", "message": message, "done": True, "total_duration": 316017665, "prompt_eval_count": 174, "eval_count": 47})

    def log_message(self, *args: object) -> None:
        pass


@pytest.fixture(scope="module")
def client() -> Iterator[OllamaClient]:
    server = HTTPServer(("127.0.0.1", 0), FakeOllama)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield OllamaClient(f"http://127.0.0.1:{server.server_port}", timeout=5)
    server.shutdown()


def test_chat_sends_the_messages_tools_and_options(client: OllamaClient) -> None:
    tools = [{"type": "function", "function": {"name": "search_datasets"}}]
    reply = client.chat("gpt-oss:120b-cloud", [{"role": "user", "content": "CPI?"}], tools, {"temperature": 0, "seed": 42})
    assert reply["message"]["tool_calls"][0]["function"]["arguments"] == {"query": "CPI"} and reply["eval_count"] == 47
    assert SEEN[-1] == {"path": "/api/chat", "model": "gpt-oss:120b-cloud", "messages": [{"role": "user", "content": "CPI?"}], "stream": False,
                        "options": {"temperature": 0, "seed": 42}, "tools": tools}
    client.chat("gpt-oss:120b-cloud", [], None, {})
    assert "tools" not in SEEN[-1]


def test_version_and_model_details(client: OllamaClient) -> None:
    assert client.version() == "0.40.4"
    assert client.show("gpt-oss:120b-cloud")["details"]["parent_model"] == "gpt-oss:120b"


def test_a_usage_limit_is_its_own_error(client: OllamaClient) -> None:
    with pytest.raises(UsageLimit, match="HTTP 429 from /api/chat: .*usage limit"):
        client.chat("limited", [], None, {})
    with pytest.raises(OllamaError, match="HTTP 500") as err:
        client.chat("broken", [], None, {})
    assert not isinstance(err.value, UsageLimit)


def test_an_unreachable_server_is_an_ollama_error() -> None:
    with pytest.raises(OllamaError, match="/api/version"):
        OllamaClient("http://127.0.0.1:9", timeout=2).version()
```

Create `analysis/tests/evallab/test_runner.py`:

```python
import json
from pathlib import Path

import pytest

from evallab.ollama import OllamaError, UsageLimit
from evallab.questions import Question
from evallab.runner import BACKOFF_SECONDS, CAP_NOTE, MAX_TOOL_CALLS, Asker, RunLog, run
from evallab.store import Store

from .fake_ollama import FakeChat, final, tool_call

MODELS = ("gpt-oss:120b-cloud", "deepseek-v4.1-flash:cloud")


def lookup(model, messages, tools):
    """Search the releases, read the newest one's second page, then answer."""
    tool_replies = [m for m in messages if m["role"] == "tool"]
    if tools and not tool_replies:
        return {"role": "assistant", "content": "", "tool_calls": [tool_call("search_releases", query="unemployment rate")]}
    if tools and len(tool_replies) == 1:
        return {"role": "assistant", "content": "", "tool_calls": [tool_call("read_release", id="labour_month_2026-08", page=2)]}
    return final(2.9, "per cent", "2026-08", "https://open.dosm.gov.my/publications/labour_month_2026-08")


def asker(store: Store, tmp_path: Path, client: FakeChat, sleeps: list[float] | None = None) -> Asker:
    return Asker(client, store, RunLog(tmp_path), "2026-10-15", 1.5, (sleeps if sleeps is not None else []).append)


def test_with_tools_the_model_reads_the_snapshot_then_answers(store: Store, questions: list[Question], tmp_path: Path) -> None:
    client = FakeChat(lookup)
    outcome = asker(store, tmp_path, client).ask(MODELS[0], "tools", questions[0])

    assert (outcome.tool_calls, outcome.status) == (2, "ok") and '"value": 2.9' in outcome.content
    last = client.requests[-1]["messages"]
    assert [m["role"] for m in last] == ["system", "user", "assistant", "tool", "assistant", "tool"]
    assert "Today is 2026-10-15." in last[0]["content"] and last[1]["content"] == "What is Malaysia's latest unemployment rate?"
    assert "eased to 2.9 per cent" in json.loads(last[5]["content"])["text"]
    assert client.requests[0]["options"] == {"temperature": 0, "seed": 42} and client.requests[0]["tools"] is not None


def test_from_memory_there_are_no_tools_and_one_call(store: Store, questions: list[Question], tmp_path: Path) -> None:
    client = FakeChat(lookup)
    outcome = asker(store, tmp_path, client).ask(MODELS[0], "memory", questions[0])
    assert len(client.requests) == 1 and client.requests[0]["tools"] is None and outcome.tool_calls == 0


def test_parallel_tool_calls_count_one_by_one_and_the_cap_forces_an_answer(store: Store, questions: list[Question], tmp_path: Path) -> None:
    greedy = lambda model, messages, tools: (  # noqa: E731
        {"role": "assistant", "content": "", "tool_calls": [tool_call("search_datasets", query="unemployment")] * 4} if tools else final(3.0, "per cent", "2026-07", "lfs_month"))
    client = FakeChat(greedy)
    outcome = asker(store, tmp_path, client).ask(MODELS[1], "tools", questions[0])

    assert (outcome.tool_calls, outcome.status) == (MAX_TOOL_CALLS, "cap") and '"value": 3.0' in outcome.content
    assert [r["tools"] is not None for r in client.requests] == [True, True, False]
    refused = [m for m in client.requests[2]["messages"] if m["role"] == "tool"][-2:]
    assert all(json.loads(m["content"]) == {"error": CAP_NOTE} for m in refused)


def test_a_failing_call_is_retried_with_backoff_then_scored_as_no_answer(store: Store, questions: list[Question], tmp_path: Path) -> None:
    attempts = iter([OllamaError("timed out"), OllamaError("HTTP 502")])
    flaky = FakeChat(lambda m, msgs, t: next(attempts, final(2.9, "per cent", "2026-08", "lfs_month")))
    sleeps: list[float] = []
    assert asker(store, tmp_path, flaky, sleeps).ask(MODELS[0], "memory", questions[0]).status == "ok"
    assert sleeps == [BACKOFF_SECONDS, BACKOFF_SECONDS * 2, 1.5]

    broken = FakeChat(lambda m, msgs, t: OllamaError("HTTP 500"))
    outcome = asker(store, tmp_path / "broken", broken).ask(MODELS[0], "memory", questions[0])
    assert (outcome.content, outcome.status) == ("", "error") and len(broken.requests) == 3
    assert [c["status"] for c in RunLog(tmp_path / "broken").calls()] == ["error"] * 3


def test_a_usage_limit_stops_the_run_and_the_next_run_resumes(store: Store, questions: list[Question], tmp_path: Path) -> None:
    run_log, calls = RunLog(tmp_path), {"n": 0}

    def limited(model, messages, tools):
        calls["n"] += 1
        return UsageLimit("HTTP 429") if calls["n"] == 3 else final(1, "per cent", "2026-08", "x")

    with pytest.raises(UsageLimit):
        run(FakeChat(limited), store, questions[:2], MODELS, run_log, "2026-10-15", 0, sleep=lambda s: None)
    assert len(run_log.answers()) == 2 and run_log.calls()[-1]["status"] == "limit"

    resumed = FakeChat(lambda m, msgs, t: final(1, "per cent", "2026-08", "x"))
    assert run(resumed, store, questions[:2], MODELS, run_log, "2026-10-15", 0, sleep=lambda s: None) == 6
    keys = [(a["question"], a["model"], a["mode"]) for a in run_log.answers()]
    assert len(keys) == len(set(keys)) == 8


def test_a_line_cut_short_by_an_interruption_is_skipped(store: Store, questions: list[Question], tmp_path: Path) -> None:
    run_log = RunLog(tmp_path)
    run(FakeChat(lambda m, msgs, t: final(1, "per cent", "2026-08", "x")), store, questions[:1], MODELS[:1], run_log, "2026-10-15", 0, sleep=lambda s: None)
    with run_log.answers_path.open("a") as handle:
        handle.write('{"question": "q002", "mod')
    assert [a["question"] for a in run_log.answers()] == ["q001", "q001"]


def test_a_pilot_runs_only_the_chosen_questions(store: Store, questions: list[Question], tmp_path: Path) -> None:
    client = FakeChat(lambda m, msgs, t: final(1, "per cent", "2026-08", "x"))
    assert run(client, store, questions, MODELS, RunLog(tmp_path), "2026-10-15", 0, only={"q003"}, sleep=lambda s: None) == 4
    assert {r["messages"][1]["content"] for r in client.requests} == {questions[2].text}
```

Create `analysis/tests/evallab/test_cli.py`:

```python
from pathlib import Path

import pytest

from evallab import cli
from evallab.cli import MODELS, pilot_ids, pilot_summary, usage
from evallab.questions import Question
from evallab.runner import RunLog
from evallab.store import Store


def test_the_pilot_spreads_twenty_questions_over_the_set(questions: list[Question]) -> None:
    hundred_twenty = [Question(f"q{i:03d}", "s", "en", "", 0, "", "", "", 0, "", "") for i in range(1, 121)]
    chosen = sorted(pilot_ids(hundred_twenty))
    assert len(chosen) == 20 and chosen[:3] == ["q001", "q007", "q013"]
    assert pilot_ids(questions) == {q.id for q in questions}  # fewer than 20: all of them


def test_usage_counts_calls_errors_and_tokens() -> None:
    calls = [{"model": "m", "mode": "tools", "status": "ok", "prompt_tokens": 10, "output_tokens": 2},
             {"model": "m", "mode": "tools", "status": "error"}, {"model": "m", "mode": "memory", "status": "limit"}]
    assert usage(calls) == {"m": {"tools": {"calls": 2, "errors": 1, "prompt_tokens": 10, "output_tokens": 2},
                                  "memory": {"calls": 1, "errors": 1, "prompt_tokens": 0, "output_tokens": 0}}}


def test_the_pilot_summary_shows_usage_timing_and_outcomes(answered: RunLog) -> None:
    summary = pilot_summary(answered.answers(), answered.calls())
    tools = summary[MODELS[0]]["tools"]
    assert {k: v for k, v in tools.items() if k != "median_seconds"} == {
        "calls": 32, "errors": 0, "prompt_tokens": 3200, "output_tokens": 640, "answers": 16, "tool_calls": 16, "statuses": {"ok": 16}}
    assert tools["median_seconds"] >= 0
    assert summary[MODELS[1]]["memory"]["calls"] == 16


def test_the_run_refuses_to_start_when_ollama_is_not_reachable(store: Store, questions: list[Question], monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    sheet = tmp_path / "questions.csv"
    monkeypatch.setattr(cli, "read_questions", lambda path, statistics: questions)
    real = cli.OllamaClient
    monkeypatch.setattr(cli, "OllamaClient", lambda: real("http://127.0.0.1:9", timeout=2))  # nothing listens on port 9
    with pytest.raises(SystemExit, match="Ollama is not reachable at the start of the run"):
        cli.main(["--raw-dir", str(store.root), "--questions", str(sheet), "run"])
```

- [ ] **Step 2: Run the tests to verify they fail**

Run (in `analysis/`): `uv run pytest tests/evallab`
Expected: FAIL with `ImportError while loading conftest` and `ImportError: cannot import name 'MODELS' from 'evallab.cli'`.

- [ ] **Step 3: Write the client**

Create `analysis/evallab/ollama.py`:

```python
"""A small client for the local Ollama server's HTTP API. Cloud models are reached through the same server."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any, Protocol

DEFAULT_URL = "http://localhost:11434"
TIMEOUT_SECONDS = 300


class OllamaError(Exception):
    """A call that failed: the server answered with an error, timed out or could not be reached."""


class UsageLimit(OllamaError):
    """Ollama Cloud refused the call because a usage limit was reached (HTTP 429). The run stops and resumes later."""


class Chat(Protocol):
    def chat(self, model: str, messages: list[dict[str, Any]], tools: list[dict[str, Any]] | None, options: dict[str, Any]) -> dict[str, Any]: ...


class OllamaClient:
    def __init__(self, base_url: str = DEFAULT_URL, timeout: float = TIMEOUT_SECONDS) -> None:
        self.base_url, self.timeout = base_url.rstrip("/"), timeout

    def _call(self, path: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
        data = None if body is None else json.dumps(body).encode()
        request = urllib.request.Request(self.base_url + path, data=data, headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                return json.load(response)
        except urllib.error.HTTPError as err:
            detail = err.read().decode(errors="replace")[:300]
            raise (UsageLimit if err.code == 429 else OllamaError)(f"HTTP {err.code} from {path}: {detail}") from err
        except (urllib.error.URLError, TimeoutError, ConnectionError) as err:
            raise OllamaError(f"{path}: {err}") from err

    def version(self) -> str:
        return str(self._call("/api/version")["version"])

    def show(self, model: str) -> dict[str, Any]:
        return self._call("/api/show", {"model": model})

    def chat(self, model: str, messages: list[dict[str, Any]], tools: list[dict[str, Any]] | None, options: dict[str, Any]) -> dict[str, Any]:
        body: dict[str, Any] = {"model": model, "messages": messages, "stream": False, "options": options}
        if tools:
            body["tools"] = tools
        return self._call("/api/chat", body)
```

- [ ] **Step 4: Write the runner**

Both system prompts ask for the period as `YYYY-MM` or `YYYY-Qn` and give the snapshot date as today, so "latest" means the same thing to every model. The assistant message is sent back as Ollama returned it, including any `thinking`.

Create `analysis/evallab/runner.py`:

```python
"""Ask every question of every model in both modes, one call at a time, logging each call so a stopped run resumes."""

from __future__ import annotations

import json
import logging
import time
from collections.abc import Callable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .ollama import Chat, OllamaError, UsageLimit
from .questions import Question
from .store import Store
from .tools import TOOLS, call_tool

log = logging.getLogger(__name__)

MODES = ("tools", "memory")
MAX_TOOL_CALLS = 6
MAX_TURNS = 10  # chat calls per question at most, so a model that never stops cannot loop forever
RETRIES = 2
BACKOFF_SECONDS = 5.0
SEED = 42
OPTIONS = {"temperature": 0, "seed": SEED}
CAP_NOTE = "Tool call limit reached. Give your final answer now."
ANSWER_FORMAT = ('End your reply with one JSON object and nothing after it: {"value": <number>, "unit": "<unit>", '
                 '"period": "<YYYY-MM for a month or YYYY-Qn for a quarter>", "source": "<dataset id or release URL>"}.')
SYSTEM = {
    "tools": ("You answer questions about Malaysia's official statistics. Today is {today}. Use the tools to find the latest official figure: "
              "datasets on data.gov.my can be out of date, and official releases from DOSM, Bank Negara Malaysia and MYNIC may be newer. " + ANSWER_FORMAT),
    "memory": ("You answer questions about Malaysia's official statistics from what you already know; you have no tools. Today is {today}. "
               "Give the latest official figure you know. " + ANSWER_FORMAT),
}

Sleep = Callable[[float], None]


@dataclass(frozen=True)
class Outcome:
    content: str  # the model's final reply, empty when there was none
    tool_calls: int  # tool calls run, at most MAX_TOOL_CALLS
    seconds: float  # time spent in chat calls, pauses excluded
    status: str  # "ok", "cap" when the tool cap was reached, "error" when a call failed after its retries


class RunLog:
    """Two append-only JSONL files: one line per chat call, one line per finished question run."""

    def __init__(self, folder: Path) -> None:
        folder.mkdir(parents=True, exist_ok=True)
        self.calls_path, self.answers_path = folder / "calls.jsonl", folder / "answers.jsonl"

    @staticmethod
    def _append(path: Path, record: dict[str, Any]) -> None:
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")

    @staticmethod
    def _read(path: Path) -> list[dict[str, Any]]:
        records = []
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines() if path.exists() else [], 1):
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                log.warning("ignoring unreadable line %d of %s, probably cut short by an interruption", number, path.name)
        return records

    def call(self, record: dict[str, Any]) -> None:
        self._append(self.calls_path, record)

    def answer(self, record: dict[str, Any]) -> None:
        self._append(self.answers_path, record)

    def calls(self) -> list[dict[str, Any]]:
        return self._read(self.calls_path)

    def answers(self) -> list[dict[str, Any]]:
        return self._read(self.answers_path)


def now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


class Asker:
    """One model, one mode, one question at a time, with retries, pacing and a log line per call."""

    def __init__(self, client: Chat, store: Store, run_log: RunLog, today: str, pace: float, sleep: Sleep) -> None:
        self.client, self.store, self.log, self.today, self.pace, self.sleep = client, store, run_log, today, pace, sleep

    def chat(self, model: str, mode: str, question: str, messages: list[dict[str, Any]], tools: list[dict[str, Any]] | None) -> tuple[dict[str, Any], float]:
        for attempt in range(RETRIES + 1):
            start = time.perf_counter()
            record = {"time": now(), "model": model, "mode": mode, "question": question, "attempt": attempt}
            try:
                response = self.client.chat(model, messages, tools, OPTIONS)
            except OllamaError as err:
                seconds = time.perf_counter() - start
                self.log.call({**record, "seconds": round(seconds, 3), "status": "limit" if isinstance(err, UsageLimit) else "error", "error": str(err)[:300]})
                if isinstance(err, UsageLimit) or attempt == RETRIES:
                    raise
                self.sleep(BACKOFF_SECONDS * 2**attempt)
                continue
            seconds = time.perf_counter() - start
            self.log.call({**record, "seconds": round(seconds, 3), "status": "ok",
                           "prompt_tokens": response.get("prompt_eval_count"), "output_tokens": response.get("eval_count")})
            self.sleep(self.pace)
            return response, seconds
        raise AssertionError("unreachable")

    def run_tools(self, calls: list[dict[str, Any]], used: int) -> tuple[list[dict[str, Any]], int]:
        """Tool replies for one assistant message. Calls past the cap are refused, not run."""
        replies = []
        for call in calls:
            name, arguments = call["function"]["name"], call["function"].get("arguments", {})
            if isinstance(arguments, str):
                try:
                    arguments = json.loads(arguments)
                except json.JSONDecodeError:
                    arguments = {}
            if used < MAX_TOOL_CALLS:
                content, used = call_tool(self.store, name, arguments), used + 1
            else:
                content = json.dumps({"error": CAP_NOTE})
            replies.append({"role": "tool", "tool_name": name, "content": content})
        return replies, used

    def ask(self, model: str, mode: str, question: Question) -> Outcome:
        messages: list[dict[str, Any]] = [{"role": "system", "content": SYSTEM[mode].replace("{today}", self.today)}, {"role": "user", "content": question.text}]
        used, seconds = 0, 0.0
        try:
            for _ in range(MAX_TURNS):
                offer = TOOLS if mode == "tools" and used < MAX_TOOL_CALLS else None
                response, took = self.chat(model, mode, question.id, messages, offer)
                seconds += took
                message = response.get("message", {})
                calls = message.get("tool_calls") or []
                if not calls or offer is None:
                    return Outcome(message.get("content") or "", used, seconds, "cap" if used >= MAX_TOOL_CALLS else "ok")
                replies, used = self.run_tools(calls, used)
                messages = [*messages, message, *replies]
        except UsageLimit:
            raise
        except OllamaError:
            return Outcome("", used, seconds, "error")
        return Outcome("", used, seconds, "cap")


def run(client: Chat, store: Store, questions: list[Question], models: tuple[str, ...], run_log: RunLog, today: str,
        pace: float, only: set[str] | None = None, sleep: Sleep = time.sleep) -> int:
    """Answer every (question, model, mode) not yet in the log. Returns how many were answered now. A usage limit stops the run."""
    done = {(a["question"], a["model"], a["mode"]) for a in run_log.answers()}
    asker = Asker(client, store, run_log, today, pace, sleep)
    answered = 0
    for question in questions:
        if only is not None and question.id not in only:
            continue
        for model in models:
            for mode in MODES:
                if (question.id, model, mode) in done:
                    continue
                outcome = asker.ask(model, mode, question)
                run_log.answer({"time": now(), "question": question.id, "model": model, "mode": mode, **asdict(outcome)})
                answered += 1
                log.info("%s %s %s: %s after %d tool calls", question.id, model, mode, outcome.status, outcome.tool_calls)
    return answered
```

- [ ] **Step 5: Add the run command**

Replace `analysis/evallab/cli.py` with:

```python
"""Entry point, run from analysis/:

  uv run python -m evallab.cli snapshot      take the snapshot once; later commands only verify it
  uv run python -m evallab.cli draft         draft every answer into evallab/questions.csv for review
  uv run python -m evallab.cli run --pilot   ask the 20 pilot questions and print usage and timing
  uv run python -m evallab.cli run           ask everything not yet answered and print usage and timing
"""

from __future__ import annotations

import argparse
import json
import logging
import statistics
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .ollama import OllamaClient, OllamaError, UsageLimit
from .questions import OUT_OF_DATE, QUESTIONS_PATH, Question, draft_all, read_questions, sheet_rows, write_sheet
from .runner import RunLog, run
from .snapshot import freeze
from .statistics import STATISTICS
from .store import load
from .tools import baseline_answer

ANALYSIS_DIR = Path(__file__).resolve().parents[1]
REPO_DIR = ANALYSIS_DIR.parent
RAW_DIR = ANALYSIS_DIR / "data/raw/evallab"
MODELS = ("gpt-oss:120b-cloud", "deepseek-v4.1-flash:cloud")
PILOT = 20
BY_ID = {s.id: s for s in STATISTICS}


def pilot_ids(questions: list[Question]) -> set[str]:
    """PILOT questions spread evenly over the set, so the pilot touches most statistics and both languages."""
    step = max(1, len(questions) // PILOT)
    return {q.id for q in questions[::step][:PILOT]}


def usage(calls: list[dict[str, Any]]) -> dict[str, dict[str, dict[str, int]]]:
    """Calls, failed calls and tokens per model and mode, from the call log."""
    out: dict[str, dict[str, dict[str, int]]] = {}
    for c in calls:
        u = out.setdefault(c["model"], {}).setdefault(c["mode"], {"calls": 0, "errors": 0, "prompt_tokens": 0, "output_tokens": 0})
        u["calls"] += 1
        u["errors"] += c["status"] != "ok"
        u["prompt_tokens"] += c.get("prompt_tokens") or 0
        u["output_tokens"] += c.get("output_tokens") or 0
    return out


def timing(answers: list[dict[str, Any]]) -> dict[str, Any]:
    if not answers:
        return {"answers": 0}
    return {"answers": len(answers), "median_seconds": round(statistics.median(a["seconds"] for a in answers), 1),
            "tool_calls": sum(a["tool_calls"] for a in answers), "statuses": dict(Counter(a["status"] for a in answers))}


def pilot_summary(answers: list[dict[str, Any]], calls: list[dict[str, Any]]) -> dict[str, dict[str, dict[str, Any]]]:
    """Usage from the call log beside timing and outcomes from the answers, per model and mode."""
    return {model: {mode: {**counts, **timing([a for a in answers if a["model"] == model and a["mode"] == mode])} for mode, counts in modes.items()}
            for model, modes in usage(calls).items()}


def cmd_snapshot(args: argparse.Namespace) -> None:
    snapshot = freeze(args.raw_dir, list(STATISTICS), datetime.now(UTC).date())
    print(f"snapshot of {snapshot['taken']}: {len(snapshot['files'])} files, {len(snapshot['releases'])} releases, catalogue at {snapshot['catalogue']['commit'][:8]}")


def cmd_draft(args: argparse.Namespace) -> None:
    drafts = draft_all(load(args.raw_dir), list(STATISTICS))
    write_sheet(args.questions, sheet_rows(drafts), force=args.force)
    stale, blank = sum(d.status == OUT_OF_DATE for d in drafts), [d.statistic.id for d in drafts if d.value is None]
    print(f"wrote {len(drafts) * 4} questions on {len(drafts)} statistics ({stale} out of date) to {args.questions}")
    if blank:
        print(f"no value found in the release text for: {', '.join(blank)}; fill these in by hand")


def cmd_run(args: argparse.Namespace) -> None:
    store = load(args.raw_dir)
    questions = read_questions(args.questions, list(STATISTICS))
    for statistic in {BY_ID[q.statistic] for q in questions}:
        baseline_answer(store, statistic)  # stops now if any statistic has no data in the snapshot
    client = OllamaClient()
    try:
        ollama = {"version": client.version(), "models": {m: client.show(m).get("details", {}) for m in MODELS}}
    except OllamaError as err:
        raise SystemExit(f"Ollama is not reachable at the start of the run: {err}") from err
    logging.info("Ollama %s; models %s", ollama["version"], ollama["models"])
    run_log = RunLog(args.raw_dir / "runs")
    try:
        run(client, store, questions, MODELS, run_log, store.taken, args.pace, only=pilot_ids(questions) if args.pilot else None)
    except UsageLimit as err:
        raise SystemExit(f"stopped at an Ollama Cloud usage limit ({err}); run the same command later to resume") from err
    print(json.dumps(pilot_summary(run_log.answers(), run_log.calls()), indent=2))


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="python -m evallab.cli", description="Run the LLM Eval Lab freshness study.")
    parser.add_argument("--raw-dir", type=Path, default=RAW_DIR)
    parser.add_argument("--questions", type=Path, default=QUESTIONS_PATH)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("snapshot", help="take the snapshot, or verify the one already taken").set_defaults(handler=cmd_snapshot)
    draft = commands.add_parser("draft", help="draft the answers into the review sheet")
    draft.add_argument("--force", action="store_true", help="replace an existing review sheet")
    draft.set_defaults(handler=cmd_draft)
    ask = commands.add_parser("run", help="ask the models every question not yet answered")
    ask.add_argument("--pilot", action="store_true", help=f"ask only {PILOT} questions and print usage")
    ask.add_argument("--pace", type=float, default=2.0, help="seconds to wait after each call")
    ask.set_defaults(handler=cmd_run)
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%H:%M:%S")
    args.handler(args)


if __name__ == "__main__":
    main()
```

- [ ] **Step 6: Run the tests**

Run (in `analysis/`): `uv run pytest tests/evallab`, then `uv run pytest`.
Expected: `70 passed`, then `196 passed`.

- [ ] **Step 7: Commit**

```bash
git add analysis/evallab/ollama.py analysis/evallab/runner.py analysis/evallab/cli.py analysis/tests/evallab
git commit -m "feat: run the LLM Eval Lab questions through Ollama with tools and resume"
```

- [ ] **Step 8: Run the pilot**

Run: `git checkout -- apps/web/next-env.d.ts`, `git status --porcelain` (expected: no output) and `curl -s http://localhost:11434/api/version` (expected: `{"version":"0.40.4"}`).

Run (in `analysis/`, in the background, with a timeout of at least 60 minutes): `uv run python -m evallab.cli run --pilot 2>&1 | tee /tmp/evallab-pilot.log`
This asks 20 questions (`q001`, `q007`, ... `q115`, spread over the statistics and both languages) of both models in both modes: 80 question runs and roughly 200 chat calls, about 15 to 25 minutes at the default pace. Expected: one `Ollama 0.40.4; models {...}` line, one log line per question run such as `q001 gpt-oss:120b-cloud tools: ok after 3 tool calls`, then a JSON summary per model and mode with `calls`, `errors`, `prompt_tokens`, `output_tokens`, `answers` (20 each), `median_seconds`, `tool_calls` and `statuses`.

If it stops with `stopped at an Ollama Cloud usage limit`, tell Subashanan; rerun the same command when the limit resets, and it continues where it stopped.

- [ ] **Step 9: Read the pilot**

Run (in `analysis/`):

```bash
uv run python - <<'EOF'
import json
answers = [json.loads(line) for line in open("data/raw/evallab/runs/answers.jsonl")]
missing = [a for a in answers if '"value"' not in a["content"] or '"period"' not in a["content"]]
for a in missing:
    print(a["question"], a["model"], a["mode"], a["status"], repr(a["content"][-160:]))
print(len(answers), "answers,", len(missing), "without a JSON answer")
EOF
```

Expected: `80 answers,` and only a few without a JSON answer. Send Subashanan the pilot summary and these counts, with an estimate for the rest: the full run is 480 question runs, so about five times the pilot's calls and tokens again. Ask him to confirm the full run fits his Ollama Cloud plan before Task 10.

If more than about one answer in ten has no JSON answer, or `errors` or `cap` are common, stop and report with examples. Changing a system prompt in `runner.py` makes the pilot's answers incomparable: with Subashanan's agreement, move them aside (`mv data/raw/evallab/runs data/raw/evallab/runs-pilot-1`), commit the change with a test, and run the pilot again.

---

### Task 8: Python: reading and scoring answers, and the bootstrap

**Files:**
- Create: `analysis/evallab/scoring.py`
- Test: `analysis/tests/evallab/test_scoring.py`

**Interfaces:**
- Consumes: `OUT_OF_DATE`, `Question` (Task 5); `Statistic` (Task 3).
- Produces, in `evallab.scoring`: `RESAMPLES = 2000`, `SEED = 42`, `INTERVAL = (2.5, 97.5)`, `BASELINE = "baseline"`, `VIEWS` (`("all-tools", "tools", False)`, `("stale-tools", "tools", True)`, `("all-memory", "memory", False)`: id, mode, out-of-date only); `Score(readable, value_ok, period_ok, source_ok, value, period)` with `latest` (value and period both right); `Run(question, model, mode, score, tool_calls, seconds, content)`; `Cell(model, share, low, high, calls, seconds, questions, by_language, sourced=0.0)` (`sourced` is the % of answers citing a dataset or release in the snapshot); `parse_answer(content) -> dict | None`; `scale_of(text) -> float`; `in_unit(value, unit, statistic) -> float | None`; `rounded(value, decimals) -> Decimal` (half up); `as_period(text, quarterly) -> str | None`; `cites(source, known) -> bool`; `score_answer(content, question, statistic, known) -> Score`; `score_runs(records, questions, statistics, known) -> list[Run]` (the first record per question, model and mode wins); `bootstrap(results, resamples=2000, seed=42) -> tuple[float, float]` over `(statistic, right)` pairs; `views(runs, questions, models, seed=42) -> dict[str, list[Cell]]` (cloud models in order, then the baseline in the two views with tools; raises `ValueError` naming a missing answer). Task 9 turns the cells into the results file.

Values are compared after rounding both sides half up to the statistic's decimals, as the publications round. A scale word in the value (`"RM2.64 trillion"`) wins over the unit field. Periods are read in English and Bahasa Malaysia (month names, `Q2 2026`, `2Q 2026`, `ST2 2026`, `second quarter of 2026`, `suku kedua 2026`); for a quarterly statistic a month counts as its quarter, and for a monthly statistic a quarter is wrong. The bootstrap resamples whole statistics, because a statistic's four questions share one answer and are not independent.

- [ ] **Step 1: Write the failing test**

Create `analysis/tests/evallab/test_scoring.py`:

```python
import json

import pytest

from evallab.questions import Question
from evallab.scoring import as_period, bootstrap, cites, in_unit, parse_answer, score_answer, score_runs, views
from evallab.statistics import STATISTICS

BY_ID = {s.id: s for s in STATISTICS}
KNOWN = frozenset({"lfs_month_youth", "domains", "https://open.dosm.gov.my/publications/labour_month_2026-08"})


@pytest.mark.parametrize(("content", "expected"), [
    ('Here it is:\n```json\n{"value": 10.1, "unit": "per cent", "period": "2026-08", "source": "x"}\n```', 10.1),
    ('The rate was 10.1%. {"value": "10.1", "period": "August 2026"} Hope that helps.', "10.1"),
    ('{"value": 9, "period": "2026-01"} then I checked again: {"value": 10.1, "period": "2026-08"}', 10.1),
    ('{"value": 10.1, "unit": "per cent"}', None),  # no period
    ("I could not find it.", None),
    ('{"value": 10.1, "period": "2026-08"', None),  # cut short
])
def test_parse_answer_takes_the_last_complete_json_answer(content: str, expected: object) -> None:
    answer = parse_answer(content)
    assert (answer or {}).get("value") == expected


@pytest.mark.parametrize(("statistic", "value", "unit", "expected"), [
    ("m3", 2.64, "RM trillion", 2640.0),
    ("m3", "RM2.64 trillion", "", 2640.0),
    ("m3", "2,636,548.8", "RM million", 2636.5488),
    ("employed_persons", 16874.4, "thousand persons", 16.8744),
    ("youth_rate_15_24", "10.1%", "per cent", 10.1),
    ("domains_active", "693,122", "domains", 693122.0),
    ("youth_rate_15_24", True, "per cent", None),
    ("youth_rate_15_24", "not published", "per cent", None),
])
def test_values_are_converted_to_the_statistics_unit(statistic: str, value: object, unit: str, expected: float | None) -> None:
    assert in_unit(value, unit, BY_ID[statistic]) == (pytest.approx(expected) if expected is not None else None)


@pytest.mark.parametrize(("text", "quarterly", "expected"), [
    ("2026-08", False, "2026-08"), ("2026-08-01", False, "2026-08"), ("August 2026", False, "2026-08"), ("Aug. 2026", False, "2026-08"),
    ("Ogos 2026", False, "2026-08"), ("08/2026", False, "2026-08"), ("2026-Q2", True, "2026-Q2"), ("Q2 2026", True, "2026-Q2"),
    ("2Q 2026", True, "2026-Q2"), ("second quarter of 2026", True, "2026-Q2"), ("suku kedua 2026", True, "2026-Q2"), ("ST2 2026", True, "2026-Q2"),
    ("June 2026", True, "2026-Q2"), ("2026-Q2", False, None), ("2026", False, None), ("latest", False, None), (None, False, None), ("2026-13", False, None),
])
def test_periods_are_read_in_english_and_malay(text: object, quarterly: bool, expected: str | None) -> None:
    assert as_period(text, quarterly) == expected


def test_a_source_must_name_something_in_the_snapshot() -> None:
    assert cites("lfs_month_youth", KNOWN) and cites("data.gov.my dataset lfs_month_youth.", KNOWN)
    assert cites("DOSM, https://open.dosm.gov.my/publications/labour_month_2026-08", KNOWN)
    assert not cites("lfs_month_youth_2", KNOWN) and not cites("domains_ipv6", KNOWN) and not cites("https://www.dosm.gov.my", KNOWN) and not cites(None, KNOWN)


def question(value: float, period: str, status: str = "out of date", statistic: str = "youth_rate_15_24", id: str = "q001", language: str = "en") -> Question:
    return Question(id, statistic, language, "?", value, "per cent", period, "", 10.2, "2026-06", status)


def answer(value: object, period: str, source: str = "lfs_month_youth", unit: str = "per cent") -> str:
    return json.dumps({"value": value, "unit": unit, "period": period, "source": source})


def test_scores_check_value_at_the_publications_rounding_and_period() -> None:
    youth = BY_ID["youth_rate_15_24"]
    right = score_answer(answer(10.14, "Aug 2026"), question(10.1, "2026-08"), youth, KNOWN)
    assert right.latest and right.source_ok
    stale = score_answer(answer(10.2, "June 2026"), question(10.1, "2026-08"), youth, KNOWN)
    assert (stale.value_ok, stale.period_ok, stale.latest, stale.value, stale.period) == (False, False, False, 10.2, "2026-06")
    half = score_answer(answer(4.95, "2026-08"), question(5.0, "2026-08"), youth, KNOWN)  # rounds half up, as publications do
    assert half.value_ok
    unreadable = score_answer("No idea.", question(10.1, "2026-08"), youth, KNOWN)
    assert not unreadable.readable and not unreadable.latest


def test_the_bootstrap_resamples_statistics_not_questions() -> None:
    # Two statistics with four questions each: one always right, one always wrong. Resampling whole statistics gives
    # shares of only 0, 50 or 100, so the interval spans 0 to 100; resampling single questions would be far narrower.
    results = [("a", True)] * 4 + [("b", False)] * 4
    assert bootstrap(results) == (0.0, 100.0)
    assert bootstrap(results, seed=7) == bootstrap(results, seed=7)


def test_views_need_every_answer_and_keep_the_baseline_out_of_memory() -> None:
    questions = [question(10.1, "2026-08", id="q001"), question(2.9, "2026-08", status="current", statistic="unemployment_rate", id="q002", language="ms")]
    records = [{"question": q.id, "model": m, "mode": mode, "content": answer(q.value if m == "a" else 1.0, q.period), "tool_calls": 2, "seconds": 3.0}
               for q in questions for m, mode in (("a", "tools"), ("a", "memory"), ("baseline", "tools"))]
    records.append({**records[0], "content": "a duplicate is ignored"})
    runs = score_runs(records, questions, BY_ID, KNOWN)
    cells = views(runs, questions, ("a",))
    assert {v: [(c.model, c.share, c.questions) for c in cs] for v, cs in cells.items()} == {
        "all-tools": [("a", 100.0, 2), ("baseline", 0.0, 2)],
        "stale-tools": [("a", 100.0, 1), ("baseline", 0.0, 1)],
        "all-memory": [("a", 100.0, 2)],
    }
    assert cells["all-tools"][0].by_language == {"en": 100.0, "ms": 100.0} and cells["all-tools"][0].calls == 2.0
    assert cells["all-tools"][0].sourced == 100.0
    with pytest.raises(ValueError, match="a has no memory answer for 1 questions, such as q002"):
        views([r for r in runs if not (r.mode == "memory" and r.question.id == "q002")], questions, ("a",))
```

- [ ] **Step 2: Run the test to verify it fails**

Run (in `analysis/`): `uv run pytest tests/evallab/test_scoring.py`
Expected: FAIL with `ModuleNotFoundError: No module named 'evallab.scoring'`.

- [ ] **Step 3: Write the scoring**

Create `analysis/evallab/scoring.py`:

```python
"""Read each final answer, score it against the verified answer, and summarise each model in each view with bootstrap intervals."""

from __future__ import annotations

import json
import re
import statistics as stats
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

import numpy as np

from .questions import OUT_OF_DATE, Question
from .statistics import Statistic

RESAMPLES = 2000
SEED = 42
INTERVAL = (2.5, 97.5)
BASELINE = "baseline"
VIEWS = (("all-tools", "tools", False), ("stale-tools", "tools", True), ("all-memory", "memory", False))  # id, mode, out-of-date only
SCALE_WORDS = {"thousand": 1e3, "ribu": 1e3, "million": 1e6, "juta": 1e6, "billion": 1e9, "bilion": 1e9, "trillion": 1e12, "trilion": 1e12}
MONTH_NAMES = (
    ("january", "jan", "januari"), ("february", "feb", "februari"), ("march", "mar", "mac"), ("april", "apr"), ("may", "mei"), ("june", "jun"),
    ("july", "jul", "julai"), ("august", "aug", "ogos", "ogo"), ("september", "sep", "sept"), ("october", "oct", "oktober", "okt"),
    ("november", "nov"), ("december", "dec", "disember", "dis"),
)
MONTHS = {name: i + 1 for i, names in enumerate(MONTH_NAMES) for name in names}
QUARTER_WORDS = {"first": 1, "second": 2, "third": 3, "fourth": 4, "pertama": 1, "kedua": 2, "ketiga": 3, "keempat": 4}
NUMBER = re.compile(r"-?\d[\d,]*(?:\.\d+)?")


@dataclass(frozen=True)
class Score:
    readable: bool  # a final JSON answer with a value and a period was found
    value_ok: bool
    period_ok: bool
    source_ok: bool
    value: float | None  # the answer's value in the statistic's unit
    period: str | None  # the answer's period as YYYY-MM or YYYY-Qn

    @property
    def latest(self) -> bool:
        return self.value_ok and self.period_ok


@dataclass(frozen=True)
class Run:
    question: Question
    model: str
    mode: str
    score: Score
    tool_calls: int
    seconds: float
    content: str


@dataclass(frozen=True)
class Cell:
    """One model in one view."""

    model: str
    share: float  # % of questions answered with the latest figure
    low: float
    high: float
    calls: float  # mean tool calls per answer
    seconds: float  # median seconds per answer
    questions: int
    by_language: dict[str, float]
    sourced: float = 0.0  # % of answers citing a dataset or release in the snapshot


def parse_answer(content: str) -> dict[str, Any] | None:
    """The last JSON object in a reply that has a value and a period, inside a code fence or not."""
    decoder, found = json.JSONDecoder(), None
    for start in (i for i, ch in enumerate(content) if ch == "{"):
        try:
            candidate, _ = decoder.raw_decode(content, start)
        except json.JSONDecodeError:
            continue
        if isinstance(candidate, dict) and "value" in candidate and "period" in candidate:
            found = candidate
    return found


def scale_of(text: str) -> float:
    words = re.findall(r"[a-z]+", text.lower())
    return next((SCALE_WORDS[w] for w in words if w in SCALE_WORDS), 1.0)


def in_unit(value: Any, unit: Any, statistic: Statistic) -> float | None:
    """The answer's value in the statistic's unit. A scale word in the value ("RM2.64 trillion") wins over the unit field."""
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, int | float):
        number, scale = float(value), scale_of(str(unit or ""))
    else:
        match = NUMBER.search(str(value))
        if match is None:
            return None
        number = float(match[0].replace(",", ""))
        scale = scale_of(str(value)) if scale_of(str(value)) != 1.0 else scale_of(str(unit or ""))
    return number * scale / scale_of(statistic.unit)


def rounded(value: float, decimals: int) -> Decimal:
    return Decimal(repr(value)).quantize(Decimal(1).scaleb(-decimals), rounding=ROUND_HALF_UP)


def as_period(text: Any, quarterly: bool) -> str | None:
    """YYYY-MM or YYYY-Qn from the ways models write a period. A month counts as its quarter for a quarterly statistic."""
    t = re.sub(r"\s+", " ", str(text or "")).strip().lower()
    quarter = (re.search(r"(\d{4}) ?-? ?q([1-4])\b", t) or re.search(r"\bq([1-4]) ?-? ?(\d{4})", t) or re.search(r"\b([1-4])q ?(\d{4})", t)
               or re.search(r"\bst([1-4]) ?(\d{4})", t))
    words = re.search(r"(first|second|third|fourth) quarter (?:of )?(\d{4})|suku (?:tahun )?(pertama|kedua|ketiga|keempat),? (\d{4})", t)
    if quarter or words:
        if not quarterly:
            return None
        if words:
            return f"{words[2] or words[4]}-Q{QUARTER_WORDS[words[1] or words[3]]}"
        year, q = (quarter[1], quarter[2]) if len(quarter[1]) == 4 else (quarter[2], quarter[1])
        return f"{year}-Q{q}"
    month = re.search(r"\b(\d{4})[-/](\d{1,2})\b", t) or re.search(r"\b(\d{1,2})/(\d{4})\b", t)
    if month:
        year, m = (month[1], int(month[2])) if len(month[1]) == 4 else (month[2], int(month[1]))
    else:
        named = re.search(r"\b([a-z]+)\.? (\d{4})\b", t)
        if named is None or named[1] not in MONTHS:
            return None
        year, m = named[2], MONTHS[named[1]]
    if not 1 <= m <= 12:
        return None
    return f"{year}-Q{(m - 1) // 3 + 1}" if quarterly else f"{year}-{m:02d}"


def cites(source: Any, known: frozenset[str]) -> bool:
    """True when the source names a dataset id or a URL that is in the snapshot."""
    text = str(source or "").strip()
    return any((k in text) if "/" in k else re.search(rf"(?<![\w.-]){re.escape(k)}(?![\w-])", text) is not None for k in known)


def score_answer(content: str, question: Question, statistic: Statistic, known: frozenset[str]) -> Score:
    answer = parse_answer(content)
    if answer is None:
        return Score(False, False, False, False, None, None)
    value = in_unit(answer.get("value"), answer.get("unit"), statistic)
    period = as_period(answer.get("period"), statistic.quarterly)
    value_ok = value is not None and rounded(value, statistic.decimals) == rounded(question.value, statistic.decimals)
    return Score(True, value_ok, period == question.period, cites(answer.get("source"), known), value, period)


def score_runs(records: list[dict[str, Any]], questions: list[Question], statistics: dict[str, Statistic], known: frozenset[str]) -> list[Run]:
    """Scored runs from answer records: one per (question, model, mode), the first record winning."""
    by_id = {q.id: q for q in questions}
    seen, runs = set(), []
    for r in records:
        key = (r["question"], r["model"], r["mode"])
        if key in seen or r["question"] not in by_id:
            continue
        seen.add(key)
        q = by_id[r["question"]]
        runs.append(Run(q, r["model"], r["mode"], score_answer(r["content"], q, statistics[q.statistic], known), r["tool_calls"], r["seconds"], r["content"]))
    return runs


def bootstrap(results: list[tuple[str, bool]], resamples: int = RESAMPLES, seed: int = SEED) -> tuple[float, float]:
    """A 95% interval for the share right, resampling statistics with all their questions, since a statistic's questions are not independent."""
    groups: dict[str, list[bool]] = {}
    for statistic, right in results:
        groups.setdefault(statistic, []).append(right)
    hits = np.array([sum(v) for v in groups.values()], dtype=float)
    counts = np.array([len(v) for v in groups.values()], dtype=float)
    picks = np.random.default_rng(seed).integers(0, len(groups), size=(resamples, len(groups)))
    low, high = np.percentile(100 * hits[picks].sum(axis=1) / counts[picks].sum(axis=1), INTERVAL)
    return float(low), float(high)


def cell(model: str, runs: list[Run], seed: int) -> Cell:
    results = [(r.question.statistic, r.score.latest) for r in runs]
    low, high = bootstrap(results, seed=seed)
    languages = sorted({r.question.language for r in runs})
    by_language = {lang: 100 * float(np.mean([r.score.latest for r in runs if r.question.language == lang])) for lang in languages}
    share = 100 * float(np.mean([right for _, right in results]))
    calls = float(np.mean([r.tool_calls for r in runs]))
    sourced = 100 * float(np.mean([r.score.source_ok for r in runs]))
    return Cell(model, share, low, high, calls, float(stats.median(r.seconds for r in runs)), len(runs), by_language, sourced)


def views(runs: list[Run], questions: list[Question], models: tuple[str, ...], seed: int = SEED) -> dict[str, list[Cell]]:
    """Each view's cells: the cloud models in order, then the baseline where it has a mode. Every model must have every question."""
    out = {}
    for view, mode, stale_only in VIEWS:
        wanted = {q.id for q in questions if not stale_only or q.status == OUT_OF_DATE}
        cells = []
        for model in (*models, BASELINE) if mode == "tools" else models:
            chosen = [r for r in runs if r.model == model and r.mode == mode and r.question.id in wanted]
            missing = wanted - {r.question.id for r in chosen}
            if missing:
                raise ValueError(f"{model} has no {mode} answer for {len(missing)} questions, such as {min(missing)}; run again to finish")
            cells.append(cell(model, chosen, seed))
        out[view] = cells
    return out
```

- [ ] **Step 4: Run the tests**

Run (in `analysis/`): `uv run pytest tests/evallab`, then `uv run pytest`.
Expected: `106 passed`, then `232 passed`.

- [ ] **Step 5: Check the scoring on the pilot's real answers**

Run (in `analysis/`):

```bash
uv run python - <<'EOF'
import json
from pathlib import Path
from evallab.questions import QUESTIONS_PATH, read_questions
from evallab.scoring import score_runs
from evallab.statistics import STATISTICS
from evallab.store import load
store = load(Path("data/raw/evallab"))
questions = read_questions(QUESTIONS_PATH, list(STATISTICS))
records = [json.loads(line) for line in open("data/raw/evallab/runs/answers.jsonl")]
runs = score_runs(records, questions, {s.id: s for s in STATISTICS}, store.sources())
for model in sorted({r.model for r in runs}):
    for mode in ("tools", "memory"):
        mine = [r for r in runs if r.model == model and r.mode == mode]
        print(model, mode, len(mine), "readable", sum(r.score.readable for r in mine), "latest", sum(r.score.latest for r in mine), "source", sum(r.score.source_ok for r in mine))
for r in runs:
    if r.score.readable and (r.score.value is None or r.score.period is None):
        print("not normalised:", r.question.id, r.model, r.mode, r.content[-160:])
EOF
```

Expected: four lines of 20 runs each, and few or no `not normalised` lines. Each `not normalised` line is a value or period format the scoring does not read yet. If one is a fair way to write the figure (for example a period written `Aug-26`), add it as a case to the matching parametrised test, see it fail, extend `in_unit` or `as_period`, and rerun the tests before committing. These counts are not results; do not report them as such.

- [ ] **Step 6: Commit**

```bash
git add analysis/evallab/scoring.py analysis/tests/evallab/test_scoring.py
git commit -m "feat: score LLM Eval Lab answers with a bootstrap over statistics"
```

---

### Task 9: Python: templated results, the manifest and the full command

**Files:**
- Create: `analysis/evallab/export.py`, `analysis/tests/evallab/contract.py`
- Modify: `analysis/evallab/cli.py`
- Test: `analysis/tests/evallab/test_export.py`, `analysis/tests/evallab/test_pipeline.py`

**Interfaces:**
- Consumes: `BASELINE`, `VIEWS`, `Cell`, `Run`, `rounded`, `RESAMPLES`, `SEED`, `score_runs`, `views` (Task 8); `OUT_OF_DATE`, `Question` (Task 5); `MAX_TOOL_CALLS`, `MODES`, `OPTIONS`, `RunLog` (Task 7); `Store.sources()`, `baseline_answer` (Task 4); `SNAPSHOT` (Task 3); `forecasting.cli.git_state`, `forecasting.export.write_json`, `forecasting.data.sha256_of`.
- Produces, in `evallab.export`: `DISPLAY` (`gpt-oss 120B`, `DeepSeek V4.1 Flash`, `Open data only`), `VIEW_LABELS`, `METRIC = "% with the latest figure"`, `PER_RULE = 2`; `name`, `pct` (whole number, half up), `join_names`, `long_date`, `period_label` (`August 2026`, `Q2 2026`), `figure(value, statistic)` (`RM7.4 billion`, `10.1 per cent`, `693,122 domains`), `seconds_label`, `leaders(cells)`, `answer_text(views)`, `key_numbers(views, statistics, questions, taken)`, `row(cell)`, `tasks(views)`, `failure_note(run, statistic)`, `error_examples(runs, statistics)`, `build_results(views, runs, questions, statistics, taken, run, retrieved) -> dict` (the `LlmEvalResults` JSON), `scores_json(views)` (unrounded scores with the English and Bahasa Malaysia split, for the manifest).
- Produces, in `evallab.cli`: `RESULTS_PATH`, `MANIFEST_PATH`, `LIBRARIES`, `baseline_records(store, questions)`, `sources(snapshot)`, `build_manifest(store, questions, questions_path, scored, run_log, ollama, packages, git) -> dict`, `finish(store, questions, answers, run_info) -> tuple[dict, dict]` (results and manifest scores); `run` without `--pilot` now scores everything and writes `apps/web/src/content/results/llm-eval-lab.json` and `analysis/outputs/llm-eval-lab-manifest.json` once every answer is in.
- Produces, in `tests/evallab/contract.py`: `check_results(results)`, the Python mirror of `parseLlmEvalResults` (Task 2). Task 10 runs it on the real file.

All prose is a template over computed numbers. The answer names the cloud model with the highest rounded share on out-of-date series with tools, or every model tied at that share, against the baseline's share on the same questions. The key numbers are that share with its interval, the change from memory to tools for the same model across all series (in points, with "higher", "lower" or no change), and the number of statistics and verified questions with the snapshot date. Error examples follow three rules in order, at most two each and one per question, with tools before memory: the open dataset's out-of-date figure quoted, the wrong period, and no readable answer. The results' `retrieved` dates are the snapshot date for the data and the question set, and the run date for Ollama Cloud.

- [ ] **Step 1: Write the failing tests**

Create `analysis/tests/evallab/contract.py`:

```python
"""The rules parseLlmEvalResults (apps/web/src/content/results/parse-llm-eval.ts) enforces, mirrored here so the
pipeline's own tests fail on a file the site would reject."""

from __future__ import annotations

import json
import math
import re
from typing import Any

TASK_IDS = ["all-tools", "stale-tools", "all-memory"]
ROLES = ["cloud", "baseline"]
ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def text(value: Any) -> bool:
    return isinstance(value, str) and value.strip() != ""


def whole(value: Any, low: int, high: int) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and low <= value <= high


def check_base(r: dict[str, Any]) -> None:
    assert text(r["answer"]), "answer"
    assert len(r["keyNumbers"]) == 3 and all(text(k[f]) for k in r["keyNumbers"] for f in ("value", "label", "caveat")), "keyNumbers"
    assert all(text(r["run"][f]) for f in ("commit", "manifest", "python")) and ISO_DATE.match(r["run"]["lastRun"]), "run"
    assert r["retrieved"] and all(ISO_DATE.match(d) for d in r["retrieved"].values()), "retrieved"


def check_row(path: str, row: dict[str, Any]) -> None:
    assert text(row["model"]) and row["role"] in ROLES, path
    assert all(whole(row[k], 0, 100) for k in ("low", "score", "high")) and row["low"] <= row["score"] <= row["high"], f"{path} score"
    calls = row["callsPerAnswer"]
    assert isinstance(calls, int | float) and not isinstance(calls, bool) and math.isfinite(calls) and 0 <= calls <= 6, f"{path} callsPerAnswer"
    assert text(row["callsLabel"]) and text(row["latency"]), f"{path} labels"


def check_task(i: int, task: dict[str, Any]) -> None:
    assert task["id"] == TASK_IDS[i] and text(task["label"]) and text(task["metric"]), f"tasks[{i}]"
    for j, row in enumerate(task["rows"]):
        check_row(f"tasks[{i}].rows[{j}]", row)
    baselines = sum(r["role"] == "baseline" for r in task["rows"])
    assert baselines == (0 if task["id"] == "all-memory" else 1) and len(task["rows"]) > baselines, f"tasks[{i}] roles"
    assert len({r["model"] for r in task["rows"]}) == len(task["rows"]), f"tasks[{i}] models"


def check_results(r: dict[str, Any]) -> None:
    json.dumps(r, allow_nan=False)  # NaN or infinity would not survive JSON
    check_base(r)
    assert len(r["tasks"]) == 3, "tasks"
    for i, task in enumerate(r["tasks"]):
        check_task(i, task)
    assert len(r["errorExamples"]) <= 6, "errorExamples"
    for e in r["errorExamples"]:
        assert all(text(e[f]) for f in ("input", "expected", "model", "output", "note")) and isinstance(e["correct"], bool), "errorExamples fields"
```

Create `analysis/tests/evallab/test_export.py`:

```python
import json
import re

import pytest

from evallab.export import answer_text, error_examples, figure, key_numbers, long_date, period_label, row
from evallab.questions import Question
from evallab.scoring import Cell, score_runs
from evallab.statistics import STATISTICS

BY_ID = {s.id: s for s in STATISTICS}
DASHES = re.compile("[–—←-↓]")
GPT, DEEPSEEK = "gpt-oss:120b-cloud", "deepseek-v4.1-flash:cloud"


def cell(model: str, share: float, low: float = 10.0, high: float = 90.0) -> Cell:
    return Cell(model, share, low, high, 3.25, 8.04, 40, {"en": share, "ms": share})


def views(gpt: float, deepseek: float, memory: float = 20.0) -> dict[str, list[Cell]]:
    return {
        "all-tools": [cell(GPT, 70.0), cell(DEEPSEEK, 60.0), cell("baseline", 50.0)],
        "stale-tools": [cell(GPT, gpt, 41.2, 79.6), cell(DEEPSEEK, deepseek), cell("baseline", 0.0, 0.0, 0.0)],
        "all-memory": [cell(GPT, memory), cell(DEEPSEEK, 15.0)],
    }


def test_the_answer_names_the_leader_on_out_of_date_series() -> None:
    assert answer_text(views(62.4, 48.0)) == (
        "On out-of-date series, gpt-oss 120B gave the latest official figure for 62% of questions with tools, against 0% for the open data alone.")


def test_a_tie_on_rounded_shares_names_both_models() -> None:
    text = answer_text(views(62.4, 61.6))
    assert text.startswith("On out-of-date series, gpt-oss 120B and DeepSeek V4.1 Flash tied, each giving the latest official figure for 62%")
    first = key_numbers(views(62.4, 61.6), 30, 120, "2026-10-16")[0]
    assert first["label"].endswith("by gpt-oss 120B and DeepSeek V4.1 Flash, with tools.") and first["caveat"].endswith("Interval for gpt-oss 120B.")


def test_key_numbers_come_from_the_views() -> None:
    first, change, size = key_numbers(views(62.4, 48.0), 30, 120, "2026-10-16")
    assert first == {"value": "62%", "label": "of questions on out-of-date series answered with the latest figure by gpt-oss 120B, with tools.",
                     "caveat": "95% interval 41 to 80%, from a bootstrap over statistics."}
    assert change == {"value": "50 points", "label": "higher latest-figure share for gpt-oss 120B with tools than from memory, across all series.",
                      "caveat": "From 20% from memory to 70% with tools."}
    assert size == {"value": "30", "label": "statistics, asked 4 ways each: 120 questions verified against the official release.",
                    "caveat": "Snapshot of open data and releases taken on 16 October 2026; results describe that day."}


@pytest.mark.parametrize(("memory", "value", "start"), [(69.0, "1 point", "higher"), (71.0, "1 point", "lower"), (70.0, "0 points", "difference for gpt-oss 120B")])
def test_the_change_from_memory_reads_well_at_any_size(memory: float, value: str, start: str) -> None:
    change = key_numbers(views(62.4, 48.0, memory), 30, 120, "2026-10-16")[1]
    assert change["value"] == value and change["label"].startswith(start)


def test_rows_round_half_up_and_keep_the_score_inside_its_interval() -> None:
    assert row(Cell(GPT, 62.5, 62.6, 80.0, 3.25, 8.04, 40, {})) == {
        "model": "gpt-oss 120B", "role": "cloud", "score": 63, "low": 63, "high": 80, "callsPerAnswer": 3.25, "callsLabel": "3.2", "latency": "8.0 s"}
    baseline = row(Cell("baseline", 50.0, 38.0, 66.0, 0.0, 0.00002, 120, {}))
    assert (baseline["model"], baseline["role"], baseline["callsLabel"], baseline["latency"]) == ("Open data only", "baseline", "0", "under 0.1 s")


def test_labels_for_periods_figures_and_dates() -> None:
    assert (period_label("2026-08"), period_label("2026-Q2"), long_date("2026-10-16")) == ("August 2026", "Q2 2026", "16 October 2026")
    assert figure(2636.5488, BY_ID["m3"]) == "RM2,636.5 billion" and figure(46.5, BY_ID["productivity_hour"]) == "RM46.5 per hour"
    assert figure(693122.0, BY_ID["domains_active"]) == "693,122 domains" and figure(10.1, BY_ID["youth_rate_15_24"]) == "10.1 per cent"


def youth(id: str, text: str = "What is it?") -> Question:
    return Question(id, "youth_rate_15_24", "en", text, 10.1, "per cent", "2026-08", "", 10.2, "2026-06", "out of date")


def reply(value: object, period: str) -> str:
    return json.dumps({"value": value, "unit": "per cent", "period": period, "source": "lfs_month_youth"})


def test_error_examples_follow_the_rules_in_order() -> None:
    questions = [youth(f"q00{i}") for i in range(1, 9)]
    contents = [reply(10.2, "2026-06"), reply(10.2, "2026-06"), reply(10.2, "2026-06"), reply(10.1, "2026-07"), "Sorry.", "", reply(10.1, "2026-08"), reply(9.0, "2026-08")]
    records = [{"question": q.id, "model": GPT, "mode": "tools", "content": c, "tool_calls": 1, "seconds": 1.0} for q, c in zip(questions, contents, strict=True)]
    records += [{"question": "q001", "model": DEEPSEEK, "mode": "memory", "content": "", "tool_calls": 0, "seconds": 1.0},
                {"question": "q001", "model": "baseline", "mode": "tools", "content": reply(10.2, "2026-06"), "tool_calls": 0, "seconds": 0.0}]
    examples = error_examples(score_runs(records, questions, BY_ID, frozenset()), BY_ID)

    assert [(e["input"], e["note"]) for e in examples] == [
        ("What is it?", "Gave the open dataset's figure for June 2026, not the release for August 2026."),
        ("What is it?", "Gave the open dataset's figure for June 2026, not the release for August 2026."),
        ("What is it?", "Named July 2026 instead of August 2026."),
        ("What is it?", "No final JSON answer could be read."),
        ("What is it?", "No final JSON answer could be read."),
    ]
    assert examples[0] == {"input": "What is it?", "expected": "10.1 per cent, August 2026", "model": "gpt-oss 120B, with tools",
                           "output": "10.2 per cent, June 2026", "note": examples[0]["note"], "correct": False}
    assert examples[3]["output"] == "No final answer"
    for line in [answer_text(views(62.4, 61.6)), *[v for k in key_numbers(views(62.4, 61.6), 30, 120, "2026-10-16") for v in k.values()], *[e["note"] for e in examples]]:
        assert not DASHES.search(line)
```

Create `analysis/tests/evallab/test_pipeline.py`:

```python
import json
from pathlib import Path

import pytest

from evallab.cli import MODELS, build_manifest, finish
from evallab.questions import Question
from evallab.runner import RunLog
from evallab.store import Store

from .contract import check_results

RUN_INFO = {"commit": "abc1234", "manifest": "analysis/outputs/llm-eval-lab-manifest.json", "python": "3.12.9", "lastRun": "2026-10-16"}


def test_a_full_run_on_the_synthetic_world_passes_the_site_contract(store: Store, questions: list[Question], answered: RunLog) -> None:
    results, scored = finish(store, questions, answered.answers(), RUN_INFO)
    check_results(results)

    shares = {t["id"]: {r["model"]: r["score"] for r in t["rows"]} for t in results["tasks"]}
    assert shares == {
        "all-tools": {"gpt-oss 120B": 100, "DeepSeek V4.1 Flash": 25, "Open data only": 25},
        "stale-tools": {"gpt-oss 120B": 100, "DeepSeek V4.1 Flash": 0, "Open data only": 0},
        "all-memory": {"gpt-oss 120B": 0, "DeepSeek V4.1 Flash": 0},
    }
    assert results["answer"] == "On out-of-date series, gpt-oss 120B gave the latest official figure for 100% of questions with tools, against 0% for the open data alone."
    assert [k["value"] for k in results["keyNumbers"]] == ["100%", "100 points", "4"]
    assert results["retrieved"] == {"data.gov.my datasets": "2026-10-15", "DOSM releases": "2026-10-15", "Bank Negara Malaysia": "2026-10-15",
                                    "MYNIC": "2026-10-15", "Question set": "2026-10-15", "Ollama Cloud": "2026-10-16"}
    assert {e["note"].split(" ")[0] for e in results["errorExamples"]} == {"Gave", "Named", "No"}
    assert scored["stale-tools"]["baseline"]["share"] == 0.0 and scored["all-tools"][MODELS[0]]["by_language"] == {"en": 100.0, "ms": 100.0}
    assert scored["all-tools"][MODELS[0]]["source_given"] == 100.0 and scored["all-memory"][MODELS[0]]["source_given"] == 0.0


def test_the_manifest_records_the_provenance_of_a_run(store: Store, questions: list[Question], answered: RunLog, tmp_path: Path) -> None:
    sheet = tmp_path / "questions.csv"
    sheet.write_text("id\n")
    _, scored = finish(store, questions, answered.answers(), RUN_INFO)
    ollama = {"version": "0.40.4", "models": {m: {"parent_model": m.split(":")[0]} for m in MODELS}}
    manifest = build_manifest(store, questions, sheet, scored, answered, ollama, {"python": "3.12.9"}, {"commit": "abc1234", "dirty": False})

    assert manifest["snapshot"]["taken"] == "2026-10-15" and manifest["snapshot"]["catalogue"]["commit"].startswith("4ba675a3")
    assert manifest["questions"]["questions"] == 16 and manifest["questions"]["out_of_date_statistics"] == ["domains_active", "m3", "youth_rate_15_24"]
    assert manifest["runs"] == {m: {"tools": 16, "memory": 16} for m in MODELS}
    assert manifest["usage"][MODELS[0]]["tools"] == {"calls": 32, "errors": 0, "prompt_tokens": 3200, "output_tokens": 640}
    assert manifest["settings"]["bootstrap"] == {"unit": "statistic", "resamples": 2000, "seed": 42} and manifest["ollama_version"] == "0.40.4"
    assert manifest["results_file"] == "apps/web/src/content/results/llm-eval-lab.json"
    json.dumps(manifest, allow_nan=False)


def test_scoring_stops_while_any_answer_is_missing(store: Store, questions: list[Question], answered: RunLog) -> None:
    with pytest.raises(ValueError, match="has no tools answer"):
        finish(store, questions, answered.answers()[1:], RUN_INFO)
```

- [ ] **Step 2: Run the tests to verify they fail**

Run (in `analysis/`): `uv run pytest tests/evallab/test_export.py tests/evallab/test_pipeline.py`
Expected: FAIL with `ModuleNotFoundError: No module named 'evallab.export'` (from `test_export.py`) and `ImportError: cannot import name 'build_manifest' from 'evallab.cli'` (from `test_pipeline.py`).

- [ ] **Step 3: Write the templates and the results**

Create `analysis/evallab/export.py`:

```python
"""Turn the scored views into the site's LlmEvalResults JSON. All prose comes from templates over computed numbers."""

from __future__ import annotations

from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

from .questions import OUT_OF_DATE, Question
from .scoring import BASELINE, VIEWS, Cell, Run, rounded
from .statistics import Statistic

DISPLAY = {"gpt-oss:120b-cloud": "gpt-oss 120B", "deepseek-v4.1-flash:cloud": "DeepSeek V4.1 Flash", BASELINE: "Open data only"}
VIEW_LABELS = {"all-tools": "All series, with tools", "stale-tools": "Out-of-date series, with tools", "all-memory": "All series, from memory"}
METRIC = "% with the latest figure"
PER_RULE = 2  # error examples per rule, so at most 6
MONTH_NAMES = ("January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December")


def name(model: str) -> str:
    return DISPLAY.get(model, model)


def pct(value: float) -> int:
    """A share as a whole number, rounding half up like the publications."""
    return int(Decimal(repr(value)).quantize(Decimal(1), rounding=ROUND_HALF_UP))


def join_names(names: list[str]) -> str:
    return names[0] if len(names) == 1 else f"{', '.join(names[:-1])} and {names[-1]}"


def long_date(iso: str) -> str:
    d = date.fromisoformat(iso[:10])
    return f"{d.day} {d:%B %Y}"


def period_label(period: str) -> str:
    year, part = period.split("-")
    return f"{part} {year}" if part.startswith("Q") else f"{MONTH_NAMES[int(part) - 1]} {year}"


def figure(value: float, statistic: Statistic) -> str:
    number = f"{rounded(value, statistic.decimals):,}"
    return f"RM{number}{statistic.unit[2:]}" if statistic.unit.startswith("RM ") else f"{number} {statistic.unit}"


def seconds_label(seconds: float) -> str:
    return "under 0.1 s" if seconds < 0.1 else f"{seconds:.1f} s"


def leaders(cells: list[Cell]) -> list[Cell]:
    """The cloud models with the highest rounded share, in model order."""
    clouds = [c for c in cells if c.model != BASELINE]
    top = max(pct(c.share) for c in clouds)
    return [c for c in clouds if pct(c.share) == top]


def answer_text(views: dict[str, list[Cell]]) -> str:
    stale = views["stale-tools"]
    top, base = leaders(stale), next(c for c in stale if c.model == BASELINE)
    against = f"against {pct(base.share)}% for the open data alone."
    if len(top) == 1:
        return f"On out-of-date series, {name(top[0].model)} gave the latest official figure for {pct(top[0].share)}% of questions with tools, {against}"
    return f"On out-of-date series, {join_names([name(c.model) for c in top])} tied, each giving the latest official figure for {pct(top[0].share)}% of questions with tools, {against}"


def key_numbers(views: dict[str, list[Cell]], statistics: int, questions: int, taken: str) -> list[dict[str, str]]:
    top = leaders(views["stale-tools"])
    best = top[0]
    tools = next(c for c in views["all-tools"] if c.model == best.model)
    memory = next(c for c in views["all-memory"] if c.model == best.model)
    gap = pct(tools.share) - pct(memory.share)
    tied = f" Interval for {name(best.model)}." if len(top) > 1 else ""
    change = f"{'higher' if gap > 0 else 'lower'} latest-figure share for {name(best.model)} with tools than from memory" if gap else f"difference for {name(best.model)} between tools and memory"
    return [
        {
            "value": f"{pct(best.share)}%",
            "label": f"of questions on out-of-date series answered with the latest figure by {join_names([name(c.model) for c in top])}, with tools.",
            "caveat": f"95% interval {pct(best.low)} to {pct(best.high)}%, from a bootstrap over statistics.{tied}",
        },
        {
            "value": f"{abs(gap)} point{'' if abs(gap) == 1 else 's'}",
            "label": f"{change}, across all series.",
            "caveat": f"From {pct(memory.share)}% from memory to {pct(tools.share)}% with tools.",
        },
        {
            "value": str(statistics),
            "label": f"statistics, asked 4 ways each: {questions:,} questions verified against the official release.",
            "caveat": f"Snapshot of open data and releases taken on {long_date(taken)}; results describe that day.",
        },
    ]


def row(c: Cell) -> dict[str, Any]:
    score = pct(c.share)
    return {
        "model": name(c.model), "role": "baseline" if c.model == BASELINE else "cloud",
        "score": score, "low": min(pct(c.low), score), "high": max(pct(c.high), score),
        "callsPerAnswer": round(c.calls, 2), "callsLabel": "0" if c.calls == 0 else f"{c.calls:.1f}", "latency": seconds_label(c.seconds),
    }


def tasks(views: dict[str, list[Cell]]) -> list[dict[str, Any]]:
    return [{"id": view, "label": VIEW_LABELS[view], "metric": METRIC, "rows": [row(c) for c in views[view]]} for view, _, _ in VIEWS]


def quoted_dataset(r: Run, s: Statistic) -> bool:
    """The answer gave the out-of-date dataset's figure instead of the release's."""
    q = r.question
    return q.status == OUT_OF_DATE and r.score.value is not None and rounded(r.score.value, s.decimals) == rounded(q.dataset_value, s.decimals)


def failure_note(r: Run, s: Statistic) -> tuple[int, str] | None:
    """The first rule a wrong answer breaks, as (rule number, note); None for a right answer."""
    q = r.question
    if not r.score.readable:
        return 2, "No final JSON answer could be read."
    if r.score.latest:
        return None
    if quoted_dataset(r, s):
        return 0, f"Gave the open dataset's figure for {period_label(q.dataset_period)}, not the release for {period_label(q.period)}."
    if not r.score.period_ok:
        given = period_label(r.score.period) if r.score.period else "no clear period"
        return 1, f"Named {given} instead of {period_label(q.period)}."
    return None


def error_examples(runs: list[Run], statistics: dict[str, Statistic]) -> list[dict[str, Any]]:
    """Up to PER_RULE real failures for each rule, with tools before memory, then by question and model; one example per question."""
    ordered = sorted((r for r in runs if r.model != BASELINE), key=lambda r: (r.mode != "tools", r.question.id, r.model))
    picked: dict[int, list[dict[str, Any]]] = {0: [], 1: [], 2: []}
    used: set[str] = set()
    for r in ordered:
        s = statistics[r.question.statistic]
        found = failure_note(r, s)
        if found is None or r.question.id in used or len(picked[found[0]]) >= PER_RULE:
            continue
        used.add(r.question.id)
        given = "No final answer" if not r.score.readable else ", ".join(
            [figure(r.score.value, s) if r.score.value is not None else "no number", period_label(r.score.period) if r.score.period else "no period"])
        picked[found[0]].append({"input": r.question.text, "expected": f"{figure(r.question.value, s)}, {period_label(r.question.period)}",
                                 "model": f"{name(r.model)}, {'with tools' if r.mode == 'tools' else 'from memory'}", "output": given, "note": found[1], "correct": False})
    return [e for rule in (0, 1, 2) for e in picked[rule]]


def build_results(views: dict[str, list[Cell]], runs: list[Run], questions: list[Question], statistics: dict[str, Statistic],
                  taken: str, run: dict[str, str], retrieved: dict[str, str]) -> dict[str, Any]:
    return {
        "answer": answer_text(views),
        "keyNumbers": key_numbers(views, len({q.statistic for q in questions}), len(questions), taken),
        "run": run,
        "retrieved": retrieved,
        "tasks": tasks(views),
        "errorExamples": error_examples(runs, statistics),
    }


def scores_json(views: dict[str, list[Cell]]) -> dict[str, dict[str, dict[str, Any]]]:
    """Unrounded scores for the manifest, by view and model, with the English and Bahasa Malaysia split."""
    return {
        view: {c.model: {"share": round(c.share, 1), "low": round(c.low, 1), "high": round(c.high, 1), "calls_per_answer": round(c.calls, 2),
                         "median_seconds": round(c.seconds, 2), "questions": c.questions, "source_given": round(c.sourced, 1),
                         "by_language": {k: round(v, 1) for k, v in c.by_language.items()}}
               for c in cells}
        for view, cells in views.items()
    }
```

- [ ] **Step 4: Finish the command line**

Replace `analysis/evallab/cli.py` with:

```python
"""Entry point, run from analysis/:

  uv run python -m evallab.cli snapshot      take the snapshot once; later commands only verify it
  uv run python -m evallab.cli draft         draft every answer into evallab/questions.csv for review
  uv run python -m evallab.cli run --pilot   ask the 20 pilot questions and print usage and timing
  uv run python -m evallab.cli run           ask everything not yet answered, then score and write the results
"""

from __future__ import annotations

import argparse
import json
import logging
import platform
import statistics
import time
from collections import Counter
from datetime import UTC, datetime
from importlib.metadata import version
from pathlib import Path
from typing import Any

from forecasting.cli import git_state
from forecasting.data import sha256_of
from forecasting.export import write_json

from .export import build_results, scores_json
from .ollama import OllamaClient, OllamaError, UsageLimit
from .questions import OUT_OF_DATE, QUESTIONS_PATH, Question, draft_all, read_questions, sheet_rows, write_sheet
from .runner import MAX_TOOL_CALLS, MODES, OPTIONS, RunLog, run
from .scoring import BASELINE, RESAMPLES, SEED, score_runs, views
from .snapshot import SNAPSHOT, freeze
from .statistics import STATISTICS
from .store import Store, load
from .tools import baseline_answer

ANALYSIS_DIR = Path(__file__).resolve().parents[1]
REPO_DIR = ANALYSIS_DIR.parent
RAW_DIR = ANALYSIS_DIR / "data/raw/evallab"
RESULTS_PATH = REPO_DIR / "apps/web/src/content/results/llm-eval-lab.json"
MANIFEST_PATH = ANALYSIS_DIR / "outputs/llm-eval-lab-manifest.json"
MODELS = ("gpt-oss:120b-cloud", "deepseek-v4.1-flash:cloud")
PILOT = 20
LIBRARIES = ("numpy", "pyarrow", "pymupdf", "openpyxl")
BY_ID = {s.id: s for s in STATISTICS}


def pilot_ids(questions: list[Question]) -> set[str]:
    """PILOT questions spread evenly over the set, so the pilot touches most statistics and both languages."""
    step = max(1, len(questions) // PILOT)
    return {q.id for q in questions[::step][:PILOT]}


def baseline_records(store: Store, questions: list[Question]) -> list[dict[str, Any]]:
    records = []
    for q in questions:
        start = time.perf_counter()
        content = baseline_answer(store, BY_ID[q.statistic])
        records.append({"question": q.id, "model": BASELINE, "mode": "tools", "content": content, "tool_calls": 0, "seconds": time.perf_counter() - start})
    return records


def usage(calls: list[dict[str, Any]]) -> dict[str, dict[str, dict[str, int]]]:
    """Calls, failed calls and tokens per model and mode, from the call log."""
    out: dict[str, dict[str, dict[str, int]]] = {}
    for c in calls:
        u = out.setdefault(c["model"], {}).setdefault(c["mode"], {"calls": 0, "errors": 0, "prompt_tokens": 0, "output_tokens": 0})
        u["calls"] += 1
        u["errors"] += c["status"] != "ok"
        u["prompt_tokens"] += c.get("prompt_tokens") or 0
        u["output_tokens"] += c.get("output_tokens") or 0
    return out


def timing(answers: list[dict[str, Any]]) -> dict[str, Any]:
    if not answers:
        return {"answers": 0}
    return {"answers": len(answers), "median_seconds": round(statistics.median(a["seconds"] for a in answers), 1),
            "tool_calls": sum(a["tool_calls"] for a in answers), "statuses": dict(Counter(a["status"] for a in answers))}


def pilot_summary(answers: list[dict[str, Any]], calls: list[dict[str, Any]]) -> dict[str, dict[str, dict[str, Any]]]:
    """Usage from the call log beside timing and outcomes from the answers, per model and mode."""
    return {model: {mode: {**counts, **timing([a for a in answers if a["model"] == model and a["mode"] == mode])} for mode, counts in modes.items()}
            for model, modes in usage(calls).items()}


def sources(snapshot: dict[str, Any]) -> list[dict[str, Any]]:
    return [{k: f[k] for k in ("path", "url", "retrieved", "bytes", "sha256")} for f in snapshot["files"]]


def build_manifest(store: Store, questions: list[Question], questions_path: Path, scored: dict[str, Any], run_log: RunLog,
                   ollama: dict[str, Any], packages: dict[str, str], git: dict[str, Any]) -> dict[str, Any]:
    snapshot = json.loads((store.root / SNAPSHOT).read_text())
    answers = run_log.answers()
    stale = {q.statistic for q in questions if q.status == OUT_OF_DATE}
    return {
        "study": "llm-eval-lab",
        "snapshot": {"taken": store.taken, "catalogue": snapshot["catalogue"], "files": sources(snapshot), "releases": [r["id"] for r in snapshot["releases"]]},
        "questions": {"file": str(questions_path.relative_to(REPO_DIR)) if questions_path.is_relative_to(REPO_DIR) else questions_path.name,
                      "sha256": sha256_of(questions_path), "questions": len(questions), "verified": len(questions),
                      "statistics": len({q.statistic for q in questions}), "out_of_date_statistics": sorted(stale),
                      "current_statistics": sorted({q.statistic for q in questions} - stale)},
        "models": ollama["models"],
        "ollama_version": ollama["version"],
        "settings": {**OPTIONS, "max_tool_calls": MAX_TOOL_CALLS, "modes": list(MODES), "bootstrap": {"unit": "statistic", "resamples": RESAMPLES, "seed": SEED}},
        "runs": {m: {mode: sum(a["model"] == m and a["mode"] == mode for a in answers) for mode in MODES} for m in MODELS},
        "usage": usage(run_log.calls()),
        "scores": scored,
        "packages": packages,
        "git": git,
        "results_file": str(RESULTS_PATH.relative_to(REPO_DIR)),
    }


def finish(store: Store, questions: list[Question], answers: list[dict[str, Any]], run_info: dict[str, str]) -> tuple[dict[str, Any], dict[str, Any]]:
    """Score every answer, and the baseline's, into the site's results and the manifest's scores."""
    runs = score_runs([*answers, *baseline_records(store, questions)], questions, BY_ID, store.sources())
    cells = views(runs, questions, MODELS)
    retrieved = {name: store.taken for name in ("data.gov.my datasets", "DOSM releases", "Bank Negara Malaysia", "MYNIC", "Question set")}
    retrieved["Ollama Cloud"] = run_info["lastRun"]
    return build_results(cells, runs, questions, BY_ID, store.taken, run_info, retrieved), scores_json(cells)


def cmd_snapshot(args: argparse.Namespace) -> None:
    snapshot = freeze(args.raw_dir, list(STATISTICS), datetime.now(UTC).date())
    print(f"snapshot of {snapshot['taken']}: {len(snapshot['files'])} files, {len(snapshot['releases'])} releases, catalogue at {snapshot['catalogue']['commit'][:8]}")


def cmd_draft(args: argparse.Namespace) -> None:
    drafts = draft_all(load(args.raw_dir), list(STATISTICS))
    write_sheet(args.questions, sheet_rows(drafts), force=args.force)
    stale, blank = sum(d.status == OUT_OF_DATE for d in drafts), [d.statistic.id for d in drafts if d.value is None]
    print(f"wrote {len(drafts) * 4} questions on {len(drafts)} statistics ({stale} out of date) to {args.questions}")
    if blank:
        print(f"no value found in the release text for: {', '.join(blank)}; fill these in by hand")


def cmd_run(args: argparse.Namespace) -> None:
    store = load(args.raw_dir)
    questions = read_questions(args.questions, list(STATISTICS))
    for statistic in {BY_ID[q.statistic] for q in questions}:
        baseline_answer(store, statistic)  # stops now if any statistic has no data in the snapshot
    client = OllamaClient()
    try:
        ollama = {"version": client.version(), "models": {m: client.show(m).get("details", {}) for m in MODELS}}
    except OllamaError as err:
        raise SystemExit(f"Ollama is not reachable at the start of the run: {err}") from err
    logging.info("Ollama %s; models %s", ollama["version"], ollama["models"])
    run_log = RunLog(args.raw_dir / "runs")
    try:
        run(client, store, questions, MODELS, run_log, store.taken, args.pace, only=pilot_ids(questions) if args.pilot else None)
    except UsageLimit as err:
        raise SystemExit(f"stopped at an Ollama Cloud usage limit ({err}); run the same command later to resume") from err
    if args.pilot:
        print(json.dumps(pilot_summary(run_log.answers(), run_log.calls()), indent=2))
        return
    git = git_state()
    packages = {"python": platform.python_version(), **{name: version(name) for name in LIBRARIES}}
    today = datetime.now(UTC).date().isoformat()
    run_info = {"commit": git["commit"], "manifest": str(MANIFEST_PATH.relative_to(REPO_DIR)), "python": packages["python"], "lastRun": today}
    results, scored = finish(store, questions, run_log.answers(), run_info)
    write_json(MANIFEST_PATH, build_manifest(store, questions, args.questions, scored, run_log, ollama, packages, git))
    write_json(RESULTS_PATH, results)
    print(f"wrote {RESULTS_PATH.relative_to(REPO_DIR)} and {MANIFEST_PATH.relative_to(REPO_DIR)}")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="python -m evallab.cli", description="Run the LLM Eval Lab freshness study.")
    parser.add_argument("--raw-dir", type=Path, default=RAW_DIR)
    parser.add_argument("--questions", type=Path, default=QUESTIONS_PATH)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("snapshot", help="take the snapshot, or verify the one already taken").set_defaults(handler=cmd_snapshot)
    draft = commands.add_parser("draft", help="draft the answers into the review sheet")
    draft.add_argument("--force", action="store_true", help="replace an existing review sheet")
    draft.set_defaults(handler=cmd_draft)
    ask = commands.add_parser("run", help="ask the models, then score and write the results")
    ask.add_argument("--pilot", action="store_true", help=f"ask only {PILOT} questions and print usage")
    ask.add_argument("--pace", type=float, default=2.0, help="seconds to wait after each call")
    ask.set_defaults(handler=cmd_run)
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%H:%M:%S")
    args.handler(args)


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Run the tests**

Run (in `analysis/`): `uv run pytest tests/evallab`, then `uv run pytest`.
Expected: `118 passed`, then `244 passed`.

- [ ] **Step 6: Commit**

```bash
git add analysis/evallab/export.py analysis/evallab/cli.py analysis/tests/evallab/contract.py \
  analysis/tests/evallab/test_export.py analysis/tests/evallab/test_pipeline.py
git commit -m "feat: write the LLM Eval Lab results and manifest from templates"
```

---

### Task 10: The full run

**Files:**
- Create (written by the pipeline): `apps/web/src/content/results/llm-eval-lab.json`, `analysis/outputs/llm-eval-lab-manifest.json`
- Not committed: `analysis/data/raw/evallab/runs/` (the call and answer logs)

**Interfaces:**
- Consumes: `python -m evallab.cli run` (Task 9), the verified sheet (Task 6), the pilot's answers (Task 7).
- Produces: the committed results file that Task 11 publishes and Task 12 quotes, and the manifest that its `run.manifest` names.

- [ ] **Step 1: Start from a clean tree**

Run: `git checkout -- apps/web/next-env.d.ts`, then `git status --porcelain`.
Expected: no output. The run records `git rev-parse --short HEAD` and whether the tree was dirty, and the results cite that commit; when the pull request is merged, keep a merge commit so the cited commit stays on `main`.

- [ ] **Step 2: Run everything**

Run (in `analysis/`, in the background, with a timeout of at least 3 hours): `uv run python -m evallab.cli run 2>&1 | tee /tmp/evallab-run.log`
The pilot's 80 question runs are skipped; the remaining 400 take roughly two hours at the default pace. Expected: `Ollama 0.40.4; models {...}`, one line per question run, and last `wrote apps/web/src/content/results/llm-eval-lab.json and analysis/outputs/llm-eval-lab-manifest.json`.

If it stops:
- `stopped at an Ollama Cloud usage limit`: tell Subashanan, wait for the limit to reset, and run the same command again; it asks only what is missing.
- `Ollama is not reachable at the start of the run`: start Ollama (`ollama serve`) or sign in again (`ollama signin`), then rerun.
- `... has no tools answer for N questions`: the run ended early (for example the machine slept); rerun the same command.
- `snapshot file ... changed` or `is missing`: the snapshot was touched. Stop and report; never edit `snapshot.json`.

- [ ] **Step 3: Check the outputs**

Run (in `analysis/`):

```bash
uv run python - <<'EOF'
import json
m = json.load(open("outputs/llm-eval-lab-manifest.json"))
r = json.load(open("../apps/web/src/content/results/llm-eval-lab.json"))
print(m["snapshot"]["taken"], m["snapshot"]["catalogue"]["commit"][:8], len(m["snapshot"]["files"]), "files")
print(m["questions"]["questions"], m["questions"]["verified"], len(m["questions"]["out_of_date_statistics"]), "out of date")
print(m["ollama_version"], m["models"], m["runs"], m["git"])
print(json.dumps(m["usage"], indent=1))
print(r["answer"])
for n in r["keyNumbers"]:
    print(n)
for t in r["tasks"]:
    print(t["label"], [(x["model"], x["score"], x["low"], x["high"], x["callsLabel"], x["latency"]) for x in t["rows"]])
for e in r["errorExamples"]:
    print(e["model"], "|", e["expected"], "|", e["output"], "|", e["note"])
EOF
uv run python -c "import json; from tests.evallab.contract import check_results; check_results(json.load(open('../apps/web/src/content/results/llm-eval-lab.json'))); print('valid')"
```

Expected: the snapshot date and commit from Task 5 and 95 files; `120 120` and the out-of-date count from Task 5; Ollama `0.40.4`, both models with their details, `{'tools': 120, 'memory': 120}` for each model, and `'dirty': False`; usage per model and mode; an answer and three key numbers in the Task 9 template shapes with no dashes; three views, the memory view without `Open data only`; up to six error examples; and `valid`.

Show Subashanan the answer, the key numbers, the three views and the error examples now. The wording is approved at pull request time; any change is made in `analysis/evallab/export.py` and the scoring rerun (`uv run python -m evallab.cli run` asks nothing new once every answer is logged), never by editing the JSON.

- [ ] **Step 4: Check that scoring reproduces**

The outputs are untracked, which would make a rerun record `"dirty": true`, so move them aside first. Run (in `analysis/`):

```bash
mkdir -p /tmp/evallab-run1 && mv ../apps/web/src/content/results/llm-eval-lab.json outputs/llm-eval-lab-manifest.json /tmp/evallab-run1/
git status --porcelain
uv run python -m evallab.cli run 2>&1 | tail -1
cmp /tmp/evallab-run1/llm-eval-lab.json ../apps/web/src/content/results/llm-eval-lab.json && cmp /tmp/evallab-run1/llm-eval-lab-manifest.json outputs/llm-eval-lab-manifest.json && echo identical
```

Expected: `git status --porcelain` prints nothing; the rerun asks no model (no question lines) and prints the `wrote ...` line; then `identical` when run on the same day, since the results carry the run date. If the files differ on the same day, find the source of nondeterminism before committing.

- [ ] **Step 5: Commit**

```bash
git add apps/web/src/content/results/llm-eval-lab.json analysis/outputs/llm-eval-lab-manifest.json
git commit -m "chore: publish the first LLM Eval Lab run"
```

---

### Task 11: Web: publish the results and update the study record

**Files:**
- Modify: `apps/web/src/content/results/index.ts`, `apps/web/src/content/studies.ts`
- Test: `apps/web/src/content/results/index.test.ts`, `apps/web/src/lib/study-results.test.ts`, `apps/web/src/components/study/study-card.test.tsx`, `apps/web/src/components/study/study-page.test.tsx` (replace)

**Interfaces:**
- Consumes: `parseLlmEvalResults` (Task 2); `apps/web/src/content/results/llm-eval-lab.json` (Task 10); `llmEvalFixture` (Task 1).
- Produces: `published["llm-eval-lab"]`, validated at import; the LLM Eval Lab study record with `status: "published"`, the new question, planned answer, figure plan, data line, method, limitations, reproduce commands and discuss note (the sources came in Task 1). Every study with a fixture is now published, so the tests that needed an unpublished study use `penang-ai-assistant` (no fixture), and the preview tests pass the fixture in directly or mock the published set.

- [ ] **Step 1: Write the failing tests**

Replace `apps/web/src/content/results/index.test.ts` with:

```ts
import { describe, expect, it } from "vitest";

import { findStudy } from "../studies";
import { published } from "./index";

const DASHES = /[–—→←↑↓]/; // en and em dashes and arrows

describe("published results", () => {
  const forecasting = published["forecasting-lab"]!;
  const pulse = published["penang-pulse"]!;
  const llm = published["llm-eval-lab"]!;

  it("publishes the forecasting lab from the validated results file", () => {
    expect(forecasting.models.map((m) => m.id)).toEqual(["persistence", "seasonal", "gb", "mlp", "chronos"]);
    expect(forecasting.horizons).toEqual([15, 30, 60, 90, 120]);
    expect(forecasting.sensors).toHaveLength(3);
  });

  it("publishes Penang Pulse from the validated results file", () => {
    expect(pulse.districts.map((d) => d.id)).toEqual(["tl", "bd", "spu", "spt", "sps"]);
    expect(pulse.geometry.bridges).toHaveLength(2);
    expect(Number(pulse.keyNumbers[1].value.replace(/,/g, ""))).toBe(pulse.points.length); // every facility counted is drawn
  });

  it("publishes the LLM Eval Lab from the validated results file", () => {
    expect(llm.tasks.map((t) => t.id)).toEqual(["all-tools", "stale-tools", "all-memory"]);
    expect(llm.tasks[2].rows.some((r) => r.role === "baseline")).toBe(false);
    expect(llm.errorExamples.length).toBeLessThanOrEqual(6);
  });

  it.each(["forecasting-lab", "penang-pulse", "llm-eval-lab"] as const)("dates every source %s lists", (slug) => {
    for (const source of findStudy(slug)!.sources) {
      expect(published[slug]!.retrieved[source.name]).toMatch(/^\d{4}-\d{2}-\d{2}$/);
    }
  });

  it.each(["forecasting-lab", "penang-pulse", "llm-eval-lab"] as const)("%s points at its committed manifest and follows the copy rules", (slug) => {
    const data = published[slug]!;
    expect(data.run.manifest).toBe(`analysis/outputs/${slug}-manifest.json`);
    const notes = slug === "llm-eval-lab" ? llm.errorExamples.map((e) => e.note) : [];
    for (const line of [data.answer, ...data.keyNumbers.flatMap((n) => [n.label, n.caveat]), ...notes]) {
      expect(line).not.toMatch(DASHES);
    }
  });
});
```

Replace `apps/web/src/lib/study-results.test.ts` with:

```ts
import { afterEach, describe, expect, it, vi } from "vitest";

import { getStudyResults } from "./study-results";

describe("getStudyResults", () => {
  it("returns nothing in production when no results are published", () => {
    expect(getStudyResults("penang-ai-assistant", "production")).toBeNull();
  });

  it("returns published results in every environment, never flagged as a preview", () => {
    for (const env of ["production", "development", "test", undefined]) {
      const forecasting = getStudyResults("forecasting-lab", env);
      expect(forecasting?.preview).toBe(false);
      expect(forecasting?.data.models).toHaveLength(5);
      const pulse = getStudyResults("penang-pulse", env);
      expect(pulse?.preview).toBe(false);
      expect(pulse?.data.districts).toHaveLength(5);
      const llm = getStudyResults("llm-eval-lab", env);
      expect(llm?.preview).toBe(false);
      expect(llm?.data.tasks).toHaveLength(3);
    }
  });

  afterEach(() => {
    vi.unstubAllEnvs();
    vi.doUnmock("@/content/results");
    vi.resetModules();
  });

  it("fails closed for an unknown or missing environment", () => {
    expect(getStudyResults("penang-ai-assistant", "staging")).toBeNull();
    // An explicit undefined argument falls back to the default, so the missing case is exercised through the real env.
    vi.stubEnv("NODE_ENV", undefined);
    expect(process.env.NODE_ENV).toBeUndefined();
    expect(getStudyResults("penang-ai-assistant")).toBeNull();
  });

  it("returns illustrative fixtures, flagged as a preview, outside production while a study is unpublished", async () => {
    // Every study with a fixture is now published, so the unpublished case is simulated with an empty set of results.
    vi.resetModules();
    vi.doMock("@/content/results", () => ({ published: {} }));
    const { getStudyResults: load } = await import("./study-results");
    expect(load("llm-eval-lab", "development")?.preview).toBe(true);
    expect(load("llm-eval-lab", "test")?.data.tasks).toHaveLength(3);
    expect(load("llm-eval-lab", "production")).toBeNull();
  });

  it("returns nothing for a study with no published result and no fixture, even in development", () => {
    expect(getStudyResults("penang-ai-assistant", "development")).toBeNull();
    expect(getStudyResults("penang-ai-assistant", "test")).toBeNull();
  });
});
```

Replace `apps/web/src/components/study/study-card.test.tsx` with:

```tsx
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { llmEvalFixture } from "@/content/fixtures/llm-eval";
import { findStudy } from "@/content/studies";

import { StudyCard } from "./study-card";

const pulse = findStudy("penang-pulse")!;

describe("StudyCard", () => {
  it("shows a visible preview label above the key number in a preview", () => {
    const llm = findStudy("llm-eval-lab")!;
    const { container } = render(<StudyCard study={llm} results={{ data: llmEvalFixture, preview: true }} headingLevel={3} />);
    const flag = screen.getByText("Illustrative preview");
    expect(flag).toHaveClass("preview-flag");
    expect(flag).not.toHaveClass("sr");
    const key = container.querySelector(".key")!;
    expect(flag.compareDocumentPosition(key.querySelector("strong")!) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  });

  it("shows a pending line and no key number without results", () => {
    const { container } = render(<StudyCard study={pulse} results={null} headingLevel={3} />);
    expect(container.querySelector(".key.pending")).toHaveTextContent("Results appear here once the analysis is published.");
    expect(container.querySelector(".key strong")).toBeNull();
    expect(screen.queryByText("Illustrative preview")).not.toBeInTheDocument();
  });
});
```

Replace `apps/web/src/components/study/study-page.test.tsx` with:

```tsx
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { llmEvalFixture } from "@/content/fixtures/llm-eval";
import { findStudy } from "@/content/studies";
import { getStudyResults } from "@/lib/study-results";

import { StudyPage } from "./study-page";

const pulse = findStudy("penang-pulse")!;
const llm = findStudy("llm-eval-lab")!;

describe("StudyPage", () => {
  it("production mode with no results shows the plan and no numbers", () => {
    const assist = findStudy("penang-ai-assistant")!;
    const { container } = render(<StudyPage study={assist} results={getStudyResults("penang-ai-assistant", "production")} />);
    expect(screen.getByRole("heading", { level: 1, name: "Penang AI Assistant" })).toBeInTheDocument();
    expect(screen.getByText(assist.plannedAnswer)).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /the analysis is in progress/i })).toBeInTheDocument();
    expect(screen.queryByText(/preview with illustrative data/i)).not.toBeInTheDocument();
    expect(container.querySelectorAll(".num-tile")).toHaveLength(0);
    expect(screen.getAllByText("Not yet retrieved")).toHaveLength(assist.sources.length);
  });

  it("production mode shows published LLM Eval Lab results, the leaderboard and no preview label", () => {
    const loaded = getStudyResults("llm-eval-lab", "production")!;
    const { container } = render(<StudyPage study={llm} results={loaded} />);
    expect(screen.getByText(loaded.data.answer)).toBeInTheDocument();
    expect(container.querySelectorAll(".num-tile")).toHaveLength(3);
    expect(screen.getByRole("tab", { name: "Out-of-date series, with tools" })).toBeInTheDocument();
    expect(screen.queryByText(/preview with illustrative data/i)).not.toBeInTheDocument();
    expect(screen.queryAllByText("Not yet retrieved")).toHaveLength(0);
  });

  it("production mode shows published Penang Pulse results, the service table and no preview label", () => {
    const loaded = getStudyResults("penang-pulse", "production")!;
    const { container } = render(<StudyPage study={pulse} results={loaded} />);
    expect(screen.getByText(loaded.data.answer)).toBeInTheDocument();
    expect(container.querySelectorAll(".num-tile")).toHaveLength(3);
    expect(screen.getByRole("table", { name: /more than 3 km by road from the nearest service/i })).toBeInTheDocument();
    expect(screen.queryByText(/preview with illustrative data/i)).not.toBeInTheDocument();
    expect(screen.queryAllByText("Not yet retrieved")).toHaveLength(0);
  });

  it("puts the title inside the single main landmark", () => {
    const { container } = render(<StudyPage study={pulse} results={null} />);
    expect(container.querySelectorAll("main")).toHaveLength(1);
    expect(container.querySelector("#main")).toContainElement(screen.getByRole("heading", { level: 1, name: "Penang Pulse" }));
  });

  it("preview mode shows fixture numbers under a visible preview label", () => {
    render(<StudyPage study={llm} results={{ data: llmEvalFixture, preview: true }} />);
    expect(screen.getAllByText("47 points").length).toBeGreaterThan(0);
    expect(screen.getAllByText(/preview with illustrative data/i).length).toBeGreaterThan(0);
  });

  it("shows the new assistant study's plan, pending evidence and no preview in development", () => {
    const assist = findStudy("penang-ai-assistant")!;
    const { container } = render(<StudyPage study={assist} results={getStudyResults("penang-ai-assistant", "development")} />);
    expect(screen.getByText(assist.plannedAnswer)).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /the analysis is in progress/i })).toBeInTheDocument();
    expect(container.querySelectorAll(".num-tile")).toHaveLength(0);
    expect(screen.queryByText(/preview with illustrative data/i)).not.toBeInTheDocument();
  });

  it("always shows the provenance chapters and wraps the pager", () => {
    render(<StudyPage study={pulse} results={null} />);
    for (const name of ["The answer", "The evidence", "How it was made", "Check it yourself"]) {
      expect(screen.getByRole("heading", { level: 2, name })).toBeInTheDocument();
    }
    expect(screen.getByRole("table")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /previous study penang ai assistant/i })).toHaveAttribute("href", "/work/penang-ai-assistant");
    expect(screen.getByRole("link", { name: /next study forecasting lab/i })).toHaveAttribute("href", "/work/forecasting-lab");
  });
});
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `npm test`
Expected: FAIL, 5 tests: in `index.test.ts`, `TypeError: Cannot read properties of undefined (reading 'tasks')`, `(reading 'retrieved')` and `(reading 'run')`; in `study-results.test.ts`, `expected undefined to be false`; in `study-page.test.tsx`, `TypeError: Cannot read properties of null (reading 'data')`.

- [ ] **Step 3: Publish the file and rewrite the record**

Replace `apps/web/src/content/results/index.ts` with:

```ts
import type { StudyResultsBySlug } from "../types";
import forecastingLab from "./forecasting-lab.json";
import llmEvalLab from "./llm-eval-lab.json";
import { parseForecastResults } from "./parse-forecast";
import { parseLlmEvalResults } from "./parse-llm-eval";
import { parsePenangResults } from "./parse-penang";
import penangPulse from "./penang-pulse.json";

// Real results written by the analysis pipelines in analysis/. Each file is validated on import,
// so a malformed file fails the build instead of reaching a page.
export const published: Partial<StudyResultsBySlug> = {
  "forecasting-lab": parseForecastResults(forecastingLab),
  "llm-eval-lab": parseLlmEvalResults(llmEvalLab),
  "penang-pulse": parsePenangResults(penangPulse),
};
```

In `apps/web/src/content/studies.ts`, replace the whole `llm-eval-lab` object (from `    slug: "llm-eval-lab",` to the `discussNote` line and its closing `  },`) with the record below. The planned answer has no digits, as `content.test.ts` requires; the method states design facts, not results:

```ts
    slug: "llm-eval-lab",
    title: "LLM Eval Lab",
    question: "When Malaysia's open data is out of date, can a language model still find the latest official figure?",
    status: "published",
    plannedAnswer:
      "This study asks two cloud models, with tools and from memory, for the latest official figure of Malaysian statistics whose open datasets sometimes lag the official releases, and compares them with simply trusting the open data.",
    figurePlan:
      "a leaderboard for each view with 95% intervals, tool calls and time per answer, a chart of tool calls against score, and real examples of where the models went wrong.",
    data: "data.gov.my, DOSM, Bank Negara Malaysia and MYNIC releases, Ollama Cloud.",
    tile: { motif: "flower", a: "rose", b: "cobalt", ground: "porcelain" },
    tint: "roseTint",
    themeClass: "s-llm",
    sources: [
      { name: "data.gov.my datasets", publisher: "Government of Malaysia, via data.gov.my", used: "Catalogue metadata and the latest value of each series", licence: "CC BY 4.0" },
      { name: "DOSM releases", publisher: "Department of Statistics Malaysia, via OpenDOSM", used: "Release text for the latest official figures; cited, not republished", licence: "DOSM terms" },
      { name: "Bank Negara Malaysia", publisher: "Bank Negara Malaysia", used: "Money supply and interest rate tables. Source: Bank Negara Malaysia", licence: "Terms of Use for BNM Datasets" },
      { name: "MYNIC", publisher: "MYNIC Berhad", used: "Domain statistics; single figures cited, raw data not republished", licence: "All rights reserved" },
      { name: "Ollama Cloud", publisher: "Ollama", used: "gpt-oss:120b-cloud and deepseek-v4.1-flash:cloud, with their versions in the manifest", licence: "Provider terms" },
      { name: "Question set", publisher: "This project", used: "Every question, with its answer verified against the official release", licence: "CC BY 4.0" },
    ],
    method: [
      "Freeze one snapshot of the data.gov.my catalogue, the dataset behind each statistic and the newest DOSM, Bank Negara Malaysia and MYNIC releases, with a checksum for every file.",
      "Draft each statistic's latest official figure from its newest release, then check every answer by hand against the release.",
      "Ask about each statistic four ways, twice in English and twice in Bahasa Malaysia, and mark it out of date when its dataset ends before the release.",
      "Ask two Ollama Cloud models every question with four read-only tools over the snapshot, at most six tool calls each, and again from memory, at temperature 0 with a fixed seed.",
      "Count an answer right when its value matches at the publication's rounding and its period matches. Compare with a baseline that returns the dataset's newest value, with 95% intervals from a bootstrap that resamples whole statistics.",
    ],
    limitations: [
      "Results describe the day the snapshot was taken; open data and releases change.",
      "Questions target headline figures only, because tables extracted from PDF releases are unreliable.",
      "Cloud models change without notice, so results are dated, and one run at temperature 0 does not measure run-to-run variation.",
      "Ollama does not publish how cloud usage is counted, so usage is reported as calls and tokens.",
      "One reviewer verified the answers.",
      "MYNIC reserves all rights to its statistics, so only single figures are shown and its raw data is not republished.",
    ],
    reproduce: {
      commands: ["cd analysis", "uv sync", "uv run python -m evallab.cli snapshot", "uv run python -m evallab.cli run", "cd .. && npm run dev"],
      note: "The run needs Ollama signed in to Ollama Cloud and picks up where it stopped after a usage limit. A new snapshot needs its answers drafted and checked again (evallab.cli draft). The tests need neither: uv run pytest.",
    },
    discussNote: "Know a series where the open data lags the official release? Suggestions and corrections are welcome.",
  },
```

- [ ] **Step 4: Run every check, and prove a bad file fails the build**

Run: `npm test`, `npm run lint`, `npm run typecheck`, then `npm run build`.
Expected: `Tests  169 passed (169)`, no lint or type errors, and the build lists `/work/llm-eval-lab` under `●  (SSG)`.

Then break the file on purpose and build again:

```bash
cp apps/web/src/content/results/llm-eval-lab.json /tmp/llm-eval-lab.json
node -e "const f='apps/web/src/content/results/llm-eval-lab.json';const fs=require('fs');const d=JSON.parse(fs.readFileSync(f));fs.writeFileSync(f,JSON.stringify({...d,tasks:d.tasks.map((t,i)=>i===2?{...t,rows:[...t.rows,d.tasks[0].rows.at(-1)]}:t)}))"
npm run build 2>&1 | grep "llm-eval-lab results"
cp /tmp/llm-eval-lab.json apps/web/src/content/results/llm-eval-lab.json
git diff --stat apps/web/src/content/results/llm-eval-lab.json
```

Expected: the build fails and the grep prints a line ending `Error: llm-eval-lab results: tasks[2].rows must have 0 baseline rows, found 1`; after the copy back, `git diff --stat` prints nothing.

- [ ] **Step 5: Restore the generated file**

Run: `git checkout -- apps/web/next-env.d.ts`

- [ ] **Step 6: Check the page against the JSON**

From `apps/web`, run `npx next start --port 3001` in the background, then `curl -s http://localhost:3001/work/llm-eval-lab | grep -o "Preview with illustrative data" | head -1`.
Expected: no output. Open `http://localhost:3001/work/llm-eval-lab` and check that the answer, the three key numbers, each view's rows, the error examples and the "Retrieved" dates match `llm-eval-lab.json` exactly, that the status pill reads "Published", and that the sources list credits Bank Negara Malaysia and MYNIC.

- [ ] **Step 7: Screenshot the figure**

With the server still running, from the repository root:

```bash
npx -y playwright@1.59 screenshot --full-page --wait-for-timeout=1500 --viewport-size=1440,900 http://localhost:3001/work/llm-eval-lab .context/llm-real-1440.png
npx -y playwright@1.59 screenshot --full-page --wait-for-timeout=1500 --viewport-size=390,844 http://localhost:3001/work/llm-eval-lab .context/llm-real-390.png
```

Look at both. Expected: the first view's leaderboard with intervals on the 0 to 100 track, tool calls and time columns; the chart with x ticks 0 to 6 and y ticks 0 to 100, every point labelled with no two labels on top of each other, and the two-item legend; the error examples readable at 390 px. Click the "All series, from memory" tab in a browser and check that both points sit at x = 0 with separate labels. Stop the server.

- [ ] **Step 8: Commit**

```bash
git add apps/web/src/content/results/index.ts apps/web/src/content/results/index.test.ts apps/web/src/content/studies.ts \
  apps/web/src/lib/study-results.test.ts apps/web/src/components/study/study-page.test.tsx apps/web/src/components/study/study-card.test.tsx
git commit -m "feat: publish real LLM Eval Lab results"
```

---

### Task 12: The CV bullet, final checks and the hand-over

**Files:**
- Replace: `analysis/tools/update_cv.py`
- Modify: `apps/web/public/subashanan-nair-cv.pdf`
- Modify, not committed: `.context/resume/Subashanan Nair Resume - Data Scientist (updated).pdf` (the full CV, which carries a phone number; its original is `.context/attachments/emjv7j/Subashanan Nair Resume - Data Scientist.pdf`), with before and after renders in `.context/resume/`
- Test: `analysis/tests/test_update_cv.py`

**Interfaces:**
- Consumes: `apps/web/src/content/results/llm-eval-lab.json` (Task 10): `tasks[1]` (`stale-tools`) rows and `keyNumbers[2]`.
- Produces, in `tools/update_cv.py`: `LLM_HEAD`, `LLM_BULLET`, `LLM_TECH_OLD`, `LLM_TECH_NEW`, `LLM_LABEL_OLD`, `LLM_LABEL_NEW`, `LABEL`, `LLM_COUNT`; `llm_text(results) -> tuple[str, ...]` (candidate wordings, preferred first, every one starting with `LLM_HEAD` so a later run finds the bullet again); `replace_tech_line(page, old, new, fitz, style=TECH)` now swaps any one span in the given style, used for the label too. The Forecasting Lab and Penang Pulse edits are unchanged.

The bullet names the cloud model with the highest score on out-of-date series with tools, its share, the baseline's share, and the counts of statistics and verified questions, all read from the results file. The label beside the heading changes from "In Progress" to "LLM Evaluation" (outside spec section 12; remove that one `replace_tech_line` call if Subashanan prefers to keep it).

- [ ] **Step 1: Write the failing tests**

In `analysis/tests/test_update_cv.py`, replace:

```python
from tools.update_cv import FORECAST_TECH_NEW, FORECAST_TECH_OLD, PULSE_BULLET, PULSE_TECH_NEW, bullet_lines, change, choose, forecast_text, pulse_text, wrap
```

with:

```python
from tools.update_cv import (
    FORECAST_TECH_NEW, FORECAST_TECH_OLD, LLM_BULLET, LLM_HEAD, LLM_TECH_NEW, PULSE_BULLET, PULSE_TECH_NEW, bullet_lines, change, choose, forecast_text, llm_text,
    pulse_text, wrap,
)
```

and add at the end of the file:

```python
LLM = {
    "keyNumbers": [{}, {}, {"value": "30", "label": "statistics, asked 4 ways each: 120 questions verified against the official release."}],
    "tasks": [
        {"id": "all-tools", "rows": []},
        {"id": "stale-tools", "rows": [
            {"model": "gpt-oss 120B", "role": "cloud", "score": 41},
            {"model": "DeepSeek V4.1 Flash", "role": "cloud", "score": 56},
            {"model": "Open data only", "role": "baseline", "score": 0},
        ]},
    ],
}


def test_llm_text_uses_only_numbers_from_the_results() -> None:
    preferred, short, shortest = llm_text(LLM)
    assert preferred == (
        "Tested whether cloud LLMs find Malaysia's latest official figure when open data lags: 30 DOSM, BNM and MYNIC statistics, 120 verified questions; "
        "with tools, DeepSeek V4.1 Flash gave the latest figure on 56% of out-of-date questions, versus 0% for the open data alone."
    )
    assert short == f"{LLM_HEAD} with tools, DeepSeek V4.1 Flash gave the latest figure on 56% of out-of-date questions, versus 0% for the open data alone."
    assert shortest.endswith("DeepSeek V4.1 Flash was right on 56% of out-of-date questions.")
    assert all(text.startswith(LLM_BULLET[-1]) for text in (preferred, short, shortest))  # so a later run finds the bullet again


def test_llm_text_stops_on_an_unexpected_label() -> None:
    odd = {**LLM, "keyNumbers": [{}, {}, {"value": "30", "label": "questions."}]}
    with pytest.raises(SystemExit, match="Unexpected LLM Eval Lab key number label"):
        llm_text(odd)


def test_llm_tech_line_names_what_the_pipeline_uses() -> None:
    assert "open weight" not in LLM_TECH_NEW and all(name in LLM_TECH_NEW for name in ("Ollama Cloud", "PyMuPDF", "data.gov.my", "MYNIC"))
```

- [ ] **Step 2: Run the tests to verify they fail**

Run (in `analysis/`): `uv run pytest tests/test_update_cv.py`
Expected: FAIL with `ImportError: cannot import name 'LLM_BULLET' from 'tools.update_cv'`.

- [ ] **Step 3: Write the LLM Eval Lab edits**

Replace `analysis/tools/update_cv.py` with:

```python
"""Rewrites the Forecasting Lab, Penang Pulse and LLM Eval Lab entries on page 2 of the CV from the published results.

Each edit finds the entry in any of its known states (the original wording or an earlier run of this tool), so running it
again on an updated CV is safe.

Run from analysis/:
  uv run --no-project --with pymupdf==1.26.7 python tools/update_cv.py SOURCE.pdf TARGET.pdf --png-dir DIR
SOURCE and TARGET may be the same file. PyMuPDF is imported inside main(), so the tests need only the standard library.
"""

from __future__ import annotations

import argparse
import json
import os
import re
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REPO_DIR = Path(__file__).resolve().parents[2]
RESULTS_DIR = REPO_DIR / "apps/web/src/content/results"
PAGE = 1  # zero-based: the projects page
RIGHT_EDGE = 562.0  # widest existing body line ends at 561.8
BODY = {"fontname": "helv", "fontsize": 9.5, "color": (0, 0, 0)}  # LiberationSans is metric-compatible with Helvetica
TECH = {"fontname": "heit", "fontsize": 8.5, "color": (0x55 / 255,) * 3}  # Helvetica-Oblique for the grey tech lines
TECH_INSET = 1.5  # the tech line's box overlaps the heading above it by 0.5 pt
LINE_GAP = 15.0  # baselines further apart than this belong to different entries
FORECAST_BULLET = ("Leakage safe 15 minute traffic forecasting",)
PULSE_BULLET = ("Reproducible study of how evenly clinics", "In progress: a reproducible study", "Road distance from every")
FORECAST_TECH_OLD = "Python, scikit-learn, NumPy, SciPy, Pydantic, UCI dataset 608"
FORECAST_TECH_NEW = "Python, scikit-learn, NumPy, SciPy, PyTorch, Chronos, UCI dataset 608"
PULSE_TECH_OLD = (
    "Python, NumPy, Pydantic, Penang GeoHub, OpenStreetMap, DOSM data, Next.js, React Three Fiber",
    "Python, NumPy, Pydantic, Penang GeoHub, OpenStreetMap, DOSM data, Next.js",
)
PULSE_TECH_NEW = "Python, NumPy, SciPy, NetworkX, rasterio, Shapely, pyosmium, OpenStreetMap, WorldPop, DOSM data, Next.js"
LLM_HEAD = "Tested whether cloud LLMs find Malaysia's latest official figure when open data lags:"
LLM_BULLET = ("Designing a benchmark of a classical baseline", LLM_HEAD)
LLM_TECH_OLD = "Python, LLM APIs, open weight models, bootstrap confidence intervals"
LLM_TECH_NEW = "Python, Ollama Cloud, tool calling, PyMuPDF, bootstrap intervals, data.gov.my, DOSM, BNM, MYNIC"
LLM_LABEL_OLD = "  |  In Progress"
LLM_LABEL_NEW = "  |  LLM Evaluation"
LABEL = {"fontname": "heit", "fontsize": 9.5, "color": (0, 0, 0)}  # the italic label beside an entry's title

Width = Callable[[str], float]


@dataclass(frozen=True)
class Line:
    x: float  # where the text starts, after any bullet
    baseline: float
    top: float
    bottom: float


@dataclass(frozen=True)
class TextLine:
    line: Line
    text: str  # without a leading bullet
    size: float
    bold: bool
    bullet: bool  # starts with a bullet glyph


def change(name: str, percent: float) -> str:
    return f"{'fell' if percent >= 0 else 'rose'} {round(abs(percent))}% with {name}"


HEADLINE_LABEL = re.compile(r"^lower error than persistence for (?P<name>.+) at \d+ minutes\.$")
HEADLINE_INTERVAL = re.compile(r"95% interval (?P<low>\d+) to (?P<high>\d+)%")
CHRONOS_LABEL = re.compile(r"^lower error for Chronos, with no tuning, than (?P<name>.+) at \d+ hours\.$")


def headline_text(results: dict[str, Any], head: str) -> str | None:
    """The wording with the published interval, parsed from keyNumbers. None unless both changes are reductions."""
    short, long = results["keyNumbers"][0], results["keyNumbers"][1]
    label, chronos_label = HEADLINE_LABEL.match(short["label"]), CHRONOS_LABEL.match(long["label"])
    interval = HEADLINE_INTERVAL.search(short["caveat"])
    if not (label and chronos_label and interval):
        return None
    hours = results["horizons"][-1] // 60
    name, rival = label["name"], chronos_label["name"]
    return (
        f"{head} {name[0].upper()}{name[1:]} cut MAE {short['value']} (95% interval {interval['low']} to {interval['high']}%) "
        f"versus persistence at {results['horizons'][0]} minutes; zero-shot Chronos beat {'it' if rival == name else rival} "
        f"by {long['value']} at {hours} hours."
    )


def forecast_text(results: dict[str, Any]) -> tuple[str, ...]:
    """Candidate wordings, preferred first, built only from numbers in the results file."""
    first = {m["id"]: m["mae"][0] for m in results["models"]}
    cut = {k: 100 * (1 - first[k] / first["persistence"]) for k in ("gb", "mlp", "chronos")}
    minutes = results["horizons"][0]
    sensors = results["keyNumbers"][2]["value"]
    head = f"Leakage safe {minutes} minute traffic forecasting benchmark across a {sensors} sensor network."
    full = (
        f"{head} At {minutes} minutes versus persistence, MAE {change('gradient boosting', cut['gb'])}, "
        f"{change('a spatial MLP', cut['mlp'])} and {change('zero-shot Chronos', cut['chronos'])}."
    )
    short = f"{head} At {minutes} minutes, MAE {change('gradient boosting', cut['gb'])} versus persistence."
    preferred = headline_text(results, head)
    return (full, short) if preferred is None else (preferred, full, short)


PULSE_LABEL = re.compile(r"^of (?P<district>.+) residents live more than 3 km by road from a public clinic\.$")


def pulse_text(results: dict[str, Any]) -> tuple[str, ...]:
    """Candidate wordings, preferred first, built only from the key numbers in the results file. All start with PULSE_BULLET[-1]."""
    far, count, transit = results["keyNumbers"]
    label = PULSE_LABEL.match(far["label"])
    if label is None:
        raise SystemExit(f"Unexpected Penang Pulse key number label: {far['label']!r}")
    claim = f"{far['value']} of {label['district']} residents live over 3 km from a clinic"
    return (
        f"Road distance from every populated 100 m cell in Penang to the nearest of {count['value']} public clinics, schools and bus stops. "
        f"{claim[0].upper()}{claim[1:]}; {transit['value']} of all residents live within 1 km of a bus stop.",
        f"Road distance from every populated 100 m cell in Penang to the nearest public clinic, school and bus stop; {claim}.",
        f"Road distance from every populated cell in Penang to the nearest clinic, school and bus stop; {claim}.",
    )


LLM_COUNT = re.compile(r"^statistics, asked 4 ways each: (?P<questions>[\d,]+) questions verified")


def llm_text(results: dict[str, Any]) -> tuple[str, ...]:
    """Candidate wordings, preferred first, built only from the results file. All start with LLM_HEAD."""
    stale = next(t for t in results["tasks"] if t["id"] == "stale-tools")["rows"]
    clouds = [r for r in stale if r["role"] == "cloud"]
    best, base = max(clouds, key=lambda r: r["score"]), next(r for r in stale if r["role"] == "baseline")
    count = LLM_COUNT.match(results["keyNumbers"][2]["label"])
    if count is None:
        raise SystemExit(f"Unexpected LLM Eval Lab key number label: {results['keyNumbers'][2]['label']!r}")
    statistics, questions = results["keyNumbers"][2]["value"], count["questions"]
    claim = f"with tools, {best['model']} gave the latest figure on {best['score']}% of out-of-date questions, versus {base['score']}% for the open data alone."
    return (
        f"{LLM_HEAD} {statistics} DOSM, BNM and MYNIC statistics, {questions} verified questions; {claim}",
        f"{LLM_HEAD} {claim}",
        f"{LLM_HEAD} with tools, {best['model']} was right on {best['score']}% of out-of-date questions.",
    )


def wrap(text: str, width: Width, limits: list[float]) -> list[str] | None:
    """Greedy word wrap into at most len(limits) lines, line i no wider than limits[i]. None when it does not fit."""
    lines: list[str] = []
    for word in text.split():
        if lines and width(f"{lines[-1]} {word}") <= limits[len(lines) - 1]:
            lines[-1] = f"{lines[-1]} {word}"
        elif len(lines) < len(limits) and width(word) <= limits[len(lines)]:
            lines.append(word)
        else:
            return None
    return lines


def choose(candidates: tuple[str, ...], width: Width, limits: list[float]) -> list[str]:
    for text in candidates:
        lines = wrap(text, width, limits)
        if lines is not None:
            return lines
    raise SystemExit(f"No wording fits in {len(limits)} lines; shorten the candidates: {candidates[-1]!r}")


def text_lines(page: Any) -> list[TextLine]:
    """Every text line on the page in reading order, with any leading bullet glyph removed. A bullet on its own is skipped."""
    found = []
    for block in page.get_text("rawdict")["blocks"]:
        for line in block.get("lines", []):
            chars = [c for span in line["spans"] for c in span["chars"]]
            lead = next((i for i, c in enumerate(chars) if c["c"] not in "• "), len(chars))
            if lead == len(chars):
                continue
            span = line["spans"][0]
            at = Line(x=chars[lead]["bbox"][0], baseline=span["origin"][1], top=line["bbox"][1], bottom=line["bbox"][3])
            text = "".join(c["c"] for c in chars[lead:])
            found.append(TextLine(at, text, round(span["size"], 1), "Bold" in span["font"], chars[0]["c"] == "•"))
    return sorted(found, key=lambda t: (t.line.baseline, t.line.x))


def bullet_lines(page: Any, starts: tuple[str, ...]) -> list[Line]:
    """The line starting with one of `starts`, then its continuation lines: same size, no bullet, not bold, close below."""
    lines = text_lines(page)
    first = next((i for i, t in enumerate(lines) if t.text.startswith(starts)), None)
    if first is None:
        raise SystemExit(f"No line starts with any of {starts}")
    found = [lines[first]]
    for t in lines[first + 1 :]:
        if t.size != found[0].size or t.bold or t.bullet or t.line.baseline - found[-1].line.baseline > LINE_GAP:
            break
        found.append(t)
    return [t.line for t in found]


def replace_bullet(page: Any, starts: tuple[str, ...], candidates: tuple[str, ...], fitz: Any) -> None:
    targets = bullet_lines(page, starts)
    width = lambda s: fitz.get_text_length(s, fontname=BODY["fontname"], fontsize=BODY["fontsize"])  # noqa: E731
    text = choose(candidates, width, [RIGHT_EDGE - line.x for line in targets])
    for line in targets:
        page.add_redact_annot(fitz.Rect(line.x + 0.2, line.top + 0.5, RIGHT_EDGE + 1, line.bottom - 0.5), fill=(1, 1, 1))
    page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE, graphics=fitz.PDF_REDACT_LINE_ART_NONE)
    for line, words in zip(targets, text, strict=False):
        page.insert_text((line.x, line.baseline), words, **BODY)


def replace_tech_line(page: Any, old: tuple[str, ...], new: str, fitz: Any, style: dict[str, Any] = TECH) -> None:
    """Swap the one span that reads any of `old`, or `new` from an earlier run, for `new`: a grey tech line unless another style is given."""
    spans = [s for b in page.get_text("dict")["blocks"] for line in b.get("lines", []) for s in line["spans"] if s["text"] in (*old, new)]
    if len(spans) != 1:
        raise SystemExit(f"Expected one span reading one of {(*old, new)}, found {len(spans)}")
    span = spans[0]
    end = span["origin"][0] + fitz.get_text_length(new, fontname=style["fontname"], fontsize=style["fontsize"])
    if end > RIGHT_EDGE:
        raise SystemExit(f"{new!r} ends at x = {end:.1f}, past {RIGHT_EDGE}")
    x0, y0, x1, y1 = span["bbox"]
    page.add_redact_annot(fitz.Rect(x0, y0 + TECH_INSET, x1, y1), fill=(1, 1, 1))  # clear of the heading's descenders above
    page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE, graphics=fitz.PDF_REDACT_LINE_ART_NONE)
    page.insert_text(span["origin"], new, **style)


def render(doc: Any, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    doc[PAGE].get_pixmap(dpi=110).save(path)


def main(argv: list[str] | None = None) -> None:
    import fitz  # PyMuPDF

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("source", type=Path)
    parser.add_argument("target", type=Path)
    parser.add_argument("--png-dir", type=Path, required=True)
    args = parser.parse_args(argv)

    forecast = json.loads((RESULTS_DIR / "forecasting-lab.json").read_text())
    pulse = json.loads((RESULTS_DIR / "penang-pulse.json").read_text())
    llm = json.loads((RESULTS_DIR / "llm-eval-lab.json").read_text())
    doc = fitz.open(args.source)
    render(doc, args.png_dir / f"{args.target.stem}-before.png")
    page = doc[PAGE]
    replace_tech_line(page, PULSE_TECH_OLD, PULSE_TECH_NEW, fitz)
    replace_tech_line(page, (FORECAST_TECH_OLD,), FORECAST_TECH_NEW, fitz)
    replace_bullet(page, PULSE_BULLET, pulse_text(pulse), fitz)
    replace_bullet(page, FORECAST_BULLET, forecast_text(forecast), fitz)
    replace_tech_line(page, (LLM_LABEL_OLD,), LLM_LABEL_NEW, fitz, LABEL)
    replace_tech_line(page, (LLM_TECH_OLD,), LLM_TECH_NEW, fitz)
    replace_bullet(page, LLM_BULLET, llm_text(llm), fitz)
    render(doc, args.png_dir / f"{args.target.stem}-after.png")
    args.target.parent.mkdir(parents=True, exist_ok=True)
    scratch = args.target.with_suffix(".tmp.pdf")
    doc.save(scratch, garbage=3, deflate=True)
    doc.close()
    os.replace(scratch, args.target)
    print(f"wrote {args.target}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run the tests**

Run (in `analysis/`): `uv run pytest tests/test_update_cv.py`, then `uv run pytest`.
Expected: `15 passed`, then `247 passed`.

- [ ] **Step 5: Inspect the spans before editing**

Run (in `analysis/`):

```bash
uv run --no-project --with pymupdf==1.26.7 python -c "
import fitz, sys
for path in sys.argv[1:]:
    page = fitz.open(path)[1]
    print('==', path)
    for b in page.get_text('dict')['blocks']:
        for l in b.get('lines', []):
            for s in l['spans']:
                if 240 < s['bbox'][1] < 310:
                    print([round(v, 1) for v in s['bbox']], s['font'], round(s['size'], 1), repr(s['text']))
" "../.context/resume/Subashanan Nair Resume - Data Scientist (updated).pdf" ../apps/web/public/subashanan-nair-cv.pdf
```

Expected, for both files (checked on 2026-10-15): `'LLM Eval Lab'` in `LiberationSans-Bold` 10 at y 247.4; `'  |  In Progress'` in `LiberationSans-Italic` 9.5 at x 114.9; the tech line `'Python, LLM APIs, open weight models, bootstrap confidence intervals'` in `LiberationSans-Italic` 8.5 at y 259.5; three `LiberationSans` 9.5 lines, the first starting `'•  Designing a benchmark of a classical baseline'` at x 54.8 and the others at x 64.9; then `'Documentation MCP Server'` at y 307.9. If the layout differs, stop and report it instead of running Step 6.

- [ ] **Step 6: Update both PDFs**

Run (in `analysis/`):

```bash
uv run --no-project --with pymupdf==1.26.7 python tools/update_cv.py \
  "../.context/resume/Subashanan Nair Resume - Data Scientist (updated).pdf" \
  "../.context/resume/Subashanan Nair Resume - Data Scientist (updated).pdf" --png-dir ../.context/resume
uv run --no-project --with pymupdf==1.26.7 python tools/update_cv.py \
  ../apps/web/public/subashanan-nair-cv.pdf ../apps/web/public/subashanan-nair-cv.pdf --png-dir ../.context/resume
```

Expected: two `wrote ...` lines. If either prints `No wording fits`, shorten the candidates in `llm_text` (the words, never the numbers), keep every candidate starting with `LLM_HEAD`, rerun the tests, and repeat.

- [ ] **Step 7: Check the result**

Run Step 5's command again.
Expected: the label reads `'  |  LLM Evaluation'`; the tech line reads `Python, Ollama Cloud, tool calling, PyMuPDF, bootstrap intervals, data.gov.my, DOSM, BNM, MYNIC` and ends before x = 562; the bullet starts `Tested whether cloud LLMs find Malaysia's latest official figure when open data lags:` and its model name, shares and counts equal the `stale-tools` rows and `keyNumbers[2]` in `llm-eval-lab.json`; no line passes x = 562; `'Documentation MCP Server'` has not moved.

Open the `*-before.png` and `*-after.png` renders in `.context/resume/` side by side: same margins and baselines, the bullet glyph intact, no overlap with the tech line or the next heading, and the Penang Pulse and Forecasting Lab entries unchanged.

Run: `git check-ignore -v ".context/resume/Subashanan Nair Resume - Data Scientist (updated).pdf"`
Expected: one line naming the ignore rule. If it prints nothing, do not commit anything from `.context/` and add `.context/` to `.git/info/exclude` first.

- [ ] **Step 8: Commit**

```bash
git add analysis/tools/update_cv.py analysis/tests/test_update_cv.py apps/web/public/subashanan-nair-cv.pdf
git commit -m "feat: update the CV from the LLM Eval Lab results"
```

- [ ] **Step 9: Run every check**

Run from the root: `npm test`, `npm run lint`, `npm run typecheck`, `npm run build`. Then in `analysis/`: `uv sync --locked` and `uv run pytest`.
Expected: `Tests  169 passed (169)`, no lint or type errors, a successful build, and `247 passed`. Restore `apps/web/next-env.d.ts` afterwards with `git checkout -- apps/web/next-env.d.ts`.

- [ ] **Step 10: Check what the branch adds**

Run: `git diff --stat main...HEAD` and `git diff main...HEAD --name-only | grep -E "data/raw|\.venv|\.env|\.vercel|\.context|\.superpowers|next-env|\.parquet$|\.pdf$|\.xlsx$|\.jsonl$|mynic"`.
Expected: the files in the file map only; the grep prints only `apps/web/public/subashanan-nair-cv.pdf`.

- [ ] **Step 11: Hand over to the controller**

Do not push or open the pull request; the controller does. Report: the commits on the branch; the test counts from Step 9; the snapshot date and catalogue commit; the current and out-of-date split; the corrections Subashanan made in Task 6 (from `git show` of that commit); the pilot and full-run usage from the manifest; and, verbatim from `llm-eval-lab.json`, the `answer`, the three key numbers, each view's rows and the error examples, for Subashanan to approve. List this plan's decisions (the section above) for the pull request body, and remind the controller to merge with a merge commit so the run commit the results cite stays on `main`.

---
