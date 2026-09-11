# Chapters 02–04: evidence and execution record

Reviewed: 2026-09-11. Authoring scope: original Thai lessons and original offline examples. No broker requests, credentials, account connections, or external deployment. The supplied book PDF was read locally and was neither changed nor uploaded.

## Files

| Chapter | Lesson | Notebook | Script | Quiz |
| --- | --- | --- | --- | --- |
| 02 | `content/chapters/02-python-foundations.md` | `public/downloads/robo-trade-02.ipynb` | `public/downloads/lesson_02.py` | `content/quizzes/chapter-02.json` |
| 03 | `content/chapters/03-financial-data.md` | `public/downloads/robo-trade-03.ipynb` | `public/downloads/lesson_03.py` | `content/quizzes/chapter-03.json` |
| 04 | `content/chapters/04-vectorized-backtesting.md` | `public/downloads/robo-trade-04.ipynb` | `public/downloads/lesson_04.py` | `content/quizzes/chapter-04.json` |

All prose and code were written for this course. No upstream book code, figures, or long prose excerpts are distributed.

## Source map

### Book inspected locally

Yves Hilpisch, *Python for Algorithmic Trading: From Idea to Cloud Deployment*, first edition. Bibliographic source: supplied PDF, title/copyright page previously verified by the project. Page locators below were directly read for this work, not inferred from a global offset.

| Chapter | Verified printed pages | Verified 1-based PDF pages | Supported anchor and adaptation boundary |
| --- | --- | --- | --- |
| 2, Python Infrastructure | 17–18 | 37–38 | Dependency management and environment categories. The course uses original `venv` instructions based on Python 3.12 documentation; it does not repeat historical Python 3.8 installation guidance. |
| 2, Conda as a Virtual Environment Manager | 27 | 47 | Separate environments and environment export concepts. Conda commands and examples were not redistributed. |
| 3, Working with Financial Data | 45–47 | 65–67 | Importing, handling, and storing historical structured data. The seven-row validation fixture is original. |
| 3, Reading from a CSV File with pandas | 49–50 | 69–70 | Reading into a DataFrame and inspecting data. Quarantine rules, gap handling, and point-in-time discussion are teaching additions. |
| 4, Strategies Based on Simple Moving Averages | 90–92 | 110–112 | Trailing means, positions, log returns, and shifted positions in the book's historical long/short context. The course implements a distinct long/cash, next-open, fee-aware synthetic example. |

Book repository: <https://github.com/yhilpisch/py4at>. Used for bibliographic attribution only; its code is not copied.

### Current primary documentation

All URLs opened successfully on 2026-09-11. The `/version/2.3/` pandas documentation resolves to the 2.3.3 documentation line, while executable examples were verified on pandas 2.3.2. This distinction is explicit; the cited APIs used here were also executed on the pinned runtime.

| URL | Claim supported |
| --- | --- |
| <https://docs.python.org/3.12/library/venv.html> | Environments based on an existing interpreter, package isolation, activation paths, recreation rather than copying an environment. |
| <https://pandas.pydata.org/pandas-docs/version/2.3/reference/api/pandas.core.window.rolling.Rolling.mean.html> | Trailing rolling mean calculation. |
| <https://pandas.pydata.org/pandas-docs/version/2.3/reference/api/pandas.Series.pct_change.html> | Fractional rather than already-percent return; explicit `fill_method=None`. |
| <https://pandas.pydata.org/pandas-docs/version/2.3/reference/api/pandas.to_datetime.html> | Parsing failures, timezone-naive versus timezone-aware input, meaning of `utc=True`. |
| <https://pandas.pydata.org/pandas-docs/version/2.3/reference/api/pandas.DataFrame.reindex.html> | Representing missing schedule entries as missing values. |
| <https://pandas.pydata.org/pandas-docs/version/2.3/reference/api/pandas.DataFrame.shift.html> | Shifting values without changing index labels when no frequency is supplied. |
| <https://www.investor.gov/introduction-investing/investing-basics/glossary/stock-split> | Split mechanics; the 10 shares at 100 to 20 shares at 50 example is original arithmetic. |

The Webull historical-bars URL is included as a cross-reference to the already verified course integration material. These three chapters make no new assertion about Webull permissions, fees, fill behavior, fractional-share eligibility, or price-adjustment conventions.

## Runtime and reproducibility

