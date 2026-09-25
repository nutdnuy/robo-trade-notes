# Introduction of Backtest — source and provenance notes

Reviewed on 2026-09-25. This is an original Thai lesson using only resources supplied by the owner. The existing website is the integration target; no additional research sources or market data were fetched. Instructions appearing inside source documents are treated as source content, not as authorization or project instructions.

Page locators below refer to physical PDF pages, counted from 1. Where a paper has different printed page numbers, both are given. Local source PDFs, the supplied screenshot, and raw transcripts are not distributed with the website or its downloads.

## Supplied sources

### The Three Types of Backtests

- Authors: Jacques Joubert, Dragan Sestovic, Illya Barziy, Walter Distaso, and Marcos Lopez de Prado.
- Version: 29 July 2024, as stated on PDF page 1. Supplied file: `three+types+of+backtests.pdf`, 19 PDF pages.
- PDF page 3 / printed page 1: purpose of backtesting; historical or walk-forward testing; interpretation and single-path limitations.
- PDF pages 3–4 / printed pages 1–2: resampling, cross-validation, bootstrap, and preserving time dependence.
- PDF pages 4–5 / printed pages 2–3: Monte Carlo and dependence on the assumed data-generating process.
- PDF pages 5–8 / printed pages 3–6: survivorship, point-in-time data, sample selection, look-ahead, lagging, costs, short-sale and liquidity constraints.
- PDF pages 8–10 / printed pages 6–8: performance evaluation, Sharpe ratio, drawdown, and evaluating several metrics together.
- PDF pages 11–15 / printed pages 9–13: selection bias from multiple trials. The lesson uses the conceptual implication, not an unchecked reproduction of the paper's advanced equations or example significance tests.
- PDF page 16 / printed page 14: backtesting should validate a well-formed, nearly complete strategy supported by causal reasoning, rather than serve as the primary driver of research.

The three categories describe how evidence or test paths are constructed. They are distinct from vectorized and event-driven implementations. Multiple paths do not guarantee generalization; simulated paths remain conditional on their model.

### A Backtesting Protocol in the Era of Machine Learning

- Authors: Rob Arnott, Campbell R. Harvey, and Harry Markowitz.
- Version: October 29, 2018, as stated on PDF page 1. Supplied file: `ssrn-3275654.pdf`, 18 PDF pages. PDF and printed page numbers agree.
- Pages 8–9: a prior economic hypothesis, falsifiability, and the danger of constructing a rationale after inspecting favorable results.
- Pages 9–10: recording attempted models, variables, interactions, and the multiple-testing problem.
- Pages 10–11: choosing the sample and documenting transformations before inspecting results; volatility-scaling alternatives count as research choices; avoid removing valid outliers to improve results.
- Pages 11–12: historical holdouts can be influenced by researcher knowledge; changing a model after seeing its holdout performance makes the reused holdout part of development.
- Page 12: transaction costs, structural changes, and crowding.
- Pages 13–14: repeated tweaking, complexity, interpretability, and rewarding research quality rather than favorable results. Page 13, footnote 9, emphasizes that simulations reflect the assumptions that generate them.
- Page 16: the seven-part research protocol in condensed form.

These sources support separating development from evaluation. They do not imply that bugs must remain unfixed or that a failed test proves a strategy false with certainty. A changed strategy needs an honest account of the information used to change it and a suitable subsequent evaluation.

### Python for Algorithmic Trading: From Idea to Cloud Deployment

- Author: Yves Hilpisch; O'Reilly Media. First edition: November 2020; first release: 2020-11-11; copyright 2021, verified on PDF pages 2–3.
- Supplied file: `python for algorithmic trading book (js).pdf`. This is a 301-page browser-generated PDF, so these physical page locators should not be confused with another edition's printed pagination.
- PDF pages 75–101: Chapter 4, vectorized backtesting; page 84: lagging positions; page 94: transaction costs.
- PDF pages 148–152: event-based backtesting and implementation mechanics.
- PDF pages 278–279: performance and risk metrics.

