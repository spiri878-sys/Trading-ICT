import numpy as np
import pandas as pd
import pytest

from raptor.prime import cells as C
from raptor.setups import build_features


def _synthetic_m1(days=6, seed=1):
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2021-03-01 01:00", periods=days * 1380, freq="1min")
    idx = idx[(idx.hour >= 1)]
    p = 1800 + np.cumsum(rng.normal(0, 0.35, len(idx)))
    o = p + rng.normal(0, 0.05, len(idx))
    c = p + rng.normal(0, 0.05, len(idx))
    h = np.maximum(o, c) + rng.random(len(idx)) * 0.4
    lo = np.minimum(o, c) - rng.random(len(idx)) * 0.4
    return pd.DataFrame({"open": o, "high": h, "low": lo, "close": c, "tickvol": 10, "vol": 0, "spread": 20},
                        index=idx)


@pytest.mark.parametrize("cell", list(C.ALL_CELLS))
def test_truncation_invariance(cell):
    """Segnali fino a T identici calcolando con dati fino a T o con dati successivi: nessun lookahead."""
    m1 = _synthetic_m1(days=30 if cell in ("PO3", "JUDAS") else 6)
    tf = C.TF_OF[cell]
    k = C.DEFAULTS[cell]["k"]
    prm = {"PO3": {"min_disp": 0.5, "min_fvg": 0.02}}
    full = C.generate({(tf, k): build_features(m1, tf, k)}, cells=[cell], params=prm)
    assert len(full) > 0, "il caso sintetico deve produrre segnali"
    cut = max(m1.index[len(m1) * 2 // 3], full.known_at.iloc[0] + pd.Timedelta(hours=4))
    part = C.generate({(tf, k): build_features(m1.loc[:cut], tf, k)}, cells=[cell], params=prm)
    lim = cut - pd.Timedelta(hours=3)  # le ultime barre della serie troncata non sono ancora chiuse in HTF
    a = full[full.known_at <= lim].reset_index(drop=True)
    b = part[part.known_at <= lim].reset_index(drop=True)
    cols = ["bar_time", "side", "price", "sl_struct"]
    pd.testing.assert_frame_equal(a[cols], b[cols])


def test_fill_times_limit_and_market():
    idx = pd.date_range("2021-03-01 10:00", periods=30, freq="1min")
    m1 = pd.DataFrame({"low": np.full(30, 100.0), "high": np.full(30, 101.0)}, index=idx)
    m1.loc[idx[10], "low"] = 98.0
    sig = pd.DataFrame({"known_at": [idx[2], idx[2], idx[2]], "tf": ["5min"] * 3, "expiry_bars": [4, 1, 4],
                        "side": [1, 1, 1], "price": [98.5, 98.5, 100.0], "otype": ["limit", "limit", "market"]})
    t = C.fill_times(sig, m1)
    assert t[0] == idx[10] and pd.isna(t[1]) and t[2] == idx[2]


def test_degraded_days_and_friday_filter():
    m1 = _synthetic_m1()
    f = build_features(m1, "5min", 3)
    s_all = C.generate({("5min", 3): f}, cells=["PPK"], params={"PPK": {"min_disp": 0.3}})
    day = s_all.bar_time.dt.normalize().iloc[0]
    s = C.generate({("5min", 3): f}, cells=["PPK"], params={"PPK": {"min_disp": 0.3}},
                   degraded=pd.DatetimeIndex([day]))
    assert (s.bar_time.dt.normalize() != day).all() and len(s) < len(s_all)
    assert not ((s.known_at.dt.dayofweek == 4) & (s.known_at.dt.hour >= 22)).any()
