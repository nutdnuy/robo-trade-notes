# Chapters 05–07: evidence, assumptions, and verification

Prepared 2026-09-11. These are original Thai teaching adaptations, not translations or redistributed implementations from the reference book. No PDF content was uploaded. No brokerage account, live price feed, or order endpoint was called.

## Scope and owned artifacts

- `content/chapters/05-honest-evaluation.md`
- `content/chapters/06-event-simulation.md`
- `content/chapters/07-machine-learning.md`
- `content/quizzes/chapter-05.json`, `chapter-06.json`, `chapter-07.json`
- `public/downloads/lesson_05.py`, `lesson_06.py`, `lesson_07.py`
- `public/downloads/robo-trade-05.ipynb`, `robo-trade-06.ipynb`, `robo-trade-07.ipynb`

## Primary source review

The local supplied PDF was read with pypdf. Page locators below were confirmed against the printed page labels in the extracted pages, not inferred from a blanket page offset.

| Source | Verified location or URL | Claim supported | Boundary |
| --- | --- | --- | --- |
| Hilpisch, *Python for Algorithmic Trading*, first edition | Chapter 4, “Data Snooping and Overfitting,” printed 111–112; 1-based PDF 131–132 | Repeated data/model selection and overfitting matter when interpreting attractive backtests | No reproduced book returns, figures, or code |
| Same book | Chapter 10, “Risk Analysis,” printed 287–288; PDF 307–308 | Running equity peaks, drawdown, recovery time | Our percentage convention and synthetic examples are original; the book's leveraged FX illustration is not reused |
| Same book | Chapter 6, printed 175–178; PDF 195–198 | Incremental events, cash/units, reusable backtesting state | Partial fills, cancellation, Decimal accounting, and assertions are new teaching code |
| Same book | Chapter 5, printed 132, 134, 146; PDF 152, 154, 166 | Lagged returns, prediction of future returns/direction, feature terminology | Ridge classifier, data generation, explicit boundaries, and train-only preprocessing are original |
| pandas | https://pandas.pydata.org/docs/reference/api/pandas.Series.cummax.html | Cumulative maximum semantics | Online stable docs showed 3.0.5; executed example uses NumPy accumulation and pandas 2.3.2 |
| scikit-learn | https://scikit-learn.org/stable/common_pitfalls.html#data-leakage | Train-only fitting of preprocessing; test data must not influence model fitting | scikit-learn is a conceptual reference, not a runtime dependency |
| scikit-learn | https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.TimeSeriesSplit.html | Time-ordered splits and a gap between train/test observations | Online docs showed 1.9.1; code creates explicit index ranges rather than importing this class |
| NumPy | https://numpy.org/doc/stable/reference/generated/numpy.linalg.solve.html | Solving full-rank linear systems | Stable docs showed 2.5; executed with NumPy 2.5.3 |
| Python | https://docs.python.org/3/library/decimal.html | Decimal arithmetic, construction from strings, rounding modes | Stable docs showed 3.14.7; executed with Python 3.12.14 using established Decimal interfaces |

All listed online pages were retrieved 2026-09-11. The FINRA stop-order page initially considered as an extra reference returned an error and is not cited or used. No source-derived verbatim passages are copied into the lessons.

## Reproducibility and execution

Verified runtime: Python 3.12.14; NumPy 2.5.3; pandas 2.3.2. Chapter 06 uses only the Python standard library. Chapters 05 and 07 use NumPy/pandas. No external datasets or local sibling files are required by any notebook.

Run scripts from the download directory:

```text
python lesson_05.py
python lesson_06.py
python lesson_07.py
```

All three scripts completed successfully with their independent assertions. The Jupyter tutorial scaffolder was used for notebook structure. At authoring, each notebook's code cells were executed sequentially in a fresh Python namespace and their actual stdout was saved. Chapter 05 has 7 code cells, chapter 06 has 6, and chapter 07 has 7. This initial capture is Python execution, not a claim that a Jupyter kernel had already run; the root task will perform the final clean-kernel validation of the complete course and refresh outputs.

## Chapter 05 model and checks

Data: 12 synthetic sessions with asset returns `[.01, -.02, .03, -.01, .02, -.04, .01, .03, -.02, .01, .02, -.01]`; frozen pre-open targets `[0, 1, 1, 0, 1, 1, 1, 0, 0, 1, 1, 0]`. Returns are open-to-close with no overnight changes. No real calendar, timezone, corporate actions, adjusted prices, or listed instrument is represented. Currency label USD is illustrative.

All-in/cash model: a cost fraction is deducted from **pre-trade NAV** on each switch; remaining capital earns the invested period return. Fractional shares, full fills, no interest/leverage/shorting. Final holdings are liquidated. This is intentionally and explicitly distinguished from chapter 04's fee charged on **traded notional**, whose exact buy multiplier is `1 / (1 + c)`. Do not silently compare equal bps labels as equal fee bases across those models.

Executed baseline at 10 bps per side:

| Result | Value |
| --- | ---: |
| Gross final equity | 10,284.368382 USD |
| Net final equity | 10,222.816232 USD |
| Net cumulative return | 2.228162% |
| Buy/hold net final equity | 10,255.661177 USD |
| Net maximum drawdown | -4.000000% |
| Net sample session volatility, ddof=1 | 1.867488% |
| Actual cash costs deducted | 60.286757 USD |
| Switch count | 6 |

Sensitivity final equities for 0, 5, 10, 20, 50 bps: 10,284.368382; 10,253.553818; 10,222.816232; 10,161.571381; 9,979.668354 USD. At 50 bps the buy/hold benchmark is 10,173.698180 USD.

