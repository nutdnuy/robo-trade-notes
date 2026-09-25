"""Build and execute the self-contained lesson 13 notebook with standard Python.

Every saved code cell is compiled and executed in order in one shared namespace;
captured stdout is saved as notebook output. No kernel, market API, or download.
"""

import contextlib
import hashlib
import io
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "public" / "downloads"
SOURCE = (OUTPUT / "lesson_13.py").read_text(encoding="utf-8")
DEFINITIONS = SOURCE.split('if __name__ == "__main__":')[0]


def markdown(text):
    return {"cell_type": "markdown", "metadata": {}, "source": text.splitlines(keepends=True)}


def code(text):
    return {"cell_type": "code", "metadata": {}, "source": text.splitlines(keepends=True),
            "execution_count": None, "outputs": []}


cells = [
    markdown("""# Introduction of Backtest — ห้องทดลองออฟไลน์

ตัวอย่างนี้ใช้ **ข้อมูลสมมติทั้งหมด** ไม่มีราคาตลาด ไม่มีวันที่จริง และไม่มีการดาวน์โหลดข้อมูล
กำหนด seed **20260925** ก่อนประเมินผล และใช้หนึ่งเส้นทางเพื่อสอนกลไก ไม่ได้ค้นหา seed หรือพารามิเตอร์ที่กำไรดี

กฎคงที่: SMA 20/50 ของ close เป็น long/cash; ประเมิน sample volatility จาก 20 close-to-close simple returns
และ annualize ด้วย √252; target volatility 10% ต่อปี; จำกัดน้ำหนักไม่เกิน 1; เงินสดและ risk-free rate 0%
ซื้อขายได้เป็นเศษหุ้น ไม่มี leverage, ดอกเบี้ย, ภาษี หรือข้อจำกัดปริมาณซื้อขาย

แบบใช้ข้อมูลทันเวลา: ใช้ close ของ session t−1 ตัดสินใจ แล้วซื้อขายที่ open t และถือจน open t+1
แบบผิด: แอบใช้ close t และ volatility ที่รวม close t ไปซื้อขายที่ open t ซึ่งยังไม่รู้ข้อมูลนั้น
ทุกแบบประเมินช่วง open60 → open319 เท่ากัน รวม 259 ช่วงผลตอบแทน

Notebook นี้ใช้เพียง Python standard library รันทุก cell จากบนลงล่างได้โดยไม่ต้องติดตั้งแพ็กเกจ
"""),
    code(DEFINITIONS + '\nprint("Definitions loaded: fixed SMA 20/50, volatility window 20, cap 1, offline only.")\n'),
    markdown("""## 1. ตรวจข้อมูลและหน่วยก่อนเริ่ม

ราคาเป็นหน่วยเงินสมมติต่อหุ้น; `session` เป็นเลขลำดับ ไม่ใช่วันทำการจริง
252 sessions/year เป็น convention สำหรับแสดง annualized statistics ในตัวอย่างเท่านั้น
"""),
    code('''data = make_data()
assert len(data["rows"]) == 320
assert data == make_data()
print("Seed:", data["metadata"]["seed"])
print("Rows:", len(data["rows"]))
print("Units:", data["metadata"]["units"])
for row in data["rows"][:3] + data["rows"][-2:]:
    print(row)
'''),
    markdown("""## 2. เปรียบเทียบสี่กรณีด้วยกฎเดิม

เปลี่ยนเฉพาะความถูกต้องของเวลาและการกำหนดขนาด position
ตัวเลขที่ดีขึ้นในกรณีใช้ข้อมูลอนาคตไม่ใช่ผลที่นำไปซื้อขายได้จริง
Volatility targeting เป็นการเปลี่ยน exposure ไม่ใช่หลักประกันว่าจะเพิ่มผลตอบแทนหรือจำกัด drawdown
"""),
    code('''results = compare_backtests(data, cost_bps=5, target_vol=0.1)
assert all(len(result["returns"]) == 259 for result in results)
assert all(result["sessions"] == list(range(60, 320)) for result in results)
print_summary(results)
'''),
    markdown("""## 3. ใช้ benchmark ในช่วงเวลาเดียวกัน

Buy and hold ซื้อที่ open60 ถือจน open319 และเสียต้นทุนเข้า/ออก 5 bps แบบเดียวกัน
ไม่มีค่าใช้จ่ายซ้ำทุก session เมื่อถือหุ้นเต็มพอร์ตอยู่แล้ว
"""),
    code('''benchmark = evaluate_benchmark(data, cost_bps=5)
print_summary([benchmark])
price_ratio = data["rows"][-1]["open"] / data["rows"][60]["open"]
c = 5 / 10000
expected_final_equity = price_ratio * (1 - c) / (1 + c)
assert math.isclose(benchmark["equity"][-1], expected_final_equity, rel_tol=1e-12)
print("Verified buy-and-hold entry/exit cost identity:", round(expected_final_equity, 8))
'''),
    markdown("""## 4. ตรวจว่าสัญญาณรู้ได้เมื่อใด

กรณีที่ถูกต้องต้องมี `decisionSession < session` เสมอ
การ lag เพียงหนึ่งแถวไม่ใช่ใบรับรองทั่วไป: ในตัวอย่างนี้เราเลือก next open เป็นราคาซื้อขายที่เกิดหลัง close ที่ใช้ตัดสินใจ
"""),
    code('''for result in results:
    causal = result["id"].startswith("causal")
    assert all(row["decisionSession"] == row["session"] - int(causal) for row in result["audit"])
    first = result["audit"][0]
    print(result["id"], "execution open", first["session"], "uses close", first["decisionSession"])

# Altering a not-yet-known close must not change the first causal weight.
changed = json.loads(json.dumps(data))
changed["rows"][60]["close"] *= 2
before = evaluate_backtest(data, vol_target=True)["weights"][0]
after = evaluate_backtest(changed, vol_target=True)["weights"][0]
assert before == after
print("Future-close perturbation leaves the first causal weight unchanged:", before)
'''),
    markdown("""## 5. ตรวจบัญชีต้นทุนและการ drift ของน้ำหนัก

ให้ E เป็น equity ก่อนซื้อขาย, a เป็น risky weight ก่อนซื้อขาย, w เป็น risky weight เป้าหมายหลังหักค่าธรรมเนียม
และ c เป็นค่าธรรมเนียมต่อมูลค่าซื้อขาย แล้ว k = equity หลังค่าธรรมเนียม / E แก้สมการ
`k = 1 − c × |w × k − a|` ได้ตรงตัว

หลังถือครองหนึ่งช่วงที่สินทรัพย์มี simple return R:
`portfolio factor = k × (1 + w × R)` และน้ำหนักก่อน rebalance ครั้งถัดไปคือ
`a_next = w × (1 + R) / (1 + w × R)`

การปิดสถานะสุดท้ายที่ open319 หัก `c × risky holdings` และรวมในผลตอบแทนช่วงสุดท้าย
turnover คือผลรวมมูลค่าซื้อขายสัมบูรณ์หาร equity ก่อนแต่ละเหตุการณ์ซื้อขาย จึงไม่ใช่จำนวน trades
"""),
    code('''trade = rebalance(0.5, 0.8, 0.001)
assert math.isclose(trade["factor"] + trade["feeFraction"], 1.0, abs_tol=1e-12)
assert math.isclose(trade["turnover"], abs(0.8 * trade["factor"] - 0.5), abs_tol=1e-12)
print("Rebalance a=0.5 -> post-fee w=0.8; c=0.1%:", trade)
for result in results + [benchmark]:
    assert all(0 <= weight <= 1 for weight in result["weights"])
    assert math.isclose(math.prod(1 + r for r in result["returns"]), result["equity"][-1], rel_tol=1e-12)
    print(result["id"], "final liquidation turnover:", round(result["audit"][-1]["finalLiquidationTurnover"], 6))
print("Verified: all weights in [0,1], compounded returns equal final equity, entry and final liquidation included.")
'''),
    markdown("""## อ่านผลอย่างไร

- Total return = final equity / initial equity − 1
- CAGR = (final equity / initial equity)^(252/n) − 1; n คือจำนวนช่วงผลตอบแทน 259
- Annualized volatility = sample standard deviation ของ net simple returns × √252
- Annualized Sharpe = mean(net simple returns) / sample standard deviation × √252 โดย rf=0
- Drawdown = equity / running peak − 1; MDD คือค่าต่ำสุด (แสดงเป็นค่าติดลบ)
- การ annualize ด้วย √252 เป็น convention ของแบบฝึกหัด ไม่ได้แก้ serial dependence หรือยืนยันความแม่นยำทางสถิติ

การได้ผลดีในข้อมูลสมมติไม่ใช่หลักฐานว่า SMA หรือ volatility targeting ทำกำไรในตลาดจริง
ต้นทุนจริงยังอาจรวม bid–ask spread, slippage, market impact และข้อจำกัด execution ที่แบบฝึกหัดนี้ไม่ได้จำลอง

แหล่งที่ Nuth ให้: Yves Hilpisch, *Python for Algorithmic Trading*, PDF หน้า 84 (lag สัญญาณ),
94 (proportional costs), 100 (data snooping/overfitting), 148–152 (event-based accounting),
278–279 (Sharpe และ relative drawdown); และ transcript *Introduction to Backtesting* ของ Hudson & Thames
สำหรับการแยก side/size และ volatility targeting
ข้อมูลสมมติ สูตรบัญชี post-fee target weight และโค้ดชุดนี้สร้างขึ้นเพื่ออธิบายกลไก ไม่ใช่ผลทดลองตลาดจากแหล่งอ้างอิง
"""),
]

