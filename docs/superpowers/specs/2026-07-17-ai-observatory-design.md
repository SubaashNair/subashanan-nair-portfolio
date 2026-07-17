# AI Observatory Portfolio Design

## Product

AI Observatory is Subaash Nair's public data-science portfolio. It combines a cinematic Three.js observatory with reproducible case studies aimed at practicing data scientists, hiring teams, researchers, and potential collaborators.

The experience is creative but not merely educational. Every analytical claim must connect to visible provenance, methodology, validation, limitations, code, and a discussion path.

## Launch Experience

The landing page presents a Penang-centered data world. Visitors can enter two launch stories:

1. **Penang Pulse** asks how evenly essential services are distributed across Penang. It combines PeGIS point layers for services such as hospitals, health facilities, schools, markets, police, and fire services with district population data and an open road network. Outputs include service density, travel-time accessibility, underserved clusters, and an uncertainty-aware accessibility index. The study remains descriptive and does not claim causality.
2. **Forecasting Lab** uses the UCI Traffic Flow Forecasting dataset (dataset 608) to compare a seasonal-naive baseline, a tree-based model, and a compact spatial/temporal neural model. Visitors inspect forecasts, residuals, time-aware backtests, feature importance, and a visual model graph. Models train offline; the website serves versioned predictions and metrics.

NASA data is a post-launch expansion, visible only as an upcoming observatory signal until a complete third study is published.

## Interaction and Visual Design

- Brand title: **AI Observatory**.
- Visual language: near-black and deep navy space, cyan/teal data signals, violet neural layers, restrained glow, monospace metadata, and editorial sans-serif narrative copy.
- Journey: **Observe → Discover → Dive → Understand**.
- The landing scene uses a persistent React Three Fiber canvas behind semantic HTML content. Selecting a signal transitions to the corresponding study.
- Desktop receives the complete scene. Mobile receives reduced geometry and effects. Reduced-motion mode uses crossfades and static camera compositions. A semantic HTML/chart experience remains complete without WebGL.
- Three.js never hides navigation, citations, methodology, downloads, or contact actions.

## Architecture

The repository contains two independently testable workspaces:

- `apps/web`: Next.js App Router, TypeScript, React Three Fiber, Three.js, MDX case studies, and typed artefact manifests.
- `analysis`: Python data ingestion, validation, spatial analysis, model training, and export jobs.

The Python pipeline exports compact web artefacts and a manifest containing source URLs, retrieval timestamps, checksums, parameters, metrics, licences, and generated versions. Heavy geospatial and model computation never runs in the browser.

The website initially serves versioned files from the repository. A scheduled GitHub Actions workflow checks sources and rebuilds affected artefacts. If an upstream source fails or changes schema, the production site continues serving the last valid snapshot and surfaces its timestamp.

Vercel is the deployment target. GitHub Pages is not the primary target because a static-only export would constrain caching, preview deployments, and future server-side data endpoints.

## Reproducibility and Community

Each case study exposes:

- dataset source, retrieval date, licence, and citation;
- analytical question, assumptions, methodology, uncertainty, and limitations;
- notebook and environment lockfile;
- repository commit associated with published results;
- downloadable derived artefacts that are legally redistributable;
- GitHub Discussion and collaboration links.

No on-site authentication or comments are included in version one.

## Reliability and Acceptance

- Invalid artefact manifests fail validation during CI and never deploy.
- Source fetch failures preserve the last valid artefact and report the failure in workflow logs.
- The landing page remains navigable with JavaScript disabled; case-study content remains readable without WebGL.
- Automated checks cover typed content, manifest parsing, key UI states, responsive rendering, reduced motion, and data-pipeline schema validation.
- Lighthouse targets on a production build: Performance 80+, Accessibility 95+, Best Practices 90+, and SEO 95+ on the landing page.

