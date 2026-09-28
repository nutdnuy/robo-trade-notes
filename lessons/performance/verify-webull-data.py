#!/usr/bin/env python3
"""Offline checks for webull_data.py: a fake SDK client, paging, parsing and engine parity.

Run: python3 verify-webull-data.py   (no credentials, no network)
"""
import math
import os
import sys
import tempfile
import types
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

sys.dont_write_bytecode = True
import lesson_14 as lesson
import webull_data as webull

ROOT = Path(__file__).resolve().parent

# 1. The helper pipeline reproduces the chapter numbers from the stored Webull SPY file.
bars, parameters = webull.lesson_bars(webull.load_csv(ROOT / 'data/spy-webull-daily.csv'), '2006-09-26', symbol='SPY')
reference = lesson.generate_bars()
assert len(bars) == len(reference) and parameters['sessions'] == lesson.DEFAULTS['sessions']
for a, b in zip(bars, reference):
    assert a['date'] == b['date'] and a['warmup'] == b['warmup'] and a['session'] == b['session']
    assert math.isclose(a['ema200'], b['ema200'], rel_tol=1e-12)
assert math.isclose(parameters['calendarYears'], lesson.DEFAULTS['calendarYears'], rel_tol=1e-12)
results = lesson.make_results(lesson.run_backtest(bars, parameters))
assert results['tradeMetrics']['count'] == 17
assert math.isclose(results['portfolioMetrics']['finalEquity'], 467410.19, abs_tol=0.01)
print('PASS: lesson_bars + run_backtest reproduce the published 17 trades and 467,410.19 USD.')

# 2. One documented batch request; parse the documented response shape and UTC times.
days = [date(2020, 1, 1) + timedelta(days=i) for i in range(2400)]
days = [d for d in days if d.weekday() < 5][-1200:]
calls = []


def fake_batch(**kwargs):
    calls.append(kwargs)
    bars = [{'time': f'{d.isoformat()}T20:00:00.000+0000', 'open': '10', 'high': '11', 'low': '9',
             'close': str(10 + i % 7), 'volume': '1000'} for i, d in enumerate(days)]
    payload = {'result': [{'symbol': 'SPY', 'instrument_id': '913243251', 'result': list(reversed(bars))}]}
    return types.SimpleNamespace(status_code=200, json=lambda: payload)


rows = webull.fetch_daily_bars('SPY', market=types.SimpleNamespace(get_batch_history_bar=fake_batch))
assert [r['date'] for r in rows] == [d.isoformat() for d in days]
assert calls == [dict(symbols=['SPY'], category='US_ETF', timespan='D', count=1200,
                      real_time_required=True, trading_sessions='RTH')]
assert webull._session_date('2021-12-28T09:00:09.945+0000') == '2021-12-28'
assert webull._session_date('2021-10-19 04:00:00+00:00') == '2021-10-19'
print(f'PASS: one documented bars/list request returns {len(rows)} sorted daily bars.')

# 2b. Paging with end_time: stop cleanly if the server ignores it, page back if it honours it.
all_days = [d for d in (date(2004, 1, 1) + timedelta(days=i) for i in range(8200)) if d.weekday() < 5]


def server(honours_end_time):
    seen_calls = []
    def batch(**kwargs):
        seen_calls.append(kwargs)
        end = datetime.fromtimestamp(kwargs['end_time'] / 1000, timezone.utc).date() if honours_end_time and 'end_time' in kwargs else all_days[-1]
        page = [d for d in all_days if d <= end][-kwargs['count']:]
        bars = [{'time': f'{d.isoformat()}T20:00:00.000+0000', 'open': '1', 'high': '1', 'low': '1', 'close': '1', 'volume': '1'} for d in page]
        return types.SimpleNamespace(status_code=200, json=lambda: {'result': [{'symbol': 'SPY', 'result': bars}]})
    return types.SimpleNamespace(get_batch_history_bar=batch), seen_calls


fake, seen_calls = server(False)
with patch('builtins.print'):
    rows = webull.fetch_daily_bars('SPY', market=fake, start='2005-01-01', pause_seconds=0)