namespace = {"__name__": "backtest_intro_notebook"}
execution_count = 0
for cell in cells:
    source = "".join(cell["source"])
    cell["id"] = hashlib.sha256((cell["cell_type"] + source).encode()).hexdigest()[:12]
    if cell["cell_type"] == "code":
        execution_count += 1
        captured = io.StringIO()
        with contextlib.redirect_stdout(captured):
            exec(compile(source, f"lesson13-cell-{execution_count}", "exec"), namespace)
        cell["execution_count"] = execution_count
        cell["outputs"] = [{"output_type": "stream", "name": "stdout", "text": captured.getvalue().splitlines(keepends=True)}]

notebook = {"cells": cells, "metadata": {
    "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
    "language_info": {"name": "python", "version": sys.version.split()[0]},
    "execution": {"method": "Each code cell executed in order by CPython in one shared namespace", "codeCells": execution_count},
}, "nbformat": 4, "nbformat_minor": 5}

snapshot = {"metadata": {"seed": namespace["SEED"], "costBps": 5, "targetVol": 0.1,
                          "generator": "scripts/build_backtest_intro.py", "kind": "synthetic teaching results"},
            "results": namespace["results"], "benchmark": namespace["benchmark"]}
for name, value in [("backtest-intro-data.json", namespace["data"]),
                    ("backtest-intro-results.json", snapshot), ("robo-trade-13.ipynb", notebook)]:
    (OUTPUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")

print(f"Executed {execution_count} notebook code cells; saved notebook, fixed synthetic data, and comparison results.")
namespace["print_summary"](namespace["results"] + [namespace["benchmark"]])
