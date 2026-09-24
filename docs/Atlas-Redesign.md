# Robo Trade learning atlas redesign

Date: 2026-09-24. The initial atlas review below records v1. Current delivery is the Quantara workshop revision described first.

## Quantara workshop revision

Nuth confirmed that the world is the Kingdom of Quantara and that the people of
Deltaris are Algorithmic Trading Masters who build the machines. Nuth explicitly
authorized a generated illustration, a playful treatment, a matching chapter 11
field manual, and publishing the completed website to GitHub.

The Welcome page now has a coastal workshop cover, the unchanged supplied
maker-and-automaton portrait, a four-state fictional automaton interaction, and
six city selectors connected to existing guide sections. The machine's states
are temporary presentation state. They do not run code or make broker requests.
The Deltaris craft and kingdom name are owner-confirmed; guild notices, workshop
jokes and other small descriptive additions are creative copy.

`src/quantara.css` styles this revision. `src/field-guide.css` scopes the chapter
reading design, and `src/App.jsx` replaces the old introductory quote picture in
the rendered page with a workshop cover. The source Markdown and original image
remain unchanged. All section bodies, quiz data and publishing boundaries remain
canonical.

The new illustration is `public/images/deltaris-workshop-v2.png`; its prompt,
provenance and SHA-256 are recorded in
`references/deltaris-workshop-generation.json` and the adjacent prompt file.
It was generated with the built-in Image Generator using the owner's explicit
exception for this request. Native HTML provides the text and controls. The
supplied portrait is copied unchanged as `public/images/deltaris-masters.png`
and recorded in `references/atlas-assets.json`. The source artwork is retained.

Six destinations: Sigmora → `before-start`, Covaria → `market-data`,
Alphora → `create-key`, Deltaris → `sdk-and-token`, Tailgard → `troubleshooting`,
Arbitra → `first-call`. City selection is a decorative route into the guide,
not a validated curriculum order or a competence assessment.

Current browser checks: all six map controls selected the correct city and
section link with exactly one pressed map control and one matching city button;
the automaton advanced through its messages by click and keyboard Enter, then
reset to OFF DUTY. Welcome at actual CSS widths 320, 384, 768 and 1440px had no
horizontal overflow. Map controls were at least 48px and the closest pins did
not overlap at 320px. Temporary viewport overrides were reset afterward.

The original and generated large illustrations total approximately 13.3 MB.
Below-fold art loads lazily; the workshop cover has high fetch priority. Slow
network performance, a complete accessibility audit and screen-reader behavior
are not claimed as tested. The initial verification record below is historical;
final revision checks are recorded in `docs/State.md`.

## Initial atlas scope (v1)

The Welcome page now presents Robo Trade Notes as a QuantCorner learning atlas, taking visual direction from the public QuantCorner Skill Tree and reusing Nuth's supplied fantasy map and Deltaris card. Four native map buttons and matching topic buttons select a description and a link into the existing OpenAPI guide. Selection is navigation state, not course completion, a skill assessment, or a game mechanic.

The guide uses the shared header and supporting atlas styling. Existing Thai learning material remains canonical. The redesign retains the Welcome account setup content, chapter 11, its screenshots, notebook and Python downloads, quiz, and section links. Chapters 01–10 remain unpublished under the existing publishing allowlist.

## Source and architecture

Base revision: `887b1c4093a9271859e08e8d3befafe9aef212a9` (`887b1c4`), the latest remote `main` inspected when the worktree was created. Review branch: `codex/quantcorner-atlas-redesign`.

Work is isolated in a separate Git worktree of the existing `robo-trade-notes` repository. All source paths below are relative to that worktree. Run `git rev-parse --show-toplevel` for its current location or `git worktree list` to locate the original checkout.

| Source | Responsibility |
| --- | --- |
| `src/components/WelcomeAtlas.jsx` | Welcome composition, topic data, map selection, shared header and skip-to-content behavior |
| `src/atlas.css` | Responsive atlas styling, reading-shell adjustments, focus and reduced-motion states |
| `src/App.jsx` | Existing route handling and chapter rendering, with the atlas Welcome and shared header |
| `src/main.jsx` | Loads the atlas stylesheet after existing reading styles |
| `_config.yml` | Canonical Welcome hero image and alternative text |
| `content/book.json` | Generated configuration; regenerate from YAML rather than editing directly |
| `src/lib/navigation.js` | Existing development hash routes and standalone HTML links; unchanged |
| `src/lib/publishing.js` | Existing allowlist: `welcome` and `chapter-11`; unchanged |
| `content/intro.md`, `content/chapters/11-webull-openapi-setup.md` | Canonical Welcome and guide prose; unchanged |
| `content/quizzes/chapter-11.json`, `src/components/LessonWidgets.jsx` | Existing quiz data and behavior; unchanged |
| `scripts/build_standalone.mjs` | Builds `_site/`, retains archived empty pages, and includes active downloads; unchanged |

