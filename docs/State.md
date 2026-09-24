# Project state — Quantara workshop

Updated: 2026-09-24.

The Welcome page presents Quantara with a generated Deltaris workshop, the
owner-supplied maker/automaton portrait, an interactive brass companion and six
city selectors. Chapter 11 uses a matching field manual with workshop cover,
numbered navigation and warm reading surfaces. The original introductory quote
picture is omitted from this presentation; its source file and Markdown remain.

Owner-confirmed premise: Quantara is the kingdom; Deltaris residents are
Algorithmic Trading Masters who build the machines. Other workshop jokes are
fictional presentation copy. Nuth explicitly authorized Image Generator for this
revision and requested GitHub publication after verification.

Implementation: `src/components/WelcomeAtlas.jsx`, `src/App.jsx`, `src/main.jsx`,
`src/atlas.css`, `src/quantara.css`, `src/field-guide.css`, `_config.yml` and
generated `content/book.json`. Assets and provenance are in `public/images/`
and `references/atlas-assets.json` / `references/deltaris-workshop-generation.json`.
Canonical lesson text, code samples, quiz, route helper and publishing allowlist
are unchanged. Chapters 01–10 remain withdrawn.

The branch `codex/quantcorner-atlas-redesign` is based on remote main `887b1c4`.
The authorized publishing path is a normal fast-forward push to repository
`nutdnuy/robo-trade-notes` main, followed by its existing GitHub Pages workflow.
The deployment's commit and conclusion must be checked in GitHub Actions; this
pre-publication record does not assert a deployment result.

Browser checks: all six map/city selections and destinations; all four machine
states and reset; keyboard Enter; skip-link focus; mobile Contents open/close
and Escape focus return. Both page types had no horizontal overflow at actual
CSS widths 320, 384, 768 and 1440px. Chapter sidebar links measured at least 48px
high, nine lesson section headings remain, and the old introductory artwork is
absent from the rendered chapter. Desktop composition was visually reviewed.
Temporary viewport overrides were reset. Final checks: `npm test` passed 25/25; `npm run build:pages` succeeded;
`python3 scripts/package_website.py` verified a 37-file website archive
(17,407,183 bytes). The static build retained all nine lesson headings and
passed the first quiz question, enabling the next button. No console warnings
or errors were observed in that tested static page. Independent code review
found no blocking issues. Command logs are in `outputs/quantara-qa/`
(ignored generated evidence).

New copy was reviewed with the no-ai-slop skill. Findings and concrete suggested
fixes are in [Copy review](Copy-Review.md). Canonical educational prose was not
rewritten as part of that review.

Local standalone preview: http://127.0.0.1:4178/index.html.
Portable export: `outputs/robo-trade-website.zip`.
Public URL after a successful deployment:
https://nutdnuy.github.io/robo-trade-notes/index.html.

Known limits: large illustrations total about 13.3 MB; no throttled-network,
full accessibility audit or screen-reader testing. Reduced-motion rules disable
animation and transitions, but OS preference emulation was not run. Build emits
existing non-blocking Motion directive warnings. No game engine or live trading
capability was added.

See [design and historical verification](Atlas-Redesign.md) for the initial
atlas work and the current revision's source relationships.
