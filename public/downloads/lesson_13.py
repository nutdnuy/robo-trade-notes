"""Offline teaching backtest: invented prices, fixed seed, no market data.

Run with Python 3 using only its standard library. A session number is an
observation index, not a date. All prices are in invented currency units.
"""

import json
import math
import random
import statistics

SEED = 20260925
SESSION_COUNT = 320
START_SESSION = 60
PERIODS_PER_YEAR = 252


def make_data(seed=SEED, sessions=SESSION_COUNT):
    """Generate one fixed path; the seed was fixed before evaluating results."""
    rng = random.Random(seed)
    rows = []
    previous_close = 100.0
    for session in range(sessions):
        opening = previous_close * math.exp(0.0001 + 0.004 * rng.gauss(0, 1))
        intraday_sigma = 0.009 + 0.004 * math.sin(2 * math.pi * session / 80)
        closing = opening * math.exp(0.0002 + intraday_sigma * rng.gauss(0, 1))
        rows.append({"session": session, "open": round(opening, 8),
                     "close": round(closing, 8)})
        previous_close = closing
    return {"metadata": {
        "seed": seed, "sessions": sessions, "kind": "synthetic teaching data",
        "units": "invented currency units per share; session indices, no calendar dates",
        "generator": "Python random.Random(seed), Gaussian log-price increments",
        "openRule": "previous_close * exp(0.0001 + 0.004 * Z_open)",
        "closeRule": "open * exp(0.0002 + (0.009 + 0.004*sin(2*pi*session/80)) * Z_close)",
        "normalDraws": "Independent standard Normal draws; first previous_close = 100",
        "rounding": "Published open and close prices rounded to 8 decimal places",
        "purpose": "Explain timing, costs, and sizing; not evidence of a profitable strategy",
    }, "rows": rows}


def sample_std(values):
    return statistics.stdev(values) if len(values) > 1 else 0.0


def indicators(rows, index):
    closes = [row["close"] for row in rows]
    fast = sum(closes[index - 19:index + 1]) / 20
    slow = sum(closes[index - 49:index + 1]) / 50
    returns = [closes[k] / closes[k - 1] - 1 for k in range(index - 19, index + 1)]
    return {"side": 1.0 if fast > slow else 0.0, "fast": fast, "slow": slow,
            "volatility": sample_std(returns) * math.sqrt(PERIODS_PER_YEAR)}


def rebalance(pretrade_weight, target_weight, cost_fraction):
    """Exact post-fee target weight, with proportional cost on traded notional.

    E is pretrade equity, a = risky holdings / E, w = target AFTER costs.
    k = E_after_cost / E solves k = 1 - c * abs(w*k - a).
    No fixed fees, spreads beyond the supplied cost, interest, or shorting.
    """
    a, w, c = pretrade_weight, target_weight, cost_fraction
    if w >= a:
        factor = (1 + c * a) / (1 + c * w)
    else:
        factor = (1 - c * a) / (1 - c * w)
    turnover = abs(w * factor - a)
    return {"factor": factor, "turnover": turnover, "feeFraction": c * turnover}


