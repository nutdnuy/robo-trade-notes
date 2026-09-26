#!/usr/bin/env python3
"""Independent audit of the historical S&P 500 EMA backtest, execution timing and exports.

Run after lesson_14.py: python3 verify-ema.py
Uses only Python's standard library and local files. Includes source snapshot, coverage and OHLC integrity checks.
"""
import copy
import itertools
import json
import math
from pathlib import Path
import sys

sys.dont_write_bytecode = True
import lesson_14 as lesson

ROOT = Path(__file__).resolve().parent
CHECKS = 0


def close(a, b, label='', relative=1e-10, absolute=1e-8):
    global CHECKS
    CHECKS += 1
    assert math.isfinite(a) and math.isfinite(b), label
    assert math.isclose(a, b, rel_tol=relative, abs_tol=absolute), f'{label}: {a} != {b}'


def reference_statistics(values, annualization=252):
    """Direct formulas, without the production statistics/drawdown functions."""
    returns = [(values[i] - values[i - 1]) / values[i - 1] for i in range(1, len(values))]
    n = len(returns)
    mean = sum(returns) / n
    variance = sum((value - mean) ** 2 for value in returns) / (n - 1)
    downside = math.sqrt(sum(value * value if value < 0 else 0 for value in returns) / n)
    peaks = list(itertools.accumulate(values, max))
    drawdowns = [(value - peak) / peak for value, peak in zip(values, peaks)]
    return {'totalReturn': (values[-1] - values[0]) / values[0],
            'cagr': math.exp(math.log(values[-1] / values[0]) / lesson.DEFAULTS['calendarYears']) - 1,
            'meanReturn': mean, 'sampleStd': math.sqrt(variance),
            'annualizedVolatility': math.sqrt(variance * annualization),
            'downsideDeviation': downside,
            'sharpe': mean / math.sqrt(variance) * math.sqrt(annualization),
            'sortino': mean / downside * math.sqrt(annualization),
            'maxDrawdown': min(drawdowns)}


