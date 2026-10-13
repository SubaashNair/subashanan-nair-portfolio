# Forecasting Lab Real-Results Pipeline

> Date: 2026-10-13. Status: draft for review.
> Brief approved by Subashanan on 2026-10-13 (`.context/forecasting-planning-brief.md`). This spec turns that brief into a design and records what the data showed when it was checked.
> Implementation plan: `docs/superpowers/plans/2026-10-13-forecasting-lab-pipeline.md`.

## 1. Purpose

Replace the Forecasting Lab's illustrative fixture with real, reproducible results, so that the production site and the CV show numbers that come from one committed results file.

Success means:

- `uv run pytest` in `analysis/` passes offline in CI, with no PyTorch installed;
- one command run locally downloads UCI dataset 608, trains and scores five models, and writes `apps/web/src/content/results/forecasting-lab.json` and a manifest;
- the production build shows the Forecasting Lab with those numbers and fails if the file is malformed;
- both CV PDFs quote numbers read from the same file.

## 2. What this changes

| Earlier decision | Where | Replaced by |
|---|---|---|
| Four models: seasonal naive, gradient boosting, GRU, Chronos | `ForecastModelId`, fixture, study record | Five models: persistence, daily seasonal naive, gradient boosting, spatial MLP, Chronos (section 7) |
| Seasonal baseline from "the same weekday last week" | Study method | Persistence is the main baseline; the seasonal baseline uses the same time one publisher day earlier (section 7) |
| Readings in "vehicles per 5 minutes", 24 steps ahead | Fixture and figure captions | A flow index per 15 minutes, 8 steps ahead (section 4.2) |
| `uv run python -m analysis.forecasting.run --seed 42` | Study reproduce commands | `uv run --group chronos python -m forecasting.cli --seed 42`, run from `analysis/` |
| `published` is empty | `content/results/index.ts` | `published["forecasting-lab"]` is the validated results file |
| Study status "In progress" | `content/studies.ts` | "Published" |

Unchanged: the honesty rule (only `src/lib/study-results.ts` branches on `NODE_ENV`; published results always win), the chart contract (`actual` has `pastSteps + aheadSteps + 1` values, each forecast `aheadSteps + 1`, index 0 is the origin), the copy rules, and the figure layout.

## 3. Scope

**In scope**

- A Python 3.12 workspace `analysis/`, managed with uv, with the package `analysis/forecasting/` and its pytest suite.
- The real run, and committing its two small outputs: the results JSON and `analysis/outputs/forecasting-lab-manifest.json`.
- Web: five model ids, the 15-minute chart fixes, the validator, publishing the results, and the updated study record.
- CI: a Python job beside the web job.
- The two CV PDFs.

**Out of scope**

- Scheduled refreshes, any runtime training, and any other study's pipeline.
- Changing the figure's design beyond the unit, tick and caption fixes in section 10.
- Committing raw data, model weights, `.env*`, `.vercel/` or the full CV.

## 4. Data

### 4.1 Source

| Item | Value |
|---|---|
| Dataset | UCI Machine Learning Repository dataset 608, "Traffic Flow Forecasting" |
| Zip | `https://archive.ics.uci.edu/static/public/608/traffic+flow+forecasting.zip` (4,398,562 bytes) |
| Zip SHA-256 on 2026-10-13 | `b09ebe53ec44228bfd008d35fb34d12174b5523f7a735d159d9eea326163bc45` |
| `traffic_dataset.mat` SHA-256 | `45a3f8b443fd48e2d687d3169d95ac68b6bc31999343b1885eadb787d3aaedbc` |
| Licence | CC BY 4.0, read on `https://archive.ics.uci.edu/dataset/608/traffic+flow+forecasting` on 2026-10-13. DOI `10.24432/C57897`. Re-checked during the real run (plan Task 11) |
| Citation requested | Zhao, Gkountouna and Pfoser (2019), ACM TSAS 5(3), DOI `10.1145/3339823` |

The zip also holds `Traffic Flow Prediction Dataset.docx` and `__MACOSX/` entries. Only `traffic_dataset.mat` is extracted. Raw files live in `analysis/data/raw/`, which `.gitignore` already excludes. The pipeline records both checksums and the download time in the manifest on every run; it does not pin them, so a re-published file is visible in review rather than silently failing.

### 4.2 What the file holds (checked on 2026-10-13)

