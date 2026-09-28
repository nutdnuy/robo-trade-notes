#!/usr/bin/env python3
"""Fetch daily bars with Webull OpenAPI, then run the chapter 14 EMA backtest on them.

Uses the only historical-bars endpoint documented for Webull Thailand,
POST /market-data/stocks/bars/list (SDK 3.0.0: MarketData.get_batch_history_bar).
Body: symbols, category (US_STOCK | US_ETF), timespan, count (max 1200),
real_time_required, trading_sessions. The reference lists no date range; SDK 3.0.0's end_time
field is used to page back (honoured by the server on 2026-09-28) and paging stops if it is
ignored. Network access happens only with --fetch.
Credentials come from WEBULL_APP_KEY / WEBULL_APP_SECRET; a verified token in
WEBULL_TOKEN_DIR (default .webull-token) is reused so Webull does not ask for 2FA again.

    python3 webull_data.py --fetch --environment production --output webull-spy-daily.csv
    python3 webull_data.py --backtest webull-spy-daily.csv --output-dir webull-run
"""
import argparse
import csv
import json
import time
from datetime import date, datetime, timezone
from pathlib import Path

ENDPOINTS = {'uat': 'th-api.uat.webullbroker.com', 'production': 'api.webull.co.th'}
MAX_BARS_PER_REQUEST = 1200
FIELDS = ['date', 'open', 'high', 'low', 'close', 'volume']


def load_env_file(path='.env'):
    """Read KEY=VALUE lines into os.environ without overriding variables already set."""
    import os
    path = Path(path).expanduser()
    if not path.is_file():
        return False
    for line in path.read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            key, value = line.split('=', 1)
            key = key.strip().removeprefix('export ').strip()
            os.environ.setdefault(key, value.strip().strip('"').strip("'"))
    return True


def market_data_client(environment='uat', token_dir=None, new_token=False):
    """Create the SDK market-data client; reuse a verified token instead of a new 2FA prompt."""
    import logging
    import os
    from webull.core.client import ApiClient

    client = ApiClient(os.environ['WEBULL_APP_KEY'], os.environ['WEBULL_APP_SECRET'], 'th')
    client.add_endpoint('th', ENDPOINTS[environment])
    client.set_stream_logger(log_level=logging.CRITICAL)
    token_dir = Path(token_dir or os.environ.get('WEBULL_TOKEN_DIR', '.webull-token')).expanduser()
    token_dir.mkdir(parents=True, exist_ok=True)
    client.set_token_dir(str(token_dir))
    token_file = token_dir / 'token.txt'
    lines = token_file.read_text(encoding='utf-8').splitlines() if token_file.exists() else []
    if not new_token and len(lines) >= 3 and lines[0] and lines[2] == 'NORMAL':
        from webull.data.quotes.market_data import MarketData
        client.set_token(lines[0])
        return MarketData(client)
    from webull.data.data_client import DataClient
    return DataClient(client).market_data  # creates and verifies a token (2FA in the app)


def _bars_in(payload):
    """Return bar dicts from a list of bars, or a batch response {"result": [{"result": [bars]}]}."""
    items = payload.get('result', []) if isinstance(payload, dict) else payload
    bars = []
    for item in items or []:
        if isinstance(item, dict) and isinstance(item.get('result'), list):
            bars.extend(item['result'])
        elif isinstance(item, dict) and 'close' in item:
            bars.append(item)
    return bars


def _session_date(value):
    """Webull bar time is UTC; convert to the New York trading date."""
    from zoneinfo import ZoneInfo
    if isinstance(value, (int, float)) or str(value).isdigit():
        moment = datetime.fromtimestamp(int(value) / 1000, tz=timezone.utc)
    else:
        text = str(value).strip().replace(' ', 'T').replace('Z', '+00:00')
        if text[-5] in '+-' and text[-3] != ':':
            text = text[:-2] + ':' + text[-2:]  # +0000 -> +00:00
        moment = datetime.fromisoformat(text)
        if moment.tzinfo is None:
            moment = moment.replace(tzinfo=timezone.utc)
    return moment.astimezone(ZoneInfo('America/New_York')).date().isoformat()


def _page_rows(response):
    if response.status_code != 200:
        raise RuntimeError(f'Webull HTTP {response.status_code}')
    rows = {}
    for bar in _bars_in(response.json()):
        day = _session_date(bar['time'])
        rows[day] = {'date': day, **{k: float(bar[k]) for k in ['open', 'high', 'low', 'close']},
                     'volume': int(float(bar.get('volume') or 0))}
    return rows


