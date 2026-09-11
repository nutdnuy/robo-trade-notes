"""Offline chronological ML tutorial with a train-fitted ridge classifier.

Run: python lesson_07.py
Synthetic daily sessions with zero overnight returns; no broker connection.
"""

# %% Setup and reproducible synthetic sessions
import platform
import numpy as np
import pandas as pd

print({"python": platform.python_version(), "numpy": np.__version__, "pandas": pd.__version__})
rng = np.random.default_rng(7)
returns = np.zeros(420)
noise = rng.normal(0, .012, len(returns))
for t in range(1, len(returns)):
    returns[t] = .25 * returns[t - 1] + noise[t]
closes = 100 * np.cumprod(1 + returns)
opens = np.r_[100, closes[:-1]]
assert np.all(returns > -1)
print({"sessions": len(returns), "seed": 7, "first_close": round(float(closes[0]), 6), "last_close": round(float(closes[-1]), 6)})

# %% Features at close t; labels from next open to next close
rows = []
for t in range(2, len(returns) - 1):
    rows.append((t, t + 1, returns[t], returns[t - 1], returns[t - 2], 1 if returns[t + 1] > 0 else -1, returns[t + 1]))
data = pd.DataFrame(rows, columns=["decision_session", "label_session", "r0", "r1", "r2", "y", "future_return"])
features = ["r0", "r1", "r2"]
X, y = data[features].to_numpy(), data.y.to_numpy()
print(data.head(5).round(6).to_string(index=False))

# %% Chronological split and training-only preprocessing
train_idx = np.arange(0, 240)
valid_idx = np.arange(241, 321)
test_idx = np.arange(322, len(data))
# One excluded decision row at each boundary; no overlapping outcome horizon.
assert data.label_session.iloc[train_idx[-1]] < data.decision_session.iloc[valid_idx[0]]
assert data.label_session.iloc[valid_idx[-1]] < data.decision_session.iloc[test_idx[0]]
mu = X[train_idx].mean(axis=0)
sigma = X[train_idx].std(axis=0, ddof=0)
sigma = np.where(sigma == 0, 1.0, sigma)
Z = np.column_stack([np.ones(len(X)), (X - mu) / sigma])
print(pd.DataFrame({"split": ["train", "validation", "test"], "rows": [len(train_idx), len(valid_idx), len(test_idx)], "first_decision": [data.decision_session.iloc[i[0]] for i in [train_idx, valid_idx, test_idx]], "last_label": [data.label_session.iloc[i[-1]] for i in [train_idx, valid_idx, test_idx]]}).to_string(index=False))
print("Training means:", np.round(mu, 8))

# %% Fit and select on validation only
def fit_ridge(design, labels, alpha):
    penalty = np.eye(design.shape[1]) * alpha
    penalty[0, 0] = 0
    return np.linalg.solve(design.T @ design + penalty, design.T @ labels)


def classification_metrics(actual, predicted):
    recalls = [np.mean(predicted[actual == label] == label) for label in [-1, 1]]
    return {"accuracy": float(np.mean(actual == predicted)), "balanced_accuracy": float(np.mean(recalls))}


alphas = [.1, 1.0, 10.0, 100.0]
models, validation_rows = {}, []
for alpha in alphas:
    models[alpha] = fit_ridge(Z[train_idx], y[train_idx], alpha)
    prediction = np.where(Z[valid_idx] @ models[alpha] > 0, 1, -1)
    validation_rows.append({"alpha": alpha, **classification_metrics(y[valid_idx], prediction)})
# Predetermined tie-break: choose the stronger regularization.
chosen = max(validation_rows, key=lambda row: (row["balanced_accuracy"], row["alpha"]))["alpha"]
frozen_coef = models[chosen].copy()
print(pd.DataFrame(validation_rows).round(6).to_string(index=False))
print({"selected_alpha": chosen, "selection_metric": "validation balanced accuracy", "refit": False})

# %% Final test, once: classifier quality is separate from trading P&L
test_prediction = np.where(Z[test_idx] @ frozen_coef > 0, 1, -1)
majority_label = 1 if (y[train_idx] == 1).sum() > (y[train_idx] == -1).sum() else -1
majority_prediction = np.full(len(test_idx), majority_label)
persistence_prediction = np.where(X[test_idx, 0] > 0, 1, -1)
predictions = {"ridge": test_prediction, "training_majority": majority_prediction, "persistence": persistence_prediction}
scores = pd.DataFrame({name: classification_metrics(y[test_idx], pred) for name, pred in predictions.items()}).T
print(scores.round(6).to_string())
matrix = pd.crosstab(pd.Series(y[test_idx], name="actual"), pd.Series(test_prediction, name="predicted")).reindex(index=[-1, 1], columns=[-1, 1], fill_value=0)
print(matrix.to_string())

# %% Illustrative all-in/cash translation, including both entry and exit costs
def strategy_result(future_returns, long_target, cost=.001):
    equity, previous, switches = 1.0, 0, 0
    path = [equity]
    for ret, target in zip(future_returns, long_target):
        change = abs(int(target) - previous)
        equity *= (1 - cost * change) * (1 + int(target) * ret)
        switches += change
        path.append(equity)
        previous = int(target)
    equity *= 1 - cost * previous
    path[-1] = equity
    switches += previous
    values = np.array(path)
    return {"return_pct": (equity - 1) * 100, "max_drawdown_pct": np.min(values / np.maximum.accumulate(values) - 1) * 100, "long_exposure_pct": np.mean(long_target) * 100, "cost_events": switches}


test_returns = data.future_return.iloc[test_idx].to_numpy()
trading = pd.DataFrame({
    "ridge_long_cash_net": strategy_result(test_returns, test_prediction == 1),
    "always_long_net": strategy_result(test_returns, np.ones(len(test_idx), dtype=int)),
    "cash_no_interest": strategy_result(test_returns, np.zeros(len(test_idx), dtype=int)),
}).T
print(trading.round(6).to_string())

# %% Leakage checks and exercise answer
assert len(data) == 417 and len(test_idx) == 95
assert np.allclose(Z[train_idx, 1:].mean(axis=0), 0, atol=1e-12)
# Altering future/test data must not change training parameters or selected alpha.
tampered_X = X.copy()
tampered_X[test_idx] += 1000
assert np.array_equal(tampered_X[train_idx], X[train_idx])
assert np.array_equal(tampered_X[train_idx].mean(axis=0), mu)
assert np.array_equal(fit_ridge(Z[train_idx], y[train_idx], chosen), frozen_coef)
# Rebuild a known prefix from a series whose distant future has been altered.
altered_returns = returns.copy()
altered_returns[325:] = .9
for t in range(2, 243):
    past_features = np.array([altered_returns[t], altered_returns[t - 1], altered_returns[t - 2]])
    assert np.array_equal(past_features, X[t - 2])
assert matrix.to_numpy().sum() == 95
# Every label exactly matches the next session's executable synthetic open-close return.
for row in data.itertuples():
    assert np.isclose(row.future_return, closes[row.label_session] / opens[row.label_session] - 1)
    assert row.r0 == returns[row.decision_session]
assert strategy_result(np.array([.01, -.02]), np.array([1, 0]))["cost_events"] == 2
assert np.isclose(strategy_result(np.array([.01, -.02]), np.array([1, 0]))["return_pct"], ((.999**2) * 1.01 - 1) * 100)
print("PASS: time boundaries, train-only scaling, next-session labels, confusion matrix, and costs")
