"""Prework P1 - use AI to write Python, then verify it yourself.

Offline teaching example. All prices are SYNTHETIC (seeded random walk), not
market data. Standard library only. Run: python3 lesson_16.py

The file is in percent format: the builder turns each `# %%` block into a
notebook cell. Running the script executes every block, so the asserts below
are the lesson's tests.
"""

import json
import math
import random

SEED = 20261108
TRADING_DAYS = 252


def make_bars(n=300, seed=SEED, start=100.0):
    """Synthetic daily bars: open/close only, invented currency units."""
    rng = random.Random(seed)
    bars, close = [], start
    for day in range(n):
        open_ = close * math.exp(rng.gauss(0, 0.004))
        close = open_ * math.exp(rng.gauss(0.0003, 0.011))
        bars.append({"day": day, "open": round(open_, 6), "close": round(close, 6)})
    return bars


def sma(values, window):
    """Trailing mean that uses values[t-window+1 .. t]; None before enough data."""
    out = []
    for t in range(len(values)):
        out.append(None if t + 1 < window else sum(values[t + 1 - window:t + 1]) / window)
    return out


# A draft of the kind an AI assistant often returns for the prompt
# "write an SMA crossover backtest". It runs and looks reasonable.
def draft_backtest(bars, window=20):
    closes = [b["close"] for b in bars]
    avg = sma(closes, window)
    returns = []
    for t in range(1, len(bars)):
        signal = 1.0 if avg[t] is not None and closes[t] > avg[t] else 0.0   # close t ...
        returns.append(signal * (closes[t] / closes[t - 1] - 1))            # ... earns close t-1 -> t
    return returns


def reviewed_backtest(bars, window=20, cost_bps=5.0):
    """Course fill rule: signal after close t, hold open t+1 -> open t+2.

    Returns one dict per holding interval with the signal day, the fill day,
    gross and net return. Cost is charged on |change in weight| at each fill.
    """
    closes = [b["close"] for b in bars]
    avg = sma(closes, window)
    rows, weight = [], 0.0
    for t in range(len(bars) - 2):
        target = 1.0 if avg[t] is not None and closes[t] > avg[t] else 0.0
        cost = abs(target - weight) * cost_bps / 10000
        gross = target * (bars[t + 2]["open"] / bars[t + 1]["open"] - 1)
        rows.append({"signal_day": t, "fill_day": t + 1, "weight": target,
                     "gross": gross, "net": (1 - cost) * (1 + gross) - 1})
        weight = target
    return rows


def unchanged_after_future_edit(known_rows, bars, cutoff, seed=1):
    """Test 1: rewrite every bar after `cutoff` at random. Rows already known by
    `cutoff` must stay identical. `known_rows(bars, cutoff)` returns those rows."""
    changed = [dict(b) for b in bars]
    rng = random.Random(seed)
    for b in changed[cutoff + 1:]:
        b["open"] *= 1 + rng.uniform(-0.3, 0.3)
        b["close"] *= 1 + rng.uniform(-0.3, 0.3)
    return known_rows(bars, cutoff) == known_rows(changed, cutoff)


def return_depends_on_own_signal_close(rows_fn, bars, day):
    """Test 2: halve only close[day]. If the return earned up to close[day]
    changes, the rule used close[day] to decide a trade it already earned."""
    changed = [dict(b) for b in bars]
    changed[day]["close"] *= 0.5
    return rows_fn(bars)[day - 1] != rows_fn(changed)[day - 1]


def annualized_volatility(daily_returns, periods=TRADING_DAYS):
    mean = sum(daily_returns) / len(daily_returns)
    var = sum((r - mean) ** 2 for r in daily_returns) / (len(daily_returns) - 1)
    return math.sqrt(var) * math.sqrt(periods)


def compound(returns):
    return math.prod(1 + r for r in returns) - 1


PROMPT_TEMPLATE = """Role: you write Python for a teaching backtest. Standard library only.
Data: list of dicts with day, open, close (synthetic, daily, no gaps).
Rule: signal from close of day t; trade at open of day t+1; hold until open t+2.
Costs: 5 bps on each change in weight. Long or cash only, weight 0 or 1.
Return: one row per holding interval with signal_day, fill_day, weight, gross, net.
Do not: drop rows silently, use future bars, annualize with 365, call any API.
Also write two asserts: (1) editing bars after day k leaves rows known by day k unchanged;
(2) editing only close k does not change any return earned up to close k."""

# %% [markdown]
# # Prework P1 — ใช้ AI เขียนโค้ด แล้วตรวจเอง
#
# ข้อมูลทุกแถวใน Notebook นี้เป็น **ราคาสมมติ** จาก random walk ที่กำหนด seed `20261108` ไม่ใช่ราคาตลาด
# ใช้แค่ Python standard library รันจากบนลงล่างได้โดยไม่ต้องต่ออินเทอร์เน็ต
#
# เป้าหมาย: รับโค้ดร่างจาก AI แล้วจับข้อผิดพลาดด้วยการทดสอบ ไม่ใช่ด้วยการอ่านผ่าน ๆ

# %%
bars = make_bars()
assert len(bars) == 300 and bars == make_bars()
print("Synthetic bars:", len(bars), "seed", SEED)
for b in bars[:3]:
    print(b)

# %% [markdown]
# ## 1. Prompt ที่ระบุกติกาครบ
#
# Prompt ที่ดีบอกข้อมูล เวลาใช้สัญญาณ ราคาที่ใช้ซื้อขาย ต้นทุน และสิ่งที่ห้ามทำ
# ยิ่งระบุชัด AI ยิ่งเดาน้อยลง แต่เรายังต้องตรวจผลทุกครั้ง