assert len(rows) == 1200 and len(seen_calls) == 2 and 'end_time' not in seen_calls[0]
fake, seen_calls = server(True)
rows = webull.fetch_daily_bars('SPY', market=fake, start='2005-01-01', pause_seconds=0)
assert rows[0]['date'] >= '2005-01-01' and rows[0]['date'] <= '2005-01-10' and rows[-1]['date'] == all_days[-1].isoformat()
assert len({r['date'] for r in rows}) == len(rows) == len([d for d in all_days if d.isoformat() >= '2005-01-01'])
print(f'PASS: end_time paging stops after 1 extra call if ignored; pages back to {rows[0]["date"]} if honoured.')

# 3. SDK wiring: region, endpoint and credentials from the environment only.
seen = {}


class FakeApiClient:
    def __init__(self, key, secret, region): seen.update(key=key, region=region)
    def add_endpoint(self, region, host): seen['host'] = host
    def set_stream_logger(self, **kwargs): pass
    def set_token_dir(self, path): seen['token_dir'] = path
    def set_token(self, token): seen['token'] = token


class FakeDataClient:
    def __init__(self, client): self.market_data = 'new-token-market'


class FakeMarketData:
    def __init__(self, client): self.kind = 'cached-token-market'


modules = {name: types.ModuleType(name) for name in
           ['webull', 'webull.core', 'webull.core.client', 'webull.data', 'webull.data.data_client',
            'webull.data.quotes', 'webull.data.quotes.market_data']}
modules['webull.core.client'].ApiClient = FakeApiClient
modules['webull.data.data_client'].DataClient = FakeDataClient
modules['webull.data.quotes.market_data'].MarketData = FakeMarketData
with tempfile.TemporaryDirectory() as tmp, patch.dict(sys.modules, modules), \
        patch.dict(os.environ, {'WEBULL_APP_KEY': 'TEST_ONLY', 'WEBULL_APP_SECRET': 'TEST_ONLY'}):
    assert webull.market_data_client('production', tmp) == 'new-token-market'
    Path(tmp, 'token.txt').write_text('TEST_TOKEN\n0\nNORMAL\n', encoding='utf-8')
    assert webull.market_data_client('production', tmp).kind == 'cached-token-market'
assert seen['region'] == 'th' and seen['host'] == 'api.webull.co.th' and seen['token'] == 'TEST_TOKEN'
print('PASS: SDK client uses region th, the selected endpoint, and reuses a NORMAL cached token.')

# 3b. An expired cached token (401 INVALID_TOKEN) falls back to a new token once.
made = []


def fake_client(environment='uat', token_dir=None, new_token=False):
    made.append(new_token)
    def batch(**kwargs):
        if not new_token:
            raise RuntimeError('HTTP Status: 401, Code: INVALID_TOKEN, Msg: Header x-access-token is missing or invalid.')
        return types.SimpleNamespace(status_code=200, json=lambda: {'result': [{'symbol': 'SPY', 'result': [
            {'time': '2026-09-25T20:00:00.000+0000', 'open': '1', 'high': '1', 'low': '1', 'close': '1', 'volume': '1'}]}]})
    return types.SimpleNamespace(get_batch_history_bar=batch)


with patch.object(webull, 'market_data_client', fake_client), patch('builtins.print'):
    assert webull.fetch_daily_bars('SPY', environment='production')[0]['date'] == '2026-09-25'
assert made == [False, True]
print('PASS: an expired cached token triggers exactly one new-token request.')

# 4. export_backtest writes the files the chapter code reads.
with tempfile.TemporaryDirectory() as tmp:
    csv_path = Path(tmp) / 'bars.csv'
    webull.save_csv(webull.load_csv(ROOT / 'data/spy-webull-daily.csv'), csv_path)
    exported = webull.export_backtest(csv_path, Path(tmp) / 'webull-run', '2006-09-26', symbol='SPY')
    for name in ['trades.csv', 'equity-daily.csv', 'ema-bars.csv', 'performance-report.html']:
        assert (Path(tmp) / 'webull-run' / name).exists(), name
    report = (Path(tmp) / 'webull-run/performance-report.html').read_text(encoding='utf-8')
    assert 'Webull OpenAPI' in report and '^GSPC' not in report
    assert exported['tradeMetrics']['count'] == 17
print('PASS: export_backtest writes trades.csv, equity-daily.csv, ema-bars.csv and a Webull-labelled report.')
