# Anora Landing

The public marketing site for Anora AI — a front-of-house operations platform for
independent restaurants and cafés. React + TypeScript + Vite, no CSS framework;
styling is hand-written in `src/styles.css`.

## Repository

Live at [github.com/gKumar1610/anora-frontend](https://github.com/gKumar1610/anora-frontend).

## Run locally

```bash
npm install
npm run dev
```

## Build

```bash
npm run build
npm run preview
```

## Structure

- `src/components/` — one component per page section (`Hero`, `Problem`,
  `HowItWorks`, `Modules`, `Differentiation`, `WhoItsFor`, `FinalCta`, `Footer`),
  plus shared pieces (`Logo`, `Brand`, `Reveal`).
- `src/constants.ts` — nav items and the demo-call mailto link, shared across
  the header, hero, and footer.
- `src/hooks.ts` — `useActiveSection`, which highlights the current section in
  the floating nav as you scroll.
- `public/fonts/` — self-hosted Poppins (400/500/600/700 + italic) and
  JetBrains Mono woff2 subsets, loaded via `@font-face` in `src/styles.css`.

## Content

Copy is drawn directly from `../anora-ai-docs` (vision, product spec, customer
segments, glossary, and build status), so a change to product positioning
should update the docs repo first and this page second.
