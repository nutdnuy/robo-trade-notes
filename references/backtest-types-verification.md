# Backtest type figures - local review

Updated 2026-09-26 with Nuth's two supplied reference images and request for 100 Monte Carlo paths. QuantCorner / QuantSeras light tokens, deterministic SVG chart route. No external research, data or assets fetched.

- Historical / walk-forward: seven rolling windows on one timeline of 10 hypothetical intervals. Each window trains on three preceding intervals and tests on the next one. Every training index is earlier than its test index.
- Resampling: original blocks A B C D, each containing three declared returns, sampled into BDDA, CABC and ADCB. Each new set has illustrative training/test windows. Text explains that the resampled sequence is not another observed history; repeated source observations can leak between training and test, and temporal dependence requires separate assessment. This is a block-bootstrap illustration, not a universal cross-validation recipe.
- Monte Carlo: exactly 100 SVG polylines in each responsive version. Twelve independent +/-2% simple returns with equal probabilities, initial index 100, seed 20260926. Compounding checked at every point. The first eight paths are unchanged from the earlier illustration. Prices range from 81.67459777647917 to 119.4614531594862, inside the 80-120 axis. The paragraph explains that paths overlap under this two-outcome model.
- Original SVGs have desktop and mobile layouts. PNG exports rendered locally at 2x resolution. Existing Noto Sans Thai fonts embedded; notices retained under public/images/fonts.
- Reproduction: python3 scripts/generate_backtest_type_visuals.py regenerates SVG files and JSON specifications. PNGs are browser renderings of those originals.
- npm run build:pages passed; standalone review folder and ZIP refreshed.
- Chromium file:// checks passed at 1440, 390 and 320px: three images decoded, correct responsive sources, no page-width overflow, no JavaScript/console errors, zero HTTP(S) requests.
- Three Quantara stories, three concept widgets and five backtest result rows remain present.
- Desktop resampling, mobile resampling, mobile historical and mobile Monte Carlo exports visually inspected.
- Owner prose preserved byte for byte before the first revised figure subsection and after the figure section. Only the three figure explanations and alt text changed.
- The scoped prose diff has no whitespace errors. Whole-tree git diff --check still identifies prior trailing spaces in owner prose and generated copies, which were preserved.

Local review only. No commit, push or publication performed.

## Publication preparation - 2026-09-26

Nuth explicitly authorized GitHub publication after editing the chapter. The publication checkout preserves that latest Markdown byte for byte. All 44 tests passed, the standalone build passed, and offline Chromium checks passed at 1440, 390 and 320px with no console errors or external requests. The earlier local-only status above records the review stage. Deployment is verified separately after pushing.
