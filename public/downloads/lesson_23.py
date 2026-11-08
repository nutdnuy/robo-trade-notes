"""Chapter 10 - time series and machine learning: catching leakage.

Offline teaching example. Daily returns are SYNTHETIC white noise: by
construction nothing is predictable, so any accuracy clearly above 50% is a
leak in the method. A second series has a small autocorrelation PLANTED BY
DESIGN for the walk-forward section. Standard library only, including a small
k-nearest-neighbours classifier. Run: python3 lesson_23.py
"""

import math
import random
import statistics

SEED = 20261123
DAYS, HORIZON, K = 1600, 20, 5


def make_returns(seed=SEED, n=DAYS, phi=0.0):
    rng = random.Random(seed)
    out, prev = [], 0.0
    for _ in range(n):
        prev = phi * prev + rng.gauss(0, 0.01)
        out.append(prev)
    return out


def trailing_sum(r, t, window):
    return sum(r[t - window + 1:t + 1])


def features_at(r, t):
    """Known at the close of day t: past 20/40/60-day returns and 60-day volatility."""
    return [trailing_sum(r, t, 20), trailing_sum(r, t, 40), trailing_sum(r, t, 60), statistics.pstdev(r[t - 59:t + 1])]


def leaky_feature_at(r, t, half=10):
    """A centred 21-day mean: looks smooth on a chart, but uses days t+1..t+10."""
    return features_at(r, t)[:3] + [statistics.fmean(r[t - half:t + half + 1])]


def label_at(r, t, horizon=HORIZON):
    """1 if the sum of returns over days t+1..t+horizon is positive. Overlaps neighbouring labels."""
    return int(sum(r[t + 1:t + 1 + horizon]) > 0)


def dataset(r, feature_fn=features_at, horizon=HORIZON):
    rows = []
    for t in range(60, len(r) - horizon - 10):
        rows.append({"t": t, "x": feature_fn(r, t), "y": label_at(r, t, horizon)})
    return rows


def standardize(train, test):
    """Scaler fitted on training rows only."""
    k = len(train[0]["x"])
    mu = [statistics.fmean(row["x"][i] for row in train) for i in range(k)]
    sd = [statistics.pstdev(row["x"][i] for row in train) or 1.0 for i in range(k)]
    scale = lambda rows: [[(v - m) / s for v, m, s in zip(row["x"], mu, sd)] for row in rows]
    return scale(train), scale(test)


def knn_predict(train_x, train_y, test_x, k=K):
    out = []
    for q in test_x:
        nearest = sorted(range(len(train_x)), key=lambda i: sum((a - b) ** 2 for a, b in zip(train_x[i], q)))[:k]
        out.append(int(sum(train_y[i] for i in nearest) * 2 > k))
    return out


def accuracy(pred, truth):
    return sum(p == y for p, y in zip(pred, truth)) / len(truth)


def evaluate(train, test, k=K):
    tx, sx = standardize(train, test)
    return accuracy(knn_predict(tx, [r["y"] for r in train], sx, k), [r["y"] for r in test])


def random_split(rows, test_share=0.2, seed=1):
    idx = list(range(len(rows)))
    random.Random(seed).shuffle(idx)
    cut = int(len(rows) * (1 - test_share))
    return [rows[i] for i in idx[:cut]], [rows[i] for i in idx[cut:]]


def chronological_split(rows, test_share=0.2, purge=HORIZON):
    """Train on the past, test on the future; drop training rows whose label window reaches the test period."""
    cut = int(len(rows) * (1 - test_share))
    test = rows[cut:]
    first_test_t = test[0]["t"]
    train = [r for r in rows[:cut] if r["t"] + purge < first_test_t]
    return train, test


def binomial_se(n, p=0.5):
    return math.sqrt(p * (1 - p) / n)

# %% [markdown]
# # บทที่ 10 — Time Series และ Machine Learning: กับดัก Leakage
#
# ผลตอบแทนรายวันในส่วนแรกเป็น **white noise สมมติ** ไม่มีอะไรทำนายได้เลยโดยการออกแบบ
# ถ้าวิธีของเราได้ accuracy สูงกว่า 50% อย่างชัดเจน แปลว่าวิธีรั่ว ไม่ใช่โมเดลเก่ง
# label คือเครื่องหมายของผลตอบแทนรวม 20 วันข้างหน้า feature คือผลตอบแทนย้อนหลัง 20/40/60 วันและ volatility 60 วัน

# %%
r = make_returns()
rows = dataset(r)
print("Rows:", len(rows), "| share of positive labels:", round(statistics.fmean(row["y"] for row in rows), 3))

# %% [markdown]
# ## 1. สุ่มแบ่ง train/test แบบข้อมูลทั่วไป

