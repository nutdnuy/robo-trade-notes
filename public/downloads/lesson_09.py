"""Offline broker contract demonstration; these names are NOT Webull SDK methods."""
from dataclasses import dataclass
from decimal import Decimal
import json

D = Decimal

@dataclass
class MockOrder:
    intent_id: str
    symbol: str
    quantity: int
    limit: Decimal
    filled: int = 0
    average: Decimal = D("0")
    status: str = "ACCEPTED"

class PaperBroker:
    """Deliberately small BUY-only simulator with deterministic partial fills."""
    def __init__(self, cash="2000.00"):
        self.cash = D(cash)
        self.position = 0
        self.orders = {}
        self.fill_ids = {}
        self.fees = D("0")

    def submit(self, intent_id, symbol, quantity, limit, lose_response=False):
        limit = D(limit)
        if intent_id in self.orders:
            old = self.orders[intent_id]
            if (old.symbol, old.quantity, old.limit) != (symbol, quantity, limit):
                raise ValueError("Intent ID reused with a different payload")
            return old
        if type(quantity) is not int or quantity <= 0 or limit <= 0:
            raise ValueError("Positive integer quantity and positive limit required")
        reserved = sum((o.quantity - o.filled) * o.limit for o in self.orders.values()
                       if o.status in ("ACCEPTED", "PARTIAL"))
        if D(quantity) * limit > self.cash - reserved:
            raise ValueError("Insufficient unreserved cash")
        order = MockOrder(intent_id, symbol, quantity, limit)
        self.orders[intent_id] = order
        if lose_response:
            raise TimeoutError("Mock accepted order but its response was lost")
        return order

    def query(self, intent_id):
        return self.orders.get(intent_id)

    def apply_fill(self, intent_id, fill_id, quantity, price, fee="0.00"):
        price, fee = D(price), D(fee)
        signature = (intent_id, quantity, price, fee)
        if fill_id in self.fill_ids:
            if self.fill_ids[fill_id] != signature:
                raise ValueError("Fill ID reused with a different payload")
            return "DUPLICATE_IGNORED"
        order = self.orders[intent_id]
        if order.status not in ("ACCEPTED", "PARTIAL"):
            raise ValueError("Order is not open")
        if type(quantity) is not int or quantity <= 0 or quantity > order.quantity - order.filled:
            raise ValueError("Invalid fill quantity")
        if not D("0") < price <= order.limit or fee < 0:
            raise ValueError("Invalid fill price or fee")
        debit = price * quantity + fee
        if debit > self.cash:
            raise ValueError("Insufficient cash including fees")
        order.average = (order.average * order.filled + price * quantity) / (order.filled + quantity)
        order.filled += quantity
        order.status = "FILLED" if order.filled == order.quantity else "PARTIAL"
        self.cash -= debit
        self.position += quantity
        self.fees += fee
        self.fill_ids[fill_id] = signature
        return order.status

    def cancel(self, intent_id):
        order = self.orders[intent_id]
        if order.status in ("ACCEPTED", "PARTIAL"):
            order.status = "CANCELED"
        return order.status

def remaining_target(target, broker):
    pending = sum(o.quantity - o.filled for o in broker.orders.values()
                  if o.status in ("ACCEPTED", "PARTIAL"))
    return target - broker.position - pending

def demonstration():
    broker = PaperBroker()
    key = "DEMO|2026-01-05T14:31:00Z|v1|BUY10"
    try:
        broker.submit(key, "DEMO", 10, "100.00", lose_response=True)
    except TimeoutError:
        recovered = broker.query(key)
        assert recovered is not None
    statuses = [broker.query(key).status]
    statuses.append(broker.apply_fill(key, "fill-1", 4, "99.90", "0.40"))
    after_partial = dict(cash=str(broker.cash), position=broker.position,
                         pending=broker.query(key).quantity-broker.query(key).filled,
                         additional_order=remaining_target(10, broker))
    duplicate = broker.apply_fill(key, "fill-1", 4, "99.90", "0.40")
    statuses.append(broker.apply_fill(key, "fill-2", 6, "100.00", "0.60"))
    return broker, key, dict(statuses=statuses, partial=after_partial, duplicate=duplicate,
        cash=str(broker.cash), position=broker.position,
        average_price=str(broker.query(key).average), fees=str(broker.fees),
        equity_at_100=str(broker.cash + broker.position*D("100")))

def checks():
    broker, key, result = demonstration()
    assert result["statuses"] == ["ACCEPTED", "PARTIAL", "FILLED"]
    assert broker.position == 10 and broker.cash == D("999.40")
    assert broker.query(key).average == D("99.96")
    assert remaining_target(10, broker) == 0
    broker.submit(key, "DEMO", 10, "100.00")
    assert len(broker.orders) == 1
    try:
        broker.submit(key, "DEMO", 11, "100.00")
    except ValueError:
        pass
    else:
        raise AssertionError("Payload mismatch must be rejected")
    canceled = PaperBroker()
    canceled.submit("c", "DEMO", 10, "100")
    canceled.apply_fill("c", "c1", 4, "100", "0.4")
    canceled.cancel("c")
    assert canceled.position == 4 and remaining_target(10, canceled) == 6
    try:
        canceled.apply_fill("c", "c2", 6, "100")
    except ValueError:
        pass
    else:
        raise AssertionError("Canceled mock order must reject new fills")
    return "8 broker-state checks passed"

if __name__ == "__main__":
    print(json.dumps(demonstration()[2], indent=2))
    print(checks())
