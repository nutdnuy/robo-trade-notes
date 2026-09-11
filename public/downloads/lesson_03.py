"""Offline financial-data validation. Every price and timestamp is synthetic."""
import hashlib
from io import StringIO
import numpy as np
import pandas as pd

RAW_CSV = """time,open,high,low,close,volume
2026-01-05T14:33:00Z,101,104,100,103,130
2026-01-05T14:31:00Z,100,102,99,101,100
2026-01-05T14:32:00Z,101,103,100,102,110
2026-01-05T14:32:00Z,101,103,100,102,110
2026-01-05T14:34:00Z,103,104,101,,140
2026-01-05T14:35:00Z,102,103,100,101,150
2026-01-05T14:36:00Z,101,99,100,102,-1
"""
FIELDS = ["open", "high", "low", "close", "volume"]

def validate_bars(raw):
    """Keep raw input untouched; quarantine bad or conflicting rows, never fill prices."""
    required = ["time"] + FIELDS
    if not set(required).issubset(raw.columns):
        raise ValueError("missing required columns")
    exact_duplicate = raw.duplicated(subset=required, keep="first")
    work = raw.loc[~exact_duplicate, required].copy()
    # utc=True is valid here because the fixture declares every timestamp in UTC.
    work["time"] = pd.to_datetime(work["time"], format="ISO8601", utc=True, errors="coerce")
    for name in FIELDS:
        work[name] = pd.to_numeric(work[name], errors="coerce")
    price = work[["open", "high", "low", "close"]]
    finite = np.isfinite(work[FIELDS]).all(axis=1)
    flags = pd.DataFrame({
        "invalid_time": work["time"].isna(),
        "missing_or_nonfinite": ~finite,
        "nonpositive_price": (price <= 0).any(axis=1),
        "negative_volume": work["volume"] < 0,
        "invalid_ohlc": (work["high"] < price.max(axis=1)) | (work["low"] > price.min(axis=1)),
        "conflicting_timestamp": work["time"].notna() & work["time"].duplicated(keep=False),
    }, index=work.index)
    bad = flags.any(axis=1)
    quarantine = work.loc[bad].copy()
    quarantine["reason"] = flags.loc[bad].apply(lambda row: ";".join(row.index[row]), axis=1)
    clean = work.loc[~bad].sort_values("time").set_index("time")
    report = {"raw_rows": len(raw), "exact_duplicates_removed": int(exact_duplicate.sum()),
              "quarantined_rows": len(quarantine), "accepted_rows": len(clean)}
    assert sum(report[k] for k in ["exact_duplicates_removed", "quarantined_rows", "accepted_rows"]) == len(raw)
    return clean, quarantine, report

def main():
    raw = pd.read_csv(StringIO(RAW_CSV), dtype=str, keep_default_na=False)
    clean, quarantine, report = validate_bars(raw)
    expected = pd.date_range("2026-01-05T14:31:00Z", periods=5, freq="min")
    missing = expected.difference(clean.index)
    print(report)
    print(clean.to_string())
    print(quarantine[["time", "reason"]].to_string(index=False))
    print("Missing scheduled synthetic bars:", missing.astype(str).tolist())
    regular = clean.reindex(expected)
    regular["return"] = regular["close"].pct_change(fill_method=None)
    print(regular[["close", "return"]].to_string())
    assert report == {"raw_rows": 7, "exact_duplicates_removed": 1, "quarantined_rows": 2, "accepted_rows": 4}
    assert len(missing) == 1
    assert regular["return"].iloc[-2:].isna().all()
    print("Raw SHA256:", hashlib.sha256(RAW_CSV.encode()).hexdigest())

if __name__ == "__main__":
    main()
