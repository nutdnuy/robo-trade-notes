"""Chapter 9 - mean reversion and pairs trading with an honest train/test split.

Offline teaching example. All price series are SYNTHETIC log-price paths:
one cointegrated pair built by design, one pair with correlated returns but no
cointegration, and 20 independent random walks for a pair search. Standard
library only. Run: python3 lesson_22.py

Timing: z-score from the close of day t sets the position held from the close
of day t to the close of day t+1. Hedge ratio, spread mean and spread standard
deviation come from the training window only.
"""

import math
import random
import statistics

SEED = 20261123
DAYS, TRAIN = 1000, 500
EG_CRITICAL_5PCT = -3.34   # Engle-Granger, 2 variables, constant: MacKinnon (2010) asymptotic value -3.3377
COST_BPS, BORROW_ANNUAL = 5, 0.01


def random_walk(rng, n, start, drift, vol):
    out, x = [], start
    for _ in range(n):
        x += rng.gauss(drift, vol)
        out.append(x)
    return out


def make_data(seed=SEED):
    rng = random.Random(seed)
    x = random_walk(rng, DAYS, math.log(50), 0.0002, 0.015)
    s, spread = 0.0, []
    for _ in range(DAYS):
        s = 0.92 * s + rng.gauss(0, 0.01)          # AR(1) spread, half-life about 8.3 days
        spread.append(s)
    y = [0.5 + 1.2 * a + b for a, b in zip(x, spread)]
    # Correlated daily returns, but the gap between them is a random walk.
    e = random_walk(rng, DAYS, math.log(40), 0.0002, 0.015)
    f, level = [], math.log(60)
    for t in range(DAYS):
        de = e[t] - (e[t - 1] if t else math.log(40))
        level += 0.9 * de + rng.gauss(0, 0.007)
        f.append(level)
    walks = [random_walk(rng, DAYS, math.log(rng.uniform(20, 200)), 0.0002, 0.016) for _ in range(20)]
    return {"pair": (y, x), "correlated": (f, e), "walks": walks}


def ols_line(y, x):
    mx, my = statistics.fmean(x), statistics.fmean(y)
    beta = sum((a - mx) * (b - my) for a, b in zip(x, y)) / sum((a - mx) ** 2 for a in x)
    return my - beta * mx, beta


def diff(v):
    return [b - a for a, b in zip(v, v[1:])]


def corr(a, b):
    ma, mb = statistics.fmean(a), statistics.fmean(b)
    num = sum((p - ma) * (q - mb) for p, q in zip(a, b))
    return num / math.sqrt(sum((p - ma) ** 2 for p in a) * sum((q - mb) ** 2 for q in b))


def df_test(series):
    """Dickey-Fuller regression d s_t = a + b s_{t-1} + e (no lags). Returns b, t-stat, half-life."""
    lag, ds = series[:-1], diff(series)
    a, b = ols_line(ds, lag)
    resid = [d - a - b * l for d, l in zip(ds, lag)]
    s2 = sum(r * r for r in resid) / (len(ds) - 2)
    ml = statistics.fmean(lag)
    se = math.sqrt(s2 / sum((l - ml) ** 2 for l in lag))
    half_life = -math.log(2) / math.log(1 + b) if -1 < b < 0 else float("inf")
    return {"b": b, "t": b / se, "half_life": half_life}


def engle_granger(y, x):
    alpha, beta = ols_line(y, x)
    resid = [a - alpha - beta * b for a, b in zip(y, x)]
    out = df_test(resid)
    out.update(alpha=alpha, beta=beta, cointegrated=out["t"] < EG_CRITICAL_5PCT)
    return out


def trade_pair(y, x, train=TRAIN, entry=2.0, exit_=0.0, cost_bps=COST_BPS, borrow=BORROW_ANNUAL):
    """Fit on [0, train); trade on [train, end). Returns daily net returns and counts.

    Position +1 = long y, short beta*x; -1 = the reverse. Return is per unit of
    gross exposure (1 + |beta|). Cost: cost_bps on gross notional traded.
    Borrow: annual rate on the short leg's notional, charged daily while open.
    """
    alpha, beta = ols_line(y[:train], x[:train])
    spread = [a - alpha - beta * b for a, b in zip(y, x)]
    mu, sd = statistics.fmean(spread[:train]), statistics.stdev(spread[:train])
    gross_exposure = 1 + abs(beta)
    pos, rets, gross_rets, trades = 0, [], [], 0
    for t in range(train, len(y) - 1):
        z = (spread[t] - mu) / sd
        new = pos
        if pos == 0 and z > entry:
            new = -1
        elif pos == 0 and z < -entry:
            new = 1
        elif pos == 1 and z >= exit_:
            new = 0
        elif pos == -1 and z <= exit_:
            new = 0
        cost = abs(new - pos) * cost_bps / 10000
        trades += abs(new - pos) > 0
        pos = new
        ry, rx = math.exp(y[t + 1] - y[t]) - 1, math.exp(x[t + 1] - x[t]) - 1
        gross = pos * (ry - beta * rx) / gross_exposure
        short_share = (abs(beta) if pos == 1 else 1) / gross_exposure
        carry = abs(pos) * short_share * borrow / 252
        gross_rets.append(gross)
        rets.append(gross - cost - carry)
    return {"beta": beta, "net": rets, "gross": gross_rets, "trades": trades,
            "days_in_market": sum(1 for g in gross_rets if g != 0)}


