# S&P 500 daily data snapshot

- Provider: Yahoo Finance, symbol `^GSPC`, instrument type `INDEX`.
- Evaluation: 2006-09-26 to 2026-09-25, the latest completed session in the download as of 2026-09-26. 5,031 daily observations.
- Warmup: 400 observations from 2005-02-24 to 2006-09-25. Excluded from performance.
- `sp500-yahoo-raw.json`: original provider response; includes additional earlier rows.
- `sp500-daily.csv`: selected source OHLC, dates and volume. No EMA or simulated portfolio values.
- `provenance.json`: exact retrieval URL/time, evaluation bounds and SHA-256 checksums.

Dates are trading session dates. Prices are S&P 500 price-index points. Portfolio values in the lesson are simulated USD exposure, using one USD per index point per fractional unit. The index itself is not directly tradable. No dividends, FX conversion, ETF tracking error or futures financing are included.

Do not mix these raw prices with adjusted ETF prices. Changing the snapshot requires rerunning the engine and updating the lesson examples; the build does not silently refresh market data. `verify-ema.py` verifies the CSV against the original response row by row.
