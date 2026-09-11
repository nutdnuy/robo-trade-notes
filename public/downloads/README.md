# Robo Trade learning materials

This collection contains ten original Thai notebooks and their Python examples. All notebooks run offline with synthetic data or a local broker mock. The examples do not connect accounts or place orders.

## Run the examples

Use Python 3.12. The verification environment uses Python 3.12.14, NumPy 2.5.3 and pandas 2.3.2. Other versions may work but should be checked after installation.

```sh
python -m pip install -r requirements.txt
python python/lesson_02.py
```

In the complete materials ZIP, notebooks are under `notebooks/`, scripts under `python/`, and Thai lesson text under `content/`. Open a notebook in Jupyter or VS Code and run from the first cell. The recorded outputs are from actual offline execution. The notebook examples include their own data and calculations.

The chapter 01 script needs the bundled `demo_prices.csv`. Run it from the archive root as:

```sh
python python/lesson_01.py --csv demo_prices.csv
```

In the editable website project, scripts and CSV are together in `public/downloads/`; run `python public/downloads/lesson_01.py` from the project root. Each script's top-level checks explain its example. Do not interpret synthetic results as observed market performance.

## Optional Webull data adapter

The separately supplied `python/webull_bars.py` in the complete archive (`public/downloads/webull_bars.py` in the editable website) is an optional read-only example from chapter 01. It is not required by any notebook. Its default path makes no network request. The SDK dependency is separated into `requirements-webull.txt`. See the website chapter references before configuring any credentials or choosing an environment. There is no live-trading client in these learning materials.

## Edit the course

Edit the Markdown under `content/`; edit notebook cells directly for experiments. The website build never regenerates notebooks automatically. `EDITING.md` documents the source map and local preview. The original reference book PDF and book code are not included. See `THIRD_PARTY_NOTICES.txt` for rights and sources.