def total(returns):
    return math.prod(1 + r for r in returns) - 1


def sharpe(returns):
    sd = statistics.stdev(returns)
    return statistics.fmean(returns) / sd * math.sqrt(252) if sd > 0 else 0.0

# %% [markdown]
# # บทที่ 9 — Mean Reversion และ Pairs Trading
#
# ราคาทุกชุดเป็น **log price สมมติ** คู่แรกสร้างให้ cointegrated โดยตั้งใจ คู่ที่สองมีผลตอบแทนสัมพันธ์กันแต่ไม่ cointegrated
# และมี random walk อิสระ 20 ชุดสำหรับทดลองค้นหาคู่ ใช้ 500 วันแรกประมาณค่า 500 วันหลังทดสอบ

# %%
d = make_data()
assert d == make_data()
y, x = d["pair"]
f, e = d["correlated"]
print("Days:", DAYS, "| train:", TRAIN, "| test:", DAYS - TRAIN)

# %% [markdown]
# ## 1. ตรวจ Dickey-Fuller ด้วยข้อมูลที่รู้คำตอบ
#
# AR(1) ที่ φ = 0.95 ต้องได้ b ใกล้ −0.05 และ half-life ใกล้ ln(0.5)/ln(0.95) ≈ 13.5 วัน

# %%
rng = random.Random(7)
s, ar = 0.0, []
for _ in range(20000):
    s = 0.95 * s + rng.gauss(0, 1)
    ar.append(s)
res = df_test(ar)
print(f"AR(1) phi=0.95: b {res['b']:.4f}, t {res['t']:.1f}, half-life {res['half_life']:.1f} days")
assert abs(res["b"] + 0.05) < 0.01 and 11 < res["half_life"] < 16

# %% [markdown]
# ## 2. Correlation ไม่ใช่ cointegration

# %%
for label, (a, b) in [("designed pair", (y, x)), ("correlated pair", (f, e))]:
    eg = engle_granger(a[:TRAIN], b[:TRAIN])
    print(f"{label:16s} return corr {corr(diff(a[:TRAIN]), diff(b[:TRAIN])):.2f} | hedge {eg['beta']:.2f} | "
          f"EG t {eg['t']:.2f} (5% critical {EG_CRITICAL_5PCT}) | cointegrated: {eg['cointegrated']} | half-life {eg['half_life']:.1f}")
assert engle_granger(y[:TRAIN], x[:TRAIN])["cointegrated"]
assert not engle_granger(f[:TRAIN], e[:TRAIN])["cointegrated"]

# %% [markdown]
# ## 3. เทรดคู่ที่ cointegrated ในช่วงทดสอบ
#
# เข้าเมื่อ |z| > 2 ออกเมื่อ z กลับถึง 0 ค่า hedge ratio, ค่าเฉลี่ย และ standard deviation มาจากช่วงฝึกเท่านั้น

# %%
res = trade_pair(y, x)
print(f"Hedge ratio (train): {res['beta']:.3f} | trades: {res['trades']} | days in market: {res['days_in_market']} of {len(res['net'])}")
print(f"Test gross return {total(res['gross']):.2%} | net {total(res['net']):.2%} | net Sharpe {sharpe(res['net']):.2f}")
assert total(res["net"]) < total(res["gross"])

# %% [markdown]
# ## 4. คู่ที่ไม่ cointegrated กับกฎเดิม

# %%
res_c = trade_pair(f, e)
print(f"Correlated, not cointegrated: trades {res_c['trades']} | days in market {res_c['days_in_market']} | net {total(res_c['net']):.2%}")

# %% [markdown]
# ## 5. ค้นหาคู่จาก random walk 20 ชุด
#
# 20 ชุดให้ 190 คู่ ทุกชุดเป็นอิสระต่อกัน ไม่มีคู่ไหน cointegrated จริง
# แต่ถ้าทดสอบ 190 ครั้งที่ระดับ 5% ก็คาดว่าจะผ่านประมาณ 9–10 คู่โดยบังเอิญ

# %%
found = []
walks = d["walks"]
for i in range(len(walks)):
    for j in range(i + 1, len(walks)):
        eg = engle_granger(walks[i][:TRAIN], walks[j][:TRAIN])
        if eg["cointegrated"]:
            found.append((i, j, eg["t"]))
print(f"Pairs tested: 190 | passed at 5%: {len(found)} | expected by chance: about {0.05 * 190:.1f}")
oos = [trade_pair(walks[i], walks[j]) for i, j, _ in found]
for (i, j, t), r in zip(found, oos):
    print(f"  walk {i:2d} & {j:2d}: train t {t:.2f} -> test net {total(r['net']):+.2%} ({r['trades']} trades)")
retest = sum(1 for i, j, _ in found if engle_granger(walks[i][TRAIN:], walks[j][TRAIN:])["cointegrated"])
print(f"Still 'cointegrated' when re-tested on the test window: {retest} of {len(found)}")
assert len(found) > 0
print("ALL CHECKS PASSED")