def main():
    import hashlib, csv, datetime
    raw = (ROOT/'data/sp500-yahoo-raw.json').read_bytes()
    provenance = json.loads((ROOT/'data/provenance.json').read_text())
    assert hashlib.sha256(raw).hexdigest()==provenance['rawSHA256']
    assert hashlib.sha256((ROOT/'data/sp500-daily.csv').read_bytes()).hexdigest()==provenance['csvSHA256']
    provider = json.loads(raw)['chart']['result'][0]
    assert provider['meta']['symbol']=='^GSPC' and provider['meta']['instrumentType']=='INDEX'
    quotes=provider['indicators']['quote'][0]
    original={datetime.datetime.fromtimestamp(ts,datetime.timezone.utc).date().isoformat():
              {k: quotes[k][i] for k in ['open','high','low','close','volume']}
              for i,ts in enumerate(provider['timestamp'])}
    bars = lesson.generate_bars()
    for bar in bars:
        for key in ['open','high','low','close','volume']:close(bar[key],original[bar['date']][key],'source '+key)
    assert max(original)==provenance['evaluationEnd']
    assert provenance['evaluationEnd']<='2026-09-26'

    assert bars == lesson.generate_bars(), 'generation must be deterministic'
    assert bars == lesson.load_bars(ROOT / 'ema-bars.csv'), 'CSV must preserve full precision'
    p = lesson.DEFAULTS
    assert len(bars) == 400 + 5031
    assert sum(row['warmup'] for row in bars) == 400
    assert bars[400]['date']=='2006-09-26' and bars[-1]['date']=='2026-09-25'
    assert len({row['date'] for row in bars})==len(bars)
    assert [row['date'] for row in bars]==sorted(row['date'] for row in bars)
    assert all(row['low'] <= min(row['open'], row['close']) <= max(row['open'], row['close']) <= row['high'] for row in bars)
    fast, slow = bars[0]['close'], bars[0]['close']
    for i, row in enumerate(bars):
        if i:
            fast += (row['close'] - fast) * (2 / 21)
            slow += (row['close'] - slow) * (2 / 201)
        close(row['ema20'], fast, f'EMA20 {i}')
        close(row['ema200'], slow, f'EMA200 {i}')

    bt = lesson.run_backtest(bars)
    result = lesson.make_results(bt)
    saved = json.loads((ROOT / 'ema-results.json').read_text())
    assert result == saved, 'results JSON must match current engine and parameters'
    assert len(bt['dailyEquity']) == 5031
    assert len(bt['observations']) == 5031
    assert len(bt['tradeLedger']) == 19
    assert len(bt['transactions']) == 38
    assert bt['finalUnits'] == 0
    assert saved['forcedExitCount'] == 1
    assert saved['tradeMetrics']['wins'] == 8
    assert saved['tradeMetrics']['losses'] == 11
    assert saved['tradeMetrics']['totalPnl'] > 0
    assert saved['tradeMetrics']['winRate'] < .5

    # Independent cash ledger: replay executions, not desired targets or production balances.
    cash, units = p['initialEquity'], 0.0
    by_bar = {}
    for tx in bt['transactions']:
        by_bar.setdefault(tx['bar'], []).append(tx)
        assert tx['bar'] >= p['warmupBars']
        if tx['reason'] == 'signal':
            assert tx['decisionBar'] + 1 == tx['bar'], 'decision must precede execution by one bar'
            prior = bars[tx['decisionBar']]
            assert (prior['ema20'] > prior['ema200']) == (tx['side'] == 'buy')
            assert tx['point'] == 'open'
            close(tx['price'], bars[tx['bar']]['open'], 'execute next open')
        close(tx['fee'], tx['quantity'] * tx['price'] * .001, 'proportional fee')
    for observation in bt['observations']:
        for tx in by_bar.get(observation['bar'], []):
            if tx['side'] == 'buy':
                assert units == 0
                close(tx['quantity'], cash / (tx['price'] * 1.001), 'all-in, no borrowing')
                cash -= tx['quantity'] * tx['price'] + tx['fee']
                units += tx['quantity']
            else:
                close(tx['quantity'], units, 'sell all holdings')
                cash += tx['quantity'] * tx['price'] - tx['fee']
                units -= tx['quantity']
            assert cash > -1e-7 and units >= 0
        close(observation['equity'], cash + units * observation['close'], 'mark to market')
        close(observation['cash'], cash, 'cash ledger')
        close(observation['units'], units, 'position ledger')
    close(cash, saved['portfolioMetrics']['finalEquity'], 'final cash')
    for trade in bt['tradeLedger']:
        close(trade['grossPnl'], trade['quantity'] * (trade['exitPrice'] - trade['entryPrice']), 'gross trade P&L')
        close(trade['totalFees'], trade['entryFee'] + trade['exitFee'], 'both-side fees')
        close(trade['netPnl'], trade['grossPnl'] - trade['totalFees'], 'net trade P&L')
        close(trade['equityAfterExit'] - trade['entryEquityBefore'], trade['netPnl'], 'trade cash change')
    tm = saved['tradeMetrics']
    close(tm['totalPnl'], saved['portfolioMetrics']['finalEquity'] - p['initialEquity'], 'sum P&L reconciles equity')
    close(tm['grossPnlBeforeFees'] - tm['totalFees'], tm['totalPnl'], 'net after fees')
    close(tm['expectancy'], tm['winRate'] * tm['averageWin'] - tm['lossRate'] * tm['averageLoss'], 'expectancy identity')
    close(tm['expectancy'] * tm['count'], tm['totalPnl'], 'expectancy × count')
    close(tm['profitFactor'], tm['winRate'] / tm['lossRate'] * tm['payoffRatio'], 'PF identity')

    evaluation = bars[p['warmupBars']:]
    benchmark_final = p['initialEquity'] * evaluation[-1]['close'] / evaluation[0]['open'] * .999 / 1.001
    close(saved['benchmarkMetrics']['finalEquity'], benchmark_final, 'benchmark includes both-side costs')
    close(saved['benchmarkMetrics']['totalFees'], bt['benchmarkEntryFee'] + bt['benchmarkExitFee'], 'benchmark fee sum')
    for column, section in [('equity', 'portfolioMetrics'), ('benchmarkEquity', 'benchmarkMetrics')]:
        values = [p['initialEquity']] + [row[column] for row in bt['dailyEquity']]
        reference = reference_statistics(values)
        for key, value in reference.items():
            close(saved[section][key], value, f'independent {section}.{key}')
        product = math.prod(values[i] / values[i - 1] for i in range(1, len(values)))
        close(product, values[-1] / values[0], 'compounding reconciliation')
    intraday_values = [p['initialEquity']] + [row['equity'] for row in bt['observations']]
    peaks = itertools.accumulate(intraday_values, max)
    close(saved['sampling']['daily']['maxDrawdown'], min((value - peak) / peak for value, peak in zip(intraday_values, peaks)), 'independent daily MDD')
    assert saved['sampling']['daily']['maxDrawdown'] <= saved['portfolioMetrics']['maxDrawdown']
    assert saved['portfolioMetrics']['maxDrawdownPeakIndex'] == 900
    assert saved['portfolioMetrics']['maxDrawdownTroughIndex'] == 1325
    assert saved['portfolioMetrics']['maxDrawdownRecoveryIndex'] == 1757
    assert saved['portfolioMetrics']['underwaterPeriodsToEnd'] == 30

    # A changed future cannot change trades/equity before that future arrives.
    cutoff = bt['tradeLedger'][2]['exitExecutionBar'] + 10
    changed = copy.deepcopy(bars)
    for row in changed[cutoff + 1:]:
        for key in ['open', 'high', 'low', 'close']:
            row[key] *= 1.17
    for i in range(cutoff + 1, len(changed)):
        changed[i]['ema20'] = changed[i - 1]['ema20'] + (changed[i]['close'] - changed[i - 1]['ema20']) * 2 / 21
        changed[i]['ema200'] = changed[i - 1]['ema200'] + (changed[i]['close'] - changed[i - 1]['ema200']) * 2 / 201
    future_test = lesson.run_backtest(changed)
    assert [x for x in future_test['transactions'] if x['bar'] <= cutoff] == [x for x in bt['transactions'] if x['bar'] <= cutoff]
    assert [x for x in future_test['observations'] if x['bar'] <= cutoff] == [x for x in bt['observations'] if x['bar'] <= cutoff]

    # End-of-test treatment is exercised on a truncated, still-open position.
    end = bt['tradeLedger'][0]['entryExecutionBar'] + 5
    forced = lesson.run_backtest(bars[:end + 1])
    assert len(forced['tradeLedger']) == 1
    assert forced['tradeLedger'][0]['exitReason'] == 'forced_end'
    assert forced['transactions'][-1]['point'] == 'close'
    assert forced['transactions'][-1]['decisionBar'] is None
    assert forced['finalUnits'] == 0
    close(forced['transactions'][-1]['price'], bars[end]['close'], 'forced final close')
    close(forced['tradeLedger'][0]['netPnl'], forced['finalCash'] - p['initialEquity'], 'forced exit reconciliation')
    one_bar = lesson.run_backtest([
        {'index': 0, 'session': 0, 'date': '2020-01-02', 'barInSession': 1, 'warmup': True, 'ema20': 101, 'ema200': 100, 'open': 100, 'close': 100},
        {'index': 1, 'session': 1, 'date': '2020-01-03', 'barInSession': 1, 'warmup': False, 'ema20': 101, 'ema200': 100, 'open': 100, 'close': 101},
    ])
    assert one_bar['tradeLedger'][0]['holdingBars'] == 1
    assert one_bar['dailyEquity'][0]['exposureBars'] == 1
    assert one_bar['observations'][0]['exposedDuringBar'] is True
    assert one_bar['finalUnits'] == 0

    # Removing fees changes future position sizes: adding fees back is not a no-fee rerun.
    no_fee = lesson.run_backtest(bars, {'feeRatePerSide': 0})
    assert all(x['fee'] == 0 for x in no_fee['transactions'])
    assert [(x['bar'], x['side']) for x in no_fee['transactions']] == [(x['bar'], x['side']) for x in bt['transactions']]
    assert no_fee['finalCash'] > bt['finalCash']
    assert not math.isclose(no_fee['finalCash'], bt['finalCash'] + tm['totalFees'], abs_tol=1e-6)

    assert lesson.trade_metrics([])['expectancy'] is None
    assert lesson.trade_metrics([1, 2])['profitFactor'] is None
    assert lesson.trade_metrics([-1, -2])['profitFactor'] == 0
    assert lesson.trade_metrics([0, 0])['winRate'] == 0
    assert lesson.trade_metrics([1, -1, 0])['breakevens'] == 1
    flat = lesson.portfolio_metrics([100, 100, 100])
    assert flat['sharpe'] is None and flat['sortino'] is None and flat['sampleStd'] == 0
    assert lesson.portfolio_metrics([100, 101, 103])['sortino'] is None
    assert lesson.portfolio_metrics([100])['cagr'] is None
    recovery = lesson.drawdown_metrics([100, 120, 90, 95, 120])
    close(recovery['maxDrawdown'], -.25, 'known recovery fixture')
    assert recovery['peakToRecoveryPeriods'] == 3 and recovery['troughToRecoveryPeriods'] == 2
    for bad in ([], [100, 0], [100, -1], [100, float('nan')]):
        try:
            lesson.portfolio_metrics(bad)
            raise AssertionError('invalid equity accepted')
        except ValueError:
            pass
    (ROOT/'qa/sp500-numeric.json').write_text(json.dumps({'status':'passed','checks':CHECKS,'sourceHashesVerified':True,'rawOHLCCompared':len(bars),'evaluationBars':len(bt['dailyEquity']),'firstDate':bars[400]['date'],'lastDate':bars[-1]['date'],'independentCashReplay':True,'futureMutationCausality':True},indent=2)+'\n')
    print(f'PASS: {CHECKS:,} numeric comparisons plus determinism, CSV precision, EMA recurrence, no-lookahead timing, ledger reconciliation, benchmark costs, daily risk, future-mutation causality, final liquidation and undefined-metric cases.')
    print(f'No-fee rerun final equity (separate diagnostic only): {no_fee["finalCash"]:,.8f}')


if __name__ == '__main__':
    main()
