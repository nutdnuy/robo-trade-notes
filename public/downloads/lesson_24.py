"""Chapter 11 - from backtest to orders: a mock broker with risk controls.

Offline teaching example. Nothing here connects to a broker or sends an order.
Bars are SYNTHETIC for invented symbols DEMO and ALT. The MockBroker fills
orders against the next bar's open with slippage and a volume cap, so learners
can see partial fills, rejections, duplicate retries and a kill switch before
they ever touch a paper-trading account. Standard library only.
Run: python3 lesson_24.py
"""

import json
import math
import random

SEED = 20261124


def make_bars(seed=SEED, days=8):
    rng = random.Random(seed)
    bars = {}
    for symbol, price, volume in [("DEMO", 50.0, 400_000), ("ALT", 120.0, 3_000)]:
        rows = []
        for d in range(days):
            open_ = price * math.exp(rng.gauss(0, 0.006))
            price = open_ * math.exp(rng.gauss(0.0005, 0.012))
            rows.append({"day": d, "open": round(open_, 2), "close": round(price, 2),
                         "volume": int(volume * rng.uniform(0.6, 1.4))})
        bars[symbol] = rows
    return bars


class RiskGate:
    """Checks run before an order reaches the broker. Every rejection has a reason."""

    def __init__(self, whitelist, max_order_notional=5_000, max_position_notional=8_000, max_orders_per_day=6):
        self.whitelist = set(whitelist)
        self.max_order_notional = max_order_notional
        self.max_position_notional = max_position_notional
        self.max_orders_per_day = max_orders_per_day
        self.kill_switch = False
        self.orders_today = 0

    def check(self, order, price, current_qty):
        if self.kill_switch:
            return "kill switch is on"
        if order["symbol"] not in self.whitelist:
            return "symbol not in whitelist"
        if order["qty"] <= 0 or order["qty"] != int(order["qty"]):
            return "quantity must be a positive whole number"
        notional = order["qty"] * price
        if notional > self.max_order_notional:
            return f"order notional {notional:.0f} exceeds {self.max_order_notional}"
        signed = order["qty"] if order["side"] == "BUY" else -order["qty"]
        if abs(current_qty + signed) * price > self.max_position_notional:
            return "position limit"
        if self.orders_today >= self.max_orders_per_day:
            return "daily order count limit"
        return None


class MockBroker:
    """Fills at the next open +/- slippage, at most `participation` of that bar's volume.

    Market orders fill what the volume cap allows; the rest is cancelled at the
    end of the day (day order). Limit orders fill only if the open is at or
    better than the limit. Re-sending a known client_order_id returns the
    existing order instead of creating a second one.
    """

    def __init__(self, bars, slippage_bps=5, participation=0.01):
        self.bars, self.slippage_bps, self.participation = bars, slippage_bps, participation
        self.orders, self.positions, self.cash, self.log = {}, {}, 0.0, []

    def record(self, event, **fields):
        self.log.append({"event": event, **fields})

    def submit(self, order, day):
        cid = order["client_order_id"]
        if cid in self.orders:
            self.record("DUPLICATE_IGNORED", client_order_id=cid, day=day)
            return self.orders[cid]
        state = {**order, "status": "NEW", "filled": 0, "avg_price": None, "submitted_day": day}
        self.orders[cid] = state
        self.record("NEW", day=day, **{k: order[k] for k in ("client_order_id", "symbol", "side", "qty", "type")})
        return state

    def reject(self, order, day, reason):
        self.orders[order["client_order_id"]] = {**order, "status": "REJECTED", "filled": 0, "reason": reason}
        self.record("REJECTED", day=day, client_order_id=order["client_order_id"], reason=reason)

    def run_day(self, day):
        for state in self.orders.values():
            if state["status"] != "NEW" or state["submitted_day"] != day - 1:
                continue
            bar = self.bars[state["symbol"]][day]
            sign = 1 if state["side"] == "BUY" else -1
            price = bar["open"] * (1 + sign * self.slippage_bps / 10000)
            if state["type"] == "LIMIT" and sign * (price - state["limit_price"]) > 0:
                state["status"] = "CANCELED"
                self.record("CANCELED", day=day, client_order_id=state["client_order_id"], reason="limit not reached at open")
                continue
            cap = int(bar["volume"] * self.participation)
            qty = min(state["qty"], cap)
            state["filled"], state["avg_price"] = qty, round(price, 4)
            state["status"] = "FILLED" if qty == state["qty"] else "PARTIALLY_FILLED_THEN_CANCELED"
            self.positions[state["symbol"]] = self.positions.get(state["symbol"], 0) + sign * qty
            self.cash -= sign * qty * price
            self.record(state["status"], day=day, client_order_id=state["client_order_id"], filled=qty, price=round(price, 4))


def implementation_shortfall(side, decision_price, fill_price):
    """Cost in bps relative to the price when the decision was made (positive = worse)."""
    sign = 1 if side == "BUY" else -1
    return sign * (fill_price / decision_price - 1) * 10000

# %% [markdown]
# # บทที่ 11 — Execution และ Paper Trading
#
# Notebook นี้ **ไม่ต่อ broker และไม่ส่งคำสั่งจริง** ใช้ `MockBroker` ที่เขียนเอง ราคาเป็นข้อมูลสมมติของหุ้นชื่อสมมติ `DEMO` และ `ALT`
# `ALT` มี volume ต่ำโดยตั้งใจ เพื่อให้เห็น partial fill

