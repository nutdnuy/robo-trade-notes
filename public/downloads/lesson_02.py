"""Offline Python foundations: synthetic prices, deterministic outputs, no API calls."""
import hashlib
import json
import platform
import numpy as np
import pandas as pd

PRICES = [100.0, 102.0, 101.0, 104.0, 103.0]

def trailing_mean(close, window=3):
    """Return a full-window trailing mean without modifying the input."""
    if isinstance(window, bool) or not isinstance(window, int) or window < 1:
        raise ValueError("window must be a positive integer")
    values = pd.Series(close, dtype="float64", copy=True)
    if not np.isfinite(values).all() or (values <= 0).any():
        raise ValueError("prices must be finite and positive")
    if not values.index.is_monotonic_increasing or not values.index.is_unique:
        raise ValueError("index must be ordered and unique")
    return values.rolling(window, min_periods=window).mean()

def main():
    close = pd.Series(PRICES, index=pd.RangeIndex(1, 6, name="bar"), name="close")
    frame = close.to_frame()
    frame["sma3"] = trailing_mean(close, 3)
    frame["return"] = close.pct_change(fill_method=None)
    print(frame.round(6).to_string())
    total = (1 + frame["return"].dropna()).prod() - 1
    assert np.isclose(total, close.iloc[-1] / close.iloc[0] - 1)
    assert frame["sma3"].iloc[:2].isna().all()
    assert np.isclose(frame["sma3"].iloc[-1], 308 / 3)
    print(f"Total synthetic price change: {total:.6%}")
    manifest = {"symbol": "SYNTHETIC", "bars": 5, "currency": "illustrative USD", "calendar": None,
                "window": 3, "python": platform.python_version(), "numpy": np.__version__, "pandas": pd.__version__}
    payload = json.dumps(PRICES, separators=(",", ":")).encode()
    print("Input SHA256:", hashlib.sha256(payload).hexdigest())
    print(json.dumps(manifest, indent=2))

if __name__ == "__main__":
    main()
