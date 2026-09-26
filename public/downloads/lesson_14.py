#!/usr/bin/env python3
"""Reproducible EMA20/EMA200 teaching backtest on historical S&P 500 daily OHLC.
Run: python3 lesson_14.py --output-dir .
The frozen market-data CSV is read locally; fills and costs are modeled.
"""
import argparse
import csv
import html
import json
import math
import statistics
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / 'data'
PROVENANCE = json.loads((DATA_DIR / 'provenance.json').read_text(encoding='utf-8'))
DEFAULTS = {
    'initialEquity': 100000.0, 'currency': 'USD', 'priceUnit': 'index points',
    'frequency': 'daily', 'barsPerSession': 1, 'sessions': PROVENANCE['evaluationBars'],
    'warmupBars': PROVENANCE['warmupBars'], 'fastSpan': 20, 'slowSpan': 200,
    'feeRatePerSide': 0.001, 'periodsPerYear': 252, 'riskFreeAnnual': 0.0, 'marAnnual': 0.0,
    'startDate': PROVENANCE['evaluationStart'], 'endDate': PROVENANCE['evaluationEnd'],
    'calendarYears': PROVENANCE['calendarYears'], 'symbol': '^GSPC',
}
ASSUMPTIONS = [
    'Historical daily S&P 500 Price Index (^GSPC) OHLC from Yahoo Finance; source snapshot and hashes accompany the files.',
    'Evaluate 2006-09-26 through 2026-09-25. The preceding 400 daily closes initialize EMA and are excluded from performance.',
    'The index itself cannot be bought. Fractional index exposure is modeled in USD at one USD per index point per unit; these are simulated fills, not realized trading profits.',
    'EMA20 and EMA200 use daily closes, seeded at the first warmup close. Target 100% long when fast EMA exceeds slow EMA, otherwise cash. Execute changes at the next trading day open.',
    'At the first evaluation open, act on the last warmup signal; this first entry need not be a new crossover inside the evaluation window.',
    'Fractional units, no borrowing, no shorting, no deposits or withdrawals. Entry quantity includes buy fees in the cash budget.',
    'Assumed fee 0.1% per side on notional. Spread, slippage, impact, taxes and cash interest are zero. Price-index returns exclude dividends; no currency conversion is applied.',
    'Force any remaining position closed at the final close and mark forced_end, including its sell fee. This is a boundary convention, not an EMA exit signal.',
    'Benchmark holds the same price-index exposure from first open to final close with equal initial capital and equal fee rate.',
    'CAGR uses elapsed calendar days / 365.25. Risk metrics use all daily close-to-close portfolio returns (including cash days), sample SD and sqrt(252). First return is initial open capital to first close.',
    'Sharpe risk-free and Sortino MAR default to zero as assumptions, not historical Treasury rates. Downside squared deviations divide by all observations.',
    'Drawdown uses daily closing equity and cannot reveal the complete intraday path. Recovery durations count trading days.',
]


def generate_bars(parameters=None):
    """Read the frozen historical CSV and calculate EMA; never synthesize prices."""
    p = dict(DEFAULTS, **(parameters or {}))
    with (DATA_DIR / 'sp500-daily.csv').open(newline='', encoding='utf-8') as f:
        source = list(csv.DictReader(f))
    bars, fast, slow = [], None, None
    af, al = 2 / (p['fastSpan'] + 1), 2 / (p['slowSpan'] + 1)
    for index, row in enumerate(source):
        close = float(row['close'])
        fast = close if fast is None else af * close + (1-af) * fast
        slow = close if slow is None else al * close + (1-al) * slow
        bars.append({'index': index, 'session': index-p['warmupBars']+1,
                     'date': row['date'], 'barInSession': 1,
                     **{k: float(row[k]) for k in ['open','high','low','close']},
                     'volume': int(row['volume']), 'ema20': fast, 'ema200': slow,
                     'warmup': index < p['warmupBars']})
    return bars


def load_bars(path):
    """Load the exported historical OHLC+EMA CSV without a network request."""
    with open(path, newline='', encoding='utf-8') as source:
        rows = list(csv.DictReader(source))
    for row in rows:
        for key, value in row.items():
            if key in {'index', 'session', 'barInSession', 'volume'}:
                row[key] = int(value)
            elif key == 'warmup':
                row[key] = value.lower() == 'true'
            elif key != 'date':
                row[key] = float(value)
    return rows


def clock_label(bar, point='open'):
    return f"{bar['date']} {point}"


