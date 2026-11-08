"""Chapter 12 - capstone: build a research dossier with a one-time holdout.

Offline teaching example. Bars are SYNTHETIC (seeded random walk with a small
upward drift and no timing signal by design), so the honest answer is that the
selected rule should not beat buy-and-hold out of sample. Standard library
only. Run: python3 lesson_25.py

Fill rule (course-wide): signal from the close of day t, trade at the open of
day t+1, hold until the open of day t+2. Costs: 5 bps per unit of weight change.
"""

import hashlib
import json
import math
import random
import statistics
from statistics import NormalDist

SEED = 20261125
DAYS = 2520                          # ten synthetic years of 252 sessions
TRAIN_END, VALID_END = 1260, 1764    # train: years 1-5, validation: years 6-7, holdout: years 8-10
COST_BPS = 5
GRID = [(f, s) for f in (5, 10, 20, 50) for s in (50, 100, 200) if f < s]
REQUIRED_SPEC = ["question", "forecast_target", "horizon", "bet_structure", "universe", "model",
                 "conditioning", "run_frequency", "data", "timezone", "price_adjustment", "fill_rule",
                 "costs", "benchmark", "risk_free", "annualization", "splits", "selection_rule"]


def make_bars(seed=SEED, n=DAYS):
    rng = random.Random(seed)
    bars, close = [], 100.0
    for day in range(n):
        open_ = close * math.exp(rng.gauss(0, 0.004))
        close = open_ * math.exp(rng.gauss(0.00025, 0.010))
        bars.append({"day": day, "open": open_, "close": close})
    return bars