def fetch_daily_bars(symbol='SPY', count=MAX_BARS_PER_REQUEST, category='US_ETF', environment='uat',
                     market=None, start=None, pause_seconds=0.25):
    """Latest `count` completed daily bars (documented request, max 1200).

    With `start`, also try paging back through SDK 3.0.0's end_time field. The Thailand
    reference does not list end_time, so stop as soon as a page is not older than the last one.
    """
    def request(client, end_ms=None):
        extra = {} if end_ms is None else {'end_time': end_ms}
        return client.get_batch_history_bar(
            symbols=[symbol], category=category, timespan='D', count=count,
            real_time_required=True, trading_sessions='RTH', **extra)

    if market is None:
        market = market_data_client(environment)
        try:
            first = request(market)
        except Exception as exc:  # a cached token can expire while token.txt still says NORMAL
            if 'INVALID_TOKEN' not in str(exc):
                raise
            print('Cached token was rejected. Requesting a new token: approve 2FA in the Webull app.')
            market = market_data_client(environment, new_token=True)
            first = request(market)
    else:
        first = request(market)
    rows = _page_rows(first)
    while start and rows and min(rows) > start and len(rows) % count == 0:
        oldest = min(rows)
        end_ms = int(datetime.fromisoformat(oldest).replace(tzinfo=timezone.utc).timestamp() * 1000) - 1
        time.sleep(pause_seconds)  # Market Data API limit: 300 requests per minute
        page = _page_rows(request(market, end_ms))
        if not page or max(page) >= oldest:
            print(f'Webull ignored end_time: only the latest {len(rows)} daily bars are available.')
            break
        rows.update(page)
    return [rows[day] for day in sorted(rows) if not start or day >= start]


def save_csv(rows, path):
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def load_csv(path):
    with open(path, newline='', encoding='utf-8') as f:
        return [{'date': _session_date(r['date']) if len(r['date']) > 10 else r['date'], **{k: float(r[k]) for k in ['open', 'high', 'low', 'close']},
                 'volume': int(float(r['volume']))} for r in csv.DictReader(f)]


def lesson_bars(rows, evaluation_start='2006-09-26', warmup_bars=400, fast_span=20, slow_span=200, symbol='SPY'):
    """Build the same bar schema as lesson_14.generate_bars from any daily OHLC rows."""
    first = warmup_bars if evaluation_start is None else \
        next((i for i, row in enumerate(rows) if row['date'] >= evaluation_start), None)
    if first is None or first < warmup_bars:
        raise ValueError(f'Need {warmup_bars} bars before {evaluation_start}; got {first or 0}')
    rows = rows[first - warmup_bars:]
    bars, fast, slow = [], None, None
    af, al = 2 / (fast_span + 1), 2 / (slow_span + 1)
    for index, row in enumerate(rows):
        fast = row['close'] if fast is None else af * row['close'] + (1 - af) * fast
        slow = row['close'] if slow is None else al * row['close'] + (1 - al) * slow
        bars.append({'index': index, 'session': index - warmup_bars + 1, 'date': row['date'],
                     'barInSession': 1, **{k: row[k] for k in ['open', 'high', 'low', 'close']},
                     'volume': row['volume'], 'ema20': fast, 'ema200': slow, 'warmup': index < warmup_bars})
    evaluation = bars[warmup_bars:]
    start_day, end_day = evaluation[0]['date'], evaluation[-1]['date']
    parameters = {'symbol': symbol, 'priceUnit': 'USD per share', 'sessions': len(evaluation),
                  'warmupBars': warmup_bars, 'fastSpan': fast_span, 'slowSpan': slow_span,
                  'startDate': start_day, 'endDate': end_day,
                  'calendarYears': (date.fromisoformat(end_day) - date.fromisoformat(start_day)).days / 365.25}
    return bars, parameters


