"""Offline journal replay and risk-gate capstone; no broker connection."""
from dataclasses import dataclass, field
from decimal import Decimal
import json

D = Decimal

@dataclass
class Ledger:
    cash: Decimal = D("2000.00")
    position: int = 0
    filled: dict = field(default_factory=dict)
    seen: dict = field(default_factory=dict)
    unknown_intents: set = field(default_factory=set)

    def apply(self, event):
        identifier = event["event_id"]
        signature = json.dumps(event, sort_keys=True)
        if identifier in self.seen:
            if self.seen[identifier] != signature:
                raise ValueError("Conflicting journal event ID")
            return
        kind = event["kind"]
        if kind == "INTENT":
            self.unknown_intents.add(event["intent_id"])
        elif kind == "ACK":
            self.unknown_intents.discard(event["intent_id"])
        elif kind == "FILL":
            quantity = event["quantity"]
            price, fee = D(event["price"]), D(event["fee"])
            if type(quantity) is not int or quantity <= 0 or price <= 0 or fee < 0:
                raise ValueError("Invalid synthetic BUY fill")
            self.position += quantity
            self.cash -= price*quantity + fee
            key = event["intent_id"]
            self.filled[key] = self.filled.get(key, 0) + quantity
        else:
            raise ValueError("Unknown journal event kind")
        self.seen[identifier] = signature

def replay(events):
    ledger = Ledger()
    for event in events:
        ledger.apply(event)
    return ledger

JOURNAL = [
    dict(event_id="e1", kind="INTENT", intent_id="demo-1"),
    dict(event_id="e2", kind="ACK", intent_id="demo-1"),
    dict(event_id="fill-1", kind="FILL", intent_id="demo-1", quantity=4,
         price="99.90", fee="0.40"),
]
BROKER_FILLS = JOURNAL[2:] + [
    dict(event_id="fill-2", kind="FILL", intent_id="demo-1", quantity=6,
         price="100.00", fee="0.60")
]

@dataclass(frozen=True)
class Limits:
    max_position: int = 20
    max_order_value: Decimal = D("500.00")
    max_data_age_s: int = 20
    loss_stop: Decimal = D("20.00")

def gate(ledger, quantity, price, data_age_s, day_pnl, *,
         pending_buy=0, pending_notional=D("0"), fee_buffer=D("0"),
         reconciled=False, kill_switch=False, limits=Limits()):
    """Illustrative BUY-only limits. All pending orders must already be reconciled."""
    reasons = []
    price, day_pnl = D(price), D(day_pnl)
    if kill_switch:
        reasons.append("MANUAL_STOP")
    if not reconciled or ledger.unknown_intents:
        reasons.append("STATE_UNCERTAIN")
    if not 0 <= data_age_s <= limits.max_data_age_s:
        reasons.append("STALE_DATA")
    if day_pnl <= -limits.loss_stop:
        reasons.append("LOSS_LIMIT")
    if type(quantity) is not int or quantity <= 0 or price <= 0:
        reasons.append("INVALID_ORDER")
        return reasons
    value = D(quantity) * price
    if ledger.position + pending_buy + quantity > limits.max_position:
        reasons.append("POSITION_LIMIT")
    if value > limits.max_order_value:
        reasons.append("ORDER_VALUE_LIMIT")
    if value + pending_notional + fee_buffer > ledger.cash:
        reasons.append("CASH_LIMIT")
    return reasons

def demonstration():
    before = replay(JOURNAL)
    after = replay(JOURNAL + BROKER_FILLS)
    snapshot = dict(position=10, cash=D("999.40"), open_orders=0)
    matched = (after.position == snapshot["position"] and after.cash == snapshot["cash"]
               and snapshot["open_orders"] == 0 and not after.unknown_intents)
    rows = {}
    for name, quantity, age, pnl, reconciled, stopped in [
        ("normal", 3, 2, "-0.60", matched, False),
        ("stale", 3, 30, "-0.60", matched, False),
        ("large_order", 6, 2, "-0.60", matched, False),
        ("loss_stop", 3, 2, "-21", matched, False),
        ("before_reconciliation", 3, 2, "-0.60", False, False),
        ("manual_stop", 3, 2, "-0.60", matched, True),
    ]:
        reasons = gate(after, quantity, "100", age, pnl, reconciled=reconciled, kill_switch=stopped)
        rows[name] = reasons or ["ALLOW_SIMULATION"]
    return before, after, dict(before=dict(position=before.position, cash=str(before.cash)),
        recovered=dict(position=after.position, cash=str(after.cash), matched=matched), gates=rows)

def capstone():
    """Research rule -> recovered state -> risk gate -> synthetic fill -> replay."""
    closes = [D("100"), D("101"), D("102")]
    sma3 = sum(closes) / 3
    target = 13 if closes[-1] > sma3 else 0
    ledger = replay(JOURNAL + BROKER_FILLS)
    delta = target - ledger.position
    marked_pnl = ledger.cash + ledger.position * closes[-1] - D("2000.00")
    reasons = gate(ledger, delta, closes[-1], 2, marked_pnl, reconciled=True,
                   fee_buffer=D("0.30"))
    if reasons:
        raise RuntimeError(reasons)
    new_events = [
        dict(event_id="e3", kind="INTENT", intent_id="demo-2"),
        dict(event_id="e4", kind="ACK", intent_id="demo-2"),
        dict(event_id="fill-3", kind="FILL", intent_id="demo-2", quantity=delta,
             price="102.00", fee="0.30"),
    ]
    serialized = json.dumps(JOURNAL + BROKER_FILLS + new_events)
    recovered = replay(json.loads(serialized))
    assert recovered.position == target and recovered.cash == D("693.10")
    return dict(sma3=str(sma3), target=target, delta=delta, simulated_fill_price="102.00",
                cash=str(recovered.cash), position=recovered.position,
                equity_at_102=str(recovered.cash + recovered.position*D("102")),
                journal_roundtrip="PASS")


def checks():
    before, after, result = demonstration()
    assert before.position == 4 and before.cash == D("1600.00")
    assert after.position == 10 and after.cash == D("999.40")
    assert len(after.seen) == 4
    assert replay(JOURNAL + BROKER_FILLS*3).position == 10
    assert result["gates"]["normal"] == ["ALLOW_SIMULATION"]
    assert result["gates"]["stale"] == ["STALE_DATA"]
    assert gate(after, 3, "100", 2, "0", pending_buy=9, reconciled=True) == ["POSITION_LIMIT"]
    unknown = replay([dict(event_id="u1", kind="INTENT", intent_id="lost-ack")])
    assert "STATE_UNCERTAIN" in gate(unknown, 1, "100", 1, "0", reconciled=True)
    assert "LOSS_LIMIT" in gate(after, 1, "100", 2, "-20", reconciled=True)
    assert "CASH_LIMIT" in gate(after, 1, "100", 2, "0", pending_notional=D("900"), reconciled=True)
    try:
        replay(JOURNAL + [{**JOURNAL[-1], "quantity": 8}])
    except ValueError:
        pass
    else:
        raise AssertionError("Conflicting event must fail")
    return "11 recovery/risk checks passed"

if __name__ == "__main__":
    print(json.dumps(demonstration()[2], indent=2))
    print(json.dumps(capstone(), indent=2))
    print(checks())
