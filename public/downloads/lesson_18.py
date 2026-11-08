"""Chapter 2 - market data and time: timezones, calendars, corporate actions.

Offline teaching example. Prices are SYNTHETIC for the invented symbol DEMO.
The calendar facts (US DST end on 2026-11-01, NYSE holidays and early closes
in Nov-Dec 2026) come from the NYSE hours and calendars page, checked
2026-11-08. Standard library only (zoneinfo needs system tz data; on Windows
run `pip install tzdata`). Run: python3 lesson_18.py
"""

import csv
import hashlib
import io
import math
import random
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

NEW_YORK = ZoneInfo("America/New_York")
BANGKOK = ZoneInfo("Asia/Bangkok")
SEED = 20261102

# NYSE, Nov-Dec 2026 (nyse.com/markets/hours-calendars, checked 2026-11-08)
HOLIDAYS = {date(2026, 11, 26): "Thanksgiving Day", date(2026, 12, 25): "Christmas Day"}
EARLY_CLOSES = {date(2026, 11, 27): time(13, 0), date(2026, 12, 24): time(13, 0)}
REGULAR_OPEN, REGULAR_CLOSE = time(9, 30), time(16, 0)

# Synthetic corporate actions for DEMO (invented for teaching).
SPLIT_DATE, SPLIT_RATIO = date(2026, 11, 16), 2.0        # 2-for-1, effective at the open
DIVIDEND_EX_DATE, DIVIDEND = date(2026, 12, 9), 0.40     # cash per post-split share


def sessions(start, end):
    """Expected NYSE sessions with their close time in New York and in UTC."""
    out, d = [], start
    while d <= end:
        if d.weekday() < 5 and d not in HOLIDAYS:
            close_local = datetime.combine(d, EARLY_CLOSES.get(d, REGULAR_CLOSE), NEW_YORK)
            out.append({"date": d, "close_ny": close_local, "close_utc": close_local.astimezone(timezone.utc)})
        d += timedelta(days=1)
    return out


def make_raw_bars(start=date(2026, 10, 19), end=date(2026, 12, 31), seed=SEED):
    """Unadjusted synthetic daily bars stamped at the session close in UTC (ISO 'Z')."""
    rng = random.Random(seed)
    price, rows = 50.0, []
    for s in sessions(start, end):
        if s["date"] == SPLIT_DATE:
            price /= SPLIT_RATIO
        if s["date"] == DIVIDEND_EX_DATE:
            price -= DIVIDEND
        open_ = price * math.exp(rng.gauss(0, 0.003))
        price = open_ * math.exp(rng.gauss(0.0004, 0.012))
        rows.append({"time": s["close_utc"].strftime("%Y-%m-%dT%H:%M:%SZ"),
                     "open": round(open_, 4), "close": round(price, 4),
                     "volume": int(800_000 * (SPLIT_RATIO if s["date"] >= SPLIT_DATE else 1) * rng.uniform(0.7, 1.3))})
    return rows


def parse_utc(text):
    return datetime.fromisoformat(text.replace("Z", "+00:00"))


def session_date(text, tz=NEW_YORK):
    return parse_utc(text).astimezone(tz).date()


def audit_bars(rows, start, end):
    """Report duplicates, unexpected dates and missing sessions against the calendar."""
    expected = [s["date"] for s in sessions(start, end)]
    seen, duplicates = set(), []
    for r in rows:
        d = session_date(r["time"])
        if d in seen:
            duplicates.append(d)
        seen.add(d)
    return {"expected": len(expected), "rows": len(rows), "duplicates": duplicates,
            "missing": [d for d in expected if d not in seen],
            "not_a_session": sorted(d for d in seen if d not in set(expected))}


def adjustment_factors(dates, closes):
    """Backward multiplicative factors (CRSP-style): multiply raw prices before
    each event so that returns across the event are economic returns.

    Split: factor 1/ratio for dates before the split date.
    Cash dividend D with ex-date e: factor (1 - D / close on the session before e).
    """
    factors = [1.0] * len(dates)
    for i, d in enumerate(dates):
        if d == SPLIT_DATE:
            for j in range(i):
                factors[j] /= SPLIT_RATIO
        if d == DIVIDEND_EX_DATE:
            k = 1 - DIVIDEND / closes[i - 1]
            for j in range(i):
                factors[j] *= k
    return factors


