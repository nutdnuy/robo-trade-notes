# SPY daily data from Webull OpenAPI

- Provider: Webull OpenAPI (Thailand), `POST /market-data/stocks/bars/list` via `webull-openapi-python-sdk` 3.0.0 `get_batch_history_bar`, symbol `SPY`, category `US_ETF`, timespan `D`, trading session `RTH`.
- Fetched 2026-09-28 with `webull_data.py --fetch --environment production`: 5,467 completed daily bars from 2005-01-03 to 2026-09-25, paged back with `end_time` (1,200 bars per request).
- Evaluation: 2006-09-26 to 2026-09-25, 5,031 daily observations.
- Warmup: the 400 observations from 2005-02-24 to 2006-09-25 initialize EMA and are excluded from performance. Earlier rows are kept as fetched but unused.
- `spy-webull-daily.csv`: date (New York trading date), OHLC in USD per share, volume in shares. No EMA or simulated portfolio values.
- `provenance.json`: request parameters, paging method, retrieval time, evaluation bounds and SHA-256 checksum.

Webull documents daily bars as forward-adjusted. The price series therefore already reflects dividends, so returns are close to SPY total return, not the S&P 500 price index. Portfolio values are simulated fractional SPY shares. No FX conversion is applied.

Changing the data requires rerunning the engine and updating the lesson text; the build does not refresh market data. `verify-ema.py` checks the checksum and compares every bar with this file.
