# Third-party notices

The rendered document bundles the existing project fonts and KaTeX font/CSS output. It does not load a CDN at runtime.

| Component | Version | License / local notice | Use |
| --- | --- | --- | --- |
| Roboto via Fontsource | 5.2.8 | SIL OFL 1.1; assets/fonts/roboto-LICENSE.txt | Latin typography |
| Noto Sans Thai via Fontsource | 5.2.8 | SIL OFL 1.1; assets/fonts/noto-sans-thai-LICENSE.txt | Thai typography |
| KaTeX | 0.16.22 | MIT; assets/katex-LICENSE.txt | Static formula markup and fonts |
| React / React DOM | 19.1.1 | MIT; assets/react-LICENSE.txt and assets/react-dom-LICENSE.txt | Build only, server-side rendering |
| React Markdown | 10.1.0 | MIT; assets/react-markdown-LICENSE.txt | Build only |
| remark-gfm | 4.0.1 | MIT; assets/remark-gfm-LICENSE.txt | Build only |
| remark-math | 6.0.0 | MIT per installed package metadata; build-only dependency, source not redistributed | Build only |
| rehype-katex | 7.0.1 | MIT per installed package metadata; build-only dependency, source not redistributed | Build only |

QuantCorner marks are owner-approved assets. They were copied without edits: light from the existing Robo Trade Notes project, dark from the canonical approved brand package. They are not generated artwork or a third-party icon set. No new third-party component or icon family was added.

All SVG charts are original deterministic renderings of the explicit synthetic fixture. No source PDF, private references, generated decoration, market data, secrets, Git history or installed dependencies are included. Dependencies for rebuilding are pinned in package-lock.json, derived from the existing project lockfile and pruned with npm in offline mode.
