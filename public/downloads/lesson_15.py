"""Lesson 15: Parameter Optimization & Overfitting with an EMA crossover.

Pure Python 3.9+ (standard library only). Reads the frozen SPY daily bars that
lesson 14 fetched with Webull OpenAPI; this script never calls an API.

Rules shared with lesson 14:
- EMA(fast) and EMA(slow) of daily closes, seeded at the first warmup close.
- Target 100% long when EMA(fast) > EMA(slow) at the previous close, else cash.
- Trade at the next open. Fee 0.1% per side on notional. No leverage or shorting.
- Close any remaining position at the final close of the window (with fee).
- Sharpe: mean / sample SD of daily returns x sqrt(252), risk-free rate 0.

Run:  python3 lesson_15.py --output-dir output
"""

import argparse
import csv
import json
import math
import random
from pathlib import Path

# Works as a script, inside the notebook (no __file__), and in the repository.
HERE = Path(__file__).resolve().parent if '__file__' in globals() else Path.cwd()
DATA_CANDIDATES = [
    HERE / 'data' / 'spy-webull-daily.csv',
    HERE / 'performance' / 'data' / 'spy-webull-daily.csv',
    HERE.parent / 'python' / 'data' / 'spy-webull-daily.csv',
    HERE.parents[1] / 'lessons' / 'performance' / 'data' / 'spy-webull-daily.csv',
]

WARMUP_BARS = 400
FEE = 0.001
PERIODS_PER_YEAR = 252
EVALUATION = ('2006-09-26', '2026-09-25')
IN_SAMPLE = ('2006-09-26', '2016-09-25')
OUT_OF_SAMPLE = ('2016-09-26', '2026-09-25')
FAST_SPANS = list(range(5, 101, 5))       # 5, 10, ..., 100
SLOW_SPANS = list(range(50, 301, 10))     # 50, 60, ..., 300
BASELINE = (20, 200)
WALK_TRAIN_YEARS = 5
NOISE_SEED = 20260929
NOISE_WORLDS = 60
NOISE_DAYS = 2520                         # 10 years of 252 days: 5 in-sample + 5 out-of-sample
NOISE_FAST = [5, 10, 20, 30, 40, 50, 60, 80, 100]
NOISE_SLOW = [50, 75, 100, 125, 150, 175, 200, 250, 300]
TRIAL_COUNTS = [1, 2, 5, 10, 20, 40, 74]   # 74 = every pair in the noise grid


# ---------------------------------------------------------------- data

def load_bars(path=None):
    """Read the frozen Webull CSV: date, open, high, low, close, volume."""
    path = Path(path) if path else next(p for p in DATA_CANDIDATES if p.is_file())
    with path.open(newline='', encoding='utf-8') as f:
        rows = list(csv.DictReader(f))
    first = next(i for i, row in enumerate(rows) if row['date'] >= EVALUATION[0])
    rows = rows[first - WARMUP_BARS:]
    return [{'date': r['date'], 'open': float(r['open']), 'close': float(r['close'])} for r in rows]


def ema(values, span):
    """Exponential moving average seeded at the first value (same as lesson 14)."""
    alpha = 2 / (span + 1)
    out, level = [], None
    for value in values:
        level = value if level is None else alpha * value + (1 - alpha) * level
        out.append(level)
    return out


class EmaCache:
    """Compute each EMA span once and reuse it across the parameter grid."""

    def __init__(self, closes):
        self.closes = closes
        self.store = {}

    def __call__(self, span):
        if span not in self.store:
            self.store[span] = ema(self.closes, span)
        return self.store[span]


def window_indices(bars, start, end):
    """First and last bar index whose date lies inside [start, end]."""
    first = next(i for i, b in enumerate(bars) if b['date'] >= start)
    last = max(i for i, b in enumerate(bars) if b['date'] <= end)
    return first, last


# ---------------------------------------------------------------- backtest