- `tra_Y_tr` float64 (36, 1261) and `tra_Y_te` float64 (36, 840): flow at 36 sensors every 15 minutes.
- `tra_X_tr` (1, 1261) and `tra_X_te` (1, 840): object arrays whose cells are 36x48 matrices. `scipy.io.loadmat` returns each cell as a sparse `csc_array`.
- `tra_adj_mat` uint8 (36, 36): symmetric, zero diagonal, every sensor has 1 to 7 neighbours.
- **Values are scaled by the publisher to 0 to 1, not vehicle counts.** The maximum in `tra_Y_tr` is exactly 1.0. The site shows them times 100 as a "flow index", where 100 is the busiest reading in the dataset.
- **The series covers weekdays only.** In every cell of `tra_X_tr`, columns 10 to 14 hold a one-hot weekday code and columns 15 to 38 a one-hot hour. For every step t, the weekday code equals `(t // 96) % 5` and the hour equals `(t // 4) % 24`. So step 0 is 00:00 on weekday code 0, each block of 96 steps is one weekday, and weekends are absent. The loader checks this on every run and fails if it ever stops holding.
- **The published start and end times do not match the publisher's own fields.** The dataset note says `tra_Y_tr` ends at 2017-02-01 00:15. The brief computed a start of 2017-01-18 13:15; counting 1,260 steps back from that end actually gives 2017-01-18 21:15, and neither matches the hour field, which puts step 0 at 00:00 and the last step at 03:00. No absolute dates are shown anywhere, so this does not affect results. Clock times on the site use the publisher's hour field.
- **That clock may be offset from local time.** On the publisher's clock, flow rises steeply between about 01:30 and 03:00 and falls after about 16:30, a shape that looks like local commuting about five hours later. This cannot be confirmed from the source, so it is stated as a limitation and the figure caption says the clock times are the dataset's own.
- The shipped lag columns are shifted (the newest lag in `tra_X_tr[t]` equals `tra_Y_tr[t - 2]`). This does not matter here because features are built from `tra_Y_tr` directly, as the brief requires.

## 5. Split and leakage rules

Only `tra_Y_tr` (1,261 steps, about 13 weekdays) is used. The dataset's own "test" block is earlier in time and is not used.

| Block | Steps | Length |
|---|---|---|
| Train | [0, 864) | 9 days |
| Validation | [864, 1056) | 2 days, tuning only |
| Test | [1056, 1261) | 205 steps: 2 days and 13 steps (51 hours 15 minutes) |

- **Forecast origins.** A model at origin t sees readings at steps t and earlier and forecasts steps t+1 to t+8. Training origins run from 9 (the first with ten lags) to `864 - steps - 1`, so every training target sits inside the training block. Validation and test origins run from `block.start - 1` to `block.stop - 9`, so every target at every step from 1 to 8 sits inside its block. Inputs may come from earlier blocks; that is history, not leakage. Test: 198 origins (1055 to 1252).
- **Fitted statistics.** The MLP's `StandardScaler` sits inside its scikit-learn pipeline, so it is fitted on training rows only. Gradient boosting uses no scaler and `early_stopping=False`, so it never carves its own validation split. The tuned estimator that is scored is the one fitted on train; it is not refitted on validation data.
- **Tests prove** (plan Tasks 3 to 5): the three blocks are ordered, contiguous and disjoint; replacing every value after step t leaves all features for origins up to t unchanged; training targets never reach the validation block; and the fitted scaler's means equal the training feature means and differ from means that include validation rows.

## 6. Features

One row per (origin, sensor), 19 columns, built from `tra_Y_tr` only:

- `lag_0` to `lag_9`: the sensor's last ten readings, newest first;
- `neighbour_now` and `neighbour_mean_4`: the mean flow of the sensor's neighbours in `tra_adj_mat` at the origin, and averaged over the last four steps;
- `slot_sin`, `slot_cos`: the quarter-hour of the publisher's day on a circle;
- `weekday_0` to `weekday_4`: the publisher's weekday code, one-hot.

Both tuned models use the same features. The brief calls the MLP "spatial" because it takes the neighbour means; giving gradient boosting the same inputs keeps the comparison about the model, not the inputs.

## 7. Models