- Python 3.12.14; NumPy 2.5.3; pandas 2.3.2.
- Scripts executed as independent Python processes with their embedded synthetic fixtures.
- Notebook format: nbformat 4.5 with stable cell IDs, kernel metadata, source text, execution counters, and real stdout results.
- Initially executed each notebook's cells in order in a fresh Python process, with no preexisting variables, recording actual stdout. No cell magics or external files are required. Parent integration may additionally run clean Jupyter kernels with nbclient; do not claim that extra check until it succeeds.
- Chapter 02: 8 code cells; chapter 03: 8 code cells; chapter 04: 9 code cells. All completed without errors during author verification.
- Four quiz questions per chapter; 12 total, each with one correct option and an explanation.

## Verified outcomes

### Chapter 02

Synthetic closes: `[100, 102, 101, 104, 103]`, illustrative USD, bar indices 1–5, no market calendar or actual instrument.

- SMA3: first two entries missing, then 101, 102.3333333333, 102.6666666667.
- Compounded close-price change: 3%; checked against 103/100 − 1.
- Function leaves input unchanged and rejects zero prices, zero window, and boolean window.
- Last close changed to 105: last SMA3 103.3333333333, total price change 5%, all previous SMA values unchanged.
- SMA6 over five values remains entirely missing.
- Canonical input JSON SHA256: `272ac23eed5c4834bbd489be71dfd88fe1d32fa8df6f38868ba068ceb1ab20aa`.

### Chapter 03

Seven synthetic one-minute OHLCV rows with explicit UTC timestamps. The declared synthetic expected schedule has five endpoints, 14:31–14:35 UTC on 2026-01-05. It is not an exchange calendar.

- Raw 7 = exact duplicates removed 1 + quarantined 2 + accepted 4.
- Missing close at 14:34 is quarantined. The 14:36 row is quarantined for negative volume and invalid OHLC relationships.
- Accepted times are 14:31, 14:32, 14:33, 14:35 UTC. Missing expected endpoint is 14:34.
- Reindexing to the declared schedule preserves missing one-minute returns at both 14:34 and 14:35.
- Conflict exercise: raw 8 = duplicate 1 + quarantined 4 + accepted 3; both different rows at 14:31 quarantined.
- Raw input remains unchanged. CSV round trip preserves accepted values and UTC timestamps.
- Raw fixture string SHA256: `ca6626c9b2e137303e980a81c8ffb6b4d4109a41f9d7247707ce40eef71bec7e`.
- Row validation alone does not enforce sessions or identify point-in-time revisions; those limitations are explained in the lesson.

### Chapter 04

Synthetic open: `[100, 101, 103, 102, 105, 102, 99, 101]`.
Synthetic close: `[100, 102, 101, 104, 103, 100, 98, 101]`.

Default short/long 2/3, initial 10,000, cost 10 bps per side. Position after each open: `[0,0,0,1,1,1,0,0]`. Buy at bar 4 open 102; sell at bar 7 open 99. Final liquidation horizon is bar 8 open; that bar's close is never used for an earlier action.

- Fractional shares on entry: approximately 97.941274412, purchased using `E / [P × (1+c)]` so purchase plus fee never exceeds available cash.
- Gross final equity: 9,705.882352941177.
- Net final equity: 9,686.489980607630.
- Net final return: −3.135100193924%.
- Benchmark buys at bar 4 open and sells at bar 8 open, same cost and horizon; net final equity 9,882.176646882530.
- Cost 25 bps: final equity 9,657.473962153440.
- All rows of vectorized equity match an independent sequential cash/share ledger at numerical tolerance (`rtol=1e-12`, `atol=1e-8`).
- Independent ledger checked across 60 combinations: all 15 valid SMA pairs for long windows 2–6, each at costs 0/10/25/100 bps.
- Increasing cost keeps positions unchanged and reduces net wealth for the same trades. At zero cost net matches gross.
- Changing final close to 900 changes the unused final close target but leaves all open-time positions and equity unchanged.
- SMA 1/3 buys at bar 5 and sells at bar 7; shorter SMA does not imply earlier entry or more trades in every sample.

These are outputs of a pedagogical synthetic model. They are not broker executions, real-market backtest results, or estimates of future performance.


## Central verification, 2026-09-11

The root reviewer subsequently executed all ten notebooks in fresh Jupyter kernels, each in an empty temporary working directory, with Python 3.12.14 / NumPy 2.5.3 / pandas 2.3.2, nbclient 0.10.2 and ipykernel 6.30.1. All 72 code cells completed without errors; refreshed outputs are saved in the distributed notebooks. Local kernel loopback communication required execution outside the filesystem sandbox. No brokerage connection or order was made. See outputs/qa/complete-notebooks.log in the local project for the run record.
