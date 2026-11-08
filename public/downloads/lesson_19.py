"""Chapter 6 - a US-stock style screener tested as a cross-sectional strategy.

Offline teaching example. The universe is SYNTHETIC: 80 invented tickers over
120 months, with listings, delistings and a small momentum effect PLANTED BY
DESIGN so the tools have something to find. A real universe has no such
guarantee. Standard library only. Run: python3 lesson_19.py

Timing convention: a month's return runs from the close of the last session of
the previous month to the close of the last session of this month. The
synthetic data has no overnight gap, so a trade at the next open is priced at
that close. The signal for month t+1 uses returns up to month t only.
"""

import math
import random
import statistics

SEED = 20261119
N_STOCKS, N_MONTHS = 80, 120
TOP_N, COST_BPS = 10, 10


def make_universe(seed=SEED):
    """returns[i][t] is None when stock i is not listed in month t.

    Each stock has a slowly moving expected return (AR(1)); past returns
    therefore carry a little information about the next month. Stocks list at
    random times; a stock whose price falls far enough is delisted with a
    final delisting return of -50%.
    """
    rng = random.Random(seed)
    market = [rng.gauss(0.008, 0.045) for _ in range(N_MONTHS)]
    universe = []
    for i in range(N_STOCKS):
        start = 0 if i < 55 else rng.randrange(12, 90)
        beta = rng.uniform(0.6, 1.4)
        drift, level, rets, delist = rng.gauss(0, 0.004), 1.0, [None] * N_MONTHS, None
        for t in range(start, N_MONTHS):
            drift = 0.95 * drift + rng.gauss(0, 0.004)
            r = beta * market[t] + drift + rng.gauss(0, 0.07)
            level *= 1 + r
            if level < 0.35 and rng.random() < 0.5:
                rets[t], delist = -0.5, t
                break
            rets[t] = r
        universe.append({"ticker": f"S{i:02d}", "listed": start, "delisted": delist, "returns": rets})
    return {"market": market, "stocks": universe}


def alive(stock, t):
    return stock["returns"][t] is not None


def momentum_12_1(stock, t):
    """Compounded return from month t-11 through t-1 (skip month t). Needs all 11 months."""
    window = stock["returns"][t - 11:t]
    if t < 12 or any(r is None for r in window) or not alive(stock, t):
        return None
    return math.prod(1 + r for r in window) - 1


def ranks(values):
    """Average ranks (1 = smallest), ties share the mean rank."""
    order = sorted(range(len(values)), key=lambda k: values[k])
    out, k = [0.0] * len(values), 0
    while k < len(order):
        j = k
        while j + 1 < len(order) and values[order[j + 1]] == values[order[k]]:
            j += 1
        for m in range(k, j + 1):
            out[order[m]] = (k + j) / 2 + 1
        k = j + 1
    return out


def pearson(x, y):
    mx, my = statistics.fmean(x), statistics.fmean(y)
    sxy = sum((a - mx) * (b - my) for a, b in zip(x, y))
    return sxy / math.sqrt(sum((a - mx) ** 2 for a in x) * sum((b - my) ** 2 for b in y))


def spearman(x, y):
    return pearson(ranks(x), ranks(y))


def cross_section(universe, t):
    """Stocks with a signal at the end of month t and their month t+1 return.

    The month t+1 return includes a delisting return if the stock delists then.
    """
    rows = []
    for s in universe["stocks"]:
        signal = momentum_12_1(s, t)
        if signal is not None and t + 1 < N_MONTHS and alive(s, t + 1):
            rows.append((s["ticker"], signal, s["returns"][t + 1]))
    return rows


def rank_ic_series(universe):
    out = []
    for t in range(12, N_MONTHS - 1):
        rows = cross_section(universe, t)
        if len(rows) >= 20:
            out.append(spearman([r[1] for r in rows], [r[2] for r in rows]))
    return out


def quintile_spread(universe):
    spreads = []
    for t in range(12, N_MONTHS - 1):
        rows = sorted(cross_section(universe, t), key=lambda r: r[1])
        q = len(rows) // 5
        spreads.append(statistics.fmean(r[2] for r in rows[-q:]) - statistics.fmean(r[2] for r in rows[:q]))
    return spreads


def backtest_top_n(universe, top_n=TOP_N, cost_bps=COST_BPS):
    """Equal-weight top-N by momentum, rebalanced monthly; EW universe benchmark.

    Cost: cost_bps on traded notional, sum |target weight - drifted weight|.
    """
    rows, held = [], {}
    for t in range(12, N_MONTHS - 1):
        xs = cross_section(universe, t)
        picks = sorted(xs, key=lambda r: r[1], reverse=True)[:top_n]
        target = {r[0]: 1 / len(picks) for r in picks}
        traded = sum(abs(target.get(k, 0) - held.get(k, 0)) for k in set(target) | set(held))
        gross = statistics.fmean(r[2] for r in picks)
        net = (1 + gross) * (1 - traded * cost_bps / 10000) - 1
        bench = statistics.fmean(r[2] for r in xs)
        drifted = {r[0]: (1 / len(picks)) * (1 + r[2]) for r in picks if r[2] > -0.5}
        total = sum(drifted.values()) + sum((1 / len(picks)) * (1 + r[2]) for r in picks if r[2] <= -0.5)
        held = {k: v / total for k, v in drifted.items()}
        rows.append({"month": t + 1, "gross": gross, "net": net, "benchmark": bench, "traded": traded})
    return rows


def survivors_only(universe):
    """The mistake: keep only stocks still listed in the last month."""
    keep = [s for s in universe["stocks"] if alive(s, N_MONTHS - 1)]
    return {"market": universe["market"], "stocks": keep}


