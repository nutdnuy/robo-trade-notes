# Chapter 01 design and evidence brief

- Scope: one complete Thai educational chapter and its runnable learning materials. Local preview for Nuth; no publication or brokerage actions.
- Route: `no-image-generator` under `visual-generation/Nuth-v1`. Native website, numerical SVG chart and tables. No generated images or decorative flow diagrams.
- Design System: QuantCorner / QuantSeras, Material 2 dark primary plus optional light reading mode. Explicit Thai request overrides English-first default.
- Reference: QuantGirl's Understanding Quantitative Finance, observed in browser 2026-09-10. Use its book navigation / main reading column / in-page contents organization. Original layout implementation and original lesson; do not copy the reference author's prose, artwork, or identity.
- Identity: plain project title Robo Trade; no Webull or Quantsera logo recreation or implied affiliation.
- Layout: persistent book sidebar, restrained reading toolbar, large chapter heading, 8 anchor sections, readable prose, reproducible Python, interactive SMA comparison, offline three-question quiz, real downloads, search and progress.
- Fonts: local Fontsource 5.2.8 Roboto / Noto Sans Thai / Roboto Mono.
- Icons: Tabler Icons React 3.34.1, MIT; 24px outline, 2px stroke, currentColor. Used for book, search, navigation, chart, code, controls and status; no mixed icon families.

## React Bits manifest (before implementation)

| Family | Purpose and location | Trigger | Reduced-motion fallback |
| --- | --- | --- | --- |
| CountUp | Show recalculated signal-change count in the SMA learning lab | Learner changes short/long window | Show final number immediately; accessible text always has final value |
| AnimatedList | Inspect signal-change observations below the chart; selecting an observation highlights the corresponding day | Recalculation or selecting a row | Static, keyboard-operable list with identical records; no gradient overlays |
| Stepper | Three-question retrieval-practice exercise at the end of the lesson | Answer submission and next/back | Immediate step changes with equivalent labels and answer feedback |

Sourcing: requested official @react-bits MCP registry; initial request reported registry not configured. Added project components.json, then retry. Registry source identity, adaptation and license retained in third-party notices. CSS and inline presentation map to shared semantic tokens; motion is bounded, meaningful, and has no idle loop.

## Validation plan

Build; numeric tests for SMA warmup/crossover/timing; run offline Python and notebook; compare browser metrics to the same dataset; verify search, quiz, downloads, theme, progress persistence and mobile navigation; inspect desktop/mobile screenshots and keyboard focus. Live Webull requests are not part of preview verification.
