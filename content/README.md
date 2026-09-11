# Canonical lesson content

The Markdown and quiz files in this folder are the source of the learning book. Edit them directly; do not edit their generated copies under `public/downloads/content/`.

| File | Purpose |
| --- | --- |
| `intro.md` | Welcome text and page heading |
| `chapters/*.md` | Original Thai lessons, worked examples and source references |
| `quizzes/chapter-NN.json` | Questions, answer options, zero-based answer index and explanations |
| `chapter-template.md` | Starting point for a new lesson; not listed as a published page |
| `book.json` | Generated intermediate metadata; **do not edit** |

Book identity and Welcome settings are in root `_config.yml`. Reading order and chapter metadata are in root `_toc.yml`. Markdown file paths in `_toc.yml` are relative to the project root, for example `content/chapters/01-data-to-signal.md`.

Run `npm run generate:book` to regenerate `book.json` after a YAML edit. Generation is also automatic before development preview and build. YAML is not watched during development; restart `npm run dev` after a YAML edit. Invalid YAML or broken configured links stops the build without replacing the last good generated configuration.

The first `# Heading` is the page heading. An introductory paragraph comes before the first `## Section {#section-id}`. Keep section IDs stable, use `###` for subheadings, and use ordinary Markdown for lists, tables and fenced code. Inline math uses `$...$`; display math uses `$$` on separate lines. Raw HTML is not executed.

A link `[label](#section-id)` opens the current page's section. A link `[label](#/chapter-01/lab)` targets a stable page ID and section; the separate-page export resolves it to the correct HTML destination.

Standalone `::: quiz` and `::: downloads` markers insert the current chapter's exercises and files. Existing `::: lab`, `::: backtest-lab`, `::: drawdown-lab`, `::: execution-lab` and chapter 01 markers insert the prepared interactive components. These are custom builder extensions, not Jupyter Book directives.

For the complete source map, supported YAML fields, adding a chapter, previewing, verification and packaging, read [EDITING.md](../EDITING.md).
