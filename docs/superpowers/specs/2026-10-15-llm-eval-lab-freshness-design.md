# LLM Eval Lab: Finding the Latest Official Figure

> Date: 2026-10-15. Status: draft for review.
> Design agreed with Subashanan in conversation on 2026-10-15. Evidence for the premise: `.context/dgm-freshness-report.md` (data.gov.my freshness audit, 2026-10-15).
> Implementation plan: `docs/superpowers/plans/2026-10-15-llm-eval-lab-freshness.md`, written after this spec is approved.

## 1. Purpose

Replace the LLM Eval Lab's planned Manglish study with a study that answers a practical question for Malaysian analysts:

**When Malaysia's open data is out of date, can a language model still find the latest official figure?**

Success means:

- a frozen snapshot of the relevant open datasets and official releases, with checksums;
- 120 questions with correct answers verified by Subashanan;
- one local command runs the baseline and two Ollama Cloud models, with tools and from memory, and writes `apps/web/src/content/results/llm-eval-lab.json` and a manifest;
- the production site shows the results with no hand-typed numbers, and the build fails on a malformed file;
- `uv run pytest` passes offline in CI with a fake Ollama.

## 2. What this changes

| Earlier plan | Replaced by | Why |
|---|---|---|
| Manglish sentiment, BM entities and BM summaries | One task: the latest official figure for a statistic, scored in three views | Subashanan chose this after the freshness audit; it needs far less labelling and is original |
| Hand-labelling 1,200 items per task with a second annotator | 120 questions whose answers are drafted from the official release and all verified by Subashanan | Answers come from authoritative sources; one careful reviewer is enough |
| Classical baseline, fine-tuned 1B, open 8B, frontier model | A dataset-only baseline script and two Ollama Cloud models | Subashanan chose cloud models only for now |
| Cost per 1,000 items in dollars | Tool calls per answer and median seconds per answer | Ollama Cloud is a subscription with no per-call price |
| Three runs per item | One run per question per mode | Saves cloud requests; settings are fixed |

## 3. Scope

In scope: an `evallab` package in `analysis/`; a frozen snapshot; the question set and review sheet; the runner, scoring and export; a results validator; site type and figure changes; the study record; CI; the CV bullet.

Out of scope: local models (may be added later as extra rows); departments other than DOSM and BNM; any live querying at answer time (tools read only the snapshot); fine-tuning.

## 4. Premise, from the freshness audit

Of 295 data.gov.my datasets assessed on 2026-10-15, 50 (17%) were behind their own schedule after allowing a normal publication delay. DOSM's headline series (CPI, overall unemployment, GDP, trade, industrial production) were current, while some DOSM series and other agencies lagged (for example `fdi_flows` ended at 2025 Q3 although the 2026 Q2 Balance of Payments report was out; `lfs_month_youth` ended at June 2026 although the August Labour Force report was out; BNM `monetary_aggregates` was two months behind). The study therefore mixes current and out-of-date series, and the site states the audit's numbers only through the results file.

## 5. Data and snapshot

- **Catalogue:** the data.gov.my catalogue metadata from the GitHub repository `data-gov-my/datagovmy-meta` (the API has no list endpoint and allows 4 requests a minute). The commit used is recorded.
- **Datasets:** the parquet files for the chosen series, from the data.gov.my storage URLs in the catalogue.
- **DOSM releases:** the release index in the same repository (the `pub-dosm` folder, 1,509 releases with dates and file links on 2026-10-15) and the release files (PDF or XLSX) for the chosen series, newest first, back far enough to cover the questions.
- **BNM:** the statistics pages or files for money supply and interest rates, cited as "Source: Bank Negara Malaysia" per BNM's terms.
- The snapshot is taken once, on a recorded date, and stored under `analysis/data/raw/evallab/` (gitignored). The manifest records every URL, retrieval time, size and SHA-256. A rerun from the cached snapshot is byte-identical.
- PDF text is extracted once into the snapshot (`pypdf` or PyMuPDF, chosen in the plan after a test on real releases). XLSX is read with `openpyxl`. Extraction quality is good for headline sentences and weak for wide tables (audit finding), so questions target headline figures.

## 6. Questions and correct answers

- About 30 statistics: mostly DOSM (CPI and inflation, overall and youth unemployment, GDP growth, exports and imports, industrial production, net FDI and others), plus BNM money supply (M3) and interest rates. The set includes series where the dataset is current and series where it is behind; the split is recorded.
- 4 questions per statistic, 120 in all: 2 in English and 2 in Bahasa Malaysia, with different phrasings.
- For each statistic the pipeline drafts the correct answer from the latest release in the snapshot: the value, its unit, the period it covers and the release URL. It also records the dataset's latest value and period, so each question is marked current or out of date.
- **Review sheet:** `analysis/evallab/questions.csv` with the drafted answers and a `verified` column. Subashanan checks every row against the linked release and corrects any value. The runner refuses to run while any row is unverified.
- The verified question set is committed and published under CC BY 4.0.

## 7. Models and runs

- **Baseline:** a script with no model, which looks up the matching data.gov.my dataset and returns its latest value and period. It is what a user gets by trusting the open data.
- **Cloud models through Ollama:** `gpt-oss:120b-cloud` and `deepseek-v4.1-flash:cloud`, called through the local Ollama server's chat API. The exact model tags and the Ollama version are recorded.
- **Two modes per model:** with tools, and from memory (no tools). One run per question per mode, so 240 cloud question runs per model. Temperature 0 and a fixed seed where the API accepts them.
- **Tools** (read only the snapshot): `search_datasets(query)`, `read_dataset(id, last_n)`, `search_releases(query, after)`, `read_release(id, page)`. At most 6 tool calls per question; a question that hits the cap is scored on whatever final answer was given.
- **Answer format:** the model must end with a JSON object `{"value": ..., "unit": ..., "period": ..., "source": ...}`. An unparseable answer scores as wrong and is kept as an error example candidate.
- **Pacing:** a 20-question pilot first, with usage and timing logged. The runner records every call (time, model, tokens if reported) to a JSONL log, sleeps between calls, and resumes from the log after a limit or interruption.

