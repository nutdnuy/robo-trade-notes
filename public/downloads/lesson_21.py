"""Chapter 8 - portfolio risk and position sizing.

Offline teaching example. Four SYNTHETIC assets (invented names EQ1, EQ2, BND,
EQ3) with known volatilities and correlations, plus a stress period in the last
150 days where volatility doubles and equity correlations rise. Standard
library only. Run: python3 lesson_21.py

Timing: weights are set from data up to the close of day t and earn the
return of day t+1 (the course's next-bar rule on daily close-to-close data).
"""

import math
import random
import statistics

SEED = 20261121
NAMES = ["EQ1", "EQ2", "BND", "EQ3"]
ANNUAL_VOL = [0.22, 0.18, 0.06, 0.30]
CORR_CALM = [[1.0, 0.6, 0.0, 0.5],
             [0.6, 1.0, 0.1, 0.5],
             [0.0, 0.1, 1.0, 0.0],
             [0.5, 0.5, 0.0, 1.0]]
CORR_STRESS = [[1.0, 0.9, -0.2, 0.85],
               [0.9, 1.0, -0.1, 0.85],
               [-0.2, -0.1, 1.0, -0.2],
               [0.85, 0.85, -0.2, 1.0]]
DAYS, STRESS_DAYS, TRAIN = 1000, 150, 500


def cholesky(a):
    n = len(a)
    low = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1):
            s = sum(low[i][k] * low[j][k] for k in range(j))
            low[i][j] = math.sqrt(a[i][i] - s) if i == j else (a[i][j] - s) / low[j][j]
    return low


def covariance(vols, corr):
    return [[corr[i][j] * vols[i] * vols[j] for j in range(len(vols))] for i in range(len(vols))]


def make_returns(seed=SEED):
    rng = random.Random(seed)
    daily_vol = [v / math.sqrt(252) for v in ANNUAL_VOL]
    calm = cholesky(covariance(daily_vol, CORR_CALM))
    stress = cholesky(covariance([2 * v for v in daily_vol], CORR_STRESS))
    drift = [0.0003, 0.00025, 0.0001, 0.00035]
    rows = []
    for t in range(DAYS):
        low = stress if t >= DAYS - STRESS_DAYS else calm
        z = [rng.gauss(0, 1) for _ in NAMES]
        shock = [sum(low[i][k] * z[k] for k in range(i + 1)) for i in range(len(NAMES))]
        rows.append([d + s - (0.0008 if t >= DAYS - STRESS_DAYS and i != 2 else 0) for i, (d, s) in enumerate(zip(drift, shock))])
    return rows


def sample_cov(rows):
    n, k = len(rows), len(rows[0])
    means = [statistics.fmean(r[i] for r in rows) for i in range(k)]
    return [[sum((r[i] - means[i]) * (r[j] - means[j]) for r in rows) / (n - 1) for j in range(k)] for i in range(k)]


def port_var(w, cov):
    return sum(w[i] * w[j] * cov[i][j] for i in range(len(w)) for j in range(len(w)))


def risk_contributions(w, cov):
    """Share of portfolio variance from each asset: w_i (Cov w)_i / w'Cov w. Sums to 1."""
    total = port_var(w, cov)
    return [w[i] * sum(cov[i][j] * w[j] for j in range(len(w))) / total for i in range(len(w))]


def inverse_vol(cov):
    inv = [1 / math.sqrt(cov[i][i]) for i in range(len(cov))]
    return [x / sum(inv) for x in inv]


def equal_risk(cov, iterations=500):
    """Equal risk contribution (long-only, fully invested) by fixed-point iteration."""
    w = inverse_vol(cov)
    for _ in range(iterations):
        marginal = [sum(cov[i][j] * w[j] for j in range(len(w))) for i in range(len(w))]
        w = [1 / m for m in marginal]          # w_i * m_i equal  ->  w_i proportional to 1/m_i
        w = [x / sum(w) for x in w]
    return w


def effective_n(w):
    return 1 / sum(x * x for x in w)


def portfolio_returns(rows, w):
    return [sum(a * b for a, b in zip(w, r)) for r in rows]


def ann_vol(returns):
    return statistics.stdev(returns) * math.sqrt(252)


def historical_var_cvar(returns, level=0.95):
    """1-day loss quantile and mean loss beyond it, reported as positive numbers."""
    losses = sorted(-r for r in returns)
    k = math.ceil(level * len(losses)) - 1
    var = losses[k]
    tail = losses[k:]
    return var, statistics.fmean(tail)


def vol_target(returns, target=0.08, window=60, cap=1.0):
    """Scale exposure by target / trailing vol known at the close of day t, applied to day t+1."""
    out, scales = [], []
    for t in range(window, len(returns)):
        vol = statistics.stdev(returns[t - window:t]) * math.sqrt(252)
        scale = min(cap, target / vol)
        out.append(scale * returns[t])
        scales.append(scale)
    return out, scales


def to_shares(target_value, price, lot=1):
    shares = math.floor(target_value / price / lot) * lot
    return shares, target_value - shares * price

# %% [markdown]
# # บทที่ 8 — Risk และ Position Sizing ระดับพอร์ต
#
# สินทรัพย์ทั้งสี่ตัวเป็น **ข้อมูลสมมติ** ชื่อสมมติ รู้ค่า volatility และ correlation จริง
# 150 วันสุดท้ายเป็นช่วงวิกฤตสมมติ: volatility เพิ่มเป็นสองเท่า หุ้นสามตัวสัมพันธ์กันสูงขึ้น
# ประมาณความเสี่ยงจาก 500 วันแรก แล้วประเมินกับ 500 วันหลัง

