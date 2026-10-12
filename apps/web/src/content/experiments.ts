import type { ExperimentCategory, ExperimentRecord } from "./types";

// `inline` is the lower-case form used after the language, for example "Python, libraries".
export const EXPERIMENT_CATEGORIES: ReadonlyArray<{ id: ExperimentCategory; label: string; inline: string }> = [
  { id: "agents", label: "Agents and MCP", inline: "agents and MCP" },
  { id: "libraries", label: "Libraries", inline: "libraries" },
  { id: "apps", label: "Apps", inline: "apps" },
  { id: "ml", label: "ML projects", inline: "ML projects" },
];

export const experimentUrl = (name: string): string => `https://github.com/SubaashNair/${name}`;

export const experiments: readonly ExperimentRecord[] = [
  { name: "penang-ai-assistant", private: true, category: "agents", language: "Python and Next.js", tile: 17, description: "Answers plain-language questions about Malaysian economic data from OpenDOSM, with Penang as the default, using governed read-only SQL and an audit trail." },
  { name: "documentation-mcp-server", category: "agents", language: "JavaScript", tile: 5, description: "An MCP server that gives coding agents up-to-date documentation for popular libraries." },
  { name: "matomari", private: true, category: "agents", language: "macOS", tile: 6, description: "A native file explorer with an agent inside, and an importance score for every file built from how you actually use it." },
  { name: "exam-monitor-app", category: "apps", language: "Go", tile: 7, description: "Real-time classroom exam monitoring: teachers see live student screens over LAN, with session tokens, lock-all, messaging and CSV audit export." },
  { name: "CU5_project_dashboard", private: true, category: "apps", language: "Python", tile: 8, description: "Monitors student repositories with GitHub activity, file evidence and requirement-based completion estimates." },
  { name: "ml-review", category: "libraries", language: "Python", tile: 9, description: "Extended evaluation metrics for scikit-learn models." },
  { name: "OutlierCleaner", category: "libraries", language: "Python", tile: 10, description: "Detects and removes outliers using several statistical methods." },
  { name: "StatClean", category: "libraries", language: "Python", tile: 11, description: "Statistical data cleaning and outlier handling." },
  { name: "OptimRL", category: "libraries", language: "Python", tile: 12, description: "Reinforcement learning optimisation experiments." },
  { name: "GRPOptim", category: "libraries", language: "Python", tile: 13, description: "GRPO training experiments." },
  { name: "pima-diabetes-mlflow", category: "ml", language: "Python", tile: 14, description: "Train, register, serve and ship a classifier end to end with MLflow, Docker and Streamlit." },
  { name: "Land-subsidence-Prediction", private: true, category: "ml", language: "Python", tile: 15, description: "Forecasts land subsidence in the Klang Valley from geospatial and temporal data." },
  { name: "Taiwan-Real-Estate-Price-Prediction-App", category: "ml", language: "Python", tile: 16, description: "Predicts property prices with a scikit-learn model behind a Gradio app." },
];

// An experiment without a description is not listed anywhere.
export const listedExperiments: readonly ExperimentRecord[] = experiments.filter((e) => e.description.trim().length > 0);