# %%
train_r, test_r = random_split(rows)
acc_random = evaluate(train_r, test_r)
print(f"Random split   : {len(train_r)} train / {len(test_r)} test -> accuracy {acc_random:.1%}")

# %% [markdown]
# ## 2. แบ่งตามเวลา และตัดช่วงที่ label ทับกัน (purge)

# %%
train_c, test_c = chronological_split(rows)
acc_chrono = evaluate(train_c, test_c)
print(f"Chronological  : {len(train_c)} train / {len(test_c)} test -> accuracy {acc_chrono:.1%}")
print(f"Standard error of accuracy for {len(test_c)} test rows at 50%: {binomial_se(len(test_c)):.1%}")
assert acc_random - acc_chrono > 0.10
assert abs(acc_chrono - 0.5) < 3 * binomial_se(len(test_c))

# %% [markdown]
# ## 3. ทำไมการสุ่มแบ่งถึงรั่ว
#
# วันที่ติดกันมี feature เกือบเหมือนกัน และ label ของวัน t กับ t+1 ใช้ผลตอบแทน 19 วันร่วมกัน
# เพื่อนบ้านที่ใกล้ที่สุดของแถวทดสอบจึงมักเป็นวันข้าง ๆ ใน train ซึ่งรู้คำตอบเกือบทั้งหมดแล้ว

# %%
same_label_next_day = statistics.fmean(int(a["y"] == b["y"]) for a, b in zip(rows, rows[1:]))
print(f"Label of day t equals label of day t+1: {same_label_next_day:.1%} of days")
tx, sx = standardize(train_r, test_r)
gaps = []
for q, row in zip(sx[:100], test_r[:100]):
    nearest = min(range(len(tx)), key=lambda i: sum((a - b) ** 2 for a, b in zip(tx[i], q)))
    gaps.append(abs(train_r[nearest]["t"] - row["t"]))
print(f"Median distance in days between a test row and its nearest training row: {statistics.median(gaps):.0f}")

# %% [markdown]
# ## 4. Feature ที่แอบใช้อนาคต
#
# ค่าเฉลี่ยแบบ centred window ใช้ข้อมูล 10 วันข้างหน้า แม้แบ่งตามเวลาอย่างถูกต้อง ผลก็ยังรั่ว
# Test จาก Prework P1 จับได้: เปลี่ยนผลตอบแทนหลังวัน t แล้ว feature ของวัน t ต้องไม่เปลี่ยน

# %%
leaky_rows = dataset(r, leaky_feature_at)
train_l, test_l = chronological_split(leaky_rows)
acc_leaky = evaluate(train_l, test_l)
print(f"Chronological with centred-mean feature: accuracy {acc_leaky:.1%}")

def feature_uses_future(fn, series, t=800):
    changed = series[:t + 1] + [x * -3 for x in series[t + 1:]]
    return fn(series, t) != fn(changed, t)

print("features_at uses the future     :", feature_uses_future(features_at, r))
print("leaky_feature_at uses the future:", feature_uses_future(leaky_feature_at, r))
assert not feature_uses_future(features_at, r) and feature_uses_future(leaky_feature_at, r)
assert acc_leaky > acc_chrono + 0.10

# %% [markdown]
# ## 5. Walk-forward กับข้อมูลที่มีสัญญาณเล็ก
#
# ชุดที่สองฝังค่า autocorrelation 0.08 ไว้โดยตั้งใจ ใช้ label วันถัดไป (horizon 1) feature ตัวเดียวคือผลตอบแทนวันนี้
# ทุก 200 วัน ฝึกใหม่ด้วยข้อมูลที่ผ่านมาทั้งหมด แล้วทำนาย 200 วันถัดไป

# %%
r2 = make_returns(seed=SEED + 1, n=4000, phi=0.08)
rows2 = [{"t": t, "x": [r2[t]], "y": label_at(r2, t, 1)} for t in range(20, len(r2) - 1)]
preds, truth = [], []
for start in range(1000, len(rows2), 200):
    train = [row for row in rows2[:start] if row["t"] + 1 < rows2[start]["t"]]
    test = rows2[start:start + 200]
    # Simple rule fitted on train: sign of the slope of next-day return on today's return.
    xs = [row["x"][0] for row in train]
    ys = [r2[row["t"] + 1] for row in train]
    mx, my = statistics.fmean(xs), statistics.fmean(ys)
    slope = sum((a - mx) * (b - my) for a, b in zip(xs, ys)) / sum((a - mx) ** 2 for a in xs)
    preds += [int((slope * row["x"][0]) > 0) for row in test]
    truth += [row["y"] for row in test]
acc_wf = accuracy(preds, truth)
print(f"Walk-forward accuracy on {len(truth)} out-of-sample days: {acc_wf:.1%} (50% +/- {2 * binomial_se(len(truth)):.1%} at two standard errors)")
assert acc_wf > 0.5
print("ALL CHECKS PASSED")