Consequential checks:

- Seven invested returns multiplied independently equal the gross loop output.
- Net final capital equals the independently calculated gross capital times `0.999**6`.
- Buy/hold includes both entry and exit factors, `0.999**2`.
- A first-period loss of 10% is counted as a -10% drawdown by including initial equity in the peak path.
- Higher nonnegative cost rates monotonically reduce final equity for the frozen target sequence.
- Nine gains of 5 USD and one loss of 60 USD give 90% wins but -15 USD total P&L.
- No annualization or performance forecast is made from 12 synthetic observations.

## Chapter 06 model and checks

Seven synthetic sessions; full table is embedded in both code and lesson. Initial cash 1,000 USD, integer shares, a single active order, no shorting or leverage. Fill price is open times `1 +/- .001`, quantized half-up to cents. Fixed cost is 1 USD per fill. Open capacity is a teaching constraint, not order-book reconstruction. Cancellation is immediate in the simulation; real cancel/fill races are explicitly left to later execution handling.

Executed fills:

| Session | Side | Quantity | Price | Cash after |
| --- | --- | ---: | ---: | ---: |
| 2 | Buy | 3 | 101.10 | 695.70 |
| 3 | Buy | 3 | 103.10 | 385.40 |
| 4 | Sell | 6 | 98.90 | 977.80 |
| 6 | Buy | 2 | 102.10 | 772.60 |
| 7 | Sell | 2 | 102.90 | 977.40 |

There are 5 fills, 2 cancellations, 5 USD in fixed costs, and 1.60 USD in slippage relative to the reference opens. Reference-price P&L is -16 USD. Final cash therefore independently reconciles as `1000 - 16 - 1.60 - 5 = 977.40`; final shares and pending orders are zero.

Assertions reconstruct every cash and share movement independently from the fill log, verify each marked equity, reject negative cash/short holdings, prevent same-session fills, avoid duplicate orders for an unchanged target, leave state unchanged for zero capacity, and reject a buy when 100 USD cannot cover one share plus the fixed cost. Status names in this code are explicitly pedagogical, not Webull API status codes.

## Chapter 07 model and checks

Data: 420 synthetic sessions, seed 7, `r[0] = 0`, `r[t] = .25 * r[t-1] + Normal(0, .012)` for subsequent t. Noise is generated as an array of length 420; its first element is unused. This deliberate autocorrelation is a teaching property, not a claim about market data. Starting price 100 USD, final synthetic close 52.239133 USD. No overnight return: each next open equals the prior close.

Each decision row t contains features `[r[t], r[t-1], r[t-2]]`, label sign of `r[t+1]`, and the next open-to-close return. Session indices are zero-based. There are 417 valid examples.

- Train: decision 2–241, 240 rows, labels 3–242.
- Excluded decision 242.
- Validation: decision 243–322, 80 rows, labels 244–323.
- Excluded decision 323.
- Test: decision 324–418, 95 rows, labels 325–419.

Mean and standard deviation (ddof=0) are fit on train only. A constant column serves as an unpenalized intercept. The ridge solve regresses labels -1/+1, then classifies by score > 0; scores are not probabilities. Alphas `[.1, 1, 10, 100]` were specified before evaluating test; selection is validation balanced accuracy, ties broken toward larger alpha. Selected alpha is 1; no refit or threshold search follows selection.

Validation balanced accuracies: .55, .55, .525, .50. Final test results:

| Model | Accuracy | Balanced accuracy |
| --- | ---: | ---: |
| Ridge | .547368 | .551197 |
| Training-majority baseline | .494737 | .500000 |
| Last-return persistence | .557895 | .557846 |

Confusion matrix, actual rows [-1,+1], predicted columns [-1,+1]: `[[43,4],[39,9]]`. Ridge has no accuracy advantage over persistence on this sample; the lesson reports this directly.

Optional Long/Cash translation uses pre-trade NAV cost fraction .001 per switch as in chapter 05, not chapter 04's notional-fee convention. Starting state is cash; final holdings are closed. Synthetic test net returns: ridge 4.150785%, always-long -0.247006%, cash 0%. Drawdowns: -2.224978%, -13.834644%, 0%. Ridge is long on 13/95 sessions (13.684211%) and has 20 entry/exit cost events. These illustrative results are explicitly separated from classification accuracy and do not establish profitability.

Checks enforce temporal boundaries; exact labels from the next synthetic open-to-close prices; zero training means after scaling; future-only changes cannot alter a reconstructed past feature prefix or training means; frozen coefficients match the train-only solve; confusion counts sum to 95; and a small independent two-session cost example includes entry and exit.

## Material limitations

All numerical performance is synthetic and explanatory. No actual market-data survivorship/corporate-action quality, broker fees, fill realism, account permissions, or live model generalization was validated. The lessons place these boundaries alongside the relevant examples rather than portraying the prototype as a deployable trading strategy.


## Central verification, 2026-09-11

The root reviewer subsequently executed all ten notebooks in fresh Jupyter kernels, each in an empty temporary working directory, with Python 3.12.14 / NumPy 2.5.3 / pandas 2.3.2, nbclient 0.10.2 and ipykernel 6.30.1. All 72 code cells completed without errors; refreshed outputs are saved in the distributed notebooks. Local kernel loopback communication required execution outside the filesystem sandbox. No brokerage connection or order was made. See outputs/qa/complete-notebooks.log in the local project for the run record.