# %%
print(PROMPT_TEMPLATE)

# %% [markdown]
# ## 2. โค้ดร่างที่รันผ่านแต่ผิดกติกา
#
# `draft_backtest` ใช้ close ของวัน t ทั้งตัดสินใจและรับผลตอบแทนถึง close วันเดียวกัน
# ผลจึงดีเกินจริง ทั้งที่โค้ดไม่มี error เลย

# %%
draft = draft_backtest(bars)
reviewed = reviewed_backtest(bars)
print("Draft compounded return   :", f"{compound(draft):.1%}")
print("Reviewed gross return     :", f"{compound([r['gross'] for r in reviewed]):.1%}")
print("Reviewed net return (5bps):", f"{compound([r['net'] for r in reviewed]):.1%}")

# %% [markdown]
# ## 3. Test สองแบบสำหรับ look-ahead
#
# Test 1 สุ่มเปลี่ยนราคาทุกแท่งหลังวัน k แถวที่รู้ผลแล้วก่อนวัน k ต้องไม่เปลี่ยน
# ฉบับร่างผ่าน test นี้ เพราะมันไม่ได้แอบดูวันพรุ่งนี้ มันใช้ราคาปิด *วันเดียวกับที่รับผลตอบแทน*
# Test 2 แก้เฉพาะ close วัน k ถ้าผลตอบแทนที่ได้มาแล้วจนถึง close k เปลี่ยนตาม แปลว่าตัดสินใจหลังรู้ผล

# %%
cutoff = 150

def reviewed_known(b, k):
    # Interval filled at open d+1 ends at open d+2: known once d+2 <= k.
    return [(r["weight"], round(r["gross"], 12)) for r in reviewed_backtest(b) if r["fill_day"] + 1 <= k]

def draft_known(b, k):
    # Draft row i covers close i -> close i+1: known once i+1 <= k.
    return [round(r, 12) for i, r in enumerate(draft_backtest(b)) if i + 1 <= k]

print("Test 1, edit bars after day", cutoff)
print("  reviewed unchanged:", unchanged_after_future_edit(reviewed_known, bars, cutoff))
print("  draft unchanged   :", unchanged_after_future_edit(draft_known, bars, cutoff), "<- passes, yet the draft is wrong")
assert unchanged_after_future_edit(reviewed_known, bars, cutoff)
assert unchanged_after_future_edit(draft_known, bars, cutoff)

def reviewed_by_signal_day(b):
    # Return earned by the decision made at close t, aligned so index day-1 is
    # the row decided at close day-1 (it cannot depend on close day).
    return [round(r["gross"], 12) for r in reviewed_backtest(b)]

print("Test 2, halve close", cutoff, "only")
print("  draft return up to close", cutoff, "changes:", return_depends_on_own_signal_close(draft_backtest, bars, cutoff))
print("  reviewed row decided at close", cutoff - 1, "changes:", return_depends_on_own_signal_close(reviewed_by_signal_day, bars, cutoff))
assert return_depends_on_own_signal_close(draft_backtest, bars, cutoff)
assert not return_depends_on_own_signal_close(reviewed_by_signal_day, bars, cutoff)

# %% [markdown]
# ## 4. ตรวจหน่วยและ annualization
#
# AI มักเลือก 365 วันเพราะเป็นจำนวนวันในปี ข้อมูลหุ้นรายวันในคอร์สนี้ใช้ 252 วันทำการ
# ตรวจด้วยค่าที่คำนวณมือได้: ผลตอบแทน +1% กับ −1% สลับกัน มี sample std เท่ากับ 0.01 × √(n/(n−1))

# %%
alternating = [0.01, -0.01] * 50
expected = 0.01 * math.sqrt(100 / 99) * math.sqrt(252)
assert math.isclose(annualized_volatility(alternating), expected, rel_tol=1e-12)
print("Annualized vol, 252 days:", round(annualized_volatility(alternating), 6))
print("Same data with 365 days :", round(annualized_volatility(alternating, 365), 6), "(wrong convention for this data)")

# %% [markdown]
# ## 5. ตรวจบัญชีต้นทุน
#
# ต้นทุนเกิดเฉพาะวันที่น้ำหนักเปลี่ยน ผลรวมจำนวนครั้งที่เปลี่ยน × 5 bps ต้องอธิบายส่วนต่าง gross กับ net ได้

# %%
changes = sum(1 for prev, cur in zip([0.0] + [r["weight"] for r in reviewed], [r["weight"] for r in reviewed]) if prev != cur)
gross_total = compound([r["gross"] for r in reviewed])
net_total = compound([r["net"] for r in reviewed])
cost_factor = (1 - 5 / 10000) ** changes
assert math.isclose((1 + net_total), (1 + gross_total) * cost_factor, rel_tol=1e-12)
print("Weight changes:", changes)
print("Gross vs net:", f"{gross_total:.2%}", "->", f"{net_total:.2%}")

# %% [markdown]
# ## 6. บันทึก trial log ทุกครั้งที่รัน
#
# ทุกครั้งที่ให้ AI แก้กฎแล้วรันใหม่ ให้เพิ่มหนึ่งบรรทัด แม้ผลจะแย่ การนับจำนวนครั้งที่ลองต้องเริ่มตั้งแต่วันแรก

# %%
trial = {"trial": 1, "rule": "close > SMA20, long/cash", "fill": "open t+1 -> open t+2",
         "cost_bps": 5, "data": "synthetic seed 20261108", "net_return": round(net_total, 6),
         "note": "first reviewed version; draft rejected for same-bar lookahead"}
print(json.dumps(trial, ensure_ascii=False))
print("ALL CHECKS PASSED")
