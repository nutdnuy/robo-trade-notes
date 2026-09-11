"""Auditable vectorized long/cash research model; synthetic 8-bar data only."""
import numpy as np
import pandas as pd

OPEN = [100.0, 101.0, 103.0, 102.0, 105.0, 102.0, 99.0, 101.0]
CLOSE = [100.0, 102.0, 101.0, 104.0, 103.0, 100.0, 98.0, 101.0]

def run_backtest(short=2, long=3, cost_bps=10.0, initial=10000.0):
    """Signal at close, fill next open, fractional shares, final open liquidation.

    Entries spend all available equity including a fee on trade notional.
    Exits receive notional less the same fee. No shorting, borrowing or interest.
    """
    if any(isinstance(v, bool) or not isinstance(v, int) for v in [short, long]):
        raise ValueError("windows must be integers")
    if not 1 <= short < long < len(OPEN) - 1:
        raise ValueError("require 1 <= short < long < 7")
    if not np.isfinite(cost_bps) or not 0 <= cost_bps < 10000:
        raise ValueError("invalid cost_bps")
    if not np.isfinite(initial) or initial <= 0:
        raise ValueError("initial must be finite and positive")
    cost = cost_bps / 10000
    data = pd.DataFrame({"open": OPEN, "close": CLOSE}, index=pd.RangeIndex(1, 9, name="bar"))
    data["sma_short"] = data["close"].rolling(short, min_periods=short).mean()
    data["sma_long"] = data["close"].rolling(long, min_periods=long).mean()
    data["target_close"] = ((data["sma_short"] > data["sma_long"]) & data["sma_long"].notna()).astype(int)
    data["position_open"] = data["target_close"].shift(1, fill_value=0)
    # At the final open we liquidate by a predeclared horizon rule, ignoring that bar's close.
    data.loc[data.index[-1], "position_open"] = 0
    data["change_open"] = data["position_open"].diff().fillna(data["position_open"])
    data["market_return"] = data["open"].pct_change(fill_method=None).fillna(0)
    held_previous = data["position_open"].shift(1, fill_value=0)
    gross_factor = 1 + held_previous * data["market_return"]
    fee_factor = np.where(data["change_open"] > 0, 1 / (1 + cost),
                          np.where(data["change_open"] < 0, 1 - cost, 1.0))
    data["equity_gross"] = initial * gross_factor.cumprod()
    data["equity_net"] = initial * (gross_factor * fee_factor).cumprod()
    # Comparison starts at the first actionable open, with the same liquidation date and fees.
    benchmark_position = pd.Series(0, index=data.index)
    benchmark_position.iloc[long:-1] = 1
    benchmark_change = benchmark_position.diff().fillna(0)
    benchmark_factor = 1 + benchmark_position.shift(1, fill_value=0) * data["market_return"]
    benchmark_fee = np.where(benchmark_change > 0, 1 / (1 + cost), np.where(benchmark_change < 0, 1 - cost, 1.0))
    data["benchmark_net"] = initial * (benchmark_factor * benchmark_fee).cumprod()
    return data

def ledger_check(data, cost_bps=10.0, initial=10000.0):
    """Independent sequential cash/share accounting against the vector model."""
    cost = cost_bps / 10000
    cash, shares = initial, 0.0
    equity = []
    for _, row in data.iterrows():
        price = row["open"]
        if row["position_open"] == 1 and shares == 0:
            shares = cash / (price * (1 + cost))
            cash = 0.0
        elif row["position_open"] == 0 and shares != 0:
            cash = shares * price * (1 - cost)
            shares = 0.0
        equity.append(cash + shares * price)
    np.testing.assert_allclose(equity, data["equity_net"], rtol=1e-12, atol=1e-8)
    return cash, shares

def main():
    data = run_backtest()
    cash, shares = ledger_check(data)
    assert data["position_open"].tolist() == [0, 0, 0, 1, 1, 1, 0, 0]
    assert np.isclose(data["equity_net"].iloc[-1], 10000 * 99 / 102 * .999 / 1.001)
    assert shares == 0
    print(data.round(6).to_string())
    print("Strategy gross / net and benchmark net:", data.iloc[-1][["equity_gross", "equity_net", "benchmark_net"]].round(6).to_dict())
    print("Final cash / shares:", round(cash, 6), shares)

if __name__ == "__main__":
    main()