Every model forecasts steps 1 to 8 for all 36 sensors at every origin. The site and the scores use steps 1, 2, 4, 6 and 8 (15, 30, 60, 90 and 120 minutes). Steps 3, 5 and 7 are also forecast, never interpolated, so each sensor's forecast line is real.

| Id | Name on site | How it forecasts |
|---|---|---|
| `persistence` | Persistence | The latest reading, for every step. The main baseline |
| `seasonal` | Daily seasonal naive | The reading 96 steps before the target: the same time on the previous publisher day, which after a Monday is the Friday |
| `gb` | Gradient boosting | `HistGradientBoostingRegressor`, one per step, `max_iter=300`, tuned over learning rate {0.05, 0.1} and max leaf nodes {15, 31} |
| `mlp` | Spatial MLP | `StandardScaler` then `MLPRegressor`, one per step, `max_iter=200`, tuned over hidden layers {(64), (128, 64)} and alpha {1e-4, 1e-3} |
| `chronos` | Chronos, zero-shot | `amazon/chronos-t5-small` at revision `a971ba21945c4f1796b17a91fe69214b5f4ad472`, CPU, float32. For each origin, each sensor's last 512 readings (the model's context length), 20 sample paths, 8 steps; the forecast is the median path. No tuning |

Tuning picks, per step, the grid point with the lowest validation MAE (the first wins a tie). All seeds are 42: `random_state` for both scikit-learn models, `torch.manual_seed` before Chronos, and the bootstrap generator.

Chronos and PyTorch are a uv dependency group, `chronos` (`chronos-forecasting==2.3.2`, `torch>=2.4,<3`). `uv sync` and CI never install it. The adapter imports `torch` and `chronos` only inside `load_chronos`, and takes any callable `predictor(context, steps)`, so tests pass a small fake.

## 8. Evaluation

- **Metric.** MAE per model per horizon over all 198 test origins and 36 sensors, in the publisher's 0 to 1 units, exported times 100.
- **Intervals.** A non-overlapping block bootstrap over test origins: blocks of 8 consecutive origins (2 hours), resampled with replacement 2,000 times with seed 42; the interval is the 2.5th to 97.5th percentile. Blocks keep neighbouring, correlated errors together. Two test days are too few to resample by day.
- **Key comparisons**, each a paired bootstrap (both models scored on the same resampled origins):
  - **Short:** at 15 minutes, the model other than persistence with the lowest MAE, against persistence, as a percentage reduction with interval.
  - **Long:** at 120 minutes, Chronos against the better of gradient boosting and the spatial MLP, as a percentage reduction with interval. A negative reduction means Chronos has higher error, and the text says so.

## 9. Outputs

### 9.1 Results file

`apps/web/src/content/results/forecasting-lab.json` matches `ForecastResults`:

