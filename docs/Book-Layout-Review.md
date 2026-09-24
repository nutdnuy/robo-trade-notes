# Book layout review — 2026-09-24

Status: Nuth authorized the final comment corrections and GitHub Pages publication on 2026-09-24.

## Scope

Welcome and chapter 11 share `src/components/BookShell.jsx`. The sidebar receives the existing published-page allowlist, reads real navigation titles and chapter numbers, and shows the current page's real section anchors. There are no future chapter placeholders. The original archive policy remains unchanged.

`src/book-shell.css` defines navigation and reading spacing. `src/quantara.css` styles Welcome; `src/field-guide.css` styles chapter 11. The former `src/atlas.css` is no longer imported. Lesson and widget styles still come from `book.css` and `src/styles.css`.

## Changes

- Welcome kicker: KINGDOM OF QUANTARA, with no leading symbol.
- Artwork label: DELTARIS WORKSHOP.
- Removed the steam tagline, six-city selector, switching map pins, and the complete apprentice-assignment block.
- Kept the exact map image, workshop illustration, masters illustration, and Deltaris card. The adjacent detail is permanently Deltaris and retains its original SDK-section link.
- Moved canonical Welcome prose after the opening illustration, before the extended world sections.
- Removed generic decorative slogans under the no-ai-slop review. Retained the specific Quantara lore, CSV joke, and robot dialogue/actions.
- Added the short blue-gem caption below the maker-and-machine illustration, explicitly framed as a Quantara story. It describes no API capability.
- Mobile Contents opens a fixed scrolling navigation panel, focuses the current page, contains keyboard focus, supports Escape, and closes on navigation or return to desktop width.

No canonical Markdown, quiz JSON, Python examples, notebooks, Webull facts, assets, package dependencies, or publishing settings were edited.

## Design and component manifest

QuantCorner / QuantSeras light book presentation; no-image-generator route. Existing authentic assets and locally bundled fonts are retained. Purple denotes links and selection; neutral surfaces support reading.

| Family | Existing source | Use | Trigger / fallback |
| --- | --- | --- | --- |
| React Bits Stepper | `src/components/reactbits/Stepper.jsx`, official Stepper-JS-CSS registry identity in existing notices | Chapter 11 quiz progress and answer sequence | Reader checks an answer and chooses next/back; useReducedMotion removes movement and preserves content/progress |

Stepper source and quiz behavior are unchanged. Removing the old brown page-level overrides restores the existing Material 2 semantic token adapter (`--rb-*`). The existing MIT + Commons Clause notice remains in `public/THIRD_PARTY_NOTICES.txt`. The user explicitly scoped React Bits to meaningful existing interactions; no extra families or decorative effects were added to meet generic component quotas.

## Verification

- Existing Node tests: 25 passed.
- Final `npm run build:pages`: passed; 12 output files include the intentionally blank archived edition and two published pages. Content checks passed for configured links, local assets, quiz structure and executed notebook structure.
- `git diff --check`: passed.
- Canonical content/assets compared against HEAD; no source payload edits.
- Local preview served HTTP 200 at http://127.0.0.1:8765/.
- Browser checks: Welcome/chapter navigation, direct quiz anchor, Deltaris-only detail (zero city buttons), robot wake/reset, quiz answer feedback, next/back, mobile Contents from the quiz, Escape and focus return.
- No horizontal document overflow at observed CSS viewport widths 1920, 1280 and 390 on the checked pages. Chapter images loaded without errors.
- Reduced-motion fallback verified in the unchanged component source and CSS; no browser reduced-motion emulation or automated contrast scan was run.
- Browser screenshots intermittently timed out and rendered cropped captures. DOM/layout and interaction checks succeeded; full screenshot-based visual QA remains limited by the capture tool.

Preview links:
- http://127.0.0.1:8765/#/welcome
- http://127.0.0.1:8765/#/chapter-11

Publication is authorized. Verify the publishing workflow and live website before reporting deployment success.

## Final owner comments

- Display published reading order as Chapter 1 and sidebar number 1; retain the stable chapter-11 route and filenames so downloads and bookmarks keep working.
- Remove the account-opening/API-key block from the Welcome presentation and local contents. Preserve its source Markdown; the old Welcome anchor lands at the opening section.
- Add desktop Hide contents / Show contents controls; mobile keeps its existing Contents drawer.
- Add a short, explicitly fictional blue-gem communication story below the chapter opening, separate from the unchanged technical introduction.

Final verification: 25 tests passed and build:pages passed after all four owner comments. Browser verified Chapter 1, desktop Hide/Show contents, the new fiction block, mobile menu at 390 CSS pixels, and absence of the removed Welcome block without horizontal overflow.