def run_window(bars, fast_line, slow_line, first, last, fee=FEE, capital=100000.0, pair_at=None):
    """Long/cash account from the open of bar `first` to the close of bar `last`.

    `pair_at(i)` may return other EMA lines for bar i (walk-forward); otherwise the
    fixed lines are used. Returns daily closing equity and the number of round trips.
    """
    cash, units, trades = capital, 0.0, 0
    equity = []
    for i in range(first, last + 1):
        f_line, s_line = pair_at(i) if pair_at else (fast_line, slow_line)
        target = 1 if f_line[i - 1] > s_line[i - 1] else 0
        price = bars[i]['open']
        if target == 1 and units == 0:
            units = cash / (price * (1 + fee))
            cash = 0.0
        elif target == 0 and units > 0:
            cash = units * price * (1 - fee)
            units, trades = 0.0, trades + 1
        if i == last and units > 0:
            cash = units * bars[i]['close'] * (1 - fee)
            units, trades = 0.0, trades + 1
        equity.append(cash + units * bars[i]['close'])
    return equity, trades


def buy_and_hold(bars, first, last, fee=FEE, capital=100000.0):
    units = capital / (bars[first]['open'] * (1 + fee))
    equity = [units * bars[i]['close'] for i in range(first, last + 1)]
    equity[-1] *= 1 - fee
    return equity


def daily_returns(equity, capital=100000.0):
    previous, out = capital, []
    for value in equity:
        out.append(value / previous - 1)
        previous = value
    return out


def sharpe(returns):
    n = len(returns)
    if n < 2:
        return float('nan')
    mean = sum(returns) / n
    var = sum((r - mean) ** 2 for r in returns) / (n - 1)
    return mean / math.sqrt(var) * math.sqrt(PERIODS_PER_YEAR) if var > 0 else 0.0


def max_drawdown(equity, capital=100000.0):
    peak, worst = capital, 0.0
    for value in equity:
        peak = max(peak, value)
        worst = min(worst, value / peak - 1)
    return worst


def years_between(start, end):
    from datetime import date
    a, b = date.fromisoformat(start), date.fromisoformat(end)
    return (b - a).days / 365.25


def metrics(equity, dates, trades=None, capital=100000.0):
    rets = daily_returns(equity, capital)
    years = years_between(dates[0], dates[-1])
    total = equity[-1] / capital - 1
    out = {'totalReturn': total, 'cagr': (1 + total) ** (1 / years) - 1,
           'sharpe': sharpe(rets), 'maxDrawdown': max_drawdown(equity, capital)}
    if trades is not None:
        out['trades'] = trades
    return out


def evaluate_pair(bars, lines, fast, slow, window):
    first, last = window_indices(bars, *window)
    equity, trades = run_window(bars, lines(fast), lines(slow), first, last)
    return metrics(equity, [bars[first]['date'], bars[last]['date']], trades), equity


def grid_pairs(fast_spans=FAST_SPANS, slow_spans=SLOW_SPANS):
    return [(f, s) for f in fast_spans for s in slow_spans if f < s]


def run_grid(bars, window, pairs=None):
    lines = EmaCache([b['close'] for b in bars])
    rows = []
    for fast, slow in pairs or grid_pairs():
        m, _ = evaluate_pair(bars, lines, fast, slow, window)
        rows.append({'fast': fast, 'slow': slow, **m})
    return rows


def best(rows, key='sharpe'):
    return max(rows, key=lambda r: r[key])


def neighbourhood_mean(rows, key='sharpe'):
    """Average of each cell and its grid neighbours (one step in each direction)."""
    table = {(r['fast'], r['slow']): r[key] for r in rows}
    out = []
    for r in rows:
        fi, si = FAST_SPANS.index(r['fast']), SLOW_SPANS.index(r['slow'])
        values = [table[(FAST_SPANS[a], SLOW_SPANS[b])]
                  for a in range(fi - 1, fi + 2) for b in range(si - 1, si + 2)
                  if 0 <= a < len(FAST_SPANS) and 0 <= b < len(SLOW_SPANS)
                  and (FAST_SPANS[a], SLOW_SPANS[b]) in table]
        out.append({**r, key + 'Neighbourhood': sum(values) / len(values)})
    return out


def rank_correlation(xs, ys):
    """Spearman rank correlation without ties handling beyond average ranks."""
    def ranks(values):
        order = sorted(range(len(values)), key=lambda i: values[i])
        result = [0.0] * len(values)
        i = 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
                j += 1
            for k in range(i, j + 1):
                result[order[k]] = (i + j) / 2 + 1
            i = j + 1
        return result
    rx, ry = ranks(xs), ranks(ys)
    mx, my = sum(rx) / len(rx), sum(ry) / len(ry)
    cov = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    return cov / math.sqrt(sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry))


# ---------------------------------------------------------------- walk-forward

