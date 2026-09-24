# Why Robo Trade — source and verification notes

Checked on 2026-09-24. Canonical chapter: `content/chapters/12-why-robo-trade.md`.
This is an original Thai chapter, not a transcript or a summary of inaccessible course videos.

## Supplied source files read for the expanded chapter

- `Introduction to Quantitative Trading.pdf` (25 pages), Google Cloud / New York Institute of Finance: pp. 4–9 trading/investing, pp. 11–13 Quant Universe, pp. 15–22 strategies, pp. 24–25 advantages/risks.
- `Sec02.Alpha_Models.pdf` (13 pages), Hudson & Thames, F. Xavier Miguel G.: pp. 3–9 alpha and idea families, pp. 10–11 strategy specifications, p. 12 blending. Its reference to Rishi Narang is attributed to these slides, not a claim to have read the entire book.
- `subtitle.txt`: Trading vs Investing.
- `subtitles-en.vtt`: The Quant Universe.
- `subtitles-en (1).vtt`: Quant Strategies.
- `subtitles-en (2).vtt`: Quant Trading Advantages and Disadvantages.

The supplied PDFs and transcripts were read locally; their raw files are not included in the repository or downloads. Explanations, fictional examples and diagrams were written anew. The four owner-supplied course URLs remain in the chapter. Earlier unauthenticated course-page attempts did not expose the videos; the expanded account uses the supplied files rather than inferred video content. Udemy lecture IDs are retained without inventing their exact titles.

## Public primary sources checked

