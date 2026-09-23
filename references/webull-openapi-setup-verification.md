# Webull OpenAPI illustrated chapter — verification

Date: 2026-09-23. Scope: one new, separate page `chapter-11.html` in Robo Trade
Notes, with a Welcome link and sidebar entry. Chapters 01–10 remain withdrawn.

## Source handling

- Ten cropped excerpts from four original Facebook post images, attributed to
  Nonthawat Laonan / Webull API Builders Club (2026-07-03).
- Image links, exact crop bounds and hashes: `webull-openapi-setup-images.json`.
- Original redactions retained; the credential example panel was excluded.
- Webull Thailand application, SDK, authentication, token and market-data
  documentation checked on 2026-09-23. The chapter links the exact sources.
- Web UI and chart route: existing QuantCorner reading design; no image generation.

## Executed checks

- `npm test`: 25 tests passed, including active-chapter/withdrawn-chapter export.
- `npm run build:pages`: content, math, internal chapter links, downloads and
  standalone asset checks passed. Two active pages and ten empty archive pages.
- `lesson_11.py`: all five offline examples and assertions passed.
- `robo-trade-11.ipynb`: five cells executed in a fresh Jupyter kernel on Python
  3.9.6; saved outputs validated. Uses only standard-library, synthetic examples.
- Both Python code blocks in the chapter parsed with `ast.parse`.
- All ten crop hashes/dimensions match the provenance manifest.
- All thirteen chapter image/download URLs returned HTTP 200 and exact local bytes.
- Chrome: Welcome-to-chapter navigation, desktop layout and section anchors;
  391 CSS-pixel mobile layout without page overflow, fixed menu opening and
  closing after section navigation; keyboard quiz submission, all four answers,
  score 4/4 and reset; no console errors observed.
- Export inspected: chapters 01–10 have empty bodies, their notebooks and the
  archived complete-materials ZIP are absent from `_site`.
- `git diff --check` passed.

## Limits

The live SDK example was checked against official documentation and parsed,
but was not run with Webull credentials. No account was accessed and no order
was sent. The offline notebook does not verify brokerage integration.
