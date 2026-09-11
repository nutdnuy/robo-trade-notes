"""Offline event simulator with partial fills and exact decimal accounting.

Run: python lesson_06.py
SYNTHETIC is not a listed security. No network or brokerage access.
"""

# %% Setup and input events
from dataclasses import dataclass
from decimal import Decimal, ROUND_FLOOR, ROUND_HALF_UP
import platform

D = Decimal
print({"python": platform.python_version(), "arithmetic": "decimal; prices rounded half-up to cents"})
bars = [
    # session, open, close, simulated available shares at this open, close target
    (1, "100", "101", 10, 8),
    (2, "101", "103", 3, 8),
    (3, "103", "99", 3, 0),
    (4, "99", "98", 10, 0),
    (5, "98", "102", 10, 5),
    (6, "102", "104", 2, 0),
    (7, "103", "103", 10, 0),
]
print("session | open | close | capacity | target_after_close")
for bar in bars:
    print(" | ".join(map(str, bar)))

# %% State and target-to-order conversion
@dataclass
class Order:
    order_id: str
    side: int
    remaining: int
    submitted_session: int


class Simulator:
    """Single asset, integer shares, at most one active order, no leverage."""
    def __init__(self, cash="1000", fee="1", slippage="0.001"):
        self.cash, self.fee, self.slippage = D(cash), D(fee), D(slippage)
        self.position = 0
        self.pending = None
        self.events, self.fills, self.ledger = [], [], []
        self.sequence = 0

    def set_target(self, session, target):
        if not isinstance(target, int) or target < 0:
            raise ValueError("Target must be a nonnegative integer")
        delta = target - self.position
        side = 1 if delta > 0 else -1
        if self.pending and self.pending.side == side and self.pending.remaining == abs(delta):
            return
        if self.pending:
            self.events.append((session, self.pending.order_id, "CANCELLED", self.pending.remaining))
            self.pending = None
        if delta:
            self.sequence += 1
            self.pending = Order(f"O{self.sequence:02d}", side, abs(delta), session)
            self.events.append((session, self.pending.order_id, "SUBMITTED", abs(delta)))

    def on_open(self, session, open_price, capacity):
        if not self.pending:
            return
        if session <= self.pending.submitted_session:
            raise ValueError("An order cannot fill before its next session")
        if capacity < 0 or int(capacity) != capacity:
            raise ValueError("Capacity must be a nonnegative integer")
        order = self.pending
        price = (D(open_price) * (1 + order.side * self.slippage)).quantize(D(".01"), rounding=ROUND_HALF_UP)
        if price <= 0:
            raise ValueError("Price must be positive")
        quantity = min(order.remaining, capacity)
        if not quantity:
            return
        if order.side == 1:
            affordable = max(0, int(((self.cash - self.fee) / price).to_integral_value(rounding=ROUND_FLOOR)))
            quantity = min(quantity, affordable)
            if quantity == 0:
                self.events.append((session, order.order_id, "REJECTED_CASH", order.remaining))
                self.pending = None
                return
        else:
            quantity = min(quantity, self.position)
            if quantity == 0 or self.cash + quantity * price < self.fee:
                self.events.append((session, order.order_id, "REJECTED_SELL", order.remaining))
                self.pending = None
                return
        self.cash -= order.side * quantity * price + self.fee
        self.position += order.side * quantity
        order.remaining -= quantity
        state = "FILLED" if order.remaining == 0 else "PARTIALLY_FILLED"
        self.events.append((session, order.order_id, state, order.remaining))
        self.fills.append({"session": session, "order": order.order_id, "side": "BUY" if order.side == 1 else "SELL", "quantity": quantity, "fill_price": price, "fee": self.fee, "cash_after": self.cash, "position_after": self.position})
        if not order.remaining:
            self.pending = None
        assert self.cash >= 0 and self.position >= 0

    def mark_close(self, session, close_price):
        equity = self.cash + self.position * D(close_price)
        self.ledger.append({"session": session, "cash": self.cash, "position": self.position, "close": D(close_price), "equity": equity})

# %% Run the ordered event loop
sim = Simulator()
for session, opening, closing, capacity, target in bars:
    sim.on_open(session, opening, capacity)
    sim.mark_close(session, closing)
    sim.set_target(session, target)
print("session | cash | shares | equity at close")
for row in sim.ledger:
    print(row["session"], row["cash"], row["position"], row["equity"], sep=" | ")

# %% Inspect orders separately from fills
print("session | order | state | remaining")
for event in sim.events:
    print(*event, sep=" | ")
print("session | side | shares | fill price | fee | cash after")
for fill in sim.fills:
    print(fill["session"], fill["side"], fill["quantity"], fill["fill_price"], fill["fee"], fill["cash_after"], sep=" | ")
print({"final_cash_usd": str(sim.cash), "net_pnl_usd": str(sim.cash - D("1000")), "fill_count": len(sim.fills), "fees_usd": str(sum(fill["fee"] for fill in sim.fills))})

# %% Independent cash reconstruction
cash = D("1000")
shares = 0
for fill in sim.fills:
    sign = 1 if fill["side"] == "BUY" else -1
    cash = cash - sign * fill["quantity"] * fill["fill_price"] - fill["fee"]
    shares += sign * fill["quantity"]
    assert cash == fill["cash_after"] and shares == fill["position_after"]
assert cash == D("977.40") and shares == 0 and sim.pending is None
assert len(sim.fills) == 5
assert len([event for event in sim.events if event[2] == "CANCELLED"]) == 2
assert sim.fills[0]["session"] == 2 and sim.fills[0]["quantity"] == 3
for row in sim.ledger:
    assert row["equity"] == row["cash"] + row["position"] * row["close"]
# Arithmetic independent of the event loop: reference-open P&L less slippage and fees.
reference_pnl = 6 * D("99") - 3 * D("101") - 3 * D("103") + 2 * (D("103") - D("102"))
slippage_cost = sum(D(fill["quantity"]) * abs(fill["fill_price"] - D(bars[fill["session"] - 1][1])) for fill in sim.fills)
assert D("1000") + reference_pnl - slippage_cost - D("5") == cash
print({"reference_open_pnl_usd": str(reference_pnl), "slippage_cost_usd": str(slippage_cost), "accounting": "PASS"})

# %% Failure cases and exercise answer
poor = Simulator(cash="100")
poor.set_target(1, 8)
poor.on_open(2, "101", 10)
assert poor.cash == D("100") and poor.position == 0
assert poor.events[-1][2] == "REJECTED_CASH" and not poor.fills
duplicate = Simulator()
duplicate.set_target(1, 8)
duplicate.on_open(2, "101", 3)
duplicate.set_target(2, 8)
assert duplicate.sequence == 1 and duplicate.pending.remaining == 5
assert duplicate.position == 3
duplicate.on_open(3, "103", 0)
assert duplicate.position == 3 and duplicate.pending.remaining == 5
try:
    too_early = Simulator()
    too_early.set_target(2, 8)
    too_early.on_open(2, "101", 10)
except ValueError:
    pass
else:
    raise AssertionError("Same-session fill should fail")
print("PASS: insufficient cash, repeated target, zero liquidity, and same-session rejection")
