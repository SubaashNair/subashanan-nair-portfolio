# Peranakan redesign: content and fixture data

All figures are ILLUSTRATIVE. They become `src/content/fixtures/` for tests and the development preview, and never ship to production (see the design spec, section 4).
Copy for pages comes from here unless the design spec says otherwise.
Writing rules: no em or en dashes as stylistic punctuation, sentence case, plain verbs, no "→" on links.

## Prototype site map (the Next.js routes are in the design spec, section 6.1)

```
index.html                    Home
work/index.html               Work: list of the three case studies
work/penang-pulse.html
work/forecasting-lab.html
work/llm-eval-lab.html
experiments.html              Tools and experiments
about.html                    About and contact
style.css                     One shared stylesheet per direction
```

Header nav on every page: wordmark "Subashanan Nair" (links home), Work, Experiments, About, GitHub (https://github.com/SubaashNair). Mark the current page with `aria-current="page"`. Nav stays visible on mobile (hide only GitHub under 420px).
Footer on every page: "Subashanan Nair, Penang" and "Source for this site" (https://github.com/SubaashNair/ai-observatory-portfolio).

## Identity

- Name: Subashanan Nair
- Role line: Data scientist in Penang. I build reproducible ML and LLM systems on Malaysian public data, and publish the sources, code and limits behind every result.
- Contact buttons: Email me (`mailto:hello@example.com`), LinkedIn (`#`), Download CV (`#`). These are placeholders.

## Home (index.html)

Keep the existing home mockup for the direction, but point the links at the real pages: "Read the case studies" goes to work/index.html, study links go to their pages, "Get in touch" goes to about.html#contact. The Experiments section on home shows 4 tools plus "See all tools and experiments" linking to experiments.html.

## Case study pages: shared structure

Each case study page has these sections, in order:
1. Title, the question, status, and a one-paragraph short answer.
2. The main interactive figure (see each study).
3. Key numbers: 3 headline figures, each with its uncertainty or caveat.
4. Data sources table: Source, Publisher, What we used, Licence, Retrieved.
5. Method: 4 to 5 numbered steps (numbering is fine here, it is a real sequence).
6. Limitations: 3 to 4 bullets, plain and honest.
7. Reproduce: a code block with the commands, plus commit `a1c9e04`, manifest `manifest.json`, Python 3.12, last run 2026-10-01.
8. Discuss: link "Discuss this study on GitHub" (https://github.com/SubaashNair/ai-observatory-portfolio/discussions).
9. Next and previous study links at the bottom.

### Penang Pulse (work/penang-pulse.html), status: In progress
- Question: How evenly are clinics, schools and transit stops spread across Penang?
- Short answer: Most residents of Timur Laut live within a kilometre of a public clinic. In Seberang Perai Selatan, about 1 in 5 live more than 3 km away, and the gap is widest for clinics rather than schools.
- Main figure: the Penang map with category toggles (Clinics, Schools, Transit stops) PLUS a district selector (Timur Laut, Barat Daya, Seberang Perai Utara, Seberang Perai Tengah, Seberang Perai Selatan) that updates a side panel with that district's numbers.
- District data (share of residents by distance to nearest public clinic, under 1 km / 1 to 3 km / over 3 km; population):
  - Timur Laut: 72 / 24 / 4; 545,000
  - Barat Daya: 48 / 34 / 18; 236,000
  - Seberang Perai Utara: 55 / 33 / 12; 330,000
  - Seberang Perai Tengah: 61 / 30 / 9; 402,000
  - Seberang Perai Selatan: 41 / 38 / 21; 205,000
- Key numbers: "21%" of Seberang Perai Selatan residents live over 3 km from a clinic (95% interval 18 to 24%); "412" public service points mapped; "5" districts compared.
- Sources: PeGIS (Penang state GIS portal) facility layers, CC BY 4.0, retrieved 2026-09-28; DOSM Census 2020 population by mukim, open government licence, retrieved 2026-09-28; OpenStreetMap road network, ODbL, retrieved 2026-09-29.
- Method: collect facility points; join to mukim population; compute road network distance from each population-weighted mukim centroid; band distances; bootstrap mukims for intervals.
- Limitations: centroids hide within-mukim variation; private clinics excluded; OSM road coverage is thinner in rural Seberang Perai; 2020 census population is six years old.
- Reproduce: `uv sync`, `uv run python -m analysis.penang.build --from-cache`, `npm run dev`.

### Forecasting Lab (work/forecasting-lab.html), status: In progress
- Question: Can a pre-trained time-series model beat a tuned baseline on traffic sensors?
- Short answer: At short horizons a tuned gradient boosting model is hard to beat. Past one hour, Chronos, used with no tuning at all, has the lowest error, about 18% below the seasonal baseline at two hours.
- Main figure: a sensor selector (Sensor 12, Sensor 47, Sensor 103) and a forecast chart showing actual traffic plus the four model forecasts for the next 2 hours, with a toggle for each model. Second figure: error by horizon (15, 30, 60, 90, 120 min) for the four models.
- Models and MAE by horizon (15/30/60/90/120 min):
  - Seasonal naive: 9.8 / 11.2 / 13.5 / 15.1 / 16.4
  - Gradient boosting: 6.1 / 7.9 / 10.6 / 12.4 / 14.0
  - Small neural net (GRU): 6.4 / 8.1 / 10.4 / 12.0 / 13.6
  - Chronos (pre-trained, zero-shot): 7.0 / 8.3 / 10.1 / 11.6 / 13.4
- Key numbers: "18%" lower error than the seasonal baseline at 2 hours (interval 12 to 23%); "4" models compared on the same splits; "0" hours of tuning for Chronos.
- Sources: UCI Machine Learning Repository dataset 608 (traffic sensor network), CC BY 4.0, retrieved 2026-09-20; Chronos model weights from Hugging Face (amazon/chronos-t5-small), Apache 2.0, retrieved 2026-09-21.
- Method: chronological train, validation, test splits with no overlap; scalers fit on training data only; seasonal naive baseline from the same weekday last week; tune gradient boosting and GRU on validation only; run Chronos zero-shot; score all on the same test window.
- Limitations: one dataset from one city; Chronos context length caps how much history it sees; no exogenous features like weather or holidays; MAE hides rare congestion spikes.
- Reproduce: `uv sync`, `uv run python -m analysis.forecasting.run --seed 42`, `npm run dev`.

### LLM Eval Lab (work/llm-eval-lab.html), status: Planned
- Question: How well do small and frontier models handle Bahasa Malaysia and Manglish?
- Short answer: On Manglish sentiment, a fine-tuned 1B model lands within 3 points of a frontier model at about a fiftieth of the cost. On summaries, the frontier model still leads clearly.
- Main figure: the leaderboard with task tabs (Manglish sentiment, BM entity extraction, BM summaries): model, score with 95% interval, cost per 1k items, median latency. Use these rows [model, score, low, high, cost per 1k, latency]:
  - Manglish sentiment (Accuracy): Frontier model 87 84 90 $2.10 900 ms; Fine-tuned 1B 84 81 87 $0.04 38 ms; Open 8B, zero-shot 79 75 83 $0.12 210 ms; TF-IDF + logistic 71 67 75 <$0.01 1 ms
  - BM entity extraction (F1): Frontier model 83 80 86 $2.40 1.1 s; Fine-tuned 1B 78 74 81 $0.05 45 ms; Open 8B, zero-shot 70 66 74 $0.14 260 ms; CRF baseline 62 58 66 <$0.01 3 ms
  - BM summaries (Faithfulness): Frontier model 82 79 85 $4.80 2.4 s; Open 8B, zero-shot 71 67 75 $0.30 640 ms; Fine-tuned 1B 66 62 70 $0.09 120 ms; Extractive baseline 58 54 62 <$0.01 5 ms
- Second figure: cost per 1k items (log scale) against score for the selected task, one point per model.
- Error examples (3 rows: input, expected, model output, note):
  - "Wah this nasi lemak damn power lah" | positive | Fine-tuned 1B: positive | correct
  - "Service ok la but wait so long sampai tak larat" | negative | Open 8B: neutral | misses "tak larat" (exhausted)
  - "Boleh tahan, not bad for the price" | positive | TF-IDF: negative | "tahan" read as a complaint
- Key numbers: "3 points" gap between fine-tuned 1B and frontier on sentiment; "1/50th" the cost; "1,200" hand-labelled items per task.
- Sources: hand-labelled Manglish and BM sets (this project, CC BY 4.0, created 2026-09); Malaysian news headlines for summaries (public, research use, retrieved 2026-09-15); model APIs and open weights listed with versions.
- Method: write and freeze labelling guidelines; label 1,200 items per task with a second annotator on 20%; version prompts (v1 to v3) in the repo; run each model 3 times at temperature 0; bootstrap 95% intervals; record cost and latency per call.
- Limitations: Manglish varies by region and age, one set cannot cover it; inter-annotator agreement was 0.81, not perfect; frontier model versions change, so results are dated; costs use list prices on the run date.
- Reproduce: `uv sync`, `uv run python -m analysis.llm_eval.run --task all --prompts v3`, `npm run dev`. Note: needs API keys for hosted models; open models run locally.

## Work index (work/index.html)

Title "Case studies", intro line, then the three studies with question, status, one key number, data, and a link to each page.

## Experiments page (experiments.html)

Filter buttons: All, Agents and MCP, Libraries, Apps, ML projects. Filtering is client-side; buttons use `aria-pressed`.
Items (name | category | language | description | link https://github.com/SubaashNair/<name>):
- documentation-mcp-server | Agents and MCP | JavaScript | An MCP server that gives coding agents up-to-date documentation for popular libraries.
- matomari | Agents and MCP | macOS | A native file explorer with an agent inside, and an importance score for every file built from how you actually use it.
- exam-monitor-app | Apps | Go | Real-time classroom exam monitoring: teachers see live student screens over LAN, with session tokens, lock-all, messaging and CSV audit export.
- CU5_project_dashboard | Apps | Python | Monitors student repositories with GitHub activity, file evidence and requirement-based completion estimates.
- ml-review | Libraries | Python | Extended evaluation metrics for scikit-learn models.
- OutlierCleaner | Libraries | Python | Detects and removes outliers using several statistical methods.
- StatClean | Libraries | Python | Statistical data cleaning and outlier handling.
- OptimRL | Libraries | Python | Reinforcement learning optimisation experiments.
- GRPOptim | Libraries | Python | GRPO training experiments.
- pima-diabetes-mlflow | ML projects | Python | Train, register, serve and ship a classifier end to end with MLflow, Docker and Streamlit.
- Land-subsidence-Prediction | ML projects | Python | Forecasts land subsidence in the Klang Valley from geospatial and temporal data.
- Taiwan-Real-Estate-Price-Prediction-App | ML projects | Python | Predicts property prices with a scikit-learn model behind a Gradio app.

## About page (about.html)

- Intro: I am a data scientist based in Penang, Malaysia. I like questions that matter locally and answers that hold up when someone else reruns them.
- "What I work on": spatial analysis of public services; forecasting; evaluating language models on Malaysian languages; small tools and agents that make data work faster.
- "How I work": every result ships with its sources, code, model versions and limits; I prefer a strong baseline before a complex model; I report uncertainty, not just a single number.
- "Toolkit": Python, pandas, scikit-learn, PyTorch, MLflow, GeoPandas, TypeScript, Next.js, Go, Swift. Present plainly, no skill bars or percentages.
- Contact block with `id="contact"`: "I am open to data science and ML engineering roles, and to collaborations on Malaysian open data." plus the three contact buttons.
- Do not invent employers, degrees, dates or testimonials.
