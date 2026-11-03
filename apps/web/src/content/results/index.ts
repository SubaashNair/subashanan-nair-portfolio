import type { StudyResultsBySlug } from "../types";
import forecastingLab from "./forecasting-lab.json";
import llmEvalLab from "./llm-eval-lab.json";
import penangPulse from "./penang-pulse.json";
import penangAiAssistant from "./penang-ai-assistant.json";
import { parseForecastResults } from "./parse-forecast";
import { parseLlmEvalResults } from "./parse-llm-eval";
import { parsePenangResults } from "./parse-penang";
import { parseAssistantResults } from "./parse-assistant";

// Real results written by the analysis pipelines in analysis/. Each file is validated on import,
// so a malformed file fails the build instead of reaching a page.
export const published: Partial<StudyResultsBySlug> = {
  "forecasting-lab": parseForecastResults(forecastingLab),
  "llm-eval-lab": parseLlmEvalResults(llmEvalLab),
  "penang-pulse": parsePenangResults(penangPulse),
  "penang-ai-assistant": parseAssistantResults(penangAiAssistant),
};