def run_backtest(bars, parameters=None):
    """Execute only previous-close target at current open. Warmup never trades."""
    p = dict(DEFAULTS, **(parameters or {}))
    fee_rate = p['feeRatePerSide']
    if not 0 <= fee_rate < 1:
        raise ValueError('feeRatePerSide must be in [0, 1)')
    if p['initialEquity'] <= 0:
        raise ValueError('initialEquity must be positive')
    evaluation = [bar for bar in bars if not bar['warmup']]
    if not evaluation:
        raise ValueError('evaluation bars are required')
    lookup = {bar['index']: bar for bar in bars}
    cash, units = p['initialEquity'], 0.0
    ledger, transactions, observations = [], [], []
    active = None
    benchmark_units = p['initialEquity'] / (evaluation[0]['open'] * (1 + fee_rate))
    benchmark_entry_fee = benchmark_units * evaluation[0]['open'] * fee_rate

    def buy(bar, decision):
        nonlocal cash, units, active
        before = cash
        units = before / (bar['open'] * (1 + fee_rate))
        notional = units * bar['open']
        entry_fee = notional * fee_rate
        cash = before - notional - entry_fee
        if abs(cash) < 1e-8:
            cash = 0.0
        active = {'id': f'T{len(ledger) + 1}', 'entryDecisionBar': decision,
                  'entryExecutionBar': bar['index'], 'entrySession': bar['session'],
                  'entryTime': clock_label(bar), 'entryPrice': bar['open'],
                  'quantity': units, 'entryNotional': notional, 'entryFee': entry_fee,
                  'entryEquityBefore': before}
        transactions.append({'tradeId': active['id'], 'side': 'buy', 'bar': bar['index'],
                             'point': 'open', 'decisionBar': decision, 'price': bar['open'],
                             'quantity': units, 'notional': notional, 'fee': entry_fee,
                             'cashAfter': cash, 'unitsAfter': units, 'reason': 'signal'})

    def sell(bar, price, reason, decision):
        nonlocal cash, units, active
        notional = units * price
        exit_fee = notional * fee_rate
        cash += notional - exit_fee
        gross_pnl = units * (price - active['entryPrice'])
        net_pnl = gross_pnl - active['entryFee'] - exit_fee
        point = 'close' if reason == 'forced_end' else 'open'
        active.update({'exitDecisionBar': decision, 'exitExecutionBar': bar['index'],
                       'exitSession': bar['session'], 'exitTime': clock_label(bar, point),
                       'exitPrice': price, 'exitNotional': notional, 'exitFee': exit_fee,
                       'totalFees': active['entryFee'] + exit_fee,
                       'grossPnl': gross_pnl, 'netPnl': net_pnl,
                       'returnOnEntryEquity': net_pnl / active['entryEquityBefore'],
                       'holdingBars': bar['index'] - active['entryExecutionBar'] + (reason == 'forced_end'),
                       'holdingSessions': (bar['index'] - active['entryExecutionBar'] + (reason == 'forced_end')) / p['barsPerSession'],
                       'exitReason': reason, 'equityAfterExit': cash})
        ledger.append(active)
        transactions.append({'tradeId': active['id'], 'side': 'sell', 'bar': bar['index'],
                             'point': point, 'decisionBar': decision, 'price': price,
                             'quantity': units, 'notional': notional, 'fee': exit_fee,
                             'cashAfter': cash, 'unitsAfter': 0.0, 'reason': reason})
        active, units = None, 0.0

    for bar in evaluation:
        previous = lookup.get(bar['index'] - 1)
        target = 1 if previous and previous['ema20'] > previous['ema200'] else 0
        decision = previous['index'] if previous else None
        if target == 1 and units == 0:
            buy(bar, decision)
        elif target == 0 and units > 0:
            sell(bar, bar['open'], 'signal', decision)
        exposed_during_bar = units > 0
        benchmark = benchmark_units * bar['close']
        if bar is evaluation[-1]:
            if units > 0:
                sell(bar, bar['close'], 'forced_end', None)
            benchmark *= 1 - fee_rate
        observations.append({'bar': bar['index'], 'session': bar['session'], 'date': bar['date'],
                             'barInSession': bar['barInSession'], 'equity': cash + units * bar['close'],
                             'benchmarkEquity': benchmark, 'target': target,
                             'units': units, 'cash': cash, 'close': bar['close'],
                             'exposedDuringBar': exposed_during_bar})
    daily = []
    previous_equity = previous_benchmark = p['initialEquity']
    session_rows = []
    for i, row in enumerate(observations):
        session_rows.append(row)
        if i == len(observations) - 1 or observations[i + 1]['session'] != row['session']:
            daily.append({'session': row['session'], 'date': row['date'], 'equity': row['equity'],
                          'benchmarkEquity': row['benchmarkEquity'],
                          'dailyReturn': row['equity'] / previous_equity - 1,
                          'benchmarkReturn': row['benchmarkEquity'] / previous_benchmark - 1,
                          'close': row['close'], 'exposureBars': sum(x['exposedDuringBar'] for x in session_rows)})
            previous_equity, previous_benchmark = row['equity'], row['benchmarkEquity']
            session_rows = []
    benchmark_exit_fee = benchmark_units * evaluation[-1]['close'] * fee_rate
    return {'parameters': p, 'tradeLedger': ledger, 'transactions': transactions,
            'observations': observations, 'dailyEquity': daily,
            'benchmarkUnits': benchmark_units, 'benchmarkEntryFee': benchmark_entry_fee,
            'benchmarkExitFee': benchmark_exit_fee,
            'benchmarkTotalFees': benchmark_entry_fee + benchmark_exit_fee,
            'finalCash': cash, 'finalUnits': units}


def trade_metrics(pnls):
    positive = [x for x in pnls if x > 0]
    negative = [-x for x in pnls if x < 0]
    n = len(pnls)
    aw, al = (statistics.mean(positive) if positive else None), (statistics.mean(negative) if negative else None)
    return {'count': n, 'wins': len(positive), 'losses': len(negative),
            'breakevens': n - len(positive) - len(negative),
            'winRate': len(positive) / n if n else None,
            'lossRate': len(negative) / n if n else None,
            'breakevenRate': (n - len(positive) - len(negative)) / n if n else None,
            'grossProfit': sum(positive), 'grossLoss': sum(negative),
            'averageWin': aw, 'averageLoss': al,
            'payoffRatio': aw / al if aw is not None and al is not None else None,
            'expectancy': statistics.mean(pnls) if n else None,
            'profitFactor': sum(positive) / sum(negative) if negative else None,
            'totalPnl': sum(pnls),
            'breakEvenWinRate': al / (aw + al) if aw is not None and al is not None else None}