## 8. Scoring

For each answer:

- **value correct:** equal to the verified value at the publication's rounding (e.g. one decimal place for a rate);
- **period correct:** the same period as the verified answer;
- **latest figure:** value and period both correct (the main score);
- **source given:** a URL or dataset id that exists in the snapshot.

Scores per model and mode, with 95% intervals from a bootstrap that resamples statistics (all 4 questions of a statistic together), 2,000 resamples, fixed seed. Three views, which become the site's tabs:

1. all series, with tools;
2. out-of-date series only, with tools (the headline);
3. all series, from memory.

Also per model and mode: median seconds per answer and mean tool calls per answer. Results are also split by question language (English and BM) in the manifest.

## 9. Outputs

### 9.1 Results file

`apps/web/src/content/results/llm-eval-lab.json`, in the `LlmEvalResults` shape with these type changes:

- `ModelRole` becomes `"cloud" | "baseline"`.
- `EvalRow.costPer1k` and `costLabel` are replaced by `callsPerAnswer: number` and `callsLabel: string`; `latency` stays (median seconds, as text).
- Tasks are the three views in section 8; rows are the baseline and the two models (the memory tab has no baseline row).
- `errorExamples`: up to 6 real failures chosen by rule (out-of-date value quoted, wrong period, unparseable), each with the question, the verified answer, the model, its answer and a short templated note.

### 9.2 Templated wording

All prose comes from templates in `evallab/export.py`, from computed numbers:

- **Answer:** which model most often gave the latest figure on out-of-date series, its share, and the baseline's share on the same questions.
- **Key numbers:** (1) the best model's latest-figure share on out-of-date series, with its interval; (2) the change in that model's latest-figure share from memory to with tools, in percentage points; (3) the number of statistics and verified questions, and the snapshot date.

### 9.3 Manifest

`analysis/outputs/llm-eval-lab-manifest.json`: snapshot sources with checksums and dates, the catalogue repository commit, the question set checksum and verified count, the current and out-of-date split, model tags, Ollama version, run counts, usage totals from the call log, scores for every view and language, package versions, git commit and dirty flag.

## 10. Website changes

- Types and figure: the role and cost changes in section 9.1; the chart's x axis becomes "tool calls per answer"; role colours and legend labels become cloud model and baseline.
- Fixture `content/fixtures/llm-eval.ts` updated to the new shape (dev-only, illustrative).
- `parseLlmEvalResults` validator with tests; `published["llm-eval-lab"]` set from the validated file.
- Study record: the new question, planned answer, figure plan, data line, sources (data.gov.my CC BY 4.0, DOSM releases, BNM with attribution, the two models via Ollama Cloud, the question set by this project under CC BY 4.0), method, limitations, reproduce commands.
- Limitations to state: the snapshot date (results describe that day); headline figures only, because table extraction from PDFs is unreliable; cloud models change, so results are dated; Ollama does not publish how cloud usage is counted; one reviewer verified the answers.

## 11. CI

The `analysis` job stays as it is. Tests use a fake Ollama server or client and a tiny synthetic snapshot; no network.

## 12. CV

Final task: `tools/update_cv.py` replaces the LLM Eval Lab bullet ("Designing a benchmark of a classical baseline, a fine tuned 1B model...") and its tech line with templated wording read from `llm-eval-lab.json`, fitting the existing lines. Both PDFs are rendered and checked; only the web copy is committed.

## 13. Error handling

- **Fail the run on:** a fixed-source checksum mismatch; any unverified question; a question whose statistic has no snapshot data; the Ollama server unreachable at start.
- **Log and continue:** a model call that errors or times out (retried twice with backoff, then scored as no answer); a usage limit (the runner stops cleanly and resumes from the log next time).

## 14. Testing

- Unit: tool functions on a synthetic snapshot; answer JSON parsing (valid, missing fields, prose around JSON); scoring rules (rounding, period matching); bootstrap grouping by statistic; template wording including ties.
- Integration: the full run on a synthetic snapshot with a fake model that follows a script of tool calls, validated with a Python mirror of the TypeScript validator.
- Web: validator tests; figure tests updated for the new roles and chart axis.

## 15. Decisions this spec makes that the conversation did not

1. Questions target headline figures only, because the audit found table extraction from PDFs unreliable.
2. Bootstrap resamples statistics, not questions, because the 4 questions of a statistic are not independent.
3. The memory tab has no baseline row, because the baseline has no memory mode.
4. Temperature 0 with one run per question; run-to-run variation is not measured (stated as a limitation).

## 16. Build order (outline for the plan)

1. Site: type changes, fixture, figure axis and roles, validator.
2. Analysis: snapshot fetch and freeze (catalogue, datasets, DOSM release index and files, BNM), text extraction.
3. Analysis: the four tools and the baseline script.
4. Analysis: question drafting and the review sheet.
5. Pause: Subashanan verifies the 120 answers.
6. Analysis: the runner (Ollama chat with tools, pacing, log, resume) and the 20-question pilot.
7. Analysis: scoring and bootstrap; export templates; manifest; CLI.
8. The full run; publish on the site; study record.
9. CV bullet, final checks, PR.
