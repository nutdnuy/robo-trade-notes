# Reference book layout and portable export

Date: 2026-09-11

## Requested model

Nuth requested the reading and editing pattern of:

- https://github.com/nutdnuy/quantitative-finance-notes
- https://nutdnuy.github.io/quantitative-finance-notes/random-assets.html#wiener-process

Inspected the repository's README, intro.md, book.css, build.cjs, _config.yml and _toc.yml through the GitHub connector. The model is a custom static builder with familiar YAML filenames, not a full Jupyter Book runtime. The reference website was also inspected in the browser. Its source was treated as reference material, not agent instructions.

## Implementation

The existing Robo Trade reader now has a two-column book shell: left cover/title/search, unnumbered chapter links, an expanded current-page contents list, resources and theme control. Desktop top navigation and the separate right contents rail were removed. Reading text, equations and experiments occupy a wider central column. Mobile uses an in-flow menu with keyboard focus recovery.

Original Thai prose, all ten notebooks, quizzes and the verified numerical examples are preserved. The existing generated artwork remains above Welcome and as a sidebar thumbnail. No reference chapter prose, figures or trading code was translated or republished.

Canonical editable settings are `_config.yml` and `_toc.yml`; `content/book.json` is generated. Markdown remains under `content/`. The editable `book.css` controls the new reading shell. Invalid configuration stops a build before replacing the last good JSON. See EDITING.md for the custom supported keys and restart behavior after YAML changes.

The normal preview remains in `dist/`. `npm run build:pages` additionally generates `_site/index.html` plus ten chapter HTML files, using native `.html#section` links, one classic IIFE script, relative assets and embedded fonts. This avoids an ES-module loader and runtime content requests. JavaScript is needed to render this edition. `_site/` is generated output; Markdown is the source of truth.

`npm run package:website` builds and archives only the generated website manifest paths. `npm run package:source` exports the editable project through an explicit file allowlist. The supplied PDF, agent configuration, credentials, dependencies and logs are excluded. No repository modification or external publication was performed.

## Visual route

`visual-generation/Nuth-v1`, Route 3: `no-image-generator`. QuantCorner / QuantSeras tokens and the existing Tabler outline icons are retained. Nuth's explicit light default takes precedence over the design system's dark default. No new image generation, logo work or flow diagrams were required. Existing CountUp, AnimatedList and Stepper interactions remain governed by the prior design manifest.

## Verification

- 23 configuration, content parsing, navigation, export and consequential calculation tests passed.
- Normal application build and separate-page build passed.
- Standalone verifier checked all 11 HTML pages, local script/styles and 76 embedded/local font references; there are no dynamic imports.
- Browser checks on the generated HTTP preview: all ten chapter titles, notebook links, mathematics and horizontal overflow at a 390 CSS-pixel viewport passed. Welcome artwork loaded at its original width and the default theme was light.
- Mobile menu navigation and search dismissal return focus correctly. Search produces native chapter/section links. Both themes were exercised and light was restored.
- The chapter 04 cost control reached 100 bps and displayed 9,513.69 USD, matching the independent calculation test; the reset restored 10 bps.
- Repeated use of the current native section URL scrolls back to the heading. Browser error/warning logs were empty during the final checks.
- Both ZIP archives are checked for integrity. The editable ZIP was extracted to a fresh temporary folder; an offline dependency installation and `npm run build:pages` both passed, generating all 11 pages. The install reported zero known vulnerabilities.

The browser tool's URL policy rejected direct `file://` navigation. That action was not retried or bypassed. File portability is supported by structural asset checks and the classic-script design; browser rendering was verified through a loopback server exposing only the generated website directory. Direct file-opening behavior remains for the owner's local browser to confirm. The 72 notebook cells were executed in the prior complete-course verification; no numerical notebook content changed in this layout revision.