- `horizons`: `[15, 30, 60, 90, 120]`.
- `models`: the five ids in the order of section 7, each with `mae` times 100, rounded to 2 decimals.
- `sensors`: three test sensors, chosen by mean test flow at positions `floor(q * 35)` of the sorted order for q = 1/6, 1/2 and 5/6 (a quiet, a typical and a busy sensor). Ids are `s<n>` and labels `Sensor <n>`, 1-based in the file's order. For each, the origin is the test origin, with at least 36 steps of history, where that sensor's flow changes most over the next two hours. That is where the models differ most, and the study's figure plan says so. `pastSteps` 36, `stepMinutes` 15, `originMinutes` from the publisher's clock, `actual` 45 values, every forecast 9 values starting with the observed origin value, and `windowMae` over the 8 forecast steps. All times 100.
- `run`: `commit` (short hash of `HEAD` when the run started), `manifest` (`analysis/outputs/forecasting-lab-manifest.json`), `python` (the interpreter's full version), `lastRun` (run date, UTC, `YYYY-MM-DD`).
- `retrieved`: `{"Dataset 608": <zip download date>, "chronos-t5-small": <run date>}`. The keys equal the source names in the study record, which a web test checks.

### 9.2 Prose templates

The answer and key numbers are produced by fixed templates in `forecasting/export.py`. Every number in them is computed. "lower" or "higher" follows the sign, and the interval is flipped to match, so a negative reduction reads as "8% higher error ... (95% interval 2 to 14%)". Example of the template's shape (numbers here are made up for illustration and are not results):

> At 15 minutes, gradient boosting is the strongest challenger, with 22% lower error than persistence (95% interval 15 to 28%). At 2 hours, Chronos, used with no tuning, has 8% higher error than the spatial MLP, the better tuned model there (95% interval 2 to 14%).

Key numbers: (1) the short comparison, (2) the long comparison, (3) the sensor count from the data, labelled "sensors scored at 5 horizons on the final 51 hours of data." with the caveat "One highway corridor near Washington DC, so treat the ranking as local." Subashanan approves the wording at PR time; a change of wording is a change to the template, never to the JSON.

### 9.3 Manifest

`analysis/outputs/forecasting-lab-manifest.json` (committed, a few kilobytes): source title, URL, page, DOI, licence, retrieval timestamp, zip and .mat SHA-256; the calendar facts; split boundaries; feature names; horizon steps; seeds; the bootstrap settings; per step the chosen settings, their validation MAE and every candidate's; the Chronos model, revision, licence, context length and sample count; every model's MAE and interval at each horizon and both comparisons; package versions (Python, numpy, scipy, scikit-learn, torch, chronos-forecasting); the git commit and whether the tree was dirty; and the results file path.

## 10. Website changes

- `ForecastModelId` becomes `"persistence" | "seasonal" | "gb" | "mlp" | "chronos"`.
- `MODEL_STYLE`: persistence `inkSoft`, dashed `7 5`; seasonal `roseDeep`; gradient boosting `mustardDeep`; spatial MLP `cobalt`; Chronos `jadeDeep`. All five are already at least 3:1 on porcelain and sky (the palette test covers four; a new `model-style.test.ts` checks all five, that they are distinct and that only persistence is dashed).
- The fixture moves to 15-minute steps, 8 ahead, five models and flow-index values. It stays illustrative and is never shown once real results exist.
- Chart fixes the real data needs:
  - `clock()` wraps across midnight, because an origin near 01:00 has history from the previous day;
  - the forecast chart puts an hour tick every `60 / stepMinutes` steps (two hours on narrow screens), not every 12 steps;
  - the error-by-horizon chart scales its axis to the largest MAE with `niceStep()` instead of a fixed 0 to 18;
  - captions and the chart's label say "flow index" instead of "vehicles per 5 minutes", and the caption adds "Clock times are the dataset's own."
- `parseForecastResults(json: unknown): ForecastResults` in `content/results/parse-forecast.ts`: a hand-written check of every field, the five model ids exactly once, MAE rows matching `horizons`, the chart contract per sensor, ISO dates and finite numbers. It throws with the path of the first problem. No new dependency.
- `content/results/index.ts` imports the JSON and sets `published["forecasting-lab"] = parseForecastResults(json)`. Because pages import it at build time, an invalid file fails `next build` (checked during planning: removing one model stops the build with "models must list each of persistence, seasonal, gb, mlp, chronos once").
- Key numbers on the study page are keyed by label rather than value, so two equal percentages cannot collide.
- The study record matches what ran: same question, status "Published", updated planned answer (still no numbers), figure plan, sources (Dataset 608 with CC BY 4.0; chronos-t5-small, Apache 2.0), five method steps, six limitations (one corridor, 13 weekdays without weekends, a short test window, no weather or holidays, MAE hides spikes, the clock caveat) and the new reproduce commands.

## 11. CI

A second job, `analysis`, in `.github/workflows/ci.yml`: checkout, `astral-sh/setup-uv@v10` (uv 0.11.4, Python 3.12, cache keyed on `analysis/uv.lock`), `uv sync --locked`, `uv run pytest`, all in `analysis/`. Tests use a synthetic 4-sensor `.mat` written by `conftest.py` into a temporary folder and a fake Chronos, so CI needs no network and no torch. The web job is unchanged.

## 12. CV

`analysis/tools/update_cv.py` edits page 2 of a CV PDF with PyMuPDF 1.26.7 (run with `uv run --no-project --with pymupdf==1.26.7`, so it adds nothing to the lock):

- **Forecasting Lab bullet:** two lines, rebuilt from the results file: the 15-minute MAE change against persistence for gradient boosting, the spatial MLP and Chronos ("fell" or "rose" by sign). If it does not fit two lines, a shorter wording is tried; if none fits, the script stops.
- **Penang Pulse bullet:** three lines describing the in-progress study (distance from each district to the nearest clinic, school and transit stop, using PeGIS, the 2020 census and OpenStreetMap; method and limitations published ahead of results), with no results claimed.
- **Penang Pulse tech line:** drops "React Three Fiber".
- Text is removed with redaction annotations (images and line art untouched) and re-inserted at the original baselines and left edges in Base-14 Helvetica (`helv`) 9.5pt for bullets and Helvetica-Oblique (`heit`) 8.5pt grey `#555555` for the tech line. LiberationSans is metric-compatible with Helvetica, so widths match. The bullet glyphs stay.
- Inputs: `.context/attachments/emjv7j/Subashanan Nair Resume - Data Scientist.pdf` becomes `.context/resume/Subashanan Nair Resume - Data Scientist (updated).pdf` (git-ignored, never committed, it has a phone number), and `apps/web/public/subashanan-nair-cv.pdf` is updated in place and committed. Before and after renders of page 2 go to `.context/resume/` for a visual check. A dry run during planning confirmed the layout fits.

The Forecasting Lab tech line still lists "Pydantic", which this pipeline does not use. The brief does not ask to change it, so it is left for Subashanan to decide.

## 13. Error handling and edge cases

- Download failure, a zip without `traffic_dataset.mat`, non-finite values, a non-square or asymmetric adjacency, a sensor with no neighbours, or a calendar mismatch: the run stops with a clear error and writes nothing.
- Chronos not installed: `load_chronos` exits with "Chronos is not installed. Run: uv sync --group chronos".
- A predictor returning the wrong shape: `ValueError` naming the shape.
- A block too short to score 8 steps, origins without enough history, or a seasonal lookup before step 0: `ValueError`.
- A malformed results file: the web validator throws and the build fails. A missing results file fails the import, so the build fails too.
- A dirty working tree during the real run is recorded in the manifest (`git.dirty: true`). The plan requires a clean tree before running.

## 14. Testing

Python (pytest, offline, about 10 seconds): data loading and calendar checks, cache reuse without network, the split, feature shapes and no lookahead, baselines, training-target bounds, scaler statistics, tuning choice and reproducibility, the Chronos adapter with a fake, MAE and bootstrap maths, the end-to-end pipeline on the synthetic file, the results contract and templates, the manifest fields, and the CV text helpers.

Web (Vitest): `clock` wrapping and `niceStep`; model styles; the figure with five models (line counts, toggles, bold best per column, hour ticks across midnight, the error axis scale); the validator with a valid file and twelve malformed ones; the published results (five models, sources dated, manifest path, no dashes); and `getStudyResults` returning the published results, not a preview, in every environment.

Every test is written before its code and seen to fail first.

## 15. Decisions the brief did not settle

1. **Clock and calendar.** Time-of-day and weekday come from the publisher's own fields, which match the step index exactly, rather than from the stated dates, which do not (section 4.2). The brief's start time was not used. The possible offset from local time is disclosed, not corrected.
2. **Units.** Values are the publisher's 0 to 1 scale, shown times 100 as a flow index. The site's "vehicles" wording was wrong for this data.
3. **All eight steps are modelled** so the forecast lines have real values at every step; scores use the five brief horizons.
4. **Shared features** for gradient boosting and the MLP (section 6).
5. **Final models are fitted on train only**, because the brief limits validation to tuning.
6. **Bootstrap** over blocks of 8 consecutive origins, 2,000 resamples.
7. **Sensor and window choice** by mean flow quantiles and largest two-hour change, disclosed in the figure plan.
8. **Status "Published"** for the Forecasting Lab once the file exists.
9. **Package layout.** Besides the brief's modules (`data`, `features`, `models`, `evaluate`, `export`, `cli`), the package has `chronos_adapter.py` (keeps torch out of everything else) and `pipeline.py` (the pure orchestration the end-to-end test calls). The CV script lives in `analysis/tools/`.
10. **Python 3.12 is pinned** through `requires-python = ">=3.12,<3.13"`; uv downloads it if the machine lacks it.

## 16. Build order (outline for the implementation plan)

1. Web: five models and the 15-minute chart fixes, against the fixture.
2. Web: the results validator.
3. Python workspace and data loading.
4. Features.
5. Baselines and tuned models.
6. Chronos adapter.
7. Evaluation.
8. Pipeline.
9. Export and templates.
10. CLI, manifest and the CI job.
11. The real run, with outputs committed.
12. Web: publish the results and update the study record.
13. CV PDFs.
14. Final checks and pull request.