def export_backtest(csv_path, output_dir='webull-run', evaluation_start=None, symbol='SPY'):
    """Run the chapter engine on Webull bars and write trades.csv, equity-daily.csv and a report."""
    import lesson_14 as lesson
    bars, parameters = lesson_bars(load_csv(csv_path), evaluation_start, symbol=symbol)
    backtest = lesson.run_backtest(bars, parameters)
    results = lesson.make_results(backtest)
    results['provenance'] = {
        'provider': 'Webull OpenAPI', 'symbol': symbol, 'name': f'{symbol} daily bars',
        'instrumentType': 'ETF', 'priceUnit': 'USD per share', 'sourceFile': Path(csv_path).name,
        'adjustment': 'Daily bars as returned by Webull (SDK docs: daily K-lines are forward-adjusted).',
        'reportLabel': {
            'note': f'ราคารายวัน {symbol} จาก Webull OpenAPI · การซื้อขายและต้นทุนเป็นแบบจำลอง',
            'benchmark': f'Buy &amp; Hold {symbol}',
            'benchmarkNote': f'Benchmark คือการถือ {symbol} ตามราคาที่ได้จาก Webull ในช่วงเดียวกัน '}}
    results['assumptions'] = [
        f'Daily {symbol} OHLC from Webull OpenAPI (get_batch_history_bar, timespan D, RTH), saved to {Path(csv_path).name}.',
        f'Evaluate {parameters["startDate"]} through {parameters["endDate"]}. The preceding 400 daily closes initialize EMA and are excluded from performance.',
        f'Fractional {symbol} shares are modeled in USD; these are simulated fills, not realized trading profits.',
    ] + lesson.ASSUMPTIONS[3:6] + [
        'Assumed fee 0.1% per side on notional. Spread, slippage, impact, taxes and cash interest are zero.',
        lesson.ASSUMPTIONS[7], *lesson.ASSUMPTIONS[9:],
        'Benchmark holds the same shares from first open to final close with equal initial capital and equal fee rate.',
        'Prices are used as returned by Webull; check split/dividend adjustment before comparing with other sources.']
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    lesson.write_csv(output / 'ema-bars.csv', bars)
    lesson.write_csv(output / 'trades.csv', backtest['tradeLedger'])
    lesson.write_csv(output / 'equity-daily.csv', backtest['dailyEquity'])
    lesson.create_report(results, output / 'performance-report.html')
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--fetch', action='store_true', help='Request daily bars from Webull')
    parser.add_argument('--environment', choices=sorted(ENDPOINTS), default='uat')
    parser.add_argument('--symbol', default='SPY')
    parser.add_argument('--category', default='US_ETF', choices=['US_ETF', 'US_STOCK'])
    parser.add_argument('--count', type=int, default=MAX_BARS_PER_REQUEST, help='Daily bars per request (max 1200)')
    parser.add_argument('--start', default='2005-01-01', help='Try to page back to this date via end_time (undocumented for TH)')
    parser.add_argument('--output', type=Path, default=Path('webull-spy-daily.csv'))
    parser.add_argument('--backtest', type=Path, help='Run the EMA backtest on a saved Webull CSV')
    parser.add_argument('--env-file', default='.env', help='File with WEBULL_APP_KEY=... lines (never commit it)')
    parser.add_argument('--output-dir', default='webull-run')
    parser.add_argument('--evaluation-start', help='First test date (YYYY-MM-DD); default: right after 400 warmup bars')
    args = parser.parse_args()
    if args.backtest and not args.backtest.exists():
        raise SystemExit(f'{args.backtest} not found. Fetch first: python3 webull_data.py --fetch --environment production')
    if args.backtest:
        results = export_backtest(args.backtest, args.output_dir, args.evaluation_start, symbol=args.symbol)
        tm, pm = results['tradeMetrics'], results['portfolioMetrics']
        print(json.dumps({'trades': tm['count'], 'winRate': tm['winRate'], 'totalReturn': pm['totalReturn'],
                          'maxDrawdown': pm['maxDrawdown'], 'outputDir': str(Path(args.output_dir).resolve())}, indent=2))
        return
    load_env_file(args.env_file)
    if not args.fetch:
        print('No network request. Set WEBULL_APP_KEY and WEBULL_APP_SECRET locally, then run:')
        print('  python3 webull_data.py --fetch --environment production')
        return
    try:
        rows = fetch_daily_bars(args.symbol, args.count, args.category, args.environment, start=args.start)
    except KeyError:
        raise SystemExit(f'Set WEBULL_APP_KEY and WEBULL_APP_SECRET in {args.env_file} or the environment.')
    if not rows:
        raise SystemExit('No bars returned. Check symbol, category, 2FA and OpenAPI market-data permission.')
    save_csv(rows, args.output)
    print(f'Saved {len(rows)} daily bars {rows[0]["date"]} to {rows[-1]["date"]} -> {args.output}')


if __name__ == '__main__':
    main()
