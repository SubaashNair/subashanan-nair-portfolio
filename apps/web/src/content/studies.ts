import type { StudyRecord, StudySlug } from "./types";

export const studies: readonly StudyRecord[] = [
  {
    slug: "penang-pulse",
    title: "Penang Pulse",
    question: "How evenly are clinics, schools and transit stops spread across Penang?",
    status: "published",
    plannedAnswer:
      "This study will measure how far residents in each of Penang's districts live from the nearest public clinic, school and transit stop, and show where the gaps are widest.",
    figurePlan:
      "a map of public clinics, schools and transit stops, one tile per district showing the share of residents under 1 km, 1 to 3 km and over 3 km from the nearest clinic, and a table of the share over 3 km from each service.",
    data: "Penang open data, Rapid Penang GTFS, DOSM, WorldPop, OpenStreetMap.",
    tile: { motif: "diamond", a: "mustard", b: "jade", ground: "warm" },
    tint: "warm",
    themeClass: "s-pulse",
    sources: [
      { name: "Public health facilities 2022", publisher: "Penang State Government, via the data.gov.my archive", used: "Public clinics and hospitals, dental clinics excluded", licence: "CC BY" },
      { name: "Schools 2022", publisher: "Penang State Government, via the data.gov.my archive", used: "Every school, private schools included", licence: "CC BY" },
      { name: "Rapid Penang GTFS", publisher: "Prasarana, via data.gov.my", used: "Bus stops inside the five districts", licence: "CC BY 4.0" },
      { name: "Population by district", publisher: "DOSM, via OpenDOSM", used: "2020 population of each district", licence: "CC BY 4.0" },
      { name: "geoBoundaries MYS ADM2", publisher: "geoBoundaries, William & Mary geoLab", used: "District outlines", licence: "CC BY 3.0" },
      { name: "WorldPop 2020 constrained", publisher: "WorldPop, University of Southampton", used: "Where residents live, on a 100 m grid", licence: "CC BY 4.0" },
      { name: "Meta population map 2020", publisher: "Meta Data for Good, via HDX", used: "A 30 m population map, as a check", licence: "CC BY" },
      { name: "OpenStreetMap", publisher: "OpenStreetMap contributors, via Geofabrik", used: "Roads, bridges and town names", licence: "ODbL" },
    ],
    method: [
      "Take every public clinic and hospital except dental clinics, every school and every Rapid Penang stop inside the five districts.",
      "Spread each district's 2020 DOSM population over the populated cells of WorldPop's 100 m grid whose centre lies in the district.",
      "Build a road network from OpenStreetMap with footpaths, ferries and private roads left out, treating every road as two-way.",
      "For each populated cell, add the straight line to its nearest road, the road distance to the nearest facility and that facility's own straight line to the road.",
      "Band residents into under 1 km, 1 to 3 km and over 3 km for each service, and repeat with Meta's 30 m population map as a check.",
    ],
    limitations: [
      "Facility records come from a legacy state portal and vary in date; the key numbers give the range.",
      "Private clinics are not included; private schools are.",
      "Population is modelled on a 100 m grid, not counted.",
      "Road distance is not travel time, and says nothing about how often buses run.",
      "Every road is treated as two-way.",
      "Clinics, schools and stops across the state border in Kedah and Perak are not counted, so shares near the border may be too high.",
    ],
    reproduce: {
      commands: ["cd analysis", "uv sync", "uv run python -m pulse.cli", "cd .. && npm run dev"],
      note: "The first run downloads about 310 MB of source data into analysis/data/raw/pulse. The tests need none of it: uv run pytest.",
    },
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
  {
    slug: "penang-ai-assistant",
    title: "Penang AI Assistant",
    question: "Can a language model answer questions about Penang's economy safely, using only official statistics?",
    status: "published",
    plannedAnswer:
      "This assistant answers plain-language questions about Penang's economy from official OpenDOSM statistics only. Each question becomes read-only SQL against approved views, is checked against a policy and is recorded in an audit log, so every answer can be traced to its source.",
    figurePlan:
      "an evaluation of answer accuracy against hand-checked questions, and how often the assistant correctly refuses questions the data cannot answer.",
    data: "OpenDOSM CPI, inflation and unemployment data, Ollama Cloud (gpt-oss:120b), evaluation report 2026-10-12.",
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
      "Answer accuracy was measured on 45 hand-checked cases run 3 times each under the committed evaluation report 20261012T122949_gpt-oss-120b_plan-v6_all.json, and all six release gates passed. Held-out figures have wide uncertainty because the set is small.",
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