def spec_hash(spec):
    return hashlib.sha256(json.dumps(spec, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:16]


def validate_spec(spec):
    missing = [k for k in REQUIRED_SPEC if not spec.get(k)]
    if missing:
        raise ValueError(f"Spec Card is missing: {missing}")
    return spec_hash(spec)


class TrialLog:
    """Append-only list of every evaluated idea. Each entry carries the spec hash."""

    def __init__(self, spec_id):
        self.spec_id, self.rows = spec_id, []

    def add(self, **fields):
        self.rows.append({"trial": len(self.rows) + 1, "spec": self.spec_id, **fields})
        return self.rows[-1]

    def jsonl(self):
        return "\n".join(json.dumps(r, ensure_ascii=False) for r in self.rows)


class HoldoutVault:
    """Keeps the final period closed until the spec is frozen; opens exactly once."""

    def __init__(self, bars, start):
        self._bars, self.start, self.opened_with = bars, start, None

    def open(self, frozen_spec_id, chosen_rule):
        if self.opened_with is not None:
            raise RuntimeError(f"holdout already opened for {self.opened_with}; a second look turns it into training data")
        self.opened_with = {"spec": frozen_spec_id, "rule": chosen_rule}
        return self._bars


def sma_weights(bars, fast, slow):
    """weights[t] = 1 if SMA_fast(close) > SMA_slow(close) at the close of day t, else 0."""
    closes = [b["close"] for b in bars]
    csum = [0.0]
    for c in closes:
        csum.append(csum[-1] + c)
    sma = lambda t, w: (csum[t + 1] - csum[t + 1 - w]) / w if t + 1 >= w else None
    out = []
    for t in range(len(bars)):
        a, b = sma(t, fast), sma(t, slow)
        out.append(1.0 if a is not None and b is not None and a > b else 0.0)
    return out


def run(bars, weights, start, end, cost_bps=COST_BPS):
    """Daily net and gross returns for holding intervals whose signal day is in [start, end - 2]."""
    gross, net, prev, traded = [], [], weights[start - 1] if start > 0 else 0.0, 0.0
    for t in range(start, end - 2):
        w = weights[t]
        r = w * (bars[t + 2]["open"] / bars[t + 1]["open"] - 1)
        c = abs(w - prev) * cost_bps / 10000
        traded += abs(w - prev)
        gross.append(r)
        net.append((1 - c) * (1 + r) - 1)
        prev = w
    return {"gross": gross, "net": net, "turnover_per_year": traded / len(net) * 252}


def metrics(returns):
    sd = statistics.stdev(returns)
    equity, peak, mdd = 1.0, 1.0, 0.0
    for r in returns:
        equity *= 1 + r
        peak = max(peak, equity)
        mdd = min(mdd, equity / peak - 1)
    return {"cagr": equity ** (252 / len(returns)) - 1, "vol": sd * math.sqrt(252),
            "sharpe": statistics.fmean(returns) / sd * math.sqrt(252) if sd else 0.0, "max_dd": mdd}


def moments(returns):
    m, sd = statistics.fmean(returns), statistics.pstdev(returns)
    skew = statistics.fmean(((r - m) / sd) ** 3 for r in returns)
    kurt = statistics.fmean(((r - m) / sd) ** 4 for r in returns)
    return skew, kurt


def expected_max_sharpe(trial_sharpes):
    """Bailey & Lopez de Prado (2014): expected maximum of N per-period Sharpe ratios under no skill."""
    n, gamma, z = len(trial_sharpes), 0.5772156649, NormalDist()
    v = statistics.variance(trial_sharpes)
    return math.sqrt(v) * ((1 - gamma) * z.inv_cdf(1 - 1 / n) + gamma * z.inv_cdf(1 - 1 / (n * math.e)))


def probabilistic_sharpe(returns, benchmark_sr):
    """PSR: probability that the true per-period Sharpe exceeds benchmark_sr, given skew and kurtosis."""
    sr = statistics.fmean(returns) / statistics.stdev(returns)
    skew, kurt = moments(returns)
    denom = math.sqrt(1 - skew * sr + (kurt - 1) / 4 * sr ** 2)
    return NormalDist().cdf((sr - benchmark_sr) * math.sqrt(len(returns) - 1) / denom)


def block_bootstrap_sharpe(returns, block=20, draws=1000, seed=1):
    rng, n, out = random.Random(seed), len(returns), []
    for _ in range(draws):
        sample = []
        while len(sample) < n:
            k = rng.randrange(0, n - block)
            sample.extend(returns[k:k + block])
        out.append(metrics(sample[:n])["sharpe"])
    out.sort()
    return out[int(0.05 * draws)], out[int(0.95 * draws)]

# %% [markdown]
# # บทที่ 12 — Capstone: Research Dossier
#
# ข้อมูลเป็น **ราคาสมมติ 10 ปี** จาก seed `20261125` มี drift ขึ้นเล็กน้อยและ **ไม่มีสัญญาณจังหวะเวลาโดยการออกแบบ**
# คำตอบที่ซื่อตรงจึงควรเป็น "กฎที่เลือกไม่ชนะการซื้อแล้วถือในช่วง holdout"
# ปี 1–5 ฝึก ปี 6–7 validation ปี 8–10 holdout ที่เปิดได้ครั้งเดียว

# %%
spec = {
    "question": "Does an SMA crossover improve risk-adjusted return over buy-and-hold for one synthetic stock?",
    "forecast_target": "sign of trend over the next weeks (long or cash)",
    "horizon": "days to weeks; position re-evaluated every session",
    "bet_structure": "long/cash, weight 0 or 1, no leverage, no shorting",
    "universe": "one synthetic stock (seed 20261125)",
    "model": "SMA fast > SMA slow on close; grid of 11 (fast, slow) pairs",
    "conditioning": "none",
    "run_frequency": "daily after the close",
    "data": "synthetic daily open/close, 2520 sessions, no gaps",
    "timezone": "session index only (no calendar)",
    "price_adjustment": "not applicable (synthetic, no corporate actions)",
    "fill_rule": "signal close t, trade open t+1, hold to open t+2",
    "costs": "5 bps per unit of weight change; cash earns 0%",
    "benchmark": "buy-and-hold over the same intervals, entry cost included",
    "risk_free": "0% (stated, not estimated)",
    "annualization": "252 sessions; Sharpe = mean/stdev * sqrt(252)",
    "splits": "train 0-1259, validation 1260-1763, holdout 1764-2519 opened once",
    "selection_rule": "highest validation net Sharpe; ties -> slower pair",
}
spec_id = validate_spec(spec)
print("Spec Card fields:", len(spec), "| spec id:", spec_id)
try:
    validate_spec({k: v for k, v in spec.items() if k != "costs"})
except ValueError as error:
    print("Incomplete spec rejected:", error)

# %% [markdown]
# ## 1. ลองทุกคู่ใน grid แล้วจดทุกครั้ง

# %%
bars = make_bars()
assert bars == make_bars()
vault = HoldoutVault(bars, VALID_END)      # the full series lives in the vault
dev = bars[:VALID_END]                     # research code only ever sees this slice
log = TrialLog(spec_id)
results = {}
for fast, slow in GRID:
    w = sma_weights(dev, fast, slow)
    tr, va = run(dev, w, slow, TRAIN_END), run(dev, w, TRAIN_END, VALID_END)
    results[(fast, slow)] = {"weights": w, "train": metrics(tr["net"]), "valid": metrics(va["net"]), "valid_net": va["net"]}
    log.add(rule=f"SMA {fast}/{slow}", train_sharpe=round(results[(fast, slow)]["train"]["sharpe"], 3),
            valid_sharpe=round(results[(fast, slow)]["valid"]["sharpe"], 3), turnover=round(va["turnover_per_year"], 1))
bh = [1.0] * DAYS
bench_valid = metrics(run(dev, bh, TRAIN_END, VALID_END)["net"])
rng = random.Random(SEED)
random_w = [float(rng.random() < 0.5) for _ in range(DAYS)]
log.add(rule="random 50% long (baseline)", valid_sharpe=round(metrics(run(dev, random_w, TRAIN_END, VALID_END)["net"])["sharpe"], 3))
log.add(rule="buy-and-hold (baseline)", valid_sharpe=round(bench_valid["sharpe"], 3))
print(log.jsonl())
print("Trials logged:", len(log.rows))

# %% [markdown]
# ## 2. เลือกตามกติกาที่ประกาศไว้ แล้ว freeze spec

# %%
chosen = max(GRID, key=lambda p: (round(results[p]["valid"]["sharpe"], 6), p[1]))
print("Chosen by validation net Sharpe:", chosen, "| validation Sharpe", round(results[chosen]["valid"]["sharpe"], 3),
      "| buy-and-hold validation Sharpe", round(bench_valid["sharpe"], 3))
frozen = dict(spec, chosen_rule=f"SMA {chosen[0]}/{chosen[1]}", trials=len(GRID))
frozen_id = spec_hash(frozen)
print("Frozen spec id:", frozen_id)

# %% [markdown]
# ## 3. หัก "ผลของการเลือก" ด้วย Deflated Sharpe
#
# Sharpe สูงสุดจาก 11 คู่ย่อมสูงกว่าค่าจริงของคู่นั้น เราคำนวณ Sharpe สูงสุดที่คาดว่าจะได้ถ้าไม่มีคู่ไหนเก่งเลย
# แล้วถามว่าคู่ที่เลือกเกินค่านั้นด้วยความน่าจะเป็นเท่าไร (Bailey & López de Prado, 2014)

# %%
per_period = [statistics.fmean(results[p]["valid_net"]) / statistics.stdev(results[p]["valid_net"]) for p in GRID]
sr0 = expected_max_sharpe(per_period)
psr_zero = probabilistic_sharpe(results[chosen]["valid_net"], 0.0)
dsr = probabilistic_sharpe(results[chosen]["valid_net"], sr0)
print(f"Expected max annualized Sharpe from {len(GRID)} unskilled trials: {sr0 * math.sqrt(252):.2f}")
print(f"P(true Sharpe > 0)            : {psr_zero:.1%}")
print(f"Deflated Sharpe ratio (P > SR0): {dsr:.1%}")
assert 0 <= dsr <= psr_zero <= 1

# %% [markdown]
# ## 4. เปิด holdout ครั้งเดียว

# %%
full = vault.open(frozen_id, frozen["chosen_rule"])
w = sma_weights(full, *chosen)
# Causality check: weights for development days do not change once later data exists.
assert w[:VALID_END] == results[chosen]["weights"]
hold = run(full, w, VALID_END, DAYS)
hold_bh = run(full, bh, VALID_END, DAYS)
m, mb = metrics(hold["net"]), metrics(hold_bh["net"])
mg = metrics(hold["gross"])
print(f"Holdout {frozen['chosen_rule']}: gross CAGR {mg['cagr']:.2%} | net CAGR {m['cagr']:.2%} | vol {m['vol']:.1%} | Sharpe {m['sharpe']:.2f} | maxDD {m['max_dd']:.1%} | turnover {hold['turnover_per_year']:.1f}/yr")
print(f"Holdout buy-and-hold   : net CAGR {mb['cagr']:.2%} | vol {mb['vol']:.1%} | Sharpe {mb['sharpe']:.2f} | maxDD {mb['max_dd']:.1%}")
lo, hi = block_bootstrap_sharpe(hold["net"])
print(f"90% block-bootstrap interval of holdout Sharpe: {lo:.2f} to {hi:.2f}")
try:
    vault.open(frozen_id, "SMA 10/50")
except RuntimeError as error:
    print("Second opening refused:", error)

# %% [markdown]
# ## 5. เขียน Dossier หน้าแรก
#
# ข้อเท็จจริง สมมติฐาน การตีความ และข้อเสนอแยกจากกัน ตัวเลขทุกตัวมาจาก cell ข้างบน

# %%
dossier = f"""# Research Dossier: SMA crossover on a synthetic stock
Spec id {spec_id} -> frozen {frozen_id} | trials logged {len(log.rows)} (grid {len(GRID)} + 2 baselines)

## Facts
- Holdout (sessions {VALID_END}-{DAYS - 1}, opened once): {frozen['chosen_rule']} net CAGR {m['cagr']:.2%}, Sharpe {m['sharpe']:.2f}, max drawdown {m['max_dd']:.1%}
- Buy-and-hold, same intervals: net CAGR {mb['cagr']:.2%}, Sharpe {mb['sharpe']:.2f}, max drawdown {mb['max_dd']:.1%}
- Gross vs net CAGR of the rule: {mg['cagr']:.2%} vs {m['cagr']:.2%}; turnover {hold['turnover_per_year']:.1f} weight units per year
- Deflated Sharpe ratio at selection: {dsr:.1%}; 90% bootstrap interval of holdout Sharpe {lo:.2f} to {hi:.2f}

## Assumptions
- Synthetic data without timing signal by design; 5 bps per weight change; cash at 0%; no taxes, no borrow, no capacity limits

## Interpretation
- The validation winner did not show evidence of skill after accounting for {len(GRID)} trials

## Recommendation
- Do not proceed to paper trading with this rule; record it as a rejected idea
"""
print(dossier)
assert "opened once" in dossier and str(len(log.rows)) in dossier
print("ALL CHECKS PASSED")
