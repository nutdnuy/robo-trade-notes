"""Offline event-time demonstration. No network or broker dependencies."""
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from statistics import mean
import json

BASE = datetime(2026, 1, 5, 14, 30, tzinfo=timezone.utc)

@dataclass(frozen=True)
class Tick:
    event_id: str
    event_s: int
    received_s: int
    price: float
    size: int = 1

TICKS = [
    Tick("t1", 10, 10, 100), Tick("t2", 40, 42, 101),
    Tick("t3", 70, 71, 102), Tick("t2", 40, 72, 101),
    Tick("t4", 65, 73, 101.5), Tick("t5", 55, 74, 99),
    Tick("t6", 125, 126, 103), Tick("t7", 190, 191, 104),
]

class EventTimeBars:
    """One synthetic instrument, 60-second bars and five-second lateness."""
    def __init__(self, bar_seconds=60, lateness_seconds=5):
        self.bar_seconds = bar_seconds
        self.lateness_seconds = lateness_seconds
        self.seen = {}
        self.pending = {}
        self.bars = []
        self.signals = []
        self.audit = []
        self.max_event_s = -1
        self.last_received_s = -1
        self.watermark_s = float("-inf")

    def ingest(self, tick):
        if tick.received_s < self.last_received_s:
            raise ValueError("Replay must preserve receive order")
        if tick.event_s > tick.received_s or tick.price <= 0 or tick.size <= 0:
            raise ValueError("Invalid synthetic tick")
        self.last_received_s = tick.received_s
        signature = (tick.event_s, tick.price, tick.size)
        if tick.event_id in self.seen:
            if self.seen[tick.event_id] != signature:
                raise ValueError("Conflicting payload for an existing event ID")
            self.audit.append((tick.event_id, "DUPLICATE"))
            return
        self.seen[tick.event_id] = signature
        start = tick.event_s // self.bar_seconds * self.bar_seconds
        if start + self.bar_seconds <= self.watermark_s:
            self.audit.append((tick.event_id, "LATE_QUARANTINE"))
            return
        self.pending.setdefault(start, []).append(tick)
        self.max_event_s = max(self.max_event_s, tick.event_s)
        self.watermark_s = self.max_event_s - self.lateness_seconds
        self.audit.append((tick.event_id, "ACCEPT"))
        for start in sorted(list(self.pending)):
            end = start + self.bar_seconds
            if end > self.watermark_s:
                continue
            rows = sorted(self.pending.pop(start), key=lambda t: (t.event_s, t.event_id))
            bar = dict(start_s=start, end_s=end, available_s=tick.received_s,
                       open=rows[0].price, high=max(t.price for t in rows),
                       low=min(t.price for t in rows), close=rows[-1].price,
                       volume=sum(t.size for t in rows))
            self.bars.append(bar)
            if len(self.bars) >= 3:
                recent = self.bars[-3:]
                if all(a["end_s"] == b["start_s"] for a, b in zip(recent, recent[1:])):
                    average = mean(b["close"] for b in recent)
                    self.signals.append(dict(bar_end_s=end, available_s=tick.received_s,
                                             sma3=average, target=int(bar["close"] > average)))

def replay(ticks=TICKS):
    engine = EventTimeBars()
    for tick in ticks:
        engine.ingest(tick)
    return engine

def freshness(engine, now_s, max_age_s=20):
    """Use the newest accepted event time; duplicates do not refresh price age."""
    age = now_s - engine.max_event_s
    return dict(age_seconds=age, allow_new_orders=0 <= age <= max_age_s)

def checks():
    engine = replay()
    assert [b["close"] for b in engine.bars] == [101, 102, 103]
    assert engine.bars[1]["open"] == 101.5
    assert [b["volume"] for b in engine.bars] == [2, 2, 1]
    assert engine.signals == [dict(bar_end_s=180, available_s=191, sma3=102, target=1)]
    assert sum(state == "DUPLICATE" for _, state in engine.audit) == 1
    assert sum(state == "LATE_QUARANTINE" for _, state in engine.audit) == 1
    assert len(engine.pending) == 1
    assert freshness(engine, 192)["allow_new_orders"]
    assert not freshness(engine, 220)["allow_new_orders"]
    assert replay().bars == engine.bars
    try:
        engine.ingest(Tick("t2", 40, 192, 999))
    except ValueError:
        pass
    else:
        raise AssertionError("Conflicting duplicate must fail")
    return "10 event-time checks passed"

if __name__ == "__main__":
    engine = replay()
    print(json.dumps(dict(bars=engine.bars, signals=engine.signals,
                          audit=engine.audit, freshness=freshness(engine, 220)), indent=2))
    print(checks())
