# Editing Robo Trade Notes

The editable source follows a book workflow: `_config.yml` sets the website identity, `_toc.yml` sets the reading order, and the lessons stay in Markdown. The material is original Thai teaching content; the reference repositories provide a reading and editing model, not copied lesson text.

This project uses its own React/Vite builder. Like the supplied Quantitative Finance Notes reference, it uses YAML filenames familiar from Jupyter Book, but it is **not a complete Jupyter Book project**. Do not run `jupyter-book build` or paste arbitrary Jupyter Book settings into these files. The supported custom format is `robo-trade-book`.

## Choose the source file

| Change | Canonical file |
| --- | --- |
| Book name, subtitle, description, edition and default theme | `_config.yml` |
| Welcome menu title, cover image, image description and buttons | `_config.yml` under `welcome` |
| Welcome text and displayed page heading | `content/intro.md` |
| Reading order, chapter menu titles, outcomes, durations and source paths | `_toc.yml` |
| Thai chapter text, tables, formulas and references | `content/chapters/*.md` |
| Questions, correct answers and explanations | `content/quizzes/chapter-NN.json` |
| Cover artwork | `public/images/robo-trade-welcome.png` |
| Python examples | `public/downloads/lesson_NN.py` |
| Executed notebooks | `public/downloads/robo-trade-NN.ipynb` |
| Book appearance | `book.css` |
| Interactive illustrations | `src/components/CourseLabs.jsx`, `src/components/LessonWidgets.jsx` |

`content/book.json` is an **intermediate generated file**. Do not edit it: the next preview or build regenerates it from YAML. Markdown files under `public/downloads/content/` and all files in `dist/` or `_site/` are also generated. Edit the canonical source, then rebuild.

Notebooks and Python scripts in `public/downloads/` are canonical runnable teaching files. The website build packages them as they are; it does not replace their code or rerun their cells.

## Edit the book settings

The top of `_config.yml` includes:

```yaml
title: "Robo Trade Notes"
subtitle: "Python · Webull OpenAPI"
language: "ภาษาไทย"
description: "จากแนวคิด สู่ระบบจำลองที่ตรวจสอบได้"
edition: "ฉบับครบเล่ม · กันยายน 2026"
apiDocs: "https://developer.webull.co.th/apis/docs/"
defaultTheme: "light"
```

The nested `welcome` settings control the Welcome sidebar label, image and buttons. `heroImage` is relative to `public/`, for example `images/robo-trade-welcome.png`; add a meaningful Thai `heroAlt` when changing the artwork. The first `#` heading in `content/intro.md` controls the large page heading separately.

Use two spaces for YAML indentation, keep quotes around chapter numbers such as `"01"`, and retain the existing setting names. Duplicate or unknown keys are reported as errors so a typo does not silently disappear. YAML aliases and custom tags are not used by this project.

The default theme is light. An explicit reader preference can still be saved by the browser; changing the default does not imply clearing the reader's preference.

## Edit the reading order

The root of `_toc.yml` is:

```yaml
format: "robo-trade-book"
root: "content/intro.md"
chapters:
  # Existing chapter entries follow here.
```

Every `file` is relative to the project root and must point inside `content/`. The `.md` extension is accepted explicitly, as in the prepared files; it may also be omitted. Reorder complete chapter entries to change the reading order. Keep `id` and `number` unchanged when only moving an existing chapter. IDs must start with a lowercase English letter; the Welcome page ID must remain `welcome` because it maps to `index.html`.

The `title` field changes the sidebar title. The first Markdown `#` heading changes the chapter page heading. The two may differ deliberately. The `part` field groups related chapters; `outcome`, `duration` and `meta` describe the learning content. All current metadata is retained in the generated JSON for the reader and export tools.

## Preview and build

Requires Node.js 22.12 or later. Install dependencies once after unpacking the editable source:

```sh
npm ci
npm run dev
```

On macOS, `Preview.command` also starts the development preview. Open the address printed in the terminal. Markdown edits refresh during development. YAML changes are not watched automatically. After changing `_config.yml` or `_toc.yml`, stop the running development preview and start `npm run dev` again so the configuration is regenerated. A production build always regenerates it before building.

Build the static reader preview:

```sh
npm run build
npm run preview
```

Build separate HTML pages for a book-style export:

```sh
npm run build:pages
```

The page export goes to `_site/`, with `index.html` and one `chapter-NN.html` per chapter. Open `_site/index.html` in a browser with JavaScript enabled to read the generated website without a development server. Local fonts and experiments are bundled; external source links need internet access. `npm run build:standalone` is an alias for the same command. The application preview build goes to `dist/`. Both workflows regenerate and validate configuration, refresh Markdown download copies and package complete learning materials first.