def simple_returns(values):
    return [b / a - 1 for a, b in zip(values, values[1:])]


def to_csv(rows):
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=list(rows[0]), lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue()


def snapshot_id(rows):
    return hashlib.sha256(to_csv(rows).encode()).hexdigest()[:16]

# %% [markdown]
# # บทที่ 2 — ข้อมูลตลาดและเวลา
#
# ราคาในไฟล์นี้เป็น **ข้อมูลสมมติ** ของหุ้นชื่อสมมติ `DEMO` มีเหตุการณ์สมมติสองอย่าง: แตกหุ้น 2:1 วันที่ 16 พ.ย. 2026
# และปันผล 0.40 ต่อหุ้น ex-date 9 ธ.ค. 2026 ส่วนปฏิทินตลาดเป็นของจริงจาก NYSE ตรวจเมื่อ 8 พ.ย. 2026

# %%
START, END = date(2026, 10, 19), date(2026, 12, 31)
cal = sessions(START, END)
print("Expected sessions:", len(cal))
for s in cal:
    if s["date"] in (date(2026, 10, 30), date(2026, 11, 2), date(2026, 11, 27)):
        print(s["date"], "close NY", s["close_ny"].strftime("%H:%M %Z"), "= UTC", s["close_utc"].strftime("%H:%M"))
assert len(cal) == 52
assert cal[9]["close_utc"].hour == 20 and cal[10]["close_utc"].hour == 21   # Oct 30 EDT, Nov 2 EST

# %% [markdown]
# ## 1. วันเดียวกันในสาม timezone
#
# ราคาปิดของตลาดสหรัฐวันที่ 3 พ.ย. เกิดตอน 04:00 ของวันที่ 4 พ.ย. ตามเวลาไทย
# ถ้าแปลงเวลาเป็น Asia/Bangkok แล้วตัดวันที่ ทุกแถวจะเลื่อนไปหนึ่งวัน

# %%
raw = make_raw_bars()
row = raw[11]
print("Stored     :", row["time"])
print("New York   :", parse_utc(row["time"]).astimezone(NEW_YORK))
print("Bangkok    :", parse_utc(row["time"]).astimezone(BANGKOK))
shifted = sum(1 for r in raw if session_date(r["time"], BANGKOK) != session_date(r["time"]))
print("Rows whose Bangkok date differs from the New York session date:", shifted, "of", len(raw))
assert shifted == len(raw)

# %% [markdown]
# ## 2. ตรวจกับปฏิทินตลาด
#
# จำลองข้อมูลที่ส่งมาไม่เรียบร้อย: แถวซ้ำหนึ่งแถว แถวหายหนึ่งวัน และแถวในวันหยุด Thanksgiving

# %%
messy = [dict(r) for r in raw]
messy.insert(5, dict(messy[5]))                              # duplicate
del messy[20]                                                # one session missing
messy.append({"time": "2026-11-26T21:00:00Z", "open": 1.0, "close": 1.0, "volume": 10})
report = audit_bars(messy, START, END)
for k, v in report.items():
    print(f"{k:14s}", v)
assert report["duplicates"] == [session_date(raw[5]["time"])]
assert report["missing"] == [session_date(raw[19]["time"])]
assert report["not_a_session"] == [date(2026, 11, 26)]
clean = audit_bars(raw, START, END)
assert not clean["duplicates"] and not clean["missing"] and not clean["not_a_session"]

# %% [markdown]
# ## 3. ราคาไม่ปรับกับราคาปรับย้อนหลัง
#
# วันแตกหุ้น ราคาไม่ปรับดูเหมือนร่วงครึ่งหนึ่งในวันเดียว ถ้าใช้ราคานี้คำนวณสัญญาณ กฎจะเห็นการร่วงที่ไม่เคยเกิดขึ้นกับเงินของผู้ถือหุ้น

