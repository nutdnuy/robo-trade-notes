"""Original SMA teaching example. Offline synthetic data; no broker requests.
Run: python lesson_01.py --short 5 --long 20
"""
import argparse
from pathlib import Path
import pandas as pd


def build_signals(data, short=5, long=20):
    import math
    if not isinstance(short, int) or not isinstance(long, int) or not 1 <= short < long:
        raise ValueError("Require 1 <= short < long")
    out = data.copy()
    out["close"] = pd.to_numeric(out["close"], errors="raise")
    if not out["close"].map(math.isfinite).all() or len(out) < long:
        raise ValueError("Missing prices or insufficient history")
    out["sma_short"] = out["close"].rolling(short).mean()
    out["sma_long"] = out["close"].rolling(long).mean()
    ready = out["sma_long"].notna()
    out["target"] = (
        (out["sma_short"] > out["sma_long"]) & ready
    ).astype(int)
    # A close-based decision can only be considered afterwards.
    out["next_open_target"] = out["target"].shift(1).fillna(0).astype(int)
    out["changed"] = out["target"].diff().fillna(0).ne(0) & ready
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path, default=Path(__file__).with_name("demo_prices.csv"))
    parser.add_argument("--short", type=int, default=5)
    parser.add_argument("--long", type=int, default=20)
    args = parser.parse_args()
    raw = pd.read_csv(args.csv)
    if "day" in raw and (raw["day"].duplicated().any() or not raw["day"].is_monotonic_increasing):
        raise ValueError("Days must be unique and in increasing order")
    result = build_signals(raw, args.short, args.long)
    print("SYNTHETIC DATA. No API requests, orders, or performance claims.")
    print(result.tail(5).to_string(index=False))
    print("Target changes:", int(result["changed"].sum()))
    print("Change bars:", result.loc[result["changed"], "day"].tolist())


if __name__ == "__main__":
    main()
