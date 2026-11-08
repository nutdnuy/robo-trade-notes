"""Prework P3 - Webull API MCP: let AI read data, then check what it says.

Offline teaching example. Nothing here connects to Webull. The bar response is
a SYNTHETIC fixture for the invented symbol DEMO, written in a simplified
shape for teaching; it is not Webull's exact response schema. Standard
library only. Run: python3 lesson_17.py
"""

import json
import math
from datetime import datetime, timedelta, timezone

# Tool groups as listed in the webull-openapi-mcp README (PyPI 1.2.6, checked
# 2026-11-08). WEBULL_TOOLSETS accepts: account, market-data, trading, instrument.
VALID_TOOLSETS = {"account", "market-data", "trading", "instrument"}
COURSE_TOOLSETS = {"market-data", "instrument"}

# Tools that change something even though they do not trade. The course keeps
# MCP read-only, so these must not be called either.
WRITE_TOOL_PREFIXES = ("place_", "modify_", "cancel_", "replace_", "create_", "update_",
                       "delete_", "add_", "remove_", "preview_")

SECRET_KEYS = ("WEBULL_APP_KEY", "WEBULL_APP_SECRET")


def check_mcp_config(server):
    """Return a list of problems in one MCP server entry (dict). Empty = OK for the course."""
    problems = []
    env = server.get("env", {})
    for key in SECRET_KEYS:
        value = env.get(key, "")
        if value and not value.startswith("${"):
            problems.append(f"{key} is written into the config file; load it from the environment instead")
    toolsets = {t.strip() for t in env.get("WEBULL_TOOLSETS", "").split(",") if t.strip()}
    if not toolsets:
        problems.append("WEBULL_TOOLSETS is empty, so every toolset including trading is enabled")
    unknown = toolsets - VALID_TOOLSETS
    if unknown:
        problems.append(f"unknown toolsets: {sorted(unknown)}")
    if "trading" in toolsets:
        problems.append("trading toolset enabled; this course is read-only")
    if "account" in toolsets:
        problems.append("account toolset exposes balances and positions; not needed for research")
    if env.get("WEBULL_ENVIRONMENT", "uat") == "prod" and ("trading" in toolsets or not toolsets):
        problems.append("prod environment together with trading tools")
    return problems


def write_tools(tool_names):
    return sorted(name for name in tool_names if name.startswith(WRITE_TOOL_PREFIXES))


def make_fixture():
    """Five synthetic daily bars for DEMO, timestamps in UTC (US market close 16:00 New York)."""
    closes = [100.00, 101.20, 100.70, 102.90, 103.40]
    bars, start = [], datetime(2026, 11, 2, 21, 0, tzinfo=timezone.utc)  # 16:00 EST
    for i, c in enumerate(closes):
        o = round(c - 0.5 + 0.2 * (i % 2), 2)
        bars.append({"time": (start + timedelta(days=i)).isoformat().replace("+00:00", "Z"),
                     "open": o, "high": round(max(o, c) + 0.6, 2), "low": round(min(o, c) - 0.7, 2),
                     "close": c, "volume": 1_000_000 + 25_000 * i})
    return {"symbol": "DEMO", "timespan": "D", "synthetic": True, "bars": bars}


REQUIRED_FIELDS = ("time", "open", "high", "low", "close", "volume")


def validate_bars(response):
    """Fail visibly on the problems that silently break a backtest."""
    errors, bars = [], response.get("bars", [])
    if not bars:
        return ["no bars returned"]
    times = []
    for i, b in enumerate(bars):
        missing = [f for f in REQUIRED_FIELDS if f not in b]
        if missing:
            errors.append(f"bar {i}: missing {missing}")
            continue
        t = datetime.fromisoformat(b["time"].replace("Z", "+00:00"))
        if t.tzinfo is None:
            errors.append(f"bar {i}: timestamp has no timezone")
        times.append(t)
        if not (b["low"] <= min(b["open"], b["close"]) and b["high"] >= max(b["open"], b["close"])):
            errors.append(f"bar {i}: high/low do not contain open/close")
        if b["volume"] < 0:
            errors.append(f"bar {i}: negative volume")
    if len(set(times)) != len(times):
        errors.append("duplicate timestamps")
    if times != sorted(times):
        errors.append("timestamps not in ascending order")
    return errors


def recompute_claims(response):
    closes = [b["close"] for b in response["bars"]]
    return {"first_close": closes[0], "last_close": closes[-1],
            "period_return": closes[-1] / closes[0] - 1, "max_close": max(closes),
            "up_days": sum(1 for a, b in zip(closes, closes[1:]) if b > a)}


def compare_claims(ai_claims, recomputed, tolerance=1e-4):
    report = {}
    for key, claimed in ai_claims.items():
        actual = recomputed[key]
        ok = math.isclose(claimed, actual, rel_tol=tolerance, abs_tol=tolerance) if isinstance(actual, float) else claimed == actual
        report[key] = {"ai": claimed, "recomputed": actual, "ok": ok}
    return report

# %% [markdown]
# # Prework P3 — Webull API MCP: ให้ AI อ่านข้อมูล แล้วตรวจสิ่งที่มันสรุป
#
# Notebook นี้ **ไม่ได้ต่อ Webull** ข้อมูลราคาเป็น fixture สมมติของหุ้นชื่อสมมติ `DEMO`
# รูปแบบ JSON ถูกย่อเพื่อการสอน ไม่ใช่ schema จริงของ Webull
# ส่วนที่เป็นของจริงคือชื่อ environment variable และ toolset ซึ่งตรวจจาก README ของ `webull-openapi-mcp` 1.2.6 เมื่อ 8 พฤศจิกายน 2026