def drawdown_metrics(equity):
    peak, peak_index = equity[0], 0
    active, episodes, drawdowns = None, [], [0.0]
    for index, value in enumerate(equity[1:], 1):
        if value >= peak:
            if active is not None:
                active.update(recoveryIndex=index, peakToRecoveryPeriods=index - active['peakIndex'],
                              troughToRecoveryPeriods=index - active['troughIndex'])
                episodes.append(active)
                active = None
            peak, peak_index = value, index
            drawdowns.append(0.0)
        else:
            depth = value / peak - 1
            drawdowns.append(depth)
            if active is None:
                active = {'peakIndex': peak_index, 'troughIndex': index, 'recoveryIndex': None,
                          'depth': depth, 'peakToRecoveryPeriods': None, 'troughToRecoveryPeriods': None}
            elif depth < active['depth']:
                active.update(troughIndex=index, depth=depth)
    if active is not None:
        episodes.append(active)
    worst = min(episodes, key=lambda x: x['depth']) if episodes else None
    return {'drawdowns': drawdowns, 'maxDrawdown': worst['depth'] if worst else 0,
            'maxDrawdownPeakIndex': worst['peakIndex'] if worst else None,
            'maxDrawdownTroughIndex': worst['troughIndex'] if worst else None,
            'maxDrawdownRecoveryIndex': worst['recoveryIndex'] if worst else None,
            'peakToRecoveryPeriods': worst['peakToRecoveryPeriods'] if worst else None,
            'troughToRecoveryPeriods': worst['troughToRecoveryPeriods'] if worst else None,
            'underwaterPeriodsToEnd': len(equity) - 1 - active['peakIndex'] if active else 0,
            'maxDrawdownObservedPeriodsToEnd': len(equity) - 1 - worst['peakIndex'] if worst and worst['recoveryIndex'] is None else None,
            'episodes': episodes}


def portfolio_metrics(equity, periods_per_year=252, risk_free_annual=0, mar_annual=0, years=None):
    if not equity or any(not math.isfinite(x) or x <= 0 for x in equity):
        raise ValueError('Equity must be positive and finite, including initial equity')
    returns = [b / a - 1 for a, b in zip(equity, equity[1:])]
    n = len(returns)
    average = statistics.mean(returns) if n else None
    sd = statistics.stdev(returns) if n > 1 else None
    rf = (1 + risk_free_annual) ** (1 / periods_per_year) - 1
    mar = (1 + mar_annual) ** (1 / periods_per_year) - 1
    downside = math.sqrt(sum(min(r - mar, 0) ** 2 for r in returns) / n) if n else None
    return {'periods': n, 'periodsPerYear': periods_per_year,
            'totalReturn': equity[-1] / equity[0] - 1,
            'cagr': (equity[-1] / equity[0]) ** (1 / years if years else periods_per_year / n) - 1 if n else None,
            'returns': returns, 'meanReturn': average, 'sampleStd': sd,
            'annualizedVolatility': sd * math.sqrt(periods_per_year) if sd is not None else None,
            'riskFreePeriod': rf, 'marPeriod': mar, 'meanExcessReturn': average - rf if n else None,
            'sharpe': (average - rf) / sd * math.sqrt(periods_per_year) if sd is not None and sd > 1e-15 else None,
            'downsideDeviation': downside,
            'sortino': (average - mar) / downside * math.sqrt(periods_per_year) if downside is not None and downside > 1e-15 else None,
            **drawdown_metrics(equity)}


def make_results(backtest):
    p, daily = backtest['parameters'], backtest['dailyEquity']
    initial = p['initialEquity']
    trade = trade_metrics([row['netPnl'] for row in backtest['tradeLedger']])
    fees = sum(row['fee'] for row in backtest['transactions'])
    trade.update(totalFees=fees, positiveTradePnl=trade['grossProfit'], negativeTradePnl=trade['grossLoss'],
                 grossPnlBeforeFees=sum(row['grossPnl'] for row in backtest['tradeLedger']))
    strategy = portfolio_metrics([initial] + [row['equity'] for row in daily], p['periodsPerYear'], p['riskFreeAnnual'], p['marAnnual'], p['calendarYears'])
    benchmark = portfolio_metrics([initial] + [row['benchmarkEquity'] for row in daily], p['periodsPerYear'], p['riskFreeAnnual'], p['marAnnual'], p['calendarYears'])
    for metrics, field, cost in [(strategy, 'equity', fees), (benchmark, 'benchmarkEquity', backtest['benchmarkTotalFees'])]:
        metrics.update(initialEquity=initial, finalEquity=daily[-1][field], totalFees=cost, frequency='daily',
                       annualizationConvention='CAGR: calendar days / 365.25; risk: 252 trading days/year, sample SD, sqrt(252)')
    daily_dd = drawdown_metrics([initial] + [row['equity'] for row in daily])
    daily_dd['periodUnit'] = 'trading days'
    return {'schemaVersion': 3, 'provenance': PROVENANCE, 'parameters': p, 'assumptions': ASSUMPTIONS,
            'tradeMetrics': trade, 'portfolioMetrics': strategy, 'benchmarkMetrics': benchmark,
            'sampling': {'daily': daily_dd, 'note': 'Daily closing equity cannot measure the full intraday path.'},
            'handExamples': {'firstWinner': next((x for x in backtest['tradeLedger'] if x['netPnl'] > 0), None),
                             'firstLoser': next((x for x in backtest['tradeLedger'] if x['netPnl'] < 0), None),
                             'firstDailyReturn': daily[0],
                             'firstNonzeroDailyReturn': next((x for x in daily if x['dailyReturn'] != 0), None)},
            'tradeLedger': backtest['tradeLedger'], 'transactions': backtest['transactions'], 'dailyEquity': daily,
            'transactionCount': len(backtest['transactions']),
            'forcedExitCount': sum(x['exitReason'] == 'forced_end' for x in backtest['tradeLedger']),
            'benchmarkExecution': {'quantity': backtest['benchmarkUnits'], 'entryFee': backtest['benchmarkEntryFee'],
                                   'exitFee': backtest['benchmarkExitFee'], 'totalFees': backtest['benchmarkTotalFees']},
            'metricConventions': {
                'totalReturn': 'finalEquity / initialEquity - 1', 'cagr': '(final / initial) ** (1 / calendarYears) - 1',
                'winRate': 'positive net closed trades / all closed trades',
                'averageLoss': 'positive magnitude of average negative net trade P&L',
                'expectancy': 'mean net P&L per closed trade = pWin × averageWin - pLoss × averageLoss',
                'profitFactor': 'sum positive net trade P&L / absolute sum negative net trade P&L',
                'sharpe': 'mean daily excess return / sample daily std × sqrt(252)',
                'sortino': '(mean daily return - daily MAR) / sqrt(sum(min(r-MAR,0)^2)/allDays) × sqrt(252)',
                'maxDrawdown': 'minimum equity / running peak - 1, reported as a negative number',
                'undefined': 'null means unavailable or undefined, never automatically zero or infinite'},
            'files': ['lesson_14.py', 'ema-data.json', 'ema-results.json', 'ema-bars.csv', 'trades.csv', 'equity-daily.csv', 'performance-report.html', 'verify-ema.py']}


