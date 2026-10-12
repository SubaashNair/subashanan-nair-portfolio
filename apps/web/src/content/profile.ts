export interface ContactLinks {
  email?: string;
  linkedin?: string;
  cv?: string;
}

// Contact links shown on the About page and the home About band. A missing value (the CV for now) hides its button.
const contact: ContactLinks = {
  email: "subaashnair12@gmail.com",
  linkedin: "https://www.linkedin.com/in/subashanan-nair/",
};

export const profile = {
  name: "Subashanan Nair",
  place: "Penang",
  roleLine:
    "Data scientist in Penang. I build reproducible ML and LLM systems on Malaysian public data, and publish the sources, code and limits behind every result.",
  githubUrl: "https://github.com/SubaashNair",
  sourceUrl: "https://github.com/SubaashNair/subashanan-nair-portfolio",
  discussUrl: "https://github.com/SubaashNair/subashanan-nair-portfolio/discussions",
  siteUrl: "https://subashanan-nair.vercel.app",
  contact,
  intro:
    "I am a data scientist based in Penang, Malaysia. I like questions that matter locally and answers that hold up when someone else reruns them.",
  openTo: "I am open to data science and ML engineering roles, and to collaborations on Malaysian open data.",
  workOn: [
    "Spatial analysis of public services",
    "Forecasting",
    "Evaluating language models on Malaysian languages",
    "Small tools and agents that make data work faster",
  ],
  howIWork: [
    "Every result ships with its sources, code, model versions and limits.",
    "I prefer a strong baseline before a complex model.",
    "I report uncertainty, not just a single number.",
  ],
  toolkit: ["Python", "pandas", "scikit-learn", "PyTorch", "MLflow", "GeoPandas", "TypeScript", "Next.js", "Go", "Swift"],
} as const;
