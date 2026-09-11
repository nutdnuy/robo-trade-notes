"""Offline teaching example: costs, drawdown, and fair comparisons.

Run: python lesson_05.py
Synthetic sessions only; no market data, broker calls, or annualized claims.
"""

# %% Setup
import platform
import numpy as np
import pandas as pd

print({"python": platform.python_version(), "numpy": np.__version__, "pandas": pd.__version__})

# %% Synthetic inputs
# Each weight is fixed before its session opens. It is an input, not a fitted rule.
asset_returns = np.array([.01, -.02, .03, -.01, .02, -.04, .01, .03, -.02, .01, .02, -.01])
weights = np.array([0, 1, 1, 0, 1, 1, 1, 0, 0, 1, 1, 0])
INITIAL_EQUITY = 10_000.0
print(pd.DataFrame({"session": np.arange(1, 13), "asset_return_pct": asset_returns * 100, "weight": weights}).to_string(index=False))

# %% Exact all-in/cash cost model
def simulate(returns, targets, cost_rate=0.001, initial=INITIAL_EQUITY):
    """Charge a fraction of current NAV at each all-in/cash switch.

    Buy with remaining capital after entry costs; sell the entire holding on exit.
    Liquidate after the last return and include that fee in the last session.
    Targets must be known before each session starts. No shorts or leverage.
    """
    returns, targets = np.asarray(returns, float), np.asarray(targets)
    if len(returns) != len(targets) or len(returns) == 0:
        raise ValueError("Inputs must have equal, nonzero length")
    if not np.isfinite(returns).all() or np.any(returns <= -1):
        raise ValueError("Returns must be finite and greater than -1")
    if not np.isin(targets, [0, 1]).all() or not 0 <= cost_rate < 1 or initial <= 0:
        raise ValueError("Invalid target, cost, or initial capital")
    targets = targets.astype(int)
    equity, previous, total_cost, rows = float(initial), 0, 0.0, []
    for i, (ret, target) in enumerate(zip(returns, targets), start=1):
        before = equity
        fee = equity * cost_rate * abs(target - previous)
        equity = (equity - fee) * (1 + target * ret)
        terminal_fee = equity * cost_rate if i == len(returns) and target else 0.0
        equity -= terminal_fee
        total_cost += fee + terminal_fee
        rows.append((i, target, ret, fee + terminal_fee, equity, equity / before - 1))
        previous = target
    frame = pd.DataFrame(rows, columns=["session", "weight", "asset_return", "cost_usd", "equity_usd", "net_return"])
    frame.attrs["total_cost_usd"] = total_cost
    return frame


def metrics(frame, initial=INITIAL_EQUITY):
    equity = np.r_[initial, frame.equity_usd.to_numpy()]
    peaks = np.maximum.accumulate(equity)
    drawdown = equity / peaks - 1
    return {
        "final_equity_usd": equity[-1],
        "total_return_pct": (equity[-1] / initial - 1) * 100,
        "max_drawdown_pct": drawdown.min() * 100,
        "session_vol_pct": frame.net_return.std(ddof=1) * 100,
        "cash_cost_usd": frame.attrs["total_cost_usd"],
    }


gross = simulate(asset_returns, weights, cost_rate=0)
net = simulate(asset_returns, weights)
benchmark = simulate(asset_returns, np.ones(12, dtype=int))
summary = pd.DataFrame({"strategy_gross": metrics(gross), "strategy_net": metrics(net), "buy_hold_net": metrics(benchmark)}).T
print(summary.round(6).to_string())

# %% Cost sensitivity with a frozen rule
sensitivity = pd.DataFrame([
    {"cost_bps_per_side": bps, **metrics(simulate(asset_returns, weights, bps / 10_000))}
    for bps in [0, 5, 10, 20, 50]
])
print(sensitivity[["cost_bps_per_side", "final_equity_usd", "total_return_pct", "max_drawdown_pct"]].round(6).to_string(index=False))

# %% Drawdown and a win-rate counterexample
equity = np.r_[INITIAL_EQUITY, net.equity_usd.to_numpy()]
peaks = np.maximum.accumulate(equity)
drawdown = equity / peaks - 1
print(pd.DataFrame({"session": np.arange(13), "equity_usd": equity, "peak_usd": peaks, "drawdown_pct": drawdown * 100}).round(6).to_string(index=False))
trade_pnl = np.array([5.0] * 9 + [-60.0])
print({"winning_trades_pct": float((trade_pnl > 0).mean() * 100), "total_pnl_usd": float(trade_pnl.sum())})

# %% Independent checks and exercise answer
# Reconstruct the gross return directly from the seven invested sessions.
expected_gross = INITIAL_EQUITY * .98 * 1.03 * 1.02 * .96 * 1.01 * 1.01 * 1.02
# There are six entry/exit events; each multiplies capital by (1 - cost_rate).
assert int(np.abs(np.diff(np.r_[0, weights, 0])).sum()) == 6
assert np.isclose(gross.equity_usd.iloc[-1], expected_gross)
assert np.isclose(net.equity_usd.iloc[-1], expected_gross * .999**6)
assert np.isclose(benchmark.equity_usd.iloc[-1], INITIAL_EQUITY * np.prod(1 + asset_returns) * .999**2)
# Initial capital must count as a peak even if the first observed return is negative.
tiny = simulate(np.array([-.1, .05]), np.ones(2, dtype=int), cost_rate=0)
assert np.isclose(metrics(tiny)["max_drawdown_pct"], -10)
assert np.all(np.diff(sensitivity.final_equity_usd) < 0)
assert np.isclose(trade_pnl.sum(), -15)
print("PASS: cost compounding, benchmark costs, initial peak, sensitivity, and win-rate counterexample")