# %%
rows = make_returns()
assert rows == make_returns()
train, test = rows[:TRAIN], rows[TRAIN:]
cov = sample_cov(train)
for i, name in enumerate(NAMES):
    print(f"{name}: estimated vol {math.sqrt(cov[i][i] * 252):.1%} (true {ANNUAL_VOL[i]:.0%})")

# %% [markdown]
# ## 1. สูตร volatility ของพอร์ตต้องตรงกับการคำนวณตรง
#
# w'Σw จาก covariance ตัวอย่างเท่ากับ variance ของผลตอบแทนพอร์ตรายวันตรงตัว

# %%
w_eq = [0.25] * 4
direct = statistics.variance(portfolio_returns(train, w_eq))
assert math.isclose(port_var(w_eq, cov), direct, rel_tol=1e-9)
print(f"Equal weight portfolio vol: {math.sqrt(direct * 252):.2%} (formula and direct agree)")

# %% [markdown]
# ## 2. น้ำหนักเท่ากันไม่ได้แปลว่าความเสี่ยงเท่ากัน

# %%
schemes = {"equal weight": w_eq, "inverse vol": inverse_vol(cov), "equal risk": equal_risk(cov)}
print(f"{'scheme':13s} " + " ".join(f"{n:>6s}" for n in NAMES) + "   risk share " + " ".join(f"{n:>6s}" for n in NAMES) + "  eff. N")
for label, w in schemes.items():
    rc = risk_contributions(w, cov)
    print(f"{label:13s} " + " ".join(f"{x:6.1%}" for x in w) + "              " + " ".join(f"{x:6.1%}" for x in rc) + f"  {effective_n(w):5.2f}")
    assert math.isclose(sum(rc), 1.0, rel_tol=1e-9)
erc = risk_contributions(schemes["equal risk"], cov)
assert max(erc) - min(erc) < 1e-6

# %% [markdown]
# ## 3. ความเสี่ยงที่ประมาณได้ เทียบกับที่เกิดจริงในช่วงทดสอบ

# %%
calm_test, stress_test = test[:-STRESS_DAYS], test[-STRESS_DAYS:]
print(f"{'scheme':13s} {'forecast':>9s} {'test calm':>10s} {'stress':>8s}")
for label, w in schemes.items():
    print(f"{label:13s} {math.sqrt(port_var(w, cov) * 252):9.1%} {ann_vol(portfolio_returns(calm_test, w)):10.1%} {ann_vol(portfolio_returns(stress_test, w)):8.1%}")

# %% [markdown]
# ## 4. VaR และ CVaR: วัดหางของการขาดทุน
#
# VaR 95% บอกว่าวันที่แย่ที่สุด 5% ขาดทุนอย่างน้อยเท่าไร CVaR บอกค่าเฉลี่ยของวันเหล่านั้น
# ถ้า VaR จากช่วงสงบใช้ได้ วันที่ขาดทุนเกิน VaR ควรมีประมาณ 5%

# %%
w = schemes["equal risk"]
var95, cvar95 = historical_var_cvar(portfolio_returns(train, w))
print(f"Equal risk, 1-day historical VaR95 {var95:.2%}, CVaR95 {cvar95:.2%} (estimated on days 0-499)")
for label, period in [("test calm", calm_test), ("stress", stress_test)]:
    pr = portfolio_returns(period, w)
    breaches = sum(1 for r in pr if -r > var95)
    print(f"  {label:9s}: {breaches} of {len(pr)} days lost more than VaR ({breaches / len(pr):.1%})")
assert sum(1 for r in portfolio_returns(stress_test, w) if -r > var95) / STRESS_DAYS > 0.10

# %% [markdown]
# ## 5. Volatility targeting ระดับพอร์ต ไม่ใช้ leverage
#
# ปรับ exposure ด้วย 8% / volatility ย้อนหลัง 60 วัน จำกัดไม่เกิน 1 เท่า ส่วนที่เหลือถือเงินสดที่ 0%
# volatility ย้อนหลังรู้ ณ close วัน t แล้วใช้กับผลตอบแทนวัน t+1

# %%
pr_all = portfolio_returns(rows, w)
targeted, scales = vol_target(pr_all)
base = pr_all[60:]
print(f"Unscaled vol, last 150 days : {ann_vol(base[-STRESS_DAYS:]):.1%}")
print(f"Targeted vol, last 150 days : {ann_vol(targeted[-STRESS_DAYS:]):.1%}")
print(f"Average exposure: calm {statistics.fmean(scales[:-STRESS_DAYS]):.2f}, stress {statistics.fmean(scales[-STRESS_DAYS:]):.2f}")
assert all(0 < s <= 1 for s in scales)
assert ann_vol(targeted[-STRESS_DAYS:]) < ann_vol(base[-STRESS_DAYS:])

# %% [markdown]
# ## 6. จากน้ำหนักเป็นจำนวนหุ้น
#
# เงินลงทุนสมมติ 10,000 USD ราคาไม่ปรับของวันนั้น ซื้อได้เป็นจำนวนเต็มหุ้น เศษที่เหลือเป็นเงินสด

# %%
capital = 10_000
prices = {"EQ1": 412.37, "EQ2": 187.05, "BND": 72.48, "EQ3": 951.10}   # invented prices, USD
total_cash = capital
for name, weight in zip(NAMES, w):
    shares, cash = to_shares(capital * weight, prices[name])
    total_cash -= shares * prices[name]
    print(f"{name}: target {capital * weight:8.2f} USD -> {shares:3d} shares, actual weight {shares * prices[name] / capital:6.2%}")
print(f"Uninvested cash: {total_cash:.2f} USD")
assert 0 <= total_cash < sum(prices.values())
print("ALL CHECKS PASSED")
