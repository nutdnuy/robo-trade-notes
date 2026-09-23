# Chapter-opening quote image — 2026-09-23

- Explicit user request: generate an image with a quote and insert it in the
  open Webull chapter. Placement: after the introduction, before `before-start`.
- QuantCorner/QuantSeras light palette; generated editorial illustration only.
  Existing brokerage screenshots, lesson content and numerical examples remain
  source-faithful. The website layout stays native Markdown/React.
- Built-in Image Generator produced the entire image and its two Thai lines;
  visual inspection confirmed the requested words and no invented attribution.
- Original: 1672 × 941 PNG; website export: same pixels, WebP, 111,576 bytes.
  Only encoding changed; no image crop, text overlay or reconstruction.
- `npm run build:pages` passed; local export contains the same image bytes.
- Browser checks: image loaded at 848px in the desktop article; at the narrow
  viewport it fit the article column without horizontal page overflow. Exact
  quote included in alt text; width/height attributes reserve the image space.
- `git diff --check` passed. Notebook and math are unchanged.
