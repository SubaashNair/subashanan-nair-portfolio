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
      "The 2020 census population is six years old.",
    ],
    reproduce: { commands: ["uv sync", "uv run python -m analysis.penang.build --from-cache", "npm run dev"] },
    discussNote: "Spotted a missing clinic or a better boundary file? Questions and corrections are welcome.",
  },
  {
    slug: "forecasting-lab",
    title: "Forecasting Lab",
    question: "Can a pre-trained time-series model beat a tuned baseline on traffic sensors?",
    status: "in-progress",
    plannedAnswer:
      "This study will test whether Chronos, a pre-trained time-series model used without tuning, can beat a seasonal baseline, a tuned gradient boosting model and a small neural net on traffic forecasts up to two hours ahead.",
    figurePlan: "forecasts for the next two hours on three sensors, and each model's error by horizon from 15 minutes to 2 hours.",
    data: "UCI dataset 608, Chronos weights from Hugging Face.",
    tile: { motif: "petals", a: "cobalt", b: "mustard", ground: "sky" },
    tint: "sky",
    themeClass: "s-forecast",
    sources: [
      { name: "Dataset 608", publisher: "UCI Machine Learning Repository", used: "Traffic sensor network flows", licence: "CC BY 4.0" },
      { name: "chronos-t5-small", publisher: "Amazon, via Hugging Face", used: "Pre-trained model weights", licence: "Apache 2.0" },
    ],
    method: [
      "Split the data into chronological train, validation and test windows with no overlap, and fit scalers on training data only.",
      "Build the seasonal naive baseline from the same weekday last week.",
      "Tune gradient boosting and the GRU on the validation window only.",
      "Run Chronos zero-shot, with no tuning.",
      "Score every model on the same test window at each horizon.",
    ],
    limitations: [
      "One dataset from one city.",
      "Chronos context length caps how much history it sees.",
      "No outside features like weather or holidays.",
      "MAE hides rare congestion spikes, which matter most to drivers.",
    ],
    reproduce: { commands: ["uv sync", "uv run python -m analysis.forecasting.run --seed 42", "npm run dev"] },
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
      "Inter-annotator agreement is not perfect.",
      "Frontier model versions change, so results are dated.",
      "Costs use list prices on the run date.",
    ],
    reproduce: {
      commands: ["uv sync", "uv run python -m analysis.llm_eval.run --task all --prompts v3", "npm run dev"],
      note: "Hosted models need API keys; open models run locally.",
    },
    discussNote: "Speak Manglish and disagree with a label? That is exactly the feedback this needs.",
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
