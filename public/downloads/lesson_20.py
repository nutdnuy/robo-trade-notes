"""Chapter 7 - beta, CAPM alpha and factor exposure with plain regression.

Offline teaching example. Market, factor and stock returns are SYNTHETIC with
known true betas, so every estimate can be checked against the truth.
Standard library only. Run: python3 lesson_20.py
"""

import math
import random
import statistics

SEED = 20261120
DAYS = 756                      # three years of 252 sessions
RF_ANNUAL = 0.045               # invented risk-free rate, annual, compounded
RF_DAILY = (1 + RF_ANNUAL) ** (1 / 252) - 1


def make_data(seed=SEED):
    rng = random.Random(seed)
    mkt_ex = [rng.gauss(0.0003, 0.011) for _ in range(DAYS)]          # market excess return
    size = [rng.gauss(0.0001, 0.005) for _ in range(DAYS)]            # long small, short large
    mom = [rng.gauss(0.0002, 0.006) for _ in range(DAYS)]             # long winners, short losers
    truth = {
        "A": {"alpha": 0.0, "beta": 1.3, "size": 0.0, "mom": 0.0, "noise": 0.012},
        "B": {"alpha": 0.0, "beta": 0.8, "size": 0.9, "mom": 0.7, "noise": 0.009},
    }
    stocks = {}
    for name, p in truth.items():
        stocks[name] = [RF_DAILY + p["alpha"] + p["beta"] * m + p["size"] * s + p["mom"] * w + rng.gauss(0, p["noise"])
                        for m, s, w in zip(mkt_ex, size, mom)]
    # C: true beta 0.7 for the first half, 1.4 for the second half.
    stocks["C"] = [RF_DAILY + (0.7 if t < DAYS // 2 else 1.4) * mkt_ex[t] + rng.gauss(0, 0.010) for t in range(DAYS)]
    return {"mkt_ex": mkt_ex, "size": size, "mom": mom, "stocks": stocks, "truth": truth}


def solve(a, b):
    """Gauss-Jordan elimination with partial pivoting for a small square system."""
    n = len(a)
    m = [row[:] + [b[i]] for i, row in enumerate(a)]
    for col in range(n):
        pivot = max(range(col, n), key=lambda r: abs(m[r][col]))
        m[col], m[pivot] = m[pivot], m[col]
        for r in range(n):
            if r != col:
                f = m[r][col] / m[col][col]
                m[r] = [x - f * y for x, y in zip(m[r], m[col])]
    return [m[i][n] / m[i][i] for i in range(n)]


def invert(a):
    n = len(a)
    cols = [solve(a, [1.0 if i == j else 0.0 for i in range(n)]) for j in range(n)]
    return [[cols[j][i] for j in range(n)] for i in range(n)]


def ols(y, regressors):
    """OLS with intercept. Returns coefficients [alpha, b1, ...], standard errors, residual std, R^2."""
    x = [[1.0] + list(row) for row in zip(*regressors)]
    k, n = len(x[0]), len(y)
    xtx = [[sum(r[i] * r[j] for r in x) for j in range(k)] for i in range(k)]
    xty = [sum(r[i] * yi for r, yi in zip(x, y)) for i in range(k)]
    coef = solve(xtx, xty)
    resid = [yi - sum(c * v for c, v in zip(coef, r)) for r, yi in zip(x, y)]
    s2 = sum(e * e for e in resid) / (n - k)
    inv = invert(xtx)
    se = [math.sqrt(s2 * inv[i][i]) for i in range(k)]
    ybar = statistics.fmean(y)
    r2 = 1 - sum(e * e for e in resid) / sum((yi - ybar) ** 2 for yi in y)
    return {"coef": coef, "se": se, "resid_std": math.sqrt(s2), "r2": r2}


def beta_cov_var(y, x):
    mx, my = statistics.fmean(x), statistics.fmean(y)
    return sum((a - mx) * (b - my) for a, b in zip(x, y)) / sum((a - mx) ** 2 for a in x)


def excess(returns, rf=RF_DAILY):
    return [r - rf for r in returns]


def rolling_beta(y, x, window):
    return [beta_cov_var(y[t - window:t], x[t - window:t]) for t in range(window, len(y) + 1)]

# %% [markdown]
# # บทที่ 7 — Beta, CAPM และ Factor Exposure
#
# ผลตอบแทนทุกชุดเป็น **ข้อมูลสมมติ** ที่รู้ค่า beta จริง เราจึงตรวจได้ว่าการประมาณใกล้ความจริงแค่ไหน
# risk-free rate สมมติ 4.5% ต่อปี แปลงเป็นรายวันด้วย (1.045)^(1/252) − 1

# %%
d = make_data()
assert d == make_data()
print("Days:", DAYS, "| daily risk-free:", f"{RF_DAILY:.6%}")
print("True parameters:", d["truth"])

# %% [markdown]
# ## 1. Beta สองวิธีต้องได้ค่าเดียวกัน
#
# cov(r, m) / var(m) กับ slope จาก OLS ที่มี intercept เป็นสูตรเดียวกัน ถ้าโค้ดสองแบบให้ค่าต่างกัน แปลว่ามีอย่างหนึ่งผิด

# %%
yA = excess(d["stocks"]["A"])
fit_A = ols(yA, [d["mkt_ex"]])
assert math.isclose(fit_A["coef"][1], beta_cov_var(yA, d["mkt_ex"]), rel_tol=1e-9)
alpha, beta = fit_A["coef"]
print(f"A: beta {beta:.3f} (se {fit_A['se'][1]:.3f}, true 1.3) | alpha {alpha * 252:.2%}/yr (se {fit_A['se'][0] * 252:.2%}) | R^2 {fit_A['r2']:.2f}")
assert abs(beta - 1.3) < 3 * fit_A["se"][1]

# %% [markdown]
# ## 2. ลบ risk-free rate ผิดความถี่
#
# ถ้าลบ 4.5% ทั้งก้อนจากผลตอบแทนรายวัน alpha จะติดลบมหาศาล ตัวเลขผิดชัด แต่ถ้าลบ 4.5%/365 ก็ผิดแบบเนียนกว่า

# %%
wrong = ols([r - RF_ANNUAL for r in d["stocks"]["A"]], [d["mkt_ex"]])
subtle = ols([r - RF_ANNUAL / 365 for r in d["stocks"]["A"]], [d["mkt_ex"]])
print(f"alpha with daily rf      : {alpha * 252:+.2%}/yr")
print(f"alpha with annual rf     : {wrong['coef'][0] * 252:+.2%}/yr  <- obviously wrong")
print(f"alpha with rf/365        : {subtle['coef'][0] * 252:+.2%}/yr  <- off by {(subtle['coef'][0] - alpha) * 252:+.2%}")
assert wrong["coef"][0] * 252 < -10

# %% [markdown]
# ## 3. Beta แบบ rolling แกว่งแม้ beta จริงคงที่
#
# หุ้น A มี beta จริง 1.3 ตลอดสามปี แต่ค่าประมาณจากหน้าต่าง 60 วันแกว่งกว้าง
# หุ้น C เปลี่ยน beta จริงจาก 0.7 เป็น 1.4 กลางช่วง

# %%
rA = rolling_beta(yA, d["mkt_ex"], 60)
yC = excess(d["stocks"]["C"])
rC = rolling_beta(yC, d["mkt_ex"], 60)
print(f"A 60-day beta range: {min(rA):.2f} to {max(rA):.2f} (true 1.30)")
print(f"C beta first half {beta_cov_var(yC[:378], d['mkt_ex'][:378]):.2f}, second half {beta_cov_var(yC[378:], d['mkt_ex'][378:]):.2f}, full sample {beta_cov_var(yC, d['mkt_ex']):.2f}")
assert max(rA) - min(rA) > 0.3

# %% [markdown]
# ## 4. Alpha ที่หายไปเมื่อเพิ่ม factor
#
# หุ้น B ไม่มี alpha จริง แต่มี exposure ต่อ size และ momentum ซึ่งในข้อมูลชุดนี้มีผลตอบแทนเฉลี่ยเป็นบวก
# CAPM จึงเห็น alpha ที่จริงเป็นผลตอบแทนจาก factor

# %%
yB = excess(d["stocks"]["B"])
capm_B = ols(yB, [d["mkt_ex"]])
ff_B = ols(yB, [d["mkt_ex"], d["size"], d["mom"]])
print(f"B CAPM   : alpha {capm_B['coef'][0] * 252:+.2%}/yr (t {capm_B['coef'][0] / capm_B['se'][0]:.2f}), beta {capm_B['coef'][1]:.2f}, R^2 {capm_B['r2']:.2f}")
print(f"B 3-factor: alpha {ff_B['coef'][0] * 252:+.2%}/yr (t {ff_B['coef'][0] / ff_B['se'][0]:.2f}), beta {ff_B['coef'][1]:.2f}, size {ff_B['coef'][2]:.2f}, mom {ff_B['coef'][3]:.2f}, R^2 {ff_B['r2']:.2f}")
assert capm_B["coef"][0] > ff_B["coef"][0]
assert all(abs(est - true) < 3 * se for est, true, se in zip(ff_B["coef"][1:], [0.8, 0.9, 0.7], ff_B["se"][1:]))

# %% [markdown]
# ## 5. Beta hedge: ประมาณในช่วงแรก ใช้ในช่วงหลัง
#
# ขาย market เท่ากับ beta ที่ประมาณจากปีแรก แล้วดูความสัมพันธ์กับตลาดในสองปีถัดมา
# การ hedge ด้วย beta ที่ประมาณจากข้อมูลทั้งหมดใช้ข้อมูลอนาคต

# %%
cut = 252
b_train = beta_cov_var(yC[:cut], d["mkt_ex"][:cut])
hedged = [r - b_train * m for r, m in zip(yC[cut:], d["mkt_ex"][cut:])]
print(f"C: beta estimated on year 1 = {b_train:.2f}")
print(f"Residual beta of hedged C in years 2-3: {beta_cov_var(hedged, d['mkt_ex'][cut:]):+.2f}")
first_test = [r - b_train * m for r, m in zip(yC[cut:378], d["mkt_ex"][cut:378])]
second_test = [r - b_train * m for r, m in zip(yC[378:], d["mkt_ex"][378:])]
print(f"  months before the beta change: {beta_cov_var(first_test, d['mkt_ex'][cut:378]):+.2f} | after: {beta_cov_var(second_test, d['mkt_ex'][378:]):+.2f}")
assert beta_cov_var(second_test, d["mkt_ex"][378:]) > 0.4
print("ALL CHECKS PASSED")
