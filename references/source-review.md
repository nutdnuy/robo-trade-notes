# Source review - 2026-09-10

## Scope and originality

Original Thai educational chapter and original examples using the concepts of market-data preparation and SMA rules. The Hilpisch repository LICENSE.txt restricts sharing/duplication without permission. No book notebook, source code, figures, data or PDF is redistributed. QuantGirl is a navigation/layout reference, not a content source. No claim of endorsement by either author or Webull.

## Evidence

1. Supplied Hilpisch PDF: inspected title/copyright/contents previously; for this chapter inspected PDF pages 108-109, printed 88-89, introducing SMA strategies. The printed/PDF offset is verified here rather than assumed globally.
2. https://github.com/yhilpisch/py4at and https://raw.githubusercontent.com/yhilpisch/py4at/master/LICENSE.txt - checked repository purpose and restrictions.
3. https://developer.webull.co.th/apis/docs/ - US-market API scope.
4. https://developer.webull.co.th/apis/docs/sdk - Python SDK; Test/Production endpoints. Public shared test credentials were observed but are neither embedded in the lesson nor used.
5. https://developer.webull.co.th/apis/docs/authentication/overview - signature/token model; App Secret stays client-side for signing, not an HTTP header.
6. https://developer.webull.co.th/apis/docs/market-data-api/overview - market-data permissions are distinct from mobile/QT subscriptions.
7. https://developer.webull.co.th/apis/docs/reference/trade-api/historical-bars - batch POST /market-data/stocks/bars/list; symbols, category, timespan, count, real_time_required, trading_sessions; nested result response; time in UTC; OHLCV returned as strings.
8. https://github.com/webull-inc/webull-openapi-python-sdk at 8e970dbeff93fcda8ea22a1c9bba6d60851ae428 and official PyPI wheel 3.0.0. Inspected DataClient.market_data, MarketData.get_batch_history_bar and BatchHistoricalBarsRequest. Verified SDK method keyword names in the wheel, not just in main.
9. https://www.facebook.com/share/p/1FXLADimwV/ resolves to Webull API Builders Club public welcome post. Inspected post via browser; used as onboarding/community context, not the final authority for endpoint or authentication details.
10. https://quantgirluk.github.io/Understanding-Quantitative-Finance/intro.html - inspected desktop dark screenshot and navigation. Adopted book sidebar, main reading column, in-page contents, code copying and download affordances.

## Material documentation differences

- API reference displays UAT; SDK page explicitly lists production api.webull.co.th and test th-api.uat.webullbroker.com. The teaching script defaults to UAT.
- Generated API-reference headers include x-app-secret and HMAC-SHA1, whereas the authentication overview explicitly says not to transmit App Secret as an HTTP header. The course uses the official SDK, does not recreate raw headers, and follows the authentication guide.
- Historical-bars reference gives counterintuitive real_time_required wording. Example uses True according to the completed-bar description. Neither its name nor that flag alone guarantees final session-close data; learners are told to validate the actual exchange session/calendar.
- UAT is a provider test environment. The browser's DEMO data is separately generated synthetic data, never a claimed UAT or production response.
- SDK example is source/signature-verified and offline mocked. No live credentials, 2FA or market-data call have been executed.

## Synthetic fixture

120 sequential daily bars with no real calendar. Units: illustrative USD, identifier DEMO. Close at zero-based i is rounded to two decimals:
100 + 0.11*i + 5.8*sin(i/9) + 1.5*sin(i/2.1).
The generated CSV is the shared input for the notebook/Python and web checks. There are no observed market prices, returns, order fills, trading costs, or profitability metrics.

## Licensing and assets

React Bits official registry identities CountUp-JS-CSS, AnimatedList-JS-CSS and Stepper-JS-CSS, downloaded 2026-09-10. Modified within this application only; upstream notices retained. AnimatedList's global Tab/arrow trapping was removed in favor of local native buttons. Stepper changed to semantic quiz controls; no custom illustrative flow was authored.
Tabler Icons React 3.34.1 (MIT), Fontsource Roboto/Noto Sans Thai/Roboto Mono 5.2.8 (OFL). All fonts and assets served locally. No logo or external reference artwork is reproduced.
