import type { StudyRecord, StudySlug } from "./types";

export const studies: readonly StudyRecord[] = [
  {
    slug: "penang-pulse",
    title: "Penang Pulse",
    question: "How evenly are clinics, schools and transit stops spread across Penang?",
    status: "in-progress",
    plannedAnswer:
      "This study will measure how far residents in each of Penang's districts live from the nearest public clinic, school and transit stop, and show where the gaps are widest.",
    figurePlan:
      "a map of public clinics, schools and transit stops, and one tile per district showing the share of residents under 1 km, 1 to 3 km and over 3 km from the nearest clinic.",
    data: "PeGIS facility layers, DOSM Census 2020, OpenStreetMap roads.",
    tile: { motif: "diamond", a: "mustard", b: "jade", ground: "warm" },
    tint: "warm",
    themeClass: "s-pulse",
    sources: [
      { name: "PeGIS", publisher: "Penang state GIS portal", used: "Facility layers for clinics, schools and transit stops", licence: "CC BY 4.0" },
      { name: "Census 2020", publisher: "DOSM", used: "Population by mukim", licence: "Open government licence" },
      { name: "OpenStreetMap", publisher: "OpenStreetMap contributors", used: "Road network for travel distances", licence: "ODbL" },
    ],
    method: [
      "Collect facility points for clinics, schools and transit stops from PeGIS.",
      "Join each mukim to its 2020 census population.",
      "Compute road network distance from each population-weighted mukim centroid to the nearest facility.",
      "Band distances into under 1 km, 1 to 3 km and over 3 km, and sum residents per band.",
      "Bootstrap mukims to get intervals for each district share.",
    ],
    limitations: [
      "Centroids hide within-mukim variation, so some residents are closer or further than their band says.",
      "Private clinics are excluded, which overstates the distance to any clinic.",
      "OpenStreetMap road coverage is thinner in rural Seberang Perai.",
      "Population figures come from the 2020 census.",
    ],
    reproduce: { commands: ["uv sync", "uv run python -m analysis.penang.build --from-cache", "npm run dev"] },
    discussNote: "Spotted a missing clinic or a better boundary file? Questions and corrections are welcome.",
  },
  {
    slug: "forecasting-lab",
    title: "Forecasting Lab",
    question: "Can a pre-trained time-series model beat a tuned baseline on traffic sensors?",
    status: "published",
    plannedAnswer:
      "This study tests whether Chronos, a pre-trained time-series model used without tuning, can beat persistence, a daily seasonal baseline, a tuned gradient boosting model and a spatial neural net on traffic forecasts up to two hours ahead.",
    figurePlan:
      "forecasts for the next two hours on three sensors, each at the test window where its flow changed most, and each model's error by horizon from 15 minutes to 2 hours.",
    data: "UCI dataset 608, Chronos weights from Hugging Face.",
    tile: { motif: "petals", a: "cobalt", b: "mustard", ground: "sky" },
    tint: "sky",
    themeClass: "s-forecast",
    sources: [
      { name: "Dataset 608", publisher: "UCI Machine Learning Repository", used: "Traffic flow every 15 minutes at 36 highway sensors", licence: "CC BY 4.0" },
      { name: "chronos-t5-small", publisher: "Amazon, via Hugging Face", used: "Pre-trained model weights, used without tuning", licence: "Apache 2.0" },
    ],
    method: [
      "Split the 13 weekdays of readings in time order: 9 days to train, the next 2 to tune and the last 2 to test, with scaling fitted on training data only.",
      "Build features from each sensor's last 10 readings, the time of day, the weekday and the mean flow at its neighbouring sensors.",
      "Compare two baselines, the latest reading and the reading at the same time on the previous day, with gradient boosting and a spatial MLP, each tuned on the validation days only.",
      "Run Chronos zero-shot on each sensor's last 512 readings (about five days) up to the forecast time, with no tuning.",
      "Score every model on the test days at 15, 30, 60, 90 and 120 minutes, with 95% intervals from a block bootstrap. The charts show a quiet, a typical and a busy sensor, each at the test window where its flow changed most.",
    ],
    limitations: [
      "One dataset from two US highways near Washington DC.",
      "Only 13 weekdays of data, and the published series leaves out weekends. Chronos sees only the last 512 readings, about five days, at each forecast.",
      "The test window is about two days, so the intervals describe only these two days.",
      "No weather or holiday features.",
      "MAE hides rare congestion spikes, which matter most to drivers.",
      "Clock times are the dataset's own and may not match local time.",
    ],
    reproduce: {
      commands: ["cd analysis", "uv sync --group chronos", "uv run --group chronos python -m forecasting.cli --seed 42", "cd .. && npm run dev"],
      note: "The first run downloads the dataset and the Chronos weights. The tests need neither: uv run pytest.",
    },
    discussNote: "Have a model you think should be on this chart? Suggestions and corrections are welcome.",
  },
  {
    slug: "llm-eval-lab",
    title: "LLM Eval Lab",
    question: "How well do small and frontier models handle Bahasa Malaysia and Manglish?",
    status: "planned",
    plannedAnswer:
      "This study will compare a classical baseline, a fine-tuned 1B model, an open 8B model and a frontier model on Manglish sentiment, Bahasa Malaysia entity extraction and Bahasa Malaysia summaries, reporting accuracy with intervals, cost and latency.",
    figurePlan: "a leaderboard per task with 95% intervals, cost per 1,000 items and latency, a cost against score chart, and examples of where models go wrong.",
    data: "Hand-labelled Manglish and BM sets, Malaysian news headlines.",
    tile: { motif: "flower", a: "rose", b: "cobalt", ground: "porcelain" },
    tint: "roseTint",
    themeClass: "s-llm",
    sources: [
      { name: "Manglish and BM sets", publisher: "This project", used: "Hand-labelled items for sentiment and entities", licence: "CC BY 4.0" },
      { name: "Malaysian news headlines", publisher: "Public news sites", used: "Articles for the summary task", licence: "Public, research use" },
      { name: "Models", publisher: "Model APIs and open weights", used: "Every model, listed with its version", licence: "Per provider" },
    ],
    method: [
      "Write and freeze the labelling guidelines.",
      "Label 1,200 items per task, with a second annotator on 20%.",
      "Version prompts (v1 to v3) in the repo.",
      "Run each model 3 times at temperature 0, recording cost and latency per call.",
      "Bootstrap 95% intervals for every score.",
    ],
    limitations: [
      "Manglish varies by region and age; one set cannot cover it.",
      "Inter-annotator agreement will not be perfect.",
      "Frontier model versions change, so results are dated.",
      "Costs use list prices on the run date.",
    ],
    reproduce: {
      commands: ["uv sync", "uv run python -m analysis.llm_eval.run --task all --prompts v3", "npm run dev"],
      note: "Hosted models need API keys; open models run locally.",
    },
    discussNote: "Speak Manglish and disagree with a label? That is exactly the feedback this needs.",
  },
  {
    slug: "penang-ai-assistant",
    title: "Penang AI Assistant",
    question: "Can a language model answer questions about Penang's economy safely, using only official statistics?",
    status: "in-progress",
    plannedAnswer:
      "This assistant answers plain-language questions about Penang's economy from official OpenDOSM statistics only. Each question becomes read-only SQL against approved views, is checked against a policy and is recorded in an audit log, so every answer can be traced to its source.",
    figurePlan:
      "an evaluation of answer accuracy against hand-checked questions, and how often the assistant correctly refuses questions the data cannot answer.",
    data: "OpenDOSM CPI, inflation and unemployment data, Ollama Cloud (gpt-oss:120b).",
    tile: { motif: "star", a: "jade", b: "rose", ground: "jadeTint" },
    tint: "jadeTint",
    themeClass: "s-assist",
    sources: [
      { name: "OpenDOSM", publisher: "Department of Statistics Malaysia", used: "CPI, CPI inflation and quarterly unemployment by state", licence: "CC BY 4.0" },
      { name: "Ollama Cloud", publisher: "Ollama", used: "gpt-oss:120b to plan each answer and its SQL", licence: "Provider terms" },
    ],
    method: [
      "Fetch CPI, CPI inflation and quarterly unemployment from the OpenDOSM API.",
      "Validate each file against a column contract, quarantining bad rows with their reasons.",
      "Load accepted data as a new snapshot, keeping the last good snapshot if a refresh fails.",
      "Have the model turn each question into SQL, then check it against a policy and run it read-only on approved views.",
      "Record every question, query and result in an insert-only audit log.",
    ],
    limitations: [
      "A personal prototype, not an official service.",
      "Covers only CPI, inflation and unemployment so far.",
      "Answers depend on a single model provider; a second provider is planned.",
      "Answer accuracy has not been evaluated yet; that is the next milestone.",
    ],
    reproduce: {
      commands: ["uv sync", "docker compose up -d --wait", "uv run python -m ingestion.cli refresh", "uv run uvicorn api.main:app --port 8010"],
      note: "The code repository is private for now.",
    },
    discussNote: "Have a question you think it should answer, or one it should refuse? Suggestions are welcome.",
  },
];

export function findStudy(slug: string): StudyRecord | undefined {
  return studies.find((s) => s.slug === slug);
}

/** Previous and next studies, wrapping around so no slot is empty. */
export function neighbours(slug: StudySlug): { prev: StudyRecord; next: StudyRecord } {
  const i = studies.findIndex((s) => s.slug === slug);
  return { prev: studies[(i - 1 + studies.length) % studies.length], next: studies[(i + 1) % studies.length] };
}