def write_csv(path, rows):
    if not rows:
        path.write_text('', encoding='utf-8')
        return
    with path.open('w', encoding='utf-8', newline='') as output:
        writer = csv.DictWriter(output, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def create_report(results, path):
    """Small standalone HTML report; generated from the same daily results as CSV."""
    p, pm, bm, tm = results['parameters'], results['portfolioMetrics'], results['benchmarkMetrics'], results['tradeMetrics']
    percent = lambda x: 'คำนวณไม่ได้' if x is None else f'{x * 100:,.2f}%'
    number = lambda x: 'คำนวณไม่ได้' if x is None else f'{x:,.2f}'
    daily = results['dailyEquity']
    equity = [[p['initialEquity']] + [x[key] for x in daily] for key in ('equity', 'benchmarkEquity')]
    dds = [pm['drawdowns'], bm['drawdowns']]

    def plot(series, title, percentage=False, zero_ceiling=False):
        width, height, left, top, right, bottom = 860, 275, 85, 20, 60, 43
        low, high = min(min(s) for s in series), max(max(s) for s in series)
        span = max(high - low, 1e-9)
        low -= span * 0.08
        high += span * 0.08
        if zero_ceiling:
            high = 0.0
        xscale = lambda i: left + i / (len(series[0]) - 1) * (width - left - right)
        yscale = lambda v: top + (high - v) / (high - low) * (height - top - bottom)
        content = []
        for fraction in [0, .25, .5, .75, 1]:
            value = low + (high - low) * fraction
            y = yscale(value)
            label = f'{value * 100:.1f}%' if percentage else f'{value:,.0f}'
            content.append(f'<line x1="{left}" x2="{width-right}" y1="{y}" y2="{y}" stroke="#dde2ea"/><text x="{left-8}" y="{y+4}" text-anchor="end">{label}</text>')
        if percentage and not zero_ceiling:
            content.append(f'<line x1="{left}" x2="{width-right}" y1="{yscale(0)}" y2="{yscale(0)}" stroke="#545c6e" stroke-dasharray="5 4"/><text x="{left+6}" y="{yscale(0)-6}">จุดเริ่มต้น 0%</text>')
        for index in [round(i*p['sessions']/4) for i in range(5)]:
            content.append(f'<text x="{xscale(index)}" y="{height-16}" text-anchor="middle">{daily[max(index-1,0)]["date"]}</text>')
        for values, color in zip(series, ['#673ab7', '#148a80']):
            points = ' '.join(f'{xscale(i):.2f},{yscale(value):.2f}' for i, value in enumerate(values))
            content.append(f'<polyline points="{points}" fill="none" stroke="{color}" stroke-width="2.5"/>')
        return f'<figure><figcaption>{html.escape(title)}</figcaption><svg role="img" aria-label="{html.escape(title)}" viewBox="0 0 {width} {height}">' + ''.join(content) + f'</svg><p class="legend"><span>━ EMA20/EMA200</span> <span>━ Buy &amp; Hold S&P 500 Price Index</span></p><p class="small">แกนนอน: วันที่ซื้อขาย {p["startDate"]} ถึง {p["endDate"]}</p></figure>'

    def distribution_plot():
        """Equal-width histogram plus exact, vertically separated trade observations."""
        ledger = results['tradeLedger']
        if not ledger:
            return '<p>ยังไม่มีเทรดที่ปิดครบ จึงยังแสดงการแจกแจงกำไร–ขาดทุนรายเทรดไม่ได้</p>'
        values = [row['netPnl'] for row in ledger]
        width, height, left, right = 860, 465, 80, 30
        raw_width = max(max(values) - min(values), 1) / 8
        magnitude = 10 ** math.floor(math.log10(raw_width))
        step = next(factor * magnitude for factor in [1, 2, 5, 10] if factor * magnitude >= raw_width)
        low = math.floor(min(min(values), 0) / step) * step
        high = math.ceil(max(max(values), 0) / step) * step
        if high == low:
            high += step
        bin_count = max(1, round((high - low) / step))
        counts = [0] * bin_count
        for value in values:
            counts[min(bin_count - 1, int((value - low) / step))] += 1
        x = lambda value: left + (value - low) / (high - low) * (width - left - right)
        max_count = max(counts)
        y = lambda count: 260 - count / max_count * 160
        pieces = ['<text x="80" y="78">จำนวนเทรด</text>']
        for count in range(max_count + 1):
            pieces.append(f'<line x1="{left}" x2="{width-right}" y1="{y(count)}" y2="{y(count)}" stroke="#dde2ea"/><text x="{left-10}" y="{y(count)+4}" text-anchor="end">{count}</text>')
        for index, count in enumerate(counts):
            start, end = low + index * step, low + (index + 1) * step
            color = '#b00020' if end <= 0 else '#148a80'
            interval = f'{start:,.0f} ถึง {end:,.0f} USD: {count} เทรด'
            pieces.append(f'<rect data-bin-count="{count}" x="{x(start)+1}" y="{y(count)}" width="{x(end)-x(start)-2}" height="{260-y(count)}" fill="{color}" opacity=".28"><title>{html.escape(interval)}</title></rect>')
            if count:
                pieces.append(f'<text x="{(x(start)+x(end))/2}" y="{y(count)-8}" text-anchor="middle">{count}</text>')
        for index in range(bin_count + 1):
            value = low + index * step
            pieces.append(f'<text x="{x(value)}" y="282" text-anchor="middle">{value:,.0f}</text>')
        pieces.append('<text x="450" y="307" text-anchor="middle">กำไร–ขาดทุนสุทธิต่อเทรด (USD)</text><text x="80" y="334">จุดแต่ละจุด = หนึ่งเทรดที่ปิดครบ</text>')
        placed = []
        for row in sorted(ledger, key=lambda item: item['netPnl']):
            px = x(row['netPnl'])
            lane = 0
            while any(abs(px-other_x) < 14 and lane == other_lane for other_x, other_lane in placed):
                lane += 1
            placed.append((px, lane))
            py = 352 + lane * 16
            color = '#b00020' if row['netPnl'] < 0 else '#148a80' if row['netPnl'] > 0 else '#545c6e'
            label = f"{row['id']}: {row['netPnl']:,.2f} USD"
            pieces.append(f'<circle data-trade-id="{html.escape(row["id"])}" cx="{px}" cy="{py}" r="5" fill="{color}"><title>{html.escape(label)}</title></circle>')
        height = max(height, 352 + max(lane for _, lane in placed) * 16 + 40)
        for value, label, color, label_y, anchor in [
                (0, '0 USD', '#545c6e', 22, 'middle'),
                (-tm['averageLoss'] if tm['averageLoss'] is not None else None, '−Average Loss', '#b00020', 42, 'end'),
                (tm['averageWin'], 'Average Win', '#148a80', 42, 'middle')]:
            if value is None:
                continue
            pieces.append(f'<line x1="{x(value)}" x2="{x(value)}" y1="62" y2="{height-40}" stroke="{color}" stroke-dasharray="5 4"/><text x="{x(value)}" y="{label_y}" text-anchor="{anchor}" fill="{color}">{label}</text><text x="{x(value)}" y="{label_y+15}" text-anchor="{anchor}" fill="{color}">{value:,.2f}</text>')
        near_zero = sum(-step <= value < step for value in values)
        winners = sorted((value for value in values if value > 0), reverse=True)
        concentration = (f' ไม้กำไรที่มากที่สุด {min(2, len(winners))} ไม้คิดเป็น {sum(winners[:2])/sum(winners):.2%} ของกำไรสุทธิรวมเฉพาะฝั่งชนะ จึงควรตรวจว่าค่าเฉลี่ยถูกดึงโดยไม้ใหญ่เพียงไม่กี่ไม้หรือไม่' if winners else ' ชุดนี้ไม่มีเทรดที่ได้กำไร จึงยังคำนวณ Average Win ไม่ได้')
        title = 'กำไร–ขาดทุนส่วนใหญ่กระจุกอยู่ที่ใด และไม้ใหญ่ดึงค่าเฉลี่ยอย่างไร'
        return (
            f'<figure><figcaption>{title}</figcaption>'
            f'<svg role="img" aria-label="{title}" viewBox="0 0 {width} {height}">'
            + ''.join(pieces) +
            f'</svg><p>แท่งแสดงจำนวนเทรดในช่วงกำไร–ขาดทุนที่กว้างเท่ากัน ช่วงละ {step:,.0f} USD '
            f'ส่วนจุดด้านล่างแสดงกำไร–ขาดทุนจริงของแต่ละเทรดรวม {len(ledger)} ไม้ '
            'การเลื่อนจุดขึ้นลงมีไว้แยกจุดที่อยู่ใกล้กัน ไม่ได้แสดงเวลา</p>'
            f'<p>ในชุดนี้ {near_zero} จาก {len(ledger)} ไม้อยู่ตั้งแต่ −{step:,.0f} '
            f'จนถึงน้อยกว่า {step:,.0f} USD{concentration}</p>'
            '<p>ด้านซ้ายของศูนย์คือเทรดที่ขาดทุน ด้านขวาคือเทรดที่ได้กำไร '
            'เส้น −Average Loss ใช้ค่าติดลบเพื่อวางตำแหน่งขาดทุนบนแกนนี้ '
            'ส่วนค่า Average Loss ในตารางรายงานเป็นขนาดบวก กราฟใช้ผลสุทธิหลังต้นทุน '
            'และนำเทรดที่บังคับปิดท้ายการทดสอบมารวมด้วย</p>'
            '<p class="small">ช่วงแต่ละแท่งรวมขอบซ้าย ไม่รวมขอบขวา ยกเว้นแท่งสุดท้ายที่รวมทั้งสองขอบ '
            'รูปทรงเปลี่ยนได้ตามความกว้างช่วง จึงควรอ่านจุดรายเทรดประกอบ '
            f'และไม่ใช้เพียง {len(ledger)} ไม้นี้ยืนยันรูปแบบการแจกแจงในอนาคต '
            'จำนวนเงินแต่ละไม้ขึ้นกับขนาดพอร์ตขณะเข้าเทรดด้วย</p></figure>'
        )

    def drawdown_period_plot():
        """Show the deepest episode on its own time axis, preserving duration ratios."""
        peak = pm['maxDrawdownPeakIndex']
        trough = pm['maxDrawdownTroughIndex']
        recovery = pm['maxDrawdownRecoveryIndex']
        if peak is None or trough is None:
            return '<p>ไม่พบช่วงที่มูลค่าพอร์ตสิ้นวันต่ำกว่ายอดเดิม จึงไม่มีช่วง Drawdown ให้แยกวัดระยะเวลา</p>'
        last = recovery if recovery is not None else len(equity[0]) - 1
        date = lambda index: p['startDate'] + ' ก่อนเริ่ม' if index == 0 else daily[index-1]['date']
        relative = [value / equity[0][peak] - 1 for value in equity[0][peak:last+1]]
        width, height, left, right = 860, 400, 85, 65
        x = lambda index: left + (index - peak) / max(last - peak, 1) * (width - left - right)
        low, high = min(relative) * 1.1, max(max(relative), .01)
        y = lambda value: 55 + (high - value) / (high - low) * 190
        pieces = [f'<rect x="{x(peak)}" y="55" width="{x(trough)-x(peak)}" height="190" fill="#673ab7" opacity=".06"/><rect x="{x(trough)}" y="55" width="{x(last)-x(trough)}" height="190" fill="#148a80" opacity=".06"/>', '<text x="85" y="25">มูลค่าพอร์ตเทียบยอดเดิม (%)</text>']
        for fraction in [0, .25, .5, .75, 1]:
            value = low * fraction
            pieces.append(f'<line x1="{left}" x2="{width-right}" y1="{y(value)}" y2="{y(value)}" stroke="#dde2ea"/><text x="{left-8}" y="{y(value)+4}" text-anchor="end">{value*100:.1f}%</text>')
        points = ' '.join(f'{x(peak+i):.2f},{y(value):.2f}' for i, value in enumerate(relative))
        pieces.append(f'<polyline points="{points}" fill="none" stroke="#673ab7" stroke-width="2.5"/>')
        for index, label, anchor in [(peak, 'ยอดเดิม', 'start'), (trough, 'จุดต่ำสุด', 'middle'), (last, 'กลับถึงยอดเดิม' if recovery is not None else 'สิ้นสุดข้อมูล', 'end')]:
            pieces.append(f'<line x1="{x(index)}" x2="{x(index)}" y1="50" y2="250" stroke="#545c6e" stroke-dasharray="3 3"/><circle cx="{x(index)}" cy="{y(equity[0][index]/equity[0][peak]-1)}" r="5" fill="#673ab7"/><text x="{x(index)}" y="275" text-anchor="{anchor}">{label}</text><text x="{x(index)}" y="293" text-anchor="{anchor}">{html.escape(date(index))}</text>')
        descending = trough - peak
        recovery_days = recovery - trough if recovery is not None else None
        underwater = recovery - peak if recovery is not None else None
        for start, end, level, label, color in [
                (peak, trough, 317, f'Drawdown period: {descending} วันซื้อขาย', '#673ab7'),
                (trough, last, 317, f'Recovery period: {recovery_days} วันซื้อขาย' if recovery_days is not None else f'หลังจุดต่ำสุด: {last-trough} วัน ยังไม่ฟื้น', '#148a80'),
                (peak, last, 366, f'Underwater period: {underwater} วันซื้อขาย' if underwater is not None else f'อยู่ใต้น้ำมาแล้ว {last-peak} วันซื้อขาย ยังไม่สิ้นสุด', '#545c6e')]:
            pieces.append(f'<path d="M{x(start)} {level-4} v8 M{x(start)} {level} H{x(end)} M{x(end)} {level-4} v8" fill="none" stroke="{color}"/><text x="{(x(start)+x(end))/2}" y="{level+20}" text-anchor="middle" fill="{color}">{label}</text>')
        title = 'ช่วงที่ขาดทุนลึกที่สุดใช้เวลาลงและฟื้นนานเท่าไร'
        if recovery is not None:
            status = f'ยอดเดิมวันที่ {date(peak)} → จุดต่ำสุดวันที่ {date(trough)} → กลับถึงยอดเดิมวันที่ {date(recovery)}: {descending} + {recovery_days} = {underwater} วันซื้อขาย ช่วงฟื้นไม่ได้แปลว่าพอร์ตขึ้นทุกวัน เพียงวัดเวลาจากจุดต่ำสุดจนกลับถึงระดับเดิมเป็นครั้งแรก'
        else:
            status = f'ยอดเดิมวันที่ {date(peak)} จุดต่ำสุดวันที่ {date(trough)} และยังไม่ฟื้นตัว ณ สิ้นสุดการทดสอบ {date(last)} จึงยังคำนวณ Recovery period และ Underwater period แบบครบช่วงไม่ได้'
        return (
            f'<figure><figcaption>{title}</figcaption>'
            f'<svg role="img" aria-label="{title}" viewBox="0 0 {width} {height}">'
            + ''.join(pieces) +
            f'</svg><p>Maximum Drawdown = {percent(pm["maxDrawdown"])} บอกความลึกของการลดลงจากยอดเดิม '
            'ส่วนระยะเวลาทั้งสามบอกว่าเงินอยู่ต่ำกว่ายอดเดิมนานเพียงใด '
            'กราฟนี้ขยายเฉพาะรอบที่ขาดทุนลึกที่สุด โดยใช้ยอดเดิมของรอบนี้เป็น 0%</p>'
            f'<p>{status}</p><ul><li><strong>Drawdown period:</strong> จากยอดเดิมถึงจุดต่ำสุด</li>'
            '<li><strong>Recovery period:</strong> จากจุดต่ำสุดถึงวันที่กลับถึงหรือสูงกว่ายอดเดิมเป็นครั้งแรก</li>'
            '<li><strong>Underwater period:</strong> จากยอดเดิมจนกลับถึงยอดเดิม รวมทั้งช่วงลงและช่วงฟื้น</li></ul>'
            '<p class="small">บทนี้นับระยะเป็นจำนวนช่วงวันซื้อขายระหว่างจุดสองจุด ไม่ได้นับวันหยุด '
            'และไม่บวกหนึ่งเพื่อรวมวันต้นทาง ชื่อระยะเวลาอาจต่างกันในซอฟต์แวร์อื่น '
            'จึงต้องอ่านนิยามก่อนเปรียบเทียบ รอบที่ลึกที่สุดไม่จำเป็นต้องเป็นรอบที่อยู่ใต้น้ำนานที่สุด</p></figure>'
        )

    cumulative = [[value / p['initialEquity'] - 1 for value in series] for series in equity]
    cumulative_caption = (
        '<p>ทั้งสองเส้นเริ่มที่ผลตอบแทนสะสม 0% จากเงินเริ่มต้นเท่ากัน ก่อนหักค่าซื้อครั้งแรก '
        'แกนตั้งคำนวณจากมูลค่าพอร์ตในวันนั้น ÷ เงินเริ่มต้น − 1 '
        'จึงอ่านได้ว่าเงินเพิ่มหรือลดจากจุดเริ่มต้นกี่เปอร์เซ็นต์ '
        'เส้นที่อยู่สูงกว่าให้ผลตอบแทนสะสมสูงกว่า ณ วันนั้น</p>'
        f'<p>เมื่อจบช่วงทดสอบ EMA ได้ {percent(pm["totalReturn"])} '
        f'เทียบกับซื้อแล้วถือที่ {percent(bm["totalReturn"])} ตัวเลขเป็นผลหลังต้นทุนตามแบบจำลองเดียวกัน '
        'ช่วงที่ EMA ถือเงินสด เส้นจะราบเพราะสมมติว่าดอกเบี้ยเงินสดเป็นศูนย์ '
        'จึงอาจช่วยหลบการลงบางช่วงและพลาดการขึ้นบางช่วงได้ '
        'ต้องอ่านกราฟ Drawdown ประกอบเพื่อดูความเสี่ยงระหว่างทาง</p>'
        '<p class="small">Benchmark คือ S&P 500 Price Index (^GSPC) ไม่รวมเงินปันผล '
        'ไม่ใช่ผลตอบแทนรวมของกองทุนที่ซื้อขายได้จริง '
        'เส้นนี้เป็นผลตอบแทนสะสมตลอดช่วง ไม่ใช่ CAGR ต่อปี</p>'
    )

    rows = [('มูลค่าพอร์ตปลายงวด (USD)', number(pm['finalEquity']), number(bm['finalEquity'])),
            ('Total Return', percent(pm['totalReturn']), percent(bm['totalReturn'])),
            ('CAGR (เวลาตามปฏิทิน)', percent(pm['cagr']), percent(bm['cagr'])),
            ('ความผันผวนต่อปีจากผลตอบแทนรายวัน', percent(pm['annualizedVolatility']), percent(bm['annualizedVolatility'])),
            ('Sharpe Ratio (ต่อปี; risk-free = 0)', number(pm['sharpe']), number(bm['sharpe'])),
            ('Sortino Ratio (ต่อปี; MAR = 0)', number(pm['sortino']), number(bm['sortino'])),
            ('Maximum Drawdown รายวัน', percent(pm['maxDrawdown']), percent(bm['maxDrawdown'])),
            ('ต้นทุนจริงที่หักในแบบจำลอง (USD)', number(pm['totalFees']), number(bm['totalFees']))]
    table = ''.join('<tr>' + ''.join(f'<{tag}>{html.escape(value)}</{tag}>' for tag, value in [('th', name), ('td', strategy), ('td', benchmark)]) + '</tr>' for name, strategy, benchmark in rows)
    trade_rows = ''.join(f'<tr><th>{label}</th><td>{value}</td></tr>' for label, value in [
        ('จำนวนเทรดปิดครบ', str(tm['count'])), ('ชนะ / แพ้ / เสมอ', f"{tm['wins']} / {tm['losses']} / {tm['breakevens']}"),
        ('Win Rate', percent(tm['winRate'])), ('Average Win (USD)', number(tm['averageWin'])), ('Average Loss (USD; ขนาดบวก)', number(tm['averageLoss'])),
        ('Payoff Ratio', number(tm['payoffRatio'])), ('Expectancy (USD ต่อเทรด)', number(tm['expectancy'])), ('Profit Factor', number(tm['profitFactor'])),
        ('รายการส่งคำสั่งที่เกิดการซื้อ/ขาย', str(results['transactionCount'])), ('ปิดสถานะบังคับปลายการทดสอบ', str(results['forcedExitCount']))])
    assumptions = ''.join(f'<li>{html.escape(a)}</li>' for a in ASSUMPTIONS)
    output = f'''<!doctype html><html lang="th"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Performance Report — EMA20 / EMA200</title>
<style>body{{margin:0;background:#f6f7fb;color:#232634;font:16px/1.7 system-ui,sans-serif}}main{{max-width:960px;margin:auto;padding:32px 20px 60px}}h1{{font-size:2rem;line-height:1.3}}h2{{font-size:1.4rem;margin-top:34px}}.note{{border-left:4px solid #d9952d;background:#fff3d9;padding:15px 20px}}table{{border-collapse:collapse;width:100%;background:white;font-size:.95rem}}th,td{{border-bottom:1px solid #e3e6ef;padding:10px 12px;text-align:left}}td{{text-align:right}}th{{font-weight:500}}thead th{{background:#eee9f6;font-weight:700}}figure{{margin:28px 0;padding:20px;background:white;border:1px solid #e2e5ed}}figcaption{{font-weight:700}}svg{{width:100%;height:auto;font:12px system-ui}}.legend{{display:flex;flex-wrap:wrap;gap:20px;font-size:14px}}.legend span:first-child{{color:#673ab7}}.legend span:last-child{{color:#148a80}}.small{{font-size:14px;color:#545c6e}}.scroll{{overflow:auto}}@media(max-width:600px){{main{{padding:20px 12px}}h1{{font-size:1.6rem}}figure{{padding:8px}}th,td{{padding:8px;font-size:13px}}}}</style>
<main><p>Robo Trade Notes · บทที่ 14 · เอกสารตรวจ</p><h1>Performance Report<br>EMA20 / EMA200 · daily bars</h1><p class="note">ราคาจริง S&P 500 (^GSPC) จาก Yahoo Finance · การซื้อขายเป็นแบบจำลองบนดัชนีราคา ไม่รวมเงินปันผล ดัชนีซื้อขายตรง ๆ ไม่ได้</p>
<p>{p['startDate']} ถึง {p['endDate']} · {p['sessions']} วันซื้อขาย · 1 แท่งต่อวัน · EMA 20/200 วัน · เงินเริ่มต้น 100,000 USD · ต้นทุน 0.10% ต่อข้าง · long/cash · สัญญาณเมื่อแท่งปิด ส่งคำสั่งที่ราคาเปิดแท่งถัดไป</p>
<h2>ผลตอบแทนและความเสี่ยงจากข้อมูลรายวัน</h2><div class="scroll"><table><thead><tr><th>ตัวชี้วัด</th><th>EMA20 / EMA200</th><th>Buy &amp; Hold</th></tr></thead><tbody>{table}</tbody></table></div>
{plot(cumulative, 'ผลตอบแทนสะสม: EMA 20/200 เทียบกับซื้อแล้วถือ S&P 500', True)}{cumulative_caption}
{plot(equity, 'เงินเริ่มต้นเท่ากัน แต่เส้นทางมูลค่าพอร์ตต่างกัน')}{plot(dds, 'Drawdown รายวันวัดระยะห่างจากจุดสูงสุดของแต่ละพอร์ต', True, True)}
<p>Maximum Drawdown วัดจากมูลค่าพอร์ตสิ้นวัน จึงไม่เห็นจุดต่ำระหว่างวันทั้งหมด</p>
{drawdown_period_plot()}
<h2>สถิติรายเทรดหลังหักต้นทุน</h2><div class="scroll"><table>{trade_rows}</table></div><p>จำนวนเทรดนับการเปิดจนปิดสถานะครบหนึ่งรอบ ส่วนจำนวนรายการซื้อขายนับการซื้อและขายแยกกัน</p>
{distribution_plot()}
<details><summary>สมมติฐานและวิธีคำนวณที่ทำซ้ำได้</summary><ul>{assumptions}</ul></details><p class="small">สร้างด้วย lesson_14.py จากการทดสอบเดียวกับ trades.csv, equity-daily.csv และ ema-results.json โดยไม่ใช้เครือข่าย</p></main></html>'''
    Path(path).write_text(output, encoding='utf-8')


def export_all(output_dir, parameters=None):
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    bars = generate_bars(parameters)
    backtest = run_backtest(bars, parameters)
    results = make_results(backtest)
    write_csv(output / 'ema-bars.csv', bars)
    write_csv(output / 'trades.csv', backtest['tradeLedger'])
    write_csv(output / 'equity-daily.csv', backtest['dailyEquity'])
    columns = ['index', 'session', 'date', 'barInSession', 'open', 'high', 'low', 'close', 'ema20', 'ema200', 'equity', 'benchmarkEquity', 'target', 'warmup']
    observations = {row['bar']: row for row in backtest['observations']}
    compact = []
    for bar in bars:
        row = dict(bar, **{k: v for k, v in observations.get(bar['index'], {}).items() if k in ('equity', 'benchmarkEquity', 'target')})
        compact.append([round(row[key], 8) if isinstance(row.get(key), float) else row.get(key) for key in columns])
    daily_columns = list(backtest['dailyEquity'][0])
    data = {'schemaVersion': 3, 'provenance': PROVENANCE, 'parameters': backtest['parameters'], 'assumptions': ASSUMPTIONS,
            'columns': columns, 'bars': compact, 'dailyColumns': daily_columns,
            'dailyRows': [[row[key] for key in daily_columns] for row in backtest['dailyEquity']]}
    (output / 'ema-data.json').write_text(json.dumps(data, ensure_ascii=False, separators=(',', ':'), allow_nan=False) + '\n', encoding='utf-8')
    (output / 'ema-results.json').write_text(json.dumps(results, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    create_report(results, output / 'performance-report.html')
    return bars, backtest, results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', default=str(Path(__file__).resolve().parent))
    args = parser.parse_args()
    _, _, results = export_all(args.output_dir)
    tm, pm = results['tradeMetrics'], results['portfolioMetrics']
    print(f"Exported historical S&P 500 backtest: {tm['count']} trades, {tm['wins']} wins, {tm['losses']} losses")
    print(f"Net final equity {pm['finalEquity']:,.2f}; total return {pm['totalReturn']:.4%}; daily MDD {pm['maxDrawdown']:.4%}")
    print(f"Output directory: {Path(args.output_dir).resolve()}")


if __name__ == '__main__':
    main()
