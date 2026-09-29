"""Build lesson 15 data and its executed notebook with standard Python.

Runs public/downloads/lesson_15.py on the frozen Webull SPY bars, writes the
compact JSON used by the interactive figures, and executes every notebook code
cell in order in one shared namespace (no Jupyter kernel, no network).
"""

import contextlib
import hashlib
import io
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'public' / 'downloads'
SOURCE = (OUTPUT / 'lesson_15.py').read_text(encoding='utf-8')
DEFINITIONS = SOURCE.split("if __name__ == '__main__':")[0]
PROVENANCE = json.loads((ROOT / 'lessons/performance/data/provenance.json').read_text(encoding='utf-8'))


def markdown(text):
    return {'cell_type': 'markdown', 'metadata': {}, 'source': text.strip('\n').splitlines(keepends=True)}


def code(text):
    return {'cell_type': 'code', 'metadata': {}, 'source': text.strip('\n').splitlines(keepends=True),
            'execution_count': None, 'outputs': []}


cells = [
    markdown("""# Parameter Optimization & Overfitting — Notebook บทที่ 5

Notebook นี้ใช้ราคา SPY รายวันจาก Webull OpenAPI ชุดเดียวกับบทที่ 4 (ไฟล์ `data/spy-webull-daily.csv`)
ไม่มีการเรียก API ใหม่ รันซ้ำกี่ครั้งก็ได้ตัวเลขเดิม ใช้เพียง Python standard library

กติกาเหมือนบทที่ 4: ถือ SPY 100% เมื่อ EMA เร็วอยู่เหนือ EMA ช้าที่ราคาปิดวันก่อน มิฉะนั้นถือเงินสด
ซื้อขายที่ราคาเปิดวันถัดไป ค่าธรรมเนียมสมมติ 0.1% ต่อข้าง ไม่มี leverage และไม่ short
Sharpe = ค่าเฉลี่ย / ส่วนเบี่ยงเบนมาตรฐานของผลตอบแทนรายวัน × √252 โดยใช้อัตราปลอดความเสี่ยง 0%
"""),
    code(DEFINITIONS + "\nprint('Loaded lesson 15 definitions; grid', len(grid_pairs()), 'pairs')\n"),
    markdown("""## 1. โหลดข้อมูลและตรวจว่าตรงกับบทที่ 4

EMA 20/200 ช่วง 2006-09-26 ถึง 2026-09-25 ต้องได้ผลตอบแทนสะสม 367.41% และ 17 เทรดเท่ากับบทที่ 4
"""),
    code("""bars = load_bars()
lines = EmaCache([b['close'] for b in bars])
baseline, _ = evaluate_pair(bars, lines, 20, 200, EVALUATION)
print('Bars loaded:', len(bars), 'first', bars[0]['date'], 'last', bars[-1]['date'])
print({k: round(v, 4) for k, v in baseline.items()})
assert abs(baseline['totalReturn'] - 3.674102) < 1e-6 and baseline['trades'] == 17
"""),
    markdown("""## 2. Grid search ทั้ง 20 ปี

ลอง EMA เร็ว 5–100 (ทีละ 5) คู่กับ EMA ช้า 50–300 (ทีละ 10) โดยให้เส้นเร็วสั้นกว่าเส้นช้า รวม 484 คู่
แล้วเรียงตาม Sharpe ของทั้ง 20 ปี ตัวเลขนี้คือผลที่ได้จากการมองย้อนหลังทั้งหมด
"""),
    code("""full = run_grid(bars, EVALUATION)
top = sorted(full, key=lambda r: -r['sharpe'])[:5]
for r in top:
    print(f"EMA {r['fast']:>3}/{r['slow']:<3} Sharpe {r['sharpe']:.3f} CAGR {r['cagr']:.2%} MDD {r['maxDrawdown']:.2%} trades {r['trades']}")
print('Pairs tested:', len(full))
"""),
    markdown("""## 3. แบ่ง In-sample และ Out-of-sample

เลือกคู่ที่ดีที่สุดจากช่วงฝึก 2006-09-26 ถึง 2016-09-25 เท่านั้น แล้วนำคู่นั้นไปอ่านผลช่วงทดสอบ 2016-09-26 ถึง 2026-09-25
แต่ละช่วงเริ่มบัญชีใหม่ด้วยเงินสด 100,000 USD แต่ EMA คำนวณต่อเนื่องจากข้อมูลก่อนหน้า
"""),
    code("""results = build_results(bars)
print_summary(results)
out_sorted = sorted(results['outOfSample'], key=lambda r: -r['sharpe'])
rank = {(r['fast'], r['slow']): i + 1 for i, r in enumerate(out_sorted)}
b = results['bestInSample']
print('Out-of-sample rank of the in-sample winner:', rank[(b['fast'], b['slow'])], 'of', len(out_sorted))
"""),
    markdown("""## 4. เทียบกับการซื้อแล้วถือในแต่ละช่วง
"""),
    code("""for name, window in [('In-sample', IN_SAMPLE), ('Out-of-sample', OUT_OF_SAMPLE)]:
    first, last = window_indices(bars, *window)
    hold = metrics(buy_and_hold(bars, first, last), [bars[first]['date'], bars[last]['date']])
    pick, _ = evaluate_pair(bars, lines, b['fast'], b['slow'], window)
    print(f"{name:<14} buy & hold Sharpe {hold['sharpe']:.2f} CAGR {hold['cagr']:.2%} | EMA {b['fast']}/{b['slow']} Sharpe {pick['sharpe']:.2f} CAGR {pick['cagr']:.2%}")
"""),
    markdown("""## 5. ตลาดที่ไม่มีสัญญาณ

สุ่มผลตอบแทนรายวันของ SPY แบบใส่คืน (bootstrap) สร้างโลกสมมติ 60 โลก โลกละ 2,520 วัน ลำดับเวลาถูกทำลาย
จึงไม่มีแนวโน้มให้ EMA จับได้จริง ในแต่ละโลก ลองสุ่ม N คู่จาก 74 คู่ เลือกคู่ที่ Sharpe ครึ่งแรกดีที่สุด แล้วอ่าน Sharpe ครึ่งหลัง
"""),
    code("""noise = noise_experiment(bars)
for row in noise['summary']:
    print(f"best of {row['trials']:>2} pairs: in-sample Sharpe {row['meanInSample']:.2f}, out-of-sample Sharpe {row['meanOutOfSample']:.2f}")
"""),
    markdown("""## 6. Walk-forward

ทุกปี เลือกคู่ที่ Sharpe ดีที่สุดใน 5 ปีก่อนหน้า แล้วใช้คู่นั้นเทรดหนึ่งปี บัญชีเดียวต่อเนื่องตั้งแต่ 2011-09-26
"""),
    code("""wf = walk_forward(bars)
for step in wf['steps']:
    print(f"{step['testStart']}: EMA {step['fast']:>3}/{step['slow']:<3} train Sharpe {step['trainSharpe']:.2f} -> next-year return {step['testReturn']:.2%}")
m = wf['metrics']
print(f"Walk-forward Sharpe {m['sharpe']:.2f}, CAGR {m['cagr']:.2%}, MDD {m['maxDrawdown']:.2%}, trades {m['trades']}")
"""),
    markdown("""## อ่านผลอย่างไร

ตัวเลขทั้งหมดเป็นผลจำลองบนราคาที่ปรับย้อนหลังแล้ว ไม่รวมภาษี spread slippage และข้อจำกัดการส่งคำสั่งจริง
ผลของช่วงทดสอบชุดเดียวเป็นเพียงหนึ่งเส้นทางของประวัติศาสตร์ ไม่ได้พิสูจน์ว่าคู่ใดจะดีในอนาคต

แหล่งอ้างอิง: Yves Hilpisch, *Python for Algorithmic Trading* (O'Reilly, 2020) หน้า PDF 87–88 (optimize_parameters แบบ brute force),
100–101 (Data Snooping and Overfitting) และ 118 (in-sample fitting กับ out-of-sample evaluation)
"""),
]


