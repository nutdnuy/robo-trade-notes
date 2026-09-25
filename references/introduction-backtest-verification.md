# Introduction of Backtest — verification

Verified locally on 2026-09-25 for chapter 13 (displayed as the third active lesson), including the later Quantara stories and concept visualizations. This record does not claim fresh verification of external broker services or investment performance.

- `python3 scripts/build_backtest_intro.py`: executed all nine notebook code cells in one fresh CPython namespace and saved actual outputs, synthetic prices and result fixtures. The three added cells reproduce timing, capped volatility sizing and drawdown/recovery arithmetic. The four backtest results and benchmark remain unchanged.
- `npm test`: 44 tests passed, including nine backtest accounting tests and ten concept tests. Coverage includes information timing, future-data perturbation, exact post-fee target weights, initial/final costs, drift, relative drawdown, annualization, JS/Python agreement, cash/Long sizing, the 100% cap and recovery percentages.
- `npm run build:pages`: passed configuration, content, equations, internal lesson links and download checks; exported 14 route files, with the earlier ten lesson bodies still archived. Four pages are active: Welcome and chapters 11–13. The chapter's data/results downloads and three new illustrations are included in the standalone export.
- Chromium at 1440px, 768px, 390px and 320px: all three new visualizations and story blocks remained within the viewport. Images decoded at 1536×1024. Screenshots of the story, timing, sizing and recovery views were visually reviewed; recovery labels were separated into two lines for small screens.
- Timing interactions: advancing the three events reveals only then-known prices; the explicit INVALID hindsight toggle exposes future prices without changing the causal cash holding. Cash remains 0%; the invalid example claims +10%.
- Sizing interactions: keyboard controls produce 25% stock weight at 40% asset volatility and a 10% target; the cap holds stock at 100% when volatility is 5%; Cash has zero risky weight and zero modeled volatility.
- Recovery interactions: a 20% decline needs 25% recovery; 50% needs 100%; 60% needs 150%. Slider controls and chart labels update together.
- Full chapter regression at 1440px, 768px and 390px: all 14 sections remained within viewport width. Tables and code scroll inside their own containers. The original three lab sliders worked by keyboard; cost/target changes recomputed results; equity/drawdown switching and reset passed; six quiz answers, explanations, completion and reset passed.
- Navigation: mobile contents and Escape, previous/next chapter, direct volatility anchor and section highlighting passed. The full supplied quotation matched after whitespace normalization. All chapter download paths resolved to local files.
- Offline: the exported chapter ran under `file://` while HTTP(S) requests were blocked. Both browser checks issued zero HTTP(S) requests and produced zero browser console/page errors.
- Independent content review checked narrative analogies, signal chronology, size versus side and recovery arithmetic. Its wording corrections were applied before the final build.
- `git diff --check`: passed.

The original chapter verification also executed `python3 public/downloads/lesson_13.py` using the standard library and no network. An independent cash/share ledger solving fees by bisection agreed with Python across 45 cost/target/mode combinations, with maximum equity discrepancy `3.58e-14`. The accounting model was not changed in the concept-visualization update.

The local browser scripts and screenshots are temporary QA outputs, not published lesson assets. Three explicitly commissioned fictional illustrations were generated with the built-in image tool; exact prompts, paths and checksums are recorded in `backtest-quantara-generation.json`. The numerical charts are native SVG/HTML, and no additional research source or market data was used. QuantCorner light reading styles and local fonts are retained.

The optional QuantStats recipe is clearly marked as unexecuted; QuantStats was not installed or invoked. Its artificial date index is only for formatting the synthetic report. Numerical validation applies to the standard-library example and website lab.

Publishing and the live page are checked separately after the commit reaches GitHub; a local build is not evidence of a completed deployment.
