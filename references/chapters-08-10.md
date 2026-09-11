# Evidence and validation: chapters 08–10

Reviewed 2026-09-11 for the Thai Robo Trade course. All teaching prose, event fixtures, calculations, Python modules, and notebooks in these chapters are original. No PDF, upstream book code, or book figures are included in the deliverables. No broker account, token, order endpoint, socket subscription, or external deployment was used.

## Deliverable scope

- Chapter 08: event time versus receive time; event-time bars, lateness policy, duplicate detection, signal availability, stale-data gating, and a replay exercise.
- Chapter 09: official Webull Thailand documentation map, explicit internal broker contract, response loss after mock acceptance, partial fills, pending quantity, duplicate fills, and cancellation exercise.
- Chapter 10: journal replay, restart recovery, snapshot reconciliation, bounded risk gates, original signal-to-simulated-fill capstone, operational monitoring, cloud-operation requirements, and failure drills.

The default audience is an intermediate beginner who has followed the preceding chapters. Each chapter has objectives, prerequisites, a worked example with verified outputs, limitations, a worked exercise, a three-question quiz, and a six-code-cell self-contained offline notebook.

## Supplied book: directly inspected page locators

Page numbers below were read from the relevant PDF pages rather than inferred from an offset. PDF page means the one-based page index in the supplied file.

| Chapter | Printed page | PDF page | Verified subject | Use in course |
| --- | ---: | ---: | --- | --- |
| 7 | 201 | 221 | Working with Real-Time Data and Sockets | Online processing context |
| 7 | 208 | 228 | Signal Generation in Real Time | Incremental information and no future knowledge |
| 8 | 223 | 243 | CFD Trading with Oanda | Historical broker example, not a Webull specification |
| 8 | 229 | 249 | The Oanda API | Provider-specific integration differs |
| 9 | 249 | 269 | FX Trading with FXCM | Historical broker example |
| 9 | 256 | 276 | Working with the API | Provider adapter context |
| 10 | 265–266 | 285–286 | Automating Trading Operations and Capital Management | Connect research, execution, capital, and operations |
| 10 | 296 | 316 | Infrastructure and Deployment | Infrastructure requirements, no current price claim |
| 10 | 297 | 317 | Logging and Monitoring | Distinguish persistent records from current observation |

TOC PDF pages 7–9 were also inspected to identify the relevant sections. The event-time watermark, journal replay, order-intent handling, and risk gates are additional original teaching material. They are not attributed as implementations provided by Hilpisch.

## Current primary Webull sources

The following pages were retrieved on 2026-09-11 using the web tool. Claims are limited to the interface taxonomy and explicitly visible endpoint information. Request schemas that the web extractor did not expose were not invented.

| Source | Verified use |
| --- | --- |
| https://developer.webull.co.th/apis/docs/reference/trade-api/market-data-streaming/ | Separate Subscribe and Unsubscribe interfaces |
| https://developer.webull.co.th/apis/docs/reference/trade-api/subscribe/ | Subscribe is a market-data streaming interface; POST /market-data/streaming/subscribe |
| https://developer.webull.co.th/apis/docs/reference/custom/trading-api/ | Instruments, Accounts, Assets, Orders taxonomy |
| https://developer.webull.co.th/apis/docs/reference/trade-api/assets/ | Balance and Positions interfaces |
| https://developer.webull.co.th/apis/docs/reference/trade-api/account-position/ | GET /trading/assets/positions/list; account-based positions |
| https://developer.webull.co.th/apis/docs/reference/custom/order/ | Trading, Order Query, Trade Events categories |
| https://developer.webull.co.th/apis/docs/reference/trade-api/trading/ | Preview, Place, Replace, Cancel categories; no account entitlement inferred |
| https://developer.webull.co.th/apis/docs/reference/trade-api/order-query/ | History, open orders, order details; used only as a reconciliation source map |
| https://developer.webull.co.th/apis/docs/reference/custom/trading-events/ | Separate trade and position event subscription interfaces |
| https://developer.webull.co.th/apis/docs/reference/trade-api/historical-bars/ | POST /market-data/stocks/bars/list; supports historical-bars context |
| https://developer.webull.co.th/apis/docs/reference/custom/authentication/ | Authentication/token taxonomy only |

The SDK, authentication overview, and market-data overview URLs used for chapter 01 could not be fetched by the web extractor during this pass. Their previous 2026-09-10 review remains documented in source-review.md. These new lessons do not add executable authentication or market-data integration instructions based on an unverified schema. UAT is described only as a provider test environment, not as proof of a retail paper-account API.

## Official SDK package inspection

Inspected the locally retained official wheel `/tmp/webull_sdk_3.whl`. METADATA confirms `webull-openapi-python-sdk`, version `3.0.0`, Apache License 2.0. The temporary wheel is not redistributed in the course package.

Directly read these request modules to confirm that API generation and folder name should not be guessed:

- `webull/data/request/get_batch_historical_bars_request.py`: BatchHistoricalBarsRequest, v3 POST historical-bars batch request, body setters, including optional start/end times.
- `webull/trade/request/v3/place_order_request.py`: v3 order placement request wrapper with account and new-orders setters.
- `webull/trade/request/v3/get_order_detail_request.py`: v3 order detail request with account and client-order ID parameters.
- `webull/trade/request/v3/get_order_open_request.py`: contains a deprecated class whose request version is v2 despite its v3 folder; illustrates why folder/name matching alone is insufficient.
- `webull/trade/request/v2/get_account_positions_request.py`: request itself uses version v3 despite a v2 folder.