`npm run build:pages` creates local files. To update the online book, commit and push the source changes to `main` in [robo-trade-notes](https://github.com/nutdnuy/robo-trade-notes). GitHub Actions then checks, builds and deploys the website automatically. See `DEPLOYMENT.md`.

For a served application under a host subdirectory, set its base path:

```sh
npm run build -- --base=/robo-trade/
```

## Write a lesson in Markdown

Use one page title, then an introductory paragraph before the first section:

```md
# ชื่อบทเรียน

คำเกริ่นที่อธิบายว่าเรากำลังเรียนรู้อะไร

## หัวข้อแรก {#section-id}

คำอธิบายและตัวอย่าง

### หัวข้อย่อย

รายละเอียดเพิ่มเติม
```

Section IDs use lowercase English words and hyphens. Keep them stable to preserve existing links. `[อ่านต่อ](#section-id)` links to a section on the current page. `[บทถัดไป](#/chapter-02)` links to another page using a stable reader ID; the separate-page export maps it to the corresponding HTML file.

Use `$r_t$` for inline mathematics and `$$` on separate lines for display mathematics. Code examples use fenced `python` blocks. Use `USD` for currency rather than an unescaped dollar sign. Raw HTML is not executed from lesson Markdown.

Standalone interactive markers:

- `::: lab` — chapter 01 SMA experiment
- `::: backtest-intro-lab` — chapter 13 signal-timing, cost and volatility-target comparisons
- `::: backtest-lab` — chapter 04 transaction-cost experiment
- `::: drawdown-lab` — chapter 05 drawdown/recovery experiment
- `::: execution-lab` — chapter 09 partial fills and duplicate events
- `::: quiz` — questions for the current chapter
- `::: downloads` — the current notebook and editable Markdown
- `::: chapter-card` — chapter overview on the Welcome page

The chapter 01 markers `api-example`, `sma-example`, `sma-formula`, and `bar-question` are also supported. These are this custom builder's extensions, not Jupyter Book directives. Keep an existing marker when editing the prose around it; the content checker reports unknown markers.

## Add a chapter

1. Create `content/chapters/11-your-topic.md`, using `content/chapter-template.md` as a starting point. Write the completed lesson, including one `::: quiz` marker and its source references.
2. Add `content/quizzes/chapter-11.json`. Each question has `title`, `options`, zero-based `answer`, and `explanation`. Each lesson needs at least three questions.
3. Add `public/downloads/lesson_11.py` and `public/downloads/robo-trade-11.ipynb`. Run the example and all notebook cells from a fresh kernel, then save the real outputs. The content checker expects at least five executed code cells without error outputs.
4. Add a chapter entry under `chapters` in `_toc.yml`:

```yaml
  - id: "chapter-11"
    file: "content/chapters/11-your-topic.md"
    title: "ชื่อบทใหม่"
    number: "11"
    eyebrow: "CHAPTER 11 / ROBO TRADE WITH PYTHON"
    part: "04 · ศึกษาต่อ"
    outcome: "อธิบายสิ่งที่ผู้เรียนจะทำได้หลังจบบท"
    duration: 45
    meta:
      - "อ่านและทดลอง 45 นาที"
      - "Python Notebook"
      - "แบบทบทวนพร้อมคำอธิบาย"
    primaryLabel: "เริ่มอ่านบทเรียน"
    primaryHref: "#/chapter-11"
    secondaryLabel: "ดาวน์โหลด Notebook"
    secondaryHref: "downloads/robo-trade-11.ipynb"
```

Add the completed page ID to `src/lib/publishing.js`, then register its Markdown, quiz and presentation settings in `src/App.jsx`. The sidebar numbers only these active lessons in reading order; stable route and download IDs do not determine the displayed chapter number. Never expose an unfinished placeholder.

Update the Welcome text or labels that state a fixed chapter count. The configuration checker catches duplicate IDs, chapter numbers, missing Markdown files, missing local downloads, invalid durations and broken configured section links.

## Check changes before sharing

```sh
npm run generate:book
npm run check:config
npm run check:content
npm test
```

`generate:book` validates the YAML and updates `content/book.json` only after all configuration checks pass. Invalid YAML leaves the last good generated file intact and stops the build. `check:config` checks that the intermediate JSON is current without rewriting it.

`check:content` additionally checks headings, links, mathematics, quizzes and executed notebook structure. After changing numerical examples, run the matching Python script and notebook again: a successful website build alone does not validate financial logic.

The notebooks are offline simulations. Keep synthetic data clearly labeled, retain the distinction between signal and actual fill, and check timing and transaction costs after edits. Original Thai explanations can be edited freely; sources retain their own rights and should remain traceable.

## Repackage the editable source

```sh
npm run package:source
```

This creates `outputs/robo-trade-editable.zip` with the canonical YAML, Markdown, Python examples, notebooks and builder. It excludes the supplied book PDF, local agent instructions, credentials, installed dependencies and logs. The complete learning-materials ZIP is for reading and running lessons; the editable website ZIP also contains the application and build tools.

## Package the ready-to-read website

Run `npm run package:website` to rebuild the separate HTML pages and create `outputs/robo-trade-website.zip`. Extract the full folder and open its `index.html`; keep the supporting folders beside it. This reading package does not require Node.js or Python.

## Backtest introduction artifacts

Chapter 13 uses `src/components/BacktestIntroLab.jsx` and `src/lib/backtest-intro.js`. Its original offline Python source is `public/downloads/lesson_13.py`; `scripts/build_backtest_intro.py` executes the notebook and refreshes the synthetic data/results JSON. Rebuild these files together after numerical changes, then run the backtest numerical tests and inspect the chapter at desktop/mobile sizes. The standalone exporter includes both JSON downloads for this chapter.