def walk_forward(bars, train_years=WALK_TRAIN_YEARS, pairs=None):
    """Each year pick the best-Sharpe pair on the previous `train_years`, then trade one year.

    Training Sharpe uses each pair's continuous daily returns inside the training window.
    Trading is one account whose active pair changes only at each yearly boundary.
    """
    pairs = pairs or grid_pairs()
    lines = EmaCache([b['close'] for b in bars])
    e_first, e_last = window_indices(bars, *EVALUATION)
    continuous = {}
    for fast, slow in pairs:
        equity, _ = run_window(bars, lines(fast), lines(slow), e_first, e_last)
        continuous[(fast, slow)] = daily_returns(equity)
    dates = [bars[i]['date'] for i in range(e_first, e_last + 1)]
    start_year = int(EVALUATION[0][:4])
    steps = []
    year = start_year + train_years
    while True:
        test_start = f'{year}{EVALUATION[0][4:]}'
        test_end = f'{year + 1}-09-25'
        if test_start > EVALUATION[1]:
            break
        train_start = f'{year - train_years}{EVALUATION[0][4:]}'
        a = next(i for i, d in enumerate(dates) if d >= train_start)
        b = max(i for i, d in enumerate(dates) if d < test_start)
        scores = {pair: sharpe(continuous[pair][a:b + 1]) for pair in pairs}
        chosen = max(pairs, key=lambda p: scores[p])
        steps.append({'trainStart': dates[a], 'trainEnd': dates[b], 'testStart': test_start,
                      'testEnd': min(test_end, EVALUATION[1]), 'fast': chosen[0], 'slow': chosen[1],
                      'trainSharpe': scores[chosen]})
        year += 1
    first, last = window_indices(bars, steps[0]['testStart'], EVALUATION[1])

    def pair_at(i):
        active = steps[0]
        for step in steps:
            if bars[i]['date'] >= step['testStart']:
                active = step
        return lines(active['fast']), lines(active['slow'])

    equity, trades = run_window(bars, None, None, first, last, pair_at=pair_at)
    for step in steps:
        a, b = window_indices(bars, step['testStart'], step['testEnd'])
        segment = equity[a - first:b - first + 1]
        base = equity[a - first - 1] if a > first else 100000.0
        step['testReturn'] = segment[-1] / base - 1
    window = (bars[first]['date'], bars[last]['date'])
    return {'steps': steps, 'equity': equity, 'trades': trades, 'window': window,
            'metrics': metrics(equity, list(window), trades)}


# ---------------------------------------------------------------- noise worlds

def noise_world(rng, source_returns, days=NOISE_DAYS):
    """Resample real daily returns with replacement: same size of moves, no time order.

    Shuffling removes any trend the EMA rule could exploit, so any 'edge' found here
    comes from fitting noise. Open equals the previous close in this synthetic world.
    """
    price, closes = 100.0, []
    for _ in range(days):
        price *= 1 + rng.choice(source_returns)
        closes.append(price)
    return closes


def noise_pair_returns(closes, fast, slow, cache, fee=FEE):
    f_line, s_line = cache(fast), cache(slow)
    out, position = [], 0
    for t in range(1, len(closes)):
        r = closes[t] / closes[t - 1] - 1
        target = 1 if f_line[t - 1] > s_line[t - 1] else 0
        cost = fee if target != position else 0.0
        out.append(target * r - cost)
        position = target
    return out


def noise_experiment(bars, worlds=NOISE_WORLDS, seed=NOISE_SEED):
    """For each synthetic world: choose the best in-sample pair among N tried, read its out-of-sample Sharpe."""
    rng = random.Random(seed)
    e_first, e_last = window_indices(bars, *EVALUATION)
    closes = [b['close'] for b in bars[e_first - 1:e_last + 1]]
    source = [closes[i] / closes[i - 1] - 1 for i in range(1, len(closes))]
    pairs = [(f, s) for f in NOISE_FAST for s in NOISE_SLOW if f < s]
    half = (NOISE_DAYS - 1) // 2
    results = []
    for world in range(worlds):
        path = noise_world(rng, source)
        cache = EmaCache(path)
        order = pairs[:]
        rng.shuffle(order)
        stats = {}
        for pair in pairs:
            rets = noise_pair_returns(path, pair[0], pair[1], cache)
            stats[pair] = (sharpe(rets[:half]), sharpe(rets[half:]))
        hold = [path[t] / path[t - 1] - 1 for t in range(1, len(path))]
        picks = []
        for n in TRIAL_COUNTS:
            chosen = max(order[:n], key=lambda p: stats[p][0])
            picks.append({'trials': n, 'fast': chosen[0], 'slow': chosen[1],
                          'inSample': stats[chosen][0], 'outOfSample': stats[chosen][1]})
        results.append({'world': world + 1, 'buyHoldInSample': sharpe(hold[:half]),
                        'buyHoldOutOfSample': sharpe(hold[half:]), 'picks': picks})
    summary = []
    for k, n in enumerate(TRIAL_COUNTS):
        ins = [w['picks'][k]['inSample'] for w in results]
        outs = [w['picks'][k]['outOfSample'] for w in results]
        summary.append({'trials': n, 'meanInSample': sum(ins) / len(ins),
                        'meanOutOfSample': sum(outs) / len(outs)})
    return {'seed': seed, 'worlds': worlds, 'days': NOISE_DAYS, 'pairs': len(pairs),
            'trialCounts': TRIAL_COUNTS, 'results': results, 'summary': summary}


