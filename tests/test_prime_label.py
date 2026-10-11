import numpy as np
import pandas as pd

from raptor.engine import _label
from raptor.prime.label import M1Arrays, manage

SLIP = 0.0


def _arrays(path, start="2021-03-02 10:00"):
    """M1 bars from a close path: o = previous close, h/l = max/min(o,c) +-0.01."""
    c = np.asarray(path, float)
    o = np.r_[c[0], c[:-1]]
    h = np.maximum(o, c) + 0.01
    lo = np.minimum(o, c) - 0.01
    idx = pd.date_range(start, periods=len(c), freq="1min")
    n = len(c)
    return dict(o=o, h=h, l=lo, c=c, sp=np.zeros(n), dow=idx.dayofweek.values.astype(np.int64),
                mod=(idx.hour * 60 + idx.minute).values.astype(np.int64), swl=np.full(n, np.nan),
                swh=np.full(n, np.nan), brk5=np.zeros(n, np.int64), atr5=np.ones(n))


def _run(a, profile, entry=100.0, sl=99.0, side=1):
    p = {"FOTO": (0.7, 0.2, 2.0, 0.2, 4.0, False, False, False),
         "V5": (1.0, 0.9, 0.0, 0.0, 4.0, True, True, True)}[profile]
    return manage(a["o"], a["h"], a["l"], a["c"], a["sp"], a["dow"], a["mod"], a["swl"], a["swh"], a["brk5"],
                  a["atr5"], 0, side, entry, sl, entry - sl if side == 1 else sl - entry, *p, 4320, 23 * 60, SLIP)


def test_foto_partial_then_breakeven():
    # up to +0.8R (P1 at close >= 0.7R -> 20% booked, stop to BE), then back to entry
    a = _arrays([100, 100.4, 100.8, 100.5, 100.0, 99.9])
    ei, pnl, rs = _run(a, "FOTO")
    assert rs == 3
    assert abs(pnl - 0.2 * 0.8) < 1e-9  # 20% at 100.8, rest at BE (100.0)


def test_v5_partial_lock_and_stop_at_lock():
    # 90% at close >= 1R (101.0), MFE reaches 2.2R -> stop locked at +1R, then falls through it
    a = _arrays([100, 100.5, 101.0, 101.6, 102.2, 101.5, 100.9, 100.5])
    a["brk5"][:] = 0
    ei, pnl, rs = _run(a, "V5")
    assert rs == 9
    assert abs(pnl - (0.9 * 1.0 + 0.1 * 1.0)) < 1e-9


def test_v5_adaptive_exit_on_opposite_mss():
    a = _arrays([100, 100.5, 101.1, 101.3, 101.2, 101.0])
    a["brk5"][4] = -1  # bearish M5 break closes at minute 4 -> exit at that close
    ei, pnl, rs = _run(a, "V5")
    assert rs == 8 and ei == 4
    assert abs(pnl - (0.9 * 1.1 + 0.1 * 1.2)) < 1e-9


def test_stop_wins_same_bar_as_target():
    a = _arrays([100, 100.2, 100.3])
    a["h"][2] = 105.0  # target 4R touched...
    a["l"][2] = 98.5   # ...and stop in the same bar -> stop
    ei, pnl, rs = _run(a, "FOTO")
    assert rs == 1 and abs(pnl - (-1.0)) < 1e-9


def test_m5_swings_visible_only_after_confirmation():
    idx = pd.date_range("2021-03-02 10:00", periods=30, freq="1min")
    m1 = pd.DataFrame({"open": 100.0, "high": 100.1, "low": 99.9, "close": 100.0}, index=idx)
    f5 = pd.DataFrame({"swing_lo": [np.nan, 99.0, 98.0, 97.0, 96.0, 95.0], "swing_hi": np.nan, "atr": 1.0,
                       "brk": [0, 0, 1, 0, 0, 0]}, index=pd.date_range("2021-03-02 10:00", periods=6, freq="5min"))
    A = M1Arrays(m1, f5)
    # M5 bar 10:05 closes at 10:10 -> visible from the M1 bar 10:09 (decided at 10:10), not before
    assert np.isnan(A.swl[idx.get_loc(pd.Timestamp("2021-03-02 10:03"))])
    assert A.swl[idx.get_loc(pd.Timestamp("2021-03-02 10:09"))] == 99.0
    assert A.swl[idx.get_loc(pd.Timestamp("2021-03-02 10:08"))] != 99.0
    # break of the 10:10 bar exists only on the minute it closes (10:14 bar)
    assert A.brk5[idx.get_loc(pd.Timestamp("2021-03-02 10:14"))] == 1
    assert A.brk5.sum() == 1


def test_foto_parity_with_engine_label():
    rng = np.random.default_rng(0)
    n = 3000
    c = 1800 + np.cumsum(rng.normal(0, 0.3, n))
    a = _arrays(c)
    sp = np.full(n, 0.3)
    day = np.zeros(n, np.int64)
    out = _label(a["o"], a["h"], a["l"], a["c"], sp, day, a["dow"], a["mod"], 0.0, 0.0,
                 np.array([10, 500]), np.array([60, 560]), np.array([1, -1]), np.array([1, 1]),
                 np.array([0.0, 0.0]), np.array([c[9] - 3.0, c[499] + 3.0]), np.ones(2), np.zeros(2),
                 0, 0.0, 0.0, 0.0, 4.0, 0.7, 0.2, 2.0, 0.2, True, True, 0.0, 4320, 23 * 60, 0.05, 10.0, 0.035)
    r_engine = out[3]
    from raptor.prime.label import label_all
    prof = np.array([[0.7, 0.2, 2.0, 0.2, 4.0, 0.0, 0.0, 0.0]])
    res = label_all(a["o"], a["h"], a["l"], a["c"], sp, a["dow"], a["mod"], day, a["swl"], a["swh"], a["brk5"],
                    a["atr5"], np.array([10, 500]), np.array([60, 560]), np.array([1, -1]),
                    np.array([True, True]), np.array([0.0, 0.0]), np.array([c[9] - 3.0, c[499] + 3.0]),
                    np.zeros(2), prof, 4320, 23 * 60, 0.05, 0.035, 10.0, 0.0, 0.0)
    np.testing.assert_allclose(res[3][:, 0], r_engine, rtol=0, atol=1e-9)