def cagr(monthly):
    return math.prod(1 + r for r in monthly) ** (12 / len(monthly)) - 1


def t_stat(values):
    return statistics.fmean(values) / (statistics.stdev(values) / math.sqrt(len(values)))

# %% [markdown]
# # บทที่ 6 — Stock Screener ที่ทดสอบได้
#
# universe ในไฟล์นี้เป็น **ข้อมูลสมมติ** 80 หุ้นชื่อสมมติ 120 เดือน มีหุ้นเข้าตลาดทีหลังและหุ้นถูกถอดออก
# เรา **ฝังผล momentum ขนาดเล็กไว้โดยตั้งใจ** เพื่อให้เครื่องมือมีอะไรให้หา universe จริงไม่มีการรับประกันแบบนี้

# %%
u = make_universe()
assert u == make_universe()
listed_late = sum(1 for s in u["stocks"] if s["listed"] > 0)
delisted = [s["ticker"] for s in u["stocks"] if s["delisted"] is not None]
print("Stocks:", len(u["stocks"]), "| listed after month 0:", listed_late, "| delisted:", len(delisted))
print("Alive in the last month:", sum(1 for s in u["stocks"] if alive(s, N_MONTHS - 1)))

# %% [markdown]
# ## 1. ตรวจ Spearman ด้วยค่าที่รู้คำตอบ

# %%
assert ranks([10, 20, 20, 30]) == [1.0, 2.5, 2.5, 4.0]
assert math.isclose(spearman([1, 2, 3, 4], [10, 20, 30, 40]), 1.0)
assert math.isclose(spearman([1, 2, 3, 4], [9, 7, 5, 1]), -1.0)
print("Spearman checks passed: ties, +1, -1")

# %% [markdown]
# ## 2. Rank IC รายเดือน
#
# ทุกสิ้นเดือน t เรียงหุ้นตาม momentum 12-1 แล้ววัด Spearman กับผลตอบแทนเดือน t+1

# %%
ic = rank_ic_series(u)
print("Months:", len(ic), "| mean IC:", round(statistics.fmean(ic), 4), "| t-stat:", round(t_stat(ic), 2),
      "| months IC > 0:", sum(1 for x in ic if x > 0))
spread = quintile_spread(u)
print("Top-minus-bottom quintile, mean monthly:", f"{statistics.fmean(spread):.2%}")

# %% [markdown]
# ## 3. พอร์ต top-10 เทียบกับ benchmark ในช่วงเดียวกัน

# %%
bt = backtest_top_n(u)
gross, net, bench = ([r[k] for r in bt] for k in ("gross", "net", "benchmark"))
print("Months:", len(bt))
print("Top-10 gross CAGR:", f"{cagr(gross):.2%}", "| net CAGR:", f"{cagr(net):.2%}", "| EW universe CAGR:", f"{cagr(bench):.2%}")
print("Average traded notional per month:", f"{statistics.fmean(r['traded'] for r in bt):.0%}")
assert all(r["net"] <= r["gross"] for r in bt)
assert math.isclose(1 + bt[0]["net"], (1 + bt[0]["gross"]) * (1 - bt[0]["traded"] * COST_BPS / 10000))
assert math.isclose(bt[0]["traded"], 1.0)   # first month buys from cash: sum |w| = 1

# %% [markdown]
# ## 4. Survivorship bias: ใช้เฉพาะหุ้นที่ยังอยู่วันนี้
#
# รายชื่อหุ้นปัจจุบันตัดหุ้นที่ถูกถอดออกไปแล้วทิ้ง ผลย้อนหลังของ benchmark และพอร์ตจึงดีเกินจริง

# %%
s_only = survivors_only(u)
bt_s = backtest_top_n(s_only)
print("Point-in-time  EW universe CAGR:", f"{cagr(bench):.2%}", "| top-10 net:", f"{cagr(net):.2%}")
print("Survivors only EW universe CAGR:", f"{cagr([r['benchmark'] for r in bt_s]):.2%}", "| top-10 net:", f"{cagr([r['net'] for r in bt_s]):.2%}")
assert cagr([r["benchmark"] for r in bt_s]) > cagr(bench)

# %% [markdown]
# ## 5. หาบั๊ก: เงื่อนไขที่ตรง "เดือนไหนก็ได้" แทน "เดือนล่าสุด"
#
# กฎที่ตั้งใจ: momentum เดือนล่าสุดเป็นบวก โค้ดที่ผิดเลือกหุ้นถ้า momentum เคยเป็นบวกเดือนใดเดือนหนึ่งในปีที่ผ่านมา

# %%
t = 100
latest = [s["ticker"] for s in u["stocks"] if (momentum_12_1(s, t) or -1) > 0]
any_month = [s["ticker"] for s in u["stocks"] if alive(s, t) and any((momentum_12_1(s, k) or -1) > 0 for k in range(t - 11, t + 1))]
print("Pass with latest month:", len(latest), "| pass with any month in the last year:", len(any_month))
assert set(latest) <= set(any_month) and len(any_month) > len(latest)

# %% [markdown]
# ## 6. หาบั๊ก: dropna ทั้งตาราง
#
# ถ้าเก็บเฉพาะหุ้นที่มีข้อมูลครบทุกเดือน หุ้นที่เข้าตลาดทีหลังและหุ้นที่ถูกถอดออกหายไปพร้อมกัน

# %%
complete = [s for s in u["stocks"] if all(r is not None for r in s["returns"])]
print("Stocks with no missing month:", len(complete), "of", len(u["stocks"]))
assert len(complete) < len(u["stocks"]) - len(delisted)
print("ALL CHECKS PASSED")