No SDK source is copied into the teaching scripts. These observations do not prove current regional availability, exact retry semantics, supported order types, or Nuth's account permissions. Those remain prerequisites for a separate integration task.

Official repository: https://github.com/webull-inc/webull-openapi-python-sdk

## Original fixture assumptions

### Chapter 08

- Instrument: synthetic DEMO, illustrative USD, no real market observations.
- Time origin: 2026-01-05 14:30:00 UTC as a synthetic labeling convention, not a verified exchange calendar.
- Tick prices/volumes and IDs are explicitly fixed in the source; eight received messages including one exact duplicate and one late event.
- 60-second half-open bars. Five-second event-time lateness. No wall-clock finalizer. No silent empty-bar fill. Signal requires three consecutive completed bars.
- Duplicates compare an ID and event-time/price/size signature. Conflicting duplicate IDs raise ValueError.
- One instrument and unique event times in the fixture. For real same-timestamp trades, provider sequence semantics must replace any arbitrary ID tie-break order.
- Stale gate checks latest accepted event age. It does not replace bar-age, session, heartbeat, or feed entitlement checks.

### Chapter 09

- Single-symbol, integer-quantity, BUY-only mock. Starting cash USD 2,000.
- Limit USD 100; fills 4 × 99.90 with fee 0.40 and 6 × 100 with fee 0.60.
- No leverage, shorts, settlement, exchange FX, corporate actions, taxes, liquidity model, market impact, or spread model.
- Fill prices and fees are fixed scenario inputs. No return prediction or strategy-performance inference.
- Duplicate prevention is in memory only. Query-after-timeout works by the deliberately defined mock contract. It is not a guarantee of Webull's production idempotency/consistency.
- Mock cancellation is immediately confirmed and rejects subsequent synthetic fills. Real cancel/fill races require additional adapter behavior.
- Pending cash reservation covers limit notional; full multi-order fee reservation is not implemented. The text discloses this and chapter 10 adds an explicit fee buffer to its order gate.

### Chapter 10

- Recovery starts from the same economic fills as chapter 09, but journal stream includes duplicate fill-1 from the recovered broker history.
- Snapshot is synthetic and mutually consistent; production snapshot timing and pagination are not modeled.
- Risk limits (20 shares, USD 500 new-order notional, 20-second data age, USD 20 daily loss stop) are arbitrary teaching parameters for new decisions. No universal suitability claim.
- Capstone closes [100,101,102], SMA3=101, target13, held10, delta3. Risk gate calculates marked P&L from the recovered account using the latest synthetic mark. The next mock fill is deliberately set to 102 with fee0.30 after the signal/risk decision.
- The capstone only executes its positive BUY delta. A target of zero needs a separately implemented SELL/pending-sell contract.
- JSON roundtrip demonstrates persistence representation. It is not atomic durable storage, locking, multi-process coordination, or full crash-consistent journaling.
- Stop control blocks new intents; it does not cancel working orders or flatten held positions.

## Executed validation

All three standalone modules were executed successfully in Python 3.12.14 using only the standard library. All three notebooks were run through actual fresh Jupyter kernels via nbclient on 2026-09-11; each has six executed code cells with saved stream outputs and no error output. Local kernel communication required loopback sockets outside the sandbox; no external network or broker call occurred. The main course verifier will repeat notebook execution with its explicitly selected QA kernel and an empty temporary working directory.

After notebook execution, the capstone's P&L input was clarified to compute marked equity less the initial USD 2,000 rather than use a fixed gate-test P&L. The script and notebook cell were updated together. The standalone capstone was rerun and produced the same downstream outputs; central notebook refresh is requested before packaging.

| Check | Verified output |
| --- | --- |
| 08 bar closes | [101, 102, 103] |
| 08 bar opens | [100, 101.5, 103] |
| 08 bar volumes | [2, 2, 1] |
| 08 signal | bar end 180, available 191, SMA3 102, target1 |
| 08 audit | one duplicate ignored, one late event quarantined |
| 08 stale | age2 passes, age30 blocks |
| 08 lateness15 exercise | first bar close99, volume3, available126 |
| 09 status | ACCEPTED → PARTIAL → FILLED |
| 09 partial | held4, pending6, new order0, cash1600.00 |
| 09 final | held10, cash999.40, average99.96 before fees, fees1.00 |
| 09 cancellation exercise | held4, cash1599.60, remaining target6 |
| 09 duplicate contract | exact fill ignored; conflicting fill payload raises ValueError |
| 10 recovery | held4/cash1600.00 → held10/cash999.40; duplicates do not add exposure |
| 10 gates | normal passes; stale, oversized order, loss stop, unreconciled, manual stop blocked |
| 10 boundary | pending exposure22 fails; loss exactly−20 fails; unknown intent fails |
| 10 capstone | SMA101, target13, delta3, finalcash693.10, held13, marked equity2019.10 |
| 10 file roundtrip | JSON write/read/replay returns held10, cash999.40 |

Notebook schema validation also passed. Quiz files each contain three questions with a valid answer index and explanatory feedback. There are no credentials or private account data in the deliverables.


## Central verification, 2026-09-11

The root reviewer subsequently executed all ten notebooks in fresh Jupyter kernels, each in an empty temporary working directory, with Python 3.12.14 / NumPy 2.5.3 / pandas 2.3.2, nbclient 0.10.2 and ipykernel 6.30.1. All 72 code cells completed without errors; refreshed outputs are saved in the distributed notebooks. Local kernel loopback communication required execution outside the filesystem sandbox. No brokerage connection or order was made. See outputs/qa/complete-notebooks.log in the local project for the run record.