# %%
bars = make_bars()
assert bars == make_bars()
for s, rows in bars.items():
    print(s, "day 0:", rows[0], "| average volume:", sum(r["volume"] for r in rows) // len(rows))

# %% [markdown]
# ## 1. Risk gate ทำงานก่อนคำสั่งถึง broker

# %%
gate = RiskGate(whitelist=["DEMO", "ALT"])
broker = MockBroker(bars)
tests = [
    {"client_order_id": "d0-DEMO-buy", "symbol": "DEMO", "side": "BUY", "qty": 80, "type": "MARKET"},
    {"client_order_id": "d0-ALT-buy", "symbol": "ALT", "side": "BUY", "qty": 40, "type": "MARKET"},
    {"client_order_id": "d0-NVDA-buy", "symbol": "NVDA", "side": "BUY", "qty": 1, "type": "MARKET"},
    {"client_order_id": "d0-DEMO-big", "symbol": "DEMO", "side": "BUY", "qty": 500, "type": "MARKET"},
    {"client_order_id": "d0-DEMO-half", "symbol": "DEMO", "side": "BUY", "qty": 2.5, "type": "MARKET"},
]
for order in tests:
    price = bars[order["symbol"]][0]["close"] if order["symbol"] in bars else 100.0
    reason = gate.check(order, price, broker.positions.get(order["symbol"], 0))
    if reason:
        broker.reject(order, 0, reason)
    else:
        broker.submit(order, 0)
        gate.orders_today += 1
    print(f"{order['client_order_id']:14s} -> {broker.orders[order['client_order_id']]['status']:8s} {reason or ''}")
assert [broker.orders[o["client_order_id"]]["status"] for o in tests] == ["NEW", "NEW", "REJECTED", "REJECTED", "REJECTED"]

# %% [markdown]
# ## 2. ส่งซ้ำด้วย client_order_id เดิม
#
# เครือข่ายหลุดหลังส่งคำสั่ง โปรแกรมไม่รู้ว่าคำสั่งถึง broker ไหม จึงส่งซ้ำ
# ถ้าใช้ id เดิม broker คืนคำสั่งเดิม ถ้าสร้าง id ใหม่ทุกครั้ง เราจะซื้อสองเท่า

# %%
again = broker.submit(tests[0], 0)
assert again is broker.orders["d0-DEMO-buy"]
print("Orders with id d0-DEMO-buy:", sum(1 for k in broker.orders if k == "d0-DEMO-buy"))
print("Last log entry:", broker.log[-1])

# %% [markdown]
# ## 3. Fill ที่ open ของวันถัดไป และ partial fill

# %%
broker.run_day(1)
for cid in ("d0-DEMO-buy", "d0-ALT-buy"):
    o = broker.orders[cid]
    print(f"{cid}: {o['status']}, filled {o['filled']} of {o['qty']} at {o['avg_price']}")
print("Positions:", broker.positions)
assert broker.orders["d0-DEMO-buy"]["status"] == "FILLED"
assert broker.orders["d0-ALT-buy"]["status"] == "PARTIALLY_FILLED_THEN_CANCELED"

# %% [markdown]
# ## 4. Implementation shortfall
#
# ราคาตอนตัดสินใจคือ close วัน 0 ราคาที่ได้จริงคือ open วัน 1 บวก slippage
# ส่วนต่างแยกได้เป็น gap ข้ามคืน (close → open) กับ slippage

# %%
for cid in ("d0-DEMO-buy", "d0-ALT-buy"):
    o = broker.orders[cid]
    decision, open1 = bars[o["symbol"]][0]["close"], bars[o["symbol"]][1]["open"]
    total = implementation_shortfall("BUY", decision, o["avg_price"])
    gap = implementation_shortfall("BUY", decision, open1)
    print(f"{o['symbol']}: decision {decision}, open {open1}, fill {o['avg_price']} -> shortfall {total:+.1f} bps = gap {gap:+.1f} + slippage {total - gap:+.1f}")
    assert math.isclose(1 + total / 10000, (1 + gap / 10000) * (1 + 5 / 10000), rel_tol=1e-6)  # fill rounded to 4 dp

# %% [markdown]
# ## 5. Limit order ที่ไม่ได้ fill

# %%
limit = {"client_order_id": "d1-DEMO-limit", "symbol": "DEMO", "side": "BUY", "qty": 20, "type": "LIMIT",
         "limit_price": round(bars["DEMO"][1]["close"] * 0.97, 2)}
assert gate.check(limit, bars["DEMO"][1]["close"], broker.positions.get("DEMO", 0)) is None
broker.submit(limit, 1)
broker.run_day(2)
print(limit["client_order_id"], "->", broker.orders["d1-DEMO-limit"]["status"], "| limit", limit["limit_price"], "| open", bars["DEMO"][2]["open"])
assert broker.orders["d1-DEMO-limit"]["status"] == "CANCELED"

# %% [markdown]
# ## 6. Kill switch และการกระทบยอด
#
# เปิด kill switch แล้วทุกคำสั่งถูกปฏิเสธ จากนั้นกระทบยอด position จาก audit log กับ position ของ broker

# %%
gate.kill_switch = True
blocked = {"client_order_id": "d2-DEMO-sell", "symbol": "DEMO", "side": "SELL", "qty": 10, "type": "MARKET"}
print("With kill switch:", gate.check(blocked, bars["DEMO"][2]["close"], broker.positions["DEMO"]))
from_log = {}
for e in broker.log:
    if e["event"] in ("FILLED", "PARTIALLY_FILLED_THEN_CANCELED"):
        o = broker.orders[e["client_order_id"]]
        from_log[o["symbol"]] = from_log.get(o["symbol"], 0) + (e["filled"] if o["side"] == "BUY" else -e["filled"])
print("Positions from log:", from_log, "| broker:", broker.positions)
assert from_log == broker.positions
print("Audit log lines:", len(broker.log))
print(json.dumps(broker.log[0]))
print("ALL CHECKS PASSED")