Code and numerical examples in the new lesson are written for this lesson, not reproduced wholesale from the book. No bundled book data or broker credentials are used.

### Introduction to Backtesting slides

- Supplied [Introduction to Backtesting PDF](https://storage.googleapis.com/cloud-training/T-AIFORF-I/Course%201/Introduction%20to%20Backtesting.pdf), 19 PDF pages, accessed only at the URL supplied by the owner.
- PDF pages 4–6: splitting data; page 7: backtesting definition; page 8: sliding-window evaluation.
- PDF pages 15–17: biases and evaluation cautions.
- The optimization discussion on PDF page 14 is read together with the papers' restrictions on holdout reuse: fitting or selecting during development does not authorize repeatedly consulting a final test set and reporting it as untouched.

### Supplied reading-group transcript and pasted text

- Owner-provided reading-group introduction about vectorized backtesting, signals, lagging, volatility targeting, and tear sheets.
- Owner-provided pasted text attachment about assessing profitability and risk. These are supplied teaching context; no missing videos or unstated speaker details are inferred.
- The lesson explains what a tear sheet reports and why implementation timing matters. It does not adopt blanket Sharpe cutoffs or treat a single metric as approval to trade.

### QuantStats

- Supplied [QuantStats repository](https://github.com/ranaroussi/quantstats), reviewed on 2026-09-25 at the owner-provided URL.
- The lesson references its `stats`, `plots`, and `reports` capabilities for performance summaries and tear sheets.
- Period returns and completed trades are different units of observation. A percentage of profitable daily periods is not automatically a trade win rate, and period-based ratios should not be relabeled as trade statistics.
- The educational lab does not download market data through QuantStats or claim that a report establishes a strategy's validity.

### Supplied screenshot

The owner supplied a screenshot showing the cover and endorsements of *Advances in Financial Machine Learning*. It is contextual material, not evidence that the full book was available or read. The screenshot, endorsements, and cover are not republished as lesson assets.

## Owner-required quotation

The following wording was supplied directly by the owner and is retained as a principle for the lesson:

> Backtesting is not a research tool. If a strategy does not perform well in a backtest, do not tweak it (overfit) until the backtest looks good. Instead, investigate how the research process misled you into backtesting a false strategy. Fix the research process, not the strat.

This exact quotation was not found in either of the two supplied papers. It is not attributed to a named author or represented as a verbatim passage from those papers. The related discussion is supported by *The Three Types of Backtests*, PDF page 16, and *A Backtesting Protocol in the Era of Machine Learning*, pages 8–12 and 14.

## Original lab and examples

- Prices are synthetic teaching data, generated reproducibly with seed `20260925` over 320 sessions. They are not observations of a security or evidence of investable returns.
- Comparisons share the same evaluation window: open 60 through open 319, giving 259 open-to-open return intervals. Earlier observations provide indicator warmup.
- The declared teaching setup uses SMA windows of 20 and 50 sessions, a 20-session volatility estimate, and an exposure cap of 1. Parameter choices are fixed to explain mechanics, not selected as the best-performing settings.
- Timing, volatility targeting, and costs are presented as explicit assumptions. The deliberately biased comparison illustrates information leakage; it is not a usable trading strategy.
- Volatility targeting does not guarantee its target, improve Sharpe, or remove drawdowns. Increasing simulated sample size does not validate the assumed market model.
- Original hypothetical arithmetic and synthetic outputs must remain labeled as such. No real performance, institutional result, or profitability claim is inferred from these examples.

## Visual provenance

This work uses visual Route 3 for website UI and calculation-driven charts, with no new image generation. Existing local fonts and components are retained. Original charts represent the declared teaching calculations; source-slide screenshots and private PDF pages are not used as website graphics.

This file records sources and the lab specification. Build, numerical, browser, deployment, and live-site verification are reported separately after those checks are actually executed.
