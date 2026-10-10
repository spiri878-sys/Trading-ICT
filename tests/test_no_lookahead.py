"""Causality tests: features at bar i must not change when future bars are removed."""
import numpy as np
import pandas as pd
from raptor.indicators import confirmed_swings, atr
from raptor.setups import build_features


def synth_m1(n=60 * 24 * 12, seed=1):
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2024-01-01 01:00", periods=n, freq="1min")
    c = 2000 + np.cumsum(rng.normal(0, 0.3, n))
    o = np.r_[c[0], c[:-1]]
    h = np.maximum(o, c) + rng.random(n) * 0.2
    l = np.minimum(o, c) - rng.random(n) * 0.2
    return pd.DataFrame({"open": o, "high": h, "low": l, "close": c, "tickvol": 1, "vol": 0, "spread": 20}, index=idx)


def test_swings_are_causal():
    rng = np.random.default_rng(0)
    h = np.cumsum(rng.normal(size=500)) + 100
    l = h - 1
    full = confirmed_swings(h, l, 3)
    cut = confirmed_swings(h[:300], l[:300], 3)
    for a, b in zip(full, cut):
        np.testing.assert_array_equal(a[:300], b)


def test_features_truncation_invariant():
    m1 = synth_m1()
    full = build_features(m1, "5min", 3)
    cut_time = m1.index[len(m1) * 2 // 3]
    part = build_features(m1[m1.index < cut_time], "5min", 3)
    # compare rows whose 5m bar closed before the cut and whose HTF context is final
    common = part.index[part.index + pd.Timedelta(minutes=5) <= cut_time]
    cols = [c for c in part.columns if c not in ("d1_atr_rel",)]
    a = full.loc[common, cols].astype(float); b = part.loc[common, cols].astype(float)
    # the very last rows may legitimately differ only for bars still open at the cut -> excluded above
    diff = ~(np.isclose(a.values, b.values, equal_nan=True))
    bad = pd.DataFrame(diff, index=common, columns=cols).sum()
    assert bad.sum() == 0, bad[bad > 0]
