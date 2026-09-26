#!/usr/bin/env python3
"""Create a self-contained teaching notebook and save actual cell outputs.

Requires nbformat for authoring only. The notebook calculations use Python's
standard library. Cells are executed sequentially in a fresh Python namespace;
this is explicitly recorded as Python execution, not a Jupyter-kernel run.
Run: python3 make_notebook.py
"""
import argparse
import ast
import contextlib
import io
import os
from pathlib import Path
import platform
import tempfile
import textwrap

import nbformat

ROOT = Path(__file__).resolve().parent


def make_notebook():
    import base64, json, re
    notebook = nbformat.v4.new_notebook()
    notebook.metadata = {
        'kernelspec': {'display_name': 'Python 3', 'language': 'python', 'name': 'python3'},
        'language_info': {'name': 'python', 'version': platform.python_version()},
        'title': 'Backtest Performance Evaluation — S&P 500 EMA20 / EMA200',
        'execution_method': 'Sequential Python exec in a fresh namespace; not a Jupyter-kernel validation run.',
        'data_provenance': json.loads((ROOT/'data/provenance.json').read_text())}
    cells = [nbformat.v4.new_markdown_cell('''# S&P 500: EMA 20/200 บนข้อมูลจริง 20 ปี

ใช้ราคา Yahoo Finance ช่วง 2006-09-26 ถึง 2026-09-25 และ 400 วันก่อนหน้าสำหรับ EMA
ราคาเป็นข้อมูลจริง แต่การซื้อขาย ต้นทุน และดอกเบี้ยเป็นสมมติฐาน ดัชนีราคาไม่รวมเงินปันผล

เลือก Run All ได้โดยไม่ต้องดาวน์โหลดข้อมูลเพิ่ม Snapshot ราคาและ engine ฝังใน Notebook นี้
เซลล์แรกแตกไฟล์ลงโฟลเดอร์ชั่วคราว ส่วนรายงานที่สร้างเองเขียนไว้ในโฟลเดอร์ที่รัน
เนื้อหาและตัวอย่างโค้ดถัดไปดึงจาก chapter.md เพื่อให้ตัวเลขตรงกับบทเรียน''')]
    files = {name:base64.b64encode((ROOT/name).read_bytes()).decode() for name in ['lesson_14.py','data/sp500-daily.csv','data/provenance.json']}
    setup = '''from pathlib import Path
import base64, tempfile, importlib.util, sys
work_dir = Path(tempfile.mkdtemp(prefix="robo-sp500-"))
embedded_files = '''+repr(files)+'''
for name, encoded in embedded_files.items():
    target = work_dir / name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(base64.b64decode(encoded))
spec = importlib.util.spec_from_file_location("lesson_14", work_dir / "lesson_14.py")
lesson = importlib.util.module_from_spec(spec)
sys.modules["lesson_14"] = lesson
spec.loader.exec_module(lesson)
bars, backtest, report = lesson.export_all(work_dir)
print(report['provenance']['name'], report['parameters']['startDate'], report['parameters']['endDate'])
print(len(backtest['dailyEquity']), "trading days;", len(backtest['tradeLedger']), "closed trades")
'''
    cells.append(nbformat.v4.new_code_cell(setup, metadata={'jupyter':{'source_hidden':True}}))
    chapter=ROOT.parents[1]/'content/chapters/14-backtest-performance-evaluation.md'
    text=(chapter if chapter.exists() else ROOT/'chapter.md').read_text()
    for i,part in enumerate(re.split(r'```python\n(.*?)\n```',text,flags=re.S)):
        if i%2:
            source=part.replace('Path("trades.csv")','(work_dir / "trades.csv")').replace('Path("equity-daily.csv")','(work_dir / "equity-daily.csv")').replace('load_bars("ema-bars.csv")','load_bars(work_dir / "ema-bars.csv")')
            cells.append(nbformat.v4.new_code_cell(source))
        else:
            part=re.sub(r' \{#[a-z0-9-]+\}','',part)
            part=re.sub(r'^::: details (.+)$',r'### \1',part,flags=re.M)
            part=re.sub(r'^:::.*$', '',part,flags=re.M)
            if part.strip():cells.append(nbformat.v4.new_markdown_cell(part.strip()))
    cells.append(nbformat.v4.new_markdown_cell('## กราฟจากข้อมูลเดียวกัน\n\nกราฟเปรียบเทียบพอร์ตใช้สีม่วงสำหรับ EMA 20/200 และสีเขียวสำหรับการถือ S&P 500 Price Index ทั้งช่วง ส่วนกราฟการแจกแจงใช้สีเขียวสำหรับกำไรและสีแดงสำหรับขาดทุน ภาพครอบคลุมมูลค่าพอร์ต ผลตอบแทนสะสม ผลรายเทรด และระยะเวลาของ Drawdown'))
    cells.append(nbformat.v4.new_code_cell('''import re
report_html = (work_dir / "performance-report.html").read_text(encoding="utf-8")
for svg in re.findall(r"<svg.*?</svg>", report_html, flags=re.S):
    svg = svg.replace('<svg ', '<svg xmlns="http://www.w3.org/2000/svg" style="background:white;color:black;font:12px sans-serif" ', 1)
    display({'image/svg+xml': svg}, raw=True)
'''))
    cells.append(nbformat.v4.new_markdown_cell('## ทดลองต้นทุนบนราคาชุดเดิม\n\n0, 10 และ 20 bps เป็นสมมติฐานต้นทุนที่ทดลอง ไม่ใช่ราคาตลาดชุดใหม่ การเปลี่ยนต้นทุนต้องรันซื้อขายใหม่เพราะจำนวนหน่วยเปลี่ยนด้วย'))
    cells.append(nbformat.v4.new_code_cell('''for bps in [0, 10, 20]:
    scenario = lesson.make_results(lesson.run_backtest(bars, {'feeRatePerSide': bps/10000}))
    print(bps, 'bps/side:', f"{scenario['portfolioMetrics']['totalReturn']:.4%}",
          'final USD', f"{scenario['portfolioMetrics']['finalEquity']:,.2f}")
'''))
    notebook.cells=cells
    return notebook