- [FINRA: What Is Market Timing?](https://www.finra.org/investors/insights/market-timing): market timing as an active investment strategy; no universal holding-day threshold used in the chapter.
- [SEC: Report to Congress on Algorithmic Trading, 2020](https://www.sec.gov/files/Algo_Trading_Report_2020.pdf): algorithmic order management/execution and HFT as a subset. No claims that retail bots inherit market-level benefits.
- Historical source, removed from the final lesson at Nuth’s request: [FINRA Regulatory Notice 15-09](https://www.finra.org/rules-guidance/notices/15-09). The final pre-event decision section uses an original explanation without this citation.
- [Bailey et al., The Probability of Backtest Overfitting](https://www.davidhbailey.com/dhbpapers/backtest-prob.pdf): selection/overfitting risk. No claim that a single holdout test guarantees future performance.
- [CFA Institute: Machine Learning](https://www.cfainstitute.org/insights/professional-learning/refresher-readings/2026/machine-learning): public introduction to data-driven models and overfitting.
- [Citadel: Global Quantitative Strategies](https://www.citadel.com/what-we-do/global-quantitative-strategies/): research, alpha design, portfolio construction and execution as one firm's workflow. Not treated as a universal organization chart.

## Original teaching material

- Brass-purchase rules and all prices, costs and capacities are hypothetical. No market data, API calls or brokerage orders.
- Purchase proposal: finite price in (0,100], finite age in [0,60], integer holdings in [0,10]. Invalid or stale input halts. Eligible proposal fills remaining capacity to 10; it does not model execution.
- Cost example uses reference entry 100 and exit 101, quantity 10, commission 0.10 per unit per side, adverse slippage 0.05 per unit per side: gross 10, costs 3, net 7. Changing slippage to 0.15 gives net 5. The editable cost cell allows that exercise.
- Eight notebook code cells were executed in a fresh Python namespace and saved stdout was compared. The standalone script and modified-cost exercise were executed separately.
- Seven original quiz questions use the existing React Bits Stepper. Existing chapter 1 technical prose, quiz and code were not rewritten.
- Earlier diagram iteration (superseded by the revision below): two diagrams were stored as `public/images/why-robo-system-flow.svg` and `why-robo-research-flow.svg`, with matching editable `.excalidraw` files. SVG embeds the project's Noto Sans Thai font under SIL OFL 1.1. Both were rendered and visually checked. The website has no dependency on Drawdy.
- Initial compositions were authored through Drawdy MCP; `references/why-robo-drawdy.json` records those definitions. Website SVG and Excalidraw are local renderings, not native Drawdy exports. The board's renderer did not honor all supplied styling, so the final local assets and downloadable editable scenes are the presentation source of truth.
- The hypothetical one-period return example uses portfolio 12%, market 10%, risk-free 2%, assumed beta 1.5: baseline 14%, difference −2 percentage points. This is not estimated regression alpha; the text distinguishes alpha plus error from a fitted residual. Beta 1 gives baseline 10% and difference +2 points.
- Same-horizon hypothetical forecasts +0.6% and −0.2% blend to +0.2% at equal weights, and +0.4% at 75/25. These are forecasts before costs, not realized returns or orders.
- Cover reuses Nuth's existing `deltaris-masters.png`. Blue-gem communication and workshop dialogue are explicitly fictional Quantara lore.

## Editorial review

Applied canonical no-ai-slop skill and evaluation. Preserved Nuth's requested final reason and the Quantara jokes. Removed the technical anthropomorphism in “คนยังเลือกสิ่งที่ระบบเชื่อ”, using “คนยังเลือกข้อมูลและสมมติฐาน”. Original examples and opinions were requested by Nuth; no personal experience, performance statistics or source quotes were invented.

## Additional primary references used in the expansion

- CFA Institute, Portfolio Risk and Return: beta, CAPM and performance evaluation. https://www.cfainstitute.org/insights/professional-learning/refresher-readings/2026/portfolio-risk-return-part-2
- SEC Release 70694, pp. 2–4: Knight Capital, 1 August 2012, approximately 45 minutes and losses exceeding $460 million. https://www.sec.gov/litigation/admin/2013/34-70694.pdf
- statsmodels coint documentation: I(1) assumption, null of no cointegration. https://www.statsmodels.org/stable/generated/statsmodels.tsa.stattools.coint.html
- AQR, Time Series Momentum and Quality Minus Junk: definitions and research context, not promises of future performance.
- Diebold and Lopez, Forecast Evaluation and Combination, NBER Technical Working Paper 192: evaluation and combining forecasts. https://www.nber.org/papers/t0192

Historical market-share claims in the course materials are not presented as current figures. High correlation is not equated with cointegration. Optimality is conditional on the specified objective and assumptions; market neutrality does not remove all risk; blending does not guarantee improvement.

## Local verification

- `npm test`: 25 tests passed.
- `npm run build:pages`: 13 source pages checked, 44 questions and 62 math expressions validated, standalone export generated. Only Welcome and the two completed lessons are publicly enabled.
- Eight notebook code cells executed in a fresh namespace; standalone `lesson_12.py` executed successfully.
- Canonical no-ai-slop review retained the requested system-thinking conclusion and explicitly fictional Quantara humor, while removing redundant source-process commentary.

- Desktop 1440px and mobile 390px browser checks: all ten sections available; both SVGs load; no document horizontal overflow; mobile Contents opens and closes on selection. Seven quiz answers submitted through the UI and result confirmed 7/7; no browser console errors observed.


## Illustrated revision, 24 September 2026

- Replaced the two large boxed diagrams and their “วงจร…” footer lines with open book-style layouts. Added Quant universe and Alpha taxonomy diagrams. Each has separate desktop/mobile SVG compositions and matching editable Excalidraw scenes. Original local vector work; no source-slide screenshot is used. The earlier Drawdy definitions remain historical provenance only.
- Added an original Alpha/Beta chart generated from 60 synthetic periods, start value100 and Rf0. Left model alpha0.002/beta1; right alpha0/beta1.3. Residuals are orthogonalized by construction, so recovering these parameters by OLS is a numerical check, not evidence about an actual strategy. CSV: `public/data/why-robo-alpha-beta.csv`; generator: `scripts/generate_alpha_beta.py`; full specification: `references/why-robo-alpha-beta.spec.json`.
- Three original Quantara interludes continue the craftsman/golem/tower story between lesson sections. Their recurring pastry joke, communications gem and city events are fictional. Image generation prompts and output hashes: `references/quantara-stories-generation.json`.
- Mobile uses separate diagram compositions instead of a horizontally scrolled desktop diagram. Story artwork loads lazily with intrinsic dimensions. No Webull prose, existing quiz questions or example code was rewritten for this revision.
- Canonical no-ai-slop editorial review applied to the new prose. The requested system-thinking conclusion is preserved verbatim.
- This revision was first reviewed in local preview. Nuth subsequently requested publication after the final wording changes.

### Verification of the illustrated revision

- `npm run build:pages` and all25 existing tests passed; `git diff --check` clean.18 new/replaced image/data links, including responsive sources, exist in both public and standalone export.
- All8 editable flow scenes validated; all flow and chart compositions visually reviewed. Numeric CSV/OLS checks passed for the synthetic chart.
- Browser: desktop composition checked; actual390CSS-pixel mobile view checked at100% zoom. All3 story images and all5 mobile diagram/chart sources loaded; no horizontal document overflow. Contents opens and closes on choosing a section. No browser console errors or warnings observed.
- Chapter1 source, quiz and code were unchanged. This revision does not alter the7 existing chapter2 quiz questions.

## Final owner wording changes before publication

- The Why Robo Trade opening combines the owner’s supplied draft with direct explanations of explicit rules, testing and reduced emotional decisions. It contains no Quantara lore.
- The pre-event decision section is headed “บังคับให้ตัดสินใจก่อนเหตุการณ์เกิดขึ้น”; its FINRA Regulatory Notice paragraph and unused citation were removed.
- “ผู้จัดการเงินลงทุน” was changed to “ผู้จัดการกองทุน”.
- The three separate illustrated Quantara story interludes remain as requested.

## 24 September 2026 — shortened ending

At Nuth's request, the chapter now stops after the model-blending section and ends with an original Thai summary. The previous Advantages and Disadvantages section and everything after it (including the third illustrated story, exercise, quiz display and closing reference list) were removed from the page. Inline citations and this source record preserve provenance. Existing illustrations, quiz source and runnable supplementary files remain unchanged. The chapter's navigation now points to the summary.