# %% [markdown]
# ## 1. ตรวจไฟล์ตั้งค่า MCP ก่อนเปิดใช้
#
# ตั้งค่าแรกเขียน key ลงไฟล์และเปิดทุก toolset ตั้งค่าที่สองอ่าน key จาก environment และเปิดเฉพาะข้อมูลตลาดกับข้อมูลหลักทรัพย์

# %%
unsafe = {"command": "uvx", "args": ["webull-openapi-mcp", "serve"],
          "env": {"WEBULL_APP_KEY": "abc123", "WEBULL_APP_SECRET": "xyz789",
                  "WEBULL_ENVIRONMENT": "prod"}}
course = {"command": "uvx", "args": ["webull-openapi-mcp", "serve"],
          "env": {"WEBULL_APP_KEY": "${WEBULL_APP_KEY}", "WEBULL_APP_SECRET": "${WEBULL_APP_SECRET}",
                  "WEBULL_TOOLSETS": "market-data,instrument", "WEBULL_ENVIRONMENT": "uat"}}
for name, server in [("unsafe", unsafe), ("course", course)]:
    problems = check_mcp_config(server)
    print(name, "->", "OK" if not problems else f"{len(problems)} problems")
    for p in problems:
        print("   -", p)
assert check_mcp_config(course) == []
assert len(check_mcp_config(unsafe)) == 4

# %% [markdown]
# ## 2. เครื่องมือที่ "ไม่ใช่การซื้อขาย" ก็เขียนข้อมูลได้
#
# รายชื่อด้านล่างมาจากเครื่องมือที่ Cloud MCP ระบุว่าเป็น Non-Trading บางตัวสร้าง แก้ หรือลบ watchlist
# ถ้าให้ AI อนุมัติเครื่องมือเหล่านี้อัตโนมัติ มันแก้บัญชีของเราได้ แม้จะไม่ได้ส่งคำสั่งซื้อขาย

# %%
cloud_non_trading = ["get_stock_bars", "get_stock_snapshot", "get_instruments", "get_company_profile",
                     "get_watchlists", "create_watchlist", "add_watchlist_instruments",
                     "remove_watchlist_instruments", "update_watchlist", "delete_watchlist",
                     "get_account_balance", "get_account_positions", "get_order_history"]
writes = write_tools(cloud_non_trading)
print("Tools that change account data:", writes)
assert writes == ["add_watchlist_instruments", "create_watchlist", "delete_watchlist",
                  "remove_watchlist_instruments", "update_watchlist"]

# %% [markdown]
# ## 3. ตรวจข้อมูลแท่งราคาที่ MCP ส่งกลับ
#
# ก่อนใช้ข้อมูลใน backtest ให้ตรวจคอลัมน์ timezone ลำดับเวลา แถวซ้ำ และความสอดคล้องของ high/low

# %%
fixture = make_fixture()
print(json.dumps(fixture["bars"][0]))
assert validate_bars(fixture) == []
broken = json.loads(json.dumps(fixture))
broken["bars"][3]["time"] = broken["bars"][2]["time"]          # duplicate
broken["bars"][4]["high"] = broken["bars"][4]["close"] - 1     # impossible high
del broken["bars"][1]["volume"]                                # missing field
for e in validate_bars(broken):
    print("caught:", e)
assert len(validate_bars(broken)) == 3

# %% [markdown]
# ## 4. คำนวณซ้ำทุกตัวเลขที่ AI สรุปให้
#
# สมมติว่าเราถาม AI ว่า "DEMO 5 วันล่าสุดเป็นอย่างไร" แล้วได้คำตอบเป็นตัวเลขห้าตัว
# เราคำนวณจากข้อมูลชุดเดียวกันเอง แล้วเทียบทีละตัว

# %%
ai_claims = {"first_close": 100.0, "last_close": 103.4, "period_return": 0.034,
             "max_close": 103.4, "up_days": 4}
report = compare_claims(ai_claims, recompute_claims(fixture))
for key, row in report.items():
    print(f"{key:14s} AI={row['ai']!s:8s} recomputed={row['recomputed']!s:22s} {'OK' if row['ok'] else 'MISMATCH'}")
assert report["period_return"]["ok"] and not report["up_days"]["ok"]

# %% [markdown]
# ## 5. เก็บ audit log ของการเรียกเครื่องมือ
#
# จดทุกครั้งที่ AI เรียกเครื่องมือ: เวลา ชื่อเครื่องมือ argument และจำนวนแถวที่ได้ ไม่จด key หรือ token

# %%
def audit_entry(tool, arguments, rows, when):
    safe_args = {k: v for k, v in arguments.items() if "key" not in k.lower() and "secret" not in k.lower() and "token" not in k.lower()}
    return {"time": when.isoformat(), "tool": tool, "args": safe_args, "rows": rows}

entry = audit_entry("get_stock_bars_single", {"symbol": "DEMO", "timespan": "D", "count": 5, "app_secret": "never-log"},
                    len(fixture["bars"]), datetime(2026, 11, 8, 9, 30, tzinfo=timezone.utc))
print(json.dumps(entry))
assert "app_secret" not in entry["args"]
print("ALL CHECKS PASSED")
