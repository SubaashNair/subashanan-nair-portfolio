# Subashanan Nair, portfolio

The portfolio site of Subashanan Nair, a data scientist in Penang. It presents reproducible ML and LLM case studies on public data, plus smaller tools and experiments, each with sources, code and limits.

The site is a Next.js App Router app in `apps/web`, designed around Peranakan floor tiles from George Town.

## Run it

```bash
npm install
npm run dev     # local development server
npm test        # unit and component tests
npm run build   # production build
```

`npm run lint` and `npm run typecheck` are also available from the repo root.

## Honesty rule

Illustrative data appears only in development, never in production: a production build shows a study's planned state until real results are published.

## Design documents

- [Design specification](docs/superpowers/specs/2026-10-12-peranakan-redesign-design.md)
- [Content specification](docs/superpowers/specs/2026-10-12-peranakan-redesign-content.md)
- [Implementation plan](docs/superpowers/plans/2026-10-12-peranakan-redesign.md)