def evaluate_backtest(data, lookahead=False, vol_target=False, cost_bps=5,
                      target_vol=0.1, benchmark=False):
    rows = data["rows"] if isinstance(data, dict) else data
    if len(rows) <= START_SESSION + 1:
        raise ValueError("At least 62 price rows are required")
    if not 0 <= cost_bps < 10000 or not math.isfinite(cost_bps):
        raise ValueError("cost_bps must be finite and between 0 and 10000 (exclusive)")
    if not target_vol > 0 or not math.isfinite(target_vol):
        raise ValueError("target_vol must be finite and positive")
    if any(not math.isfinite(row[key]) or row[key] <= 0
           for row in rows for key in ("open", "close")):
        raise ValueError("All open and close prices must be finite and positive")
    c = cost_bps / 10000
    equity, returns, weights, audit = [1.0], [], [], []
    sessions = [rows[START_SESSION]["session"]]
    pretrade_weight, total_turnover = 0.0, 0.0
    for t in range(START_SESSION, len(rows) - 1):
        decision_index = t if lookahead else t - 1
        info = indicators(rows, decision_index)
        size = min(1.0, target_vol / info["volatility"]) if info["volatility"] > 0 else 0.0
        weight = 1.0 if benchmark else info["side"] * (size if vol_target else 1.0)
        trade = rebalance(pretrade_weight, weight, c)
        asset_return = rows[t + 1]["open"] / rows[t]["open"] - 1
        holding_factor = 1 + weight * asset_return
        period_factor = trade["factor"] * holding_factor
        drifted_weight = weight * (1 + asset_return) / holding_factor
        final_turnover = drifted_weight if t == len(rows) - 2 else 0.0
        if final_turnover:
            period_factor *= 1 - c * final_turnover
        total_turnover += trade["turnover"] + final_turnover
        returns.append(period_factor - 1)
        equity.append(equity[-1] * period_factor)
        sessions.append(rows[t + 1]["session"])
        weights.append(weight)
        audit.append({"session": rows[t]["session"], "decisionSession": rows[decision_index]["session"],
                      "pretradeWeight": pretrade_weight, "weight": weight,
                      "estimatedVolatility": info["volatility"], "side": info["side"],
                      "assetReturn": asset_return, "rebalanceTurnover": trade["turnover"],
                      "rebalanceFeeFraction": trade["feeFraction"],
                      "postFeeEquityFactor": trade["factor"],
                      "finalLiquidationTurnover": final_turnover})
        pretrade_weight = drifted_weight
    peak, drawdowns = 1.0, []
    for value in equity:
        peak = max(peak, value)
        drawdowns.append(value / peak - 1)
    n = len(returns)
    volatility = sample_std(returns)
    identifier = "benchmark" if benchmark else ("biased" if lookahead else "causal") + ("-target" if vol_target else "-fixed")
    labels = {"causal-fixed": "ใช้ข้อมูลทันเวลา · ขนาดคงที่", "causal-target": "ใช้ข้อมูลทันเวลา · Vol target",
              "biased-fixed": "ใช้ข้อมูลอนาคต · ขนาดคงที่", "biased-target": "ใช้ข้อมูลอนาคต · Vol target",
              "benchmark": "Buy and hold · ช่วงเวลาเดียวกัน"}
    return {"id": identifier, "label": labels[identifier], "returns": returns, "equity": equity,
            "drawdowns": drawdowns, "weights": weights, "sessions": sessions, "audit": audit,
            "metrics": {"totalReturn": equity[-1] - 1, "cagr": equity[-1] ** (PERIODS_PER_YEAR / n) - 1,
                        "volatility": volatility * math.sqrt(PERIODS_PER_YEAR),
                        "sharpe": statistics.mean(returns) / volatility * math.sqrt(PERIODS_PER_YEAR) if volatility else None,
                        "maxDrawdown": min(drawdowns), "turnover": total_turnover},
            "assumptions": {"startSession": rows[START_SESSION]["session"], "endSession": rows[-1]["session"],
                            "periods": n, "periodsPerYear": PERIODS_PER_YEAR, "costBps": cost_bps,
                            "targetVol": target_vol, "leverageCap": 1, "riskFreeRate": 0,
                            "smaWindows": [20, 50], "volatilityWindow": 20,
                            "volatilityEstimator": "sample standard deviation of close-to-close simple returns",
                            "execution": "rebalance at open t, hold to open t+1",
                            "information": "close t (impossible at open t)" if lookahead and not benchmark else "close t-1",
                            "zeroEstimatedVolatility": "hold cash when volatility targeting",
                            "costConvention": "exact target weight after proportional fees; initial entry and final liquidation included",
                            "turnoverConvention": "sum absolute traded notional / equity immediately before each trade event"}}


def compare_backtests(data, cost_bps=5, target_vol=0.1):
    return [evaluate_backtest(data, lookahead=lookahead, vol_target=vol_target,
                              cost_bps=cost_bps, target_vol=target_vol)
            for lookahead, vol_target in [(False, False), (False, True), (True, False), (True, True)]]


def evaluate_benchmark(data, cost_bps=5, target_vol=0.1):
    return evaluate_backtest(data, cost_bps=cost_bps, target_vol=target_vol, benchmark=True)


def print_summary(results):
    print(f"{'scenario':<16} {'total':>10} {'CAGR*':>10} {'vol*':>10} {'Sharpe*':>9} {'MDD':>10} {'turnover':>10}")
    for result in results:
        m = result["metrics"]
        sharpe = f"{m['sharpe']:.3f}" if m["sharpe"] is not None else "undefined"
        print(f"{result['id']:<16} {m['totalReturn']:>9.2%} {m['cagr']:>9.2%} {m['volatility']:>9.2%} {sharpe:>9} {m['maxDrawdown']:>9.2%} {m['turnover']:>10.3f}")
    print("* Annualized using 252 sessions/year; invented sessions, not actual dates. Sharpe uses rf=0.")


if __name__ == "__main__":
    data = make_data()
    results = compare_backtests(data) + [evaluate_benchmark(data)]
    print(f"Synthetic seed={SEED}; sessions={SESSION_COUNT}; interval open60 to open319")
    print_summary(results)
