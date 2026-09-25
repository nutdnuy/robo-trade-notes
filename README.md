# Robo Trade Notes

[Read the book online](https://nutdnuy.github.io/robo-trade-notes/) · [Edit the source on GitHub](https://github.com/nutdnuy/robo-trade-notes)

A Thai learning website about Python and Webull OpenAPI. The book contains Welcome and three lessons: Why Robo Trade (concepts, four original editable flows, a synthetic Alpha/Beta chart, two illustrated Quantara interludes and a closing summary) and the illustrated setup guide, [เริ่มต้นใช้ Webull OpenAPI ทีละขั้น](https://nutdnuy.github.io/robo-trade-notes/chapter-11.html), with 10 attributed image excerpts, an executed offline notebook and a quiz. The third lesson, [Introduction of Backtest](https://nutdnuy.github.io/robo-trade-notes/chapter-13.html), explains research integrity, signal timing, backtest types, costs, volatility targeting and tear sheets, with four backtest comparisons, three illustrated Quantara stories, three concept visualizations and an executed offline notebook. The earlier ten-chapter edition remains archived; see [archive/README.md](archive/README.md). Light is the default theme.

## Edit the book

The canonical source is deliberately small and familiar:

```text
_config.yml                 Book identity, default theme and Welcome settings
_toc.yml                    Reading order, chapter titles and source paths
content/intro.md             Welcome text
content/chapters/*.md        Original Thai lessons
content/quizzes/*.json       Questions and explanations
public/downloads/           Executed notebooks and Python examples
src/lib/publishing.js       Published-page allowlist (old chapters stay archived)
book.css                    Book appearance
references/                 Evidence and verified page locators
```

See [EDITING.md](EDITING.md) for YAML examples, Markdown and mathematics conventions, and the complete editing workflow. `content/book.json` is generated from the two root YAML files; edit the YAML rather than that intermediate JSON. The lesson Markdown remains in one canonical location under `content/`.

This is a custom React/Vite builder inspired by [Nuth's Quantitative Finance Notes](https://github.com/nutdnuy/quantitative-finance-notes) and [QuantGirl's Understanding Quantitative Finance](https://github.com/quantgirluk/Understanding-Quantitative-Finance). It is not a full Jupyter Book project; `_toc.yml` uses the custom format `robo-trade-book`. No reference lesson text or book code has been copied.

## Preview

Requires Node.js 22.12 or later:

```sh
npm ci
npm run dev
```

On macOS, `Preview.command` starts the same development preview. Open the address shown in the terminal. Markdown edits refresh automatically. YAML is not watched automatically: after editing `_config.yml` or `_toc.yml`, stop and restart `npm run dev`. Builds always regenerate the configuration.

## Build and verify

```sh
npm test
npm run build
npm run preview
```

The application build creates `dist/`. It first validates the canonical YAML, refreshes Markdown download copies and packages the complete learning materials. It does not overwrite edited notebooks or Python scripts. To serve from a subdirectory, use `npm run build -- --base=/robo-trade/`.

For separate HTML pages, build the book export:

```sh
npm run build:pages
```

The export is created in `_site/` with `index.html` and chapter HTML files. To read the built book, open `_site/index.html` in a browser with JavaScript enabled. Fonts, mathematics, diagrams and experiments are bundled locally; external reference links still require the internet. `build:standalone` is an alias. This command builds local output. On GitHub, the Pages workflow builds and deploys automatically after a push to `main`; see [DEPLOYMENT.md](DEPLOYMENT.md).

Configuration and lesson checks can also be run directly:

```sh
npm run generate:book
npm run check:config
npm run check:content
```

Python verification uses Python 3.12 and the pinned offline requirements:

```sh
python3 -m pip install -r public/downloads/requirements.txt
python3 scripts/verify_course.py
```

`webull_bars.py` is a separate optional read-only adapter from chapter 01. It requires explicit CLI opt-in for a network request and is unnecessary for every course notebook. Its SDK dependencies are in `requirements-webull.txt`. The learning website does not connect brokerage accounts or place orders.

## Ready-to-read website package

```sh
npm run package:website
```

Creates `outputs/robo-trade-website.zip`. Extract the complete folder, then open `index.html`. Keep its `assets`, `images` and `downloads` folders together. This package does not require Node.js or Python to read the website. Python is only needed to run the separate notebook examples.

## Portable source package

```sh
npm run package:source
```

Creates `outputs/robo-trade-editable.zip`. The source package includes `_config.yml`, `_toc.yml`, canonical Markdown and the builder, while excluding the supplied book PDF, local agent configuration, credentials, installed dependencies and logs.

## Sources and rights

Teaching prose and examples are original. Hilpisch's *Python for Algorithmic Trading* provides conceptual anchors; Webull-specific claims rely on official Thailand documentation. Chapter references separate historical book examples, verified interface facts and new teaching adaptations. Offline simulations are labeled and do not establish investment performance.

The source PDF stays local and is excluded from exports. Third-party component and source rights are recorded in `public/THIRD_PARTY_NOTICES.txt`.

## Introduction of Backtest

Edit `content/chapters/13-introduction-backtest.md`. Source boundaries and verified page locators are in `references/introduction-backtest-sources.md`. This lesson uses only the owner-supplied resources; the supplied PDFs stay local. Charts and interactive visualizations use deterministic Route 3 rendering. Three fictional Quantara story illustrations were explicitly commissioned separately and generated with the built-in image tool; their prompts and provenance are in `references/backtest-quantara-generation.json`.

Rebuild and execute the standard-library notebook and synthetic fixtures with `python3 scripts/build_backtest_intro.py`. Run `npm test` to verify timing, exact post-fee rebalancing, costs, liquidation, JS/Python consistency and the three concept calculations. The fixed seed is 20260925; the sample is 259 open-to-open intervals (open 60 to open 319). These are synthetic teaching results, not market evidence.