The four atlas destinations were checked against actual chapter 11 heading IDs:

| Atlas topic | Section ID |
| --- | --- |
| API access | `create-key` |
| Market data | `market-data` |
| Python & SDK | `sdk-and-token` |
| Your first request | `first-call` |

## Asset provenance and visual route

Route: `no-image-generator`, under `visual-generation/Nuth-v1`, using the selected QuantCorner web and asset modules. No Image Generator call was used for this redesign. Existing artwork and the approved light-surface QuantCorner mark were copied without alteration; the separate green evidence point is preserved.

`references/atlas-assets.json` records portable source paths, destination paths, dimensions, byte counts, source/target SHA-256 hashes, and byte equality verification for:

- `public/images/learning-atlas.png`: 1536 × 1024, 4,102,681 bytes.
- `public/images/deltaris-card.png`: 1024 × 1536, 3,411,068 bytes.
- `public/images/quantcorner-mark-light.svg`: viewBox 0 0 128 128, 589 bytes.

All three source/target pairs were verified byte-for-byte equal. The two original PNGs total approximately 7.5 MB, so initial loading on slow connections remains a performance limitation. No compressed derivatives have been substituted.

## Preview and review

Run from this worktree with Node.js 22.12 or later and Python 3 available:

```sh
npm ci
npm run dev
```

Open the local address Vite prints. The development routes are `#/welcome` and `#/chapter-11`. YAML changes require restarting the development server.

```sh
npm test
npm run build:pages
python3 -m http.server 4178 --bind 127.0.0.1 --directory _site
```

The standalone preview is `http://127.0.0.1:4178/index.html`; the guide is `http://127.0.0.1:4178/chapter-11.html`. The export also supports opening `_site/index.html` from disk. `_site/` is generated output, not an editing source. No lint script is configured in `package.json`.

Review the branch without altering the original checkout:

```sh
git status --short
git diff 887b1c4 --
```

New, untracked files are listed by `git status` and require separate inspection until staged or committed. The original checkout and base commit remain available for comparison. To restore the previous presentation, first preserve the review branch and then use the baseline files at `887b1c4`; no restore or branch reset has been executed.

## Verification record

Verified on 2026-09-24:

- `npm test`: 25 of 25 tests passed; final run log is in `outputs/atlas-qa/tests.log`.
- `npm run build:pages`: succeeded; final run log is in `outputs/atlas-qa/build.log`. The existing Motion dependency emits non-blocking ignored `use client` warnings.
- Independent source review confirmed all four atlas destination anchors exist in chapter 11.
- Independent diff inspection confirmed that canonical Welcome/guide prose, quiz data, publishing allowlist, route helper, lesson widgets and standalone builder remain unchanged from `887b1c4`.
- The skip-link fix now prevents hash navigation and directly focuses and scrolls the main landmark; both page types expose `tabIndex="-1"` on that target. This preserves the current chapter in development preview.
- The shared header now handles Escape while its Contents menu is open and returns focus to the trigger. The layout retains its Escape handler for focus inside the menu.
- Browser DOM checks at actual CSS viewport widths 320, 384, 768 and 1440px found no horizontal page overflow; all eight topic buttons met 48px targets. Narrow lesson navigation was also checked at 320px.
- All four map controls updated their pressed state, matching topic card, detail text and correct chapter link. The first-request link opened the existing heading, settling 62px from the viewport top.
- Keyboard Enter selected a map topic with a visible outline. Skip links focused the main landmark without changing the chapter route, verified in both standalone and Vite builds. Mobile Contents opened and closed with Escape while focus returned to its trigger.
- The existing quiz accepted the correct first answer and enabled the next question. Code-copy feedback showed success. No browser console errors/warnings were observed in the tested standalone page.
- Main text, muted text, primary action and detail-panel text contrast ratios were 11.51, 5.26, 7.63 and 4.80 respectively. This is a targeted check, not a complete accessibility audit.
- Reduced-motion CSS explicitly disables smooth scrolling, transitions and hover translation. OS reduced-motion emulation and screen-reader testing were not performed.
- Desktop screenshots were visually inspected. Mobile viewport DOM geometry and screenshots were inspected, but the in-app browser's screenshot scaling produced extra blank capture space under overrides; actual CSS dimensions were recorded separately. The viewport override was reset afterward.
- All three reused assets matched their sources byte-for-byte and matched the recorded SHA-256 hashes. No new image generation occurred.
- `python3 scripts/package_website.py` created `outputs/robo-trade-website.zip`: 35 generated files, 11,660,274 bytes, ZIP CRC verified. Only Welcome and chapter 11 contain the active app; chapters 01–10 retain empty bodies.
- `git diff --check` passed. The generated unrelated complete-course ZIP was restored to its base bytes; no withdrawn content was republished.

At the end of v1 this was a local implementation for review. Publication was subsequently requested for the Quantara revision above.
