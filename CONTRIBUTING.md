# Contributing to AI Observatory

Thanks for your interest in contributing. This repository is a monorepo with two workspaces: a Next.js web application (`apps/web`) and a Python analysis pipeline (`analysis`).

## Getting started

```bash
npm install
npm run dev
```

## Development workflow

1. Create a branch from `main`.
2. Make focused, well-scoped changes.
3. Run the checks locally before opening a pull request:

```bash
npm run lint
npm run typecheck
npm test
npm run build
```

4. Open a pull request. CI runs lint, typecheck, tests, build, and a dependency audit on every push.

## Conventions

- TypeScript with strict mode enabled.
- React function components with hooks; no class components.
- Accessibility is a first-class concern: use semantic landmarks, `aria-*` attributes, and respect `prefers-reduced-motion`.
- Every analytical claim must carry provenance, methodology, uncertainty, and reproducibility metadata.

## Reporting issues

Open an issue with a clear title, steps to reproduce, and expected versus actual behaviour. For security issues, do not open a public issue; contact the maintainer directly.