def execute_cells(notebook):
    namespace = {'__name__': '__notebook__'}
    count = 0
    original_cwd = Path.cwd()
    with tempfile.TemporaryDirectory(prefix='robo-ema-notebook-') as execution_dir:
        os.chdir(execution_dir)
        try:
            for cell in notebook.cells:
                if cell.cell_type != 'code':
                    continue
                count += 1
                outputs = []

                def display(data, raw=False, **_kwargs):
                    if raw:
                        outputs.append(nbformat.v4.new_output('display_data', data=data, metadata={}))
                    else:
                        outputs.append(nbformat.v4.new_output('display_data', data={'text/plain': repr(data)}, metadata={}))

                namespace['display'] = display
                stdout, stderr = io.StringIO(), io.StringIO()
                with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                    exec(compile(cell.source, f'notebook-cell-{count}', 'exec'), namespace)
                if stdout.getvalue():
                    outputs.insert(0, nbformat.v4.new_output('stream', name='stdout', text=stdout.getvalue()))
                if stderr.getvalue():
                    outputs.append(nbformat.v4.new_output('stream', name='stderr', text=stderr.getvalue()))
                cell.execution_count = count
                cell.outputs = outputs
        finally:
            os.chdir(original_cwd)
    notebook.metadata['executed_code_cells'] = count
    return count


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--no-execute', action='store_true')
    args = parser.parse_args()
    notebook = make_notebook()
    count = execute_cells(notebook) if not args.no_execute else 0
    nbformat.validate(notebook)
    target = ROOT / 'robo-trade-14.ipynb'
    nbformat.write(notebook, target)
    print(f'Wrote {target.name}: {len(notebook.cells)} cells; {count} code cells actually executed sequentially in Python.')
    print('Validated notebook schema; execution method is recorded explicitly and is not a Jupyter-kernel claim.')


if __name__ == '__main__':
    main()
