# Backtest Performance Evaluation

The published prose is edited in `content/chapters/14-backtest-performance-evaluation.md` at the repository root. The renderer preserves that Markdown exactly. In the downloaded standalone package, edit `chapter.md` instead.

From the repository root, run `npm run build:pages` to rebuild the book and chapter. Run `python3 lessons/performance/make_notebook.py` after editing the lesson's Python examples to regenerate and execute the notebook; this authoring command requires nbformat. The notebook records sequential Python execution, not a Jupyter-kernel validation.

The downloadable package runs offline with Python 3.9+:

```sh
python3 lesson_14.py --output-dir output
```

Open `chapter-14-review.html` for the complete lesson or `output/performance-report.html` for the generated report. To rebuild the standalone lesson HTML, run `npm ci` then `node build.mjs`.

`data/` contains the SPY daily bars fetched with Webull OpenAPI and their provenance. Trading, fees, cash interest and risk-free rates are model assumptions. Webull daily prices are forward-adjusted, so dividends are reflected in the price series. `webull_data.py` refetches the data (credentials in `.env`, never committed or packaged); `verify-webull-data.py` tests it offline. See `SOURCES.md` for theory-source boundaries. Private book PDFs are excluded.
