import type { AssistantResults } from "../types";
import { checks, type Json } from "./parse-checks";

// Checks a results file against the AssistantResults shape (BaseResults) before the site uses it.
const { object, base } = checks("penang-ai-assistant");

export function parseAssistantResults(json: unknown): AssistantResults {
  const root: Json = object(json, "file");
  base(root);
  return root as unknown as AssistantResults;
}