def run_notebook():
    namespace = {'__name__': 'optimization_notebook', '__file__': str(OUTPUT / 'lesson_15.py')}
    count = 0
    for cell in cells:
        source = ''.join(cell['source'])
        cell['id'] = hashlib.sha256((cell['cell_type'] + source).encode()).hexdigest()[:12]
        if cell['cell_type'] != 'code':
            continue
        count += 1
        captured = io.StringIO()
        with contextlib.redirect_stdout(captured):
            exec(compile(source, f'lesson15-cell-{count}', 'exec'), namespace)
        cell['execution_count'] = count
        cell['outputs'] = [{'output_type': 'stream', 'name': 'stdout',
                            'text': captured.getvalue().splitlines(keepends=True)}]
    notebook = {'cells': cells, 'metadata': {
        'kernelspec': {'display_name': 'Python 3', 'language': 'python', 'name': 'python3'},
        'language_info': {'name': 'python', 'version': sys.version.split()[0]},
        'execution': {'method': 'Each code cell executed in order by CPython in one shared namespace', 'codeCells': count},
    }, 'nbformat': 4, 'nbformat_minor': 5}
    return namespace, notebook


def r4(value):
    return round(value, 4)


def compact(m):
    out = {'sharpe': r4(m['sharpe']), 'cagr': r4(m['cagr']), 'mdd': r4(m['maxDrawdown'])}
    if 'trades' in m:
        out['trades'] = m['trades']
    return out


