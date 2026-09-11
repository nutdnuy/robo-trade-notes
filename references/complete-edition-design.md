# Complete edition: design and evidence manifest

Date: 2026-09-11

## User direction

Continue all Robo Trade chapters, use Nuth's Quantitative Finance Notes as the reading reference, let the owner review the whole course together, and make the default theme light.

Reference pages read: GitHub README.md, _config.yml, _toc.yml; browser inspection of https://nutdnuy.github.io/quantitative-finance-notes/random-assets.html#wiener-process. The reference separates editable Markdown, notebook examples, navigation settings and interactive plots. No reference source code or figures were copied.

## Production route

Website, interface, plots, tables and mathematics: visual-generation/Nuth-v1 Route 3 (`no-image-generator`). QuantCorner/QuantSeras Design System, with the user's explicit light-default preference taking precedence over its dark default. Existing requested hero artwork from the previous Welcome task is preserved; no new image generation in this edition. No flow diagrams were added.

Material 2 light background/surface #FFFFFF, text black87%, muted black60%, primary #6200EE with white text. Dark option preserved. Semantic comparison color #006F65 on white; no color-only status. Fonts bundled from Fontsource5.2.8. The existing Tabler3.34.1 outline icon family is used for controls. New selected icon: IconCheck. No logos imported or generated.

## Reading structure

Welcome +10 lesson routes. Thai prose, native mathematics via remark-math6.0.0 / rehype-katex7.0.1 / KaTeX0.16.22, chapter-local quizzes and notebook downloads, previous/next chapter navigation, local bookmarks and search across the whole book. Markdown downloads are generated from original content at build time. Notebooks are not overwritten by the build.

## React Bits manifest

Existing governed adaptations retained from prior manifest:

- CountUp: chapter01 event count. Chapter04 monetary values update immediately without animation. Final event count exposed immediately to assistive technology; reduced motion renders the final value. Added optional fixed decimal formatting.
- AnimatedList: chapter01 signal event exploration; chapter09 fill audit as events are appended. Added optional native row renderer/accessible list label for non-selectable audit messages; reduced motion disables displacement.
- Stepper: each chapter's question progression with feedback before advancing. No autoplay. Chapter state is isolated by page ID.

## New interactive illustrations

- Chapter04: eight fixed synthetic OHLC observations matching lesson_04.py. Signals SMA2/3, entry open4, exit open7; net and gross values at each open, per-side cost slider, fair same-horizon buy/hold result. Pure JS calculation checked against an independent round-trip cash formula.
- Chapter05: separate four-point synthetic portfolio path, indexed100, peak120; loss/recovery controls. Drawdown uses a running peak and recovery required uses the trough as denominator. This illustration does not reuse the 12-session notebook example.
- Chapter09: accepted mock order for10 shares, fills4@99.90 fee0.40 and6@100 fee0.60. Duplicate fill IDs do not change cash or shares; conflicting payloads reject. Memory-only teaching state explicitly distinguished from durable restart recovery in chapter10.

Source and licensing: references/licenses/, public/THIRD_PARTY_NOTICES.txt. Build, browser and notebook verification recorded under outputs/qa/complete-verification.md after execution.
