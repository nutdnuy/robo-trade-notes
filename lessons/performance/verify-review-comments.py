"""Check the new interpretations against frozen observations and SVG output."""
import json
import math
import re
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent
r = json.loads((ROOT / 'ema-results.json').read_text())
pnl = [t['netPnl'] for t in r['tradeLedger']]
eq = [r['parameters']['initialEquity']] + [d['equity'] for d in r['dailyEquity']]
benchmark = [eq[0]] + [d['benchmarkEquity'] for d in r['dailyEquity']]
assert len(pnl) == 19 and sum(x > 0 for x in pnl) == 8 and sum(x < 0 for x in pnl) == 11
assert sum(-20000 <= x < 20000 for x in pnl) == 14
assert sum(-10000 <= x < 10000 for x in pnl) == 12
top_two = sum(sorted((x for x in pnl if x > 0), reverse=True)[:2])
share = top_two / sum(x for x in pnl if x > 0)
assert round(share * 100, 2) == 47.26
assert round(max(pnl), 2) == 69362.18 and round(min(pnl), 2) == -17730.43

# Derive the worst episode from the full cash-and-position equity path.
running = eq[0]
dd = []
for value in eq:
    running = max(running, value)
    dd.append(value / running - 1)
trough = min(range(len(dd)), key=dd.__getitem__)
high = max(eq[:trough + 1])
peak = max(i for i in range(trough) if eq[i] == high)
recovery = next(i for i in range(trough + 1, len(eq)) if eq[i] >= high)
assert (peak, trough, recovery) == (900, 1325, 1757)
assert (trough - peak, recovery - trough, recovery - peak) == (425, 432, 857)
assert all(x < high for x in eq[peak + 1:recovery])

cumulative = [x / eq[0] - 1 for x in eq]
cum_benchmark = [x / eq[0] - 1 for x in benchmark]
assert cumulative[0] == cum_benchmark[0] == 0
assert math.isclose(cumulative[-1], r['portfolioMetrics']['totalReturn'])
assert math.isclose(cum_benchmark[-1], r['benchmarkMetrics']['totalReturn'])
dates = ['initial'] + [d['date'] for d in r['dailyEquity']]
for date, a, b in [('2009-03-09', 1.04, -49.04), ('2009-07-15', 1.04, -29.75)]:
    i = dates.index(date)
    assert round(cumulative[i] * 100, 2) == a
    assert round(cum_benchmark[i] * 100, 2) == b

charts = json.loads(subprocess.check_output(['node', '-e', '''
const C=require('./ema-charts.js'),r=require('./ema-results.json');
console.log(JSON.stringify({
 distribution:C.tradeDistribution(r.tradeLedger,18),
 cumulative:C.equity(r.dailyEquity,r.parameters.initialEquity,0,'cumulative'),
 duration:C.drawdownEpisode(r.dailyEquity,r.parameters.initialEquity,r.portfolioMetrics)
}));
'''], cwd=ROOT, text=True))
for svg in charts.values():
    assert not re.search(r'NaN|undefined|Infinity', svg)
    ET.fromstring(svg)
distribution = ET.fromstring(charts['distribution'])
counts = [int(x.attrib['data-bin-count']) for x in distribution.iter() if 'data-bin-count' in x.attrib]
assert counts == [11, 3, 1, 2, 2], counts
ids = [x.attrib['data-trade-id'] for x in distribution.iter() if 'data-trade-id' in x.attrib]
assert set(ids) == {f'T{i}' for i in range(1, 20)} and len(ids) == 19

result = {'status': 'passed', 'revision': 6, 'closedTrades': len(pnl),
          'histogramWidthUSD': 20000, 'histogramCounts': counts,
          'topTwoShareOfWinningNetPnl': share,
          'drawdownPeriod': 425, 'recoveryPeriod': 432, 'underwaterPeriod': 857,
          'cumulativeFinalPercent': [100 * cumulative[-1], 100 * cum_benchmark[-1]],
          'svgValid': list(charts)}
(ROOT / 'qa/review-comments-numeric.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