# %%
dates = [session_date(r["time"]) for r in raw]
closes = [r["close"] for r in raw]
factors = adjustment_factors(dates, closes)
adjusted = [c * f for c, f in zip(closes, factors)]
i_split, i_div = dates.index(SPLIT_DATE), dates.index(DIVIDEND_EX_DATE)
raw_ret, adj_ret = simple_returns(closes), simple_returns(adjusted)
print("Split day close-to-close   raw:", f"{raw_ret[i_split - 1]:+.2%}", " adjusted:", f"{adj_ret[i_split - 1]:+.2%}")
print("Ex-dividend day            raw:", f"{raw_ret[i_div - 1]:+.2%}", " adjusted:", f"{adj_ret[i_div - 1]:+.2%}")
# Economic check: adjusted return on the split day equals raw close * ratio / previous close - 1.
assert math.isclose(adj_ret[i_split - 1], closes[i_split] * SPLIT_RATIO / closes[i_split - 1] - 1, rel_tol=1e-12)
# Multiplicative adjustment on the ex-date gives close / (previous close - D) - 1.
assert math.isclose(adj_ret[i_div - 1], closes[i_div] / (closes[i_div - 1] - DIVIDEND) - 1, rel_tol=1e-12)
total_return = (closes[i_div] + DIVIDEND) / closes[i_div - 1] - 1
print("Ex-dividend day total return (close + D) / previous close:", f"{total_return:+.2%}")
assert abs(adj_ret[i_div - 1] - total_return) < 1e-4
assert raw_ret[i_split - 1] < -0.4

# %% [markdown]
# ## 4. ราคาปรับย้อนหลังเปลี่ยนได้ ต้องจด as-of
#
# ราคาปรับย้อนหลังที่ดาวน์โหลดก่อนวันปันผลกับหลังวันปันผล *ไม่ตรงกัน* แม้เป็นวันเดียวกันในอดีต
# เราจึงเก็บ snapshot ของข้อมูลพร้อมวันที่ดาวน์โหลดและ checksum

# %%
before_div = [i for i, d in enumerate(dates) if d < DIVIDEND_EX_DATE]
asof_nov = adjustment_factors(dates[:before_div[-1] + 1], closes[:before_div[-1] + 1])
asof_dec = factors[:before_div[-1] + 1]
print("Adjusted close on", dates[0], "as of Dec 8:", round(closes[0] * asof_nov[0], 4))
print("Adjusted close on", dates[0], "as of Dec 31:", round(closes[0] * asof_dec[0], 4))
assert closes[0] * asof_nov[0] != closes[0] * asof_dec[0]
print("Snapshot id of raw bars:", snapshot_id(raw), "rows", len(raw))
assert snapshot_id(raw) == snapshot_id(make_raw_bars())

# %% [markdown]
# ## 5. วันที่ปิดเร็ว
#
# วันหลัง Thanksgiving และวันที่ 24 ธ.ค. ตลาดปิด 13:00 แท่งรายวันยังมีหนึ่งแถว
# แต่ volume และช่วงเวลาซื้อขายสั้นกว่าปกติ ถ้ากฎใช้เวลา 15:50 เพื่อส่งคำสั่ง วันนั้นตลาดปิดไปแล้ว

# %%
for s in cal:
    if s["date"] in EARLY_CLOSES:
        minutes = (datetime.combine(s["date"], EARLY_CLOSES[s["date"]]) - datetime.combine(s["date"], REGULAR_OPEN)).seconds // 60
        print(s["date"], "closes", s["close_ny"].strftime("%H:%M %Z"), "- session minutes:", minutes, "instead of 390")
order_time = time(15, 50)
blocked = [s["date"] for s in cal if order_time >= EARLY_CLOSES.get(s["date"], REGULAR_CLOSE)]
print("Days a 15:50 order would miss:", blocked)
assert blocked == sorted(EARLY_CLOSES)
print("ALL CHECKS PASSED")
