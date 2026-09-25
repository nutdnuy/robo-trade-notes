# Introduction of Backtest — verification

Verified locally on 2026-09-25 for chapter 13 (displayed as the third active lesson). This record concerns the new chapter; it does not claim fresh verification of external broker services or investment performance.

- `python3 scripts/build_backtest_intro.py`: executed all six notebook code cells in one fresh CPython namespace and saved actual outputs, synthetic prices and result fixtures.
- `python3 public/downloads/lesson_13.py`: completed using the standard library and no network.
- `npm test`: 34 tests passed, including nine new numerical tests. The new checks cover information timing, future-data perturbation, exact post-fee target weights, initial/final costs, drift, relative drawdown, annualization and JS/Python agreement.
- Independent accounting review compared a cash/share ledger that solves fees by bisection against Python in 45 combinations of costs, targets and modes. Maximum equity discrepancy was `3.58e-14`.
- `npm run build:pages`: passed configuration, content, equations, internal lesson links and download checks; exported 14 route files, with the earlier ten lesson bodies still archived. Four pages are active: Welcome and chapters 11–13. The new chapter's data/results downloads are included in the standalone export.
- Chromium at 1440px, 768px and 390px: all 14 new chapter sections remained within viewport width. Tables and code scroll inside their own containers. Title and chart views were inspected visually.
- Browser interactions: all three sliders worked by keyboard, cost/target changes recomputed results, equity/drawdown switching and reset passed; six quiz answers, explanations, completion and reset passed.
- Navigation: mobile contents and Escape, previous/next chapter, direct volatility anchor and section highlighting passed. The full supplied quotation matched after whitespace normalization. All chapter download paths resolved to local files.
- Offline: the exported chapter ran under `file://` while HTTP(S) requests were blocked. It issued zero HTTP(S) requests and produced zero browser console/page errors.
- `git diff --check`: passed.

The local browser check script and screenshots are temporary QA outputs, not published lesson assets. No new image generator or research source was used. QuantCorner light reading styles and local fonts are retained.

The optional QuantStats recipe is clearly marked as unexecuted; QuantStats was not installed or invoked. Its artificial date index is only for formatting the synthetic report. Numerical validation applies to the standard-library example and website lab.

Publishing and the live page are checked separately after the commit reaches GitHub; a local build is not evidence of a completed deployment.