def sample(dates, series, step=5):
    idx = list(range(0, len(dates), step))
    if idx[-1] != len(dates) - 1:
        idx.append(len(dates) - 1)
    return [dates[i] for i in idx], [[round(s[i], 2) for i in idx] for s in series]


def web_data(ns):
    bars, lines, results, noise, wf = ns['bars'], ns['lines'], ns['results'], ns['noise'], ns['wf']
    key = lambda r: (r['fast'], r['slow'])
    full = {key(r): r for r in results['full']}
    ins = {key(r): r for r in results['inSample']}
    outs = {key(r): r for r in results['outOfSample']}
    grid = [{'f': f, 's': s, 'full': compact(full[(f, s)]), 'is': compact(ins[(f, s)]), 'oos': compact(outs[(f, s)])}
            for (f, s) in ns['grid_pairs']()]
    pick = results['bestInSample']
    first, last = ns['window_indices'](bars, *ns['EVALUATION'])
    dates = [bars[i]['date'] for i in range(first, last + 1)]
    series = [ns['run_window'](bars, lines(f), lines(s), first, last)[0] for f, s in [(pick['fast'], pick['slow']), (20, 200)]]
    series.append(ns['buy_and_hold'](bars, first, last))
    eq_dates, eq_values = sample(dates, series)
    wf_first, wf_last = ns['window_indices'](bars, *wf['window'])
    wf_dates = [bars[i]['date'] for i in range(wf_first, wf_last + 1)]
    fixed = ns['run_window'](bars, lines(20), lines(200), wf_first, wf_last)[0]
    hold = ns['buy_and_hold'](bars, wf_first, wf_last)
    wf_sample_dates, wf_values = sample(wf_dates, [wf['equity'], fixed, hold])
    wf_compare = {'walkForward': compact(wf['metrics']),
                  'fixed': compact(ns['metrics'](fixed, list(wf['window']), ns['run_window'](bars, lines(20), lines(200), wf_first, wf_last)[1])),
                  'hold': compact(ns['metrics'](hold, list(wf['window'])))}
    windows = {}
    for name, window in [('full', ns['EVALUATION']), ('is', ns['IN_SAMPLE']), ('oos', ns['OUT_OF_SAMPLE'])]:
        a, b = ns['window_indices'](bars, *window)
        windows[name] = {'start': bars[a]['date'], 'end': bars[b]['date'], 'bars': b - a + 1,
                         'hold': compact(ns['metrics'](ns['buy_and_hold'](bars, a, b), [bars[a]['date'], bars[b]['date']]))}
    return {
        'metadata': {
            'symbol': 'SPY', 'source': PROVENANCE['provider'], 'endpoint': PROVENANCE['endpoint'],
            'retrievedAtUTC': PROVENANCE['retrievedAtUTC'], 'csvSHA256': PROVENANCE['csvSHA256'],
            'feePerSide': ns['FEE'], 'periodsPerYear': ns['PERIODS_PER_YEAR'], 'riskFree': 0,
            'fastSpans': ns['FAST_SPANS'], 'slowSpans': ns['SLOW_SPANS'], 'pairs': len(grid),
            'generator': 'scripts/build_optimization.py', 'kind': 'simulated backtests on Webull SPY daily bars',
        },
        'windows': windows,
        'grid': grid,
        'highlights': {'bestFull': list(key(results['bestFull'])), 'bestInSample': list(key(pick)),
                       'plateauInSample': list(key(results['plateauInSample'])), 'baseline': [20, 200]},
        'rankCorrelation': r4(results['rankCorrelation']),
        'equity': {'dates': eq_dates, 'split': ns['OUT_OF_SAMPLE'][0],
                   'series': [{'id': 'pick', 'label': f"EMA {pick['fast']}/{pick['slow']}", 'values': eq_values[0]},
                              {'id': 'baseline', 'label': 'EMA 20/200', 'values': eq_values[1]},
                              {'id': 'hold', 'label': 'ซื้อแล้วถือ SPY', 'values': eq_values[2]}]},
        'walkForward': {'trainYears': ns['WALK_TRAIN_YEARS'], 'window': list(wf['window']),
                        'steps': [{'testStart': s['testStart'], 'testEnd': s['testEnd'], 'trainStart': s['trainStart'],
                                   'fast': s['fast'], 'slow': s['slow'], 'trainSharpe': r4(s['trainSharpe']),
                                   'testReturn': r4(s['testReturn'])} for s in wf['steps']],
                        'dates': wf_sample_dates,
                        'series': [{'id': 'walk', 'label': 'Walk-forward', 'values': wf_values[0]},
                                   {'id': 'baseline', 'label': 'EMA 20/200 คงที่', 'values': wf_values[1]},
                                   {'id': 'hold', 'label': 'ซื้อแล้วถือ SPY', 'values': wf_values[2]}],
                        'metrics': wf_compare},
        'noise': {'seed': noise['seed'], 'worlds': noise['worlds'], 'days': noise['days'], 'pairs': noise['pairs'],
                  'trialCounts': noise['trialCounts'],
                  'summary': [{'trials': s['trials'], 'is': r4(s['meanInSample']), 'oos': r4(s['meanOutOfSample'])} for s in noise['summary']],
                  'worldsData': [[[r4(p['inSample']), r4(p['outOfSample'])] for p in w['picks']] for w in noise['results']]},
    }


if __name__ == '__main__':
    namespace, notebook = run_notebook()
    data = web_data(namespace)
    (OUTPUT / 'optimization-results.json').write_text(json.dumps(data, ensure_ascii=False, separators=(',', ':'), allow_nan=False) + '\n', encoding='utf-8')
    (OUTPUT / 'robo-trade-15.ipynb').write_text(json.dumps(notebook, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print(f"Executed {notebook['metadata']['execution']['codeCells']} notebook code cells; wrote optimization-results.json and robo-trade-15.ipynb")