# ---------------------------------------------------------------- report

def build_results(bars):
    pairs = grid_pairs()
    full = run_grid(bars, EVALUATION, pairs)
    ins = neighbourhood_mean(run_grid(bars, IN_SAMPLE, pairs))
    outs = run_grid(bars, OUT_OF_SAMPLE, pairs)
    best_is = best(ins)
    plateau = max(ins, key=lambda r: r['sharpeNeighbourhood'])
    lookup_out = {(r['fast'], r['slow']): r for r in outs}
    lookup_full = {(r['fast'], r['slow']): r for r in full}
    return {
        'pairs': len(pairs), 'fastSpans': FAST_SPANS, 'slowSpans': SLOW_SPANS,
        'windows': {'evaluation': EVALUATION, 'inSample': IN_SAMPLE, 'outOfSample': OUT_OF_SAMPLE},
        'full': full, 'inSample': ins, 'outOfSample': outs,
        'bestFull': best(full), 'bestInSample': best_is, 'plateauInSample': plateau,
        'bestInSampleOut': lookup_out[(best_is['fast'], best_is['slow'])],
        'plateauOut': lookup_out[(plateau['fast'], plateau['slow'])],
        'baselineFull': lookup_full[BASELINE], 'baselineOut': lookup_out[BASELINE],
        'rankCorrelation': rank_correlation([r['sharpe'] for r in ins],
                                            [lookup_out[(r['fast'], r['slow'])]['sharpe'] for r in ins]),
    }


def print_summary(results):
    def line(label, m):
        print(f"{label:<34} Sharpe {m['sharpe']:.2f}  CAGR {m['cagr']:.2%}  MDD {m['maxDrawdown']:.2%}  trades {m.get('trades', '-')}")
    print(f"Grid: {results['pairs']} EMA pairs, fast {FAST_SPANS[0]}-{FAST_SPANS[-1]}, slow {SLOW_SPANS[0]}-{SLOW_SPANS[-1]}")
    b = results['bestInSample']
    line(f"Best in-sample {b['fast']}/{b['slow']} (IS)", b)
    line(f"Same pair {b['fast']}/{b['slow']} (OOS)", results['bestInSampleOut'])
    line(f"Baseline 20/200 (OOS)", results['baselineOut'])
    print(f"Rank correlation IS vs OOS Sharpe: {results['rankCorrelation']:.2f}")


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--output-dir', default='output')
    parser.add_argument('--data', default=None)
    args = parser.parse_args()
    bars = load_bars(args.data)
    results = build_results(bars)
    print_summary(results)
    wf = walk_forward(bars)
    print(f"Walk-forward {wf['window'][0]} to {wf['window'][1]}: Sharpe {wf['metrics']['sharpe']:.2f}, CAGR {wf['metrics']['cagr']:.2%}")
    noise = noise_experiment(bars)
    for row in noise['summary']:
        print(f"Noise, best of {row['trials']:>2} pairs: IS Sharpe {row['meanInSample']:.2f}, OOS Sharpe {row['meanOutOfSample']:.2f}")
    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / 'optimization-results.json').write_text(json.dumps(
        {'grid': results, 'walkForward': {k: v for k, v in wf.items() if k != 'equity'}, 'noise': noise},
        ensure_ascii=False, indent=1), encoding='utf-8')
    print(f"Saved {out / 'optimization-results.json'}")


if __name__ == '__main__':
    main()
