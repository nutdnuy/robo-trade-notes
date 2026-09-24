# Alpha / Beta teaching chart

Original synthetic example for Why Robo Trade, QuantCorner / Quantara.
No real market observations, dates, annualized claims, fees or live trades.

## Files

- `why-robo-alpha-beta.svg`: 780 × 450, side by side.
- `why-robo-alpha-beta-mobile.svg`: 360 × 735, stacked; use below the mobile breakpoint.
- Matching PNG files are local QA previews.
- `why-robo-alpha-beta.csv`: exact plotted series to 12 decimal places.
- `generate_alpha_beta.py`: deterministic model and Matplotlib source.
- `why-robo-alpha-beta.spec.json`: parameters, transformations, limitations, alt text and completed QA.

## Model

60 unitless periods, wealth starts at 100, risk-free return is zero each period.
Left: alpha = 0.002 (0.20% per period), beta = 1, residual population std = 0.004.
Right: alpha = 0, beta = 1.3, residual population std = 0.003.
The seed is 42026. Each noise vector is projected orthogonal to the intercept and benchmark returns before scaling. As a result, the sample OLS coefficients equal the imposed parameters by construction. This is an illustration device, not evidence of forecasting skill.

Both panels show the same benchmark and use the same 90–130 vertical scale. All three paths have upward and downward moves. The line chart alone cannot prove alpha.

## Generate

From the project root with Python, NumPy, Matplotlib and FontTools installed:

```sh
python3 scripts/generate_alpha_beta.py --font-root node_modules/@fontsource --output-dir public/images --data-dir public/data
```

Fonts are the existing Fontsource project fonts. The generator reads WOFF for native text measurement and embeds original WOFF2 in SVG, keeping Thai/Latin text editable and self-contained. Greek characters use a system sans-serif fallback. Strategy is purple with a solid line. Benchmark is teal with a dashed line and a darker contrast outline on white. No image generator, downloaded chart or decorative artwork was used.

Both PNGs and both native SVGs were visually inspected. CSV OLS, font embedding, dimensions and text nodes were checked. The temporary `.matplotlib-cache` folder is a local build cache and should not be copied into the repository.

The two `*-LICENSE.txt` files preserve the licenses of the fonts embedded in the SVGs. Retain the repository's corresponding font notices when publishing.
