import numpy as np
import pandas as pd

from raptor.data import load_semicolon_csv, resample
from scripts.phase0_data import day_quality, remove_bad_ticks, weekly


def _m1(start, n, price=100.0):
    idx = pd.date_range(start, periods=n, freq="1min")
    p = price + np.arange(n) * 0.01
    return pd.DataFrame({"open": p, "high": p + 0.05, "low": p - 0.05, "close": p, "tickvol": 1, "vol": 0,
                         "spread": -1}, index=idx)


def test_semicolon_loader(tmp_path):
    f = tmp_path / "x.csv"
    f.write_text("Date;Open;High;Low;Close;Volume\n2004.06.11 07:18;384;384.1;384;384;3\n"
                 "2004.06.11 07:23;384.1;384.1;384;384;2\n")
    d = load_semicolon_csv(f)
    assert list(d.columns) == ["open", "high", "low", "close", "tickvol", "vol", "spread"]
    assert d.index[1] == pd.Timestamp("2004-06-11 07:23") and d.tickvol.iloc[0] == 3 and d.spread.iloc[0] == -1


def test_m3_m12_anchored_to_hour_and_no_synthetic_bars():
    m1 = pd.concat([_m1("2020-01-06 01:07", 30), _m1("2020-01-06 03:00", 30)])  # gap 01:37 -> 03:00
    for rule, k in (("3min", 3), ("12min", 12)):
        r = resample(m1, rule)
        assert (r.index.minute % k == 0).all()
        assert not ((r.index >= "2020-01-06 01:37") & (r.index < "2020-01-06 03:00")).any()


def test_weekly_starts_sunday():
    m1 = _m1("2020-01-06 01:00", 10)  # Monday
    w = weekly(m1)
    assert w.index[0] == pd.Timestamp("2020-01-05")


def test_bad_tick_removed_real_move_kept():
    m1 = _m1("2020-01-06 01:00", 40, 600.0)
    m1.loc[m1.index[20], ["open", "high", "low", "close"]] = 580.0  # isolated print
    m1.loc[m1.index[30:], ["open", "high", "low", "close"]] -= 20.0  # real level shift
    m1["high"] = m1[["open", "close"]].max(axis=1) + 0.05
    m1["low"] = m1[["open", "close"]].min(axis=1) - 0.05
    kept, bad = remove_bad_ticks(m1)
    assert list(bad.index) == [m1.index[20]] and len(kept) == 39


def test_degraded_day():
    full = _m1("2020-01-06 01:00", 1380)
    thin = _m1("2020-01-07 01:00", 22)
    dq = day_quality(pd.concat([full, thin]))
    assert not dq.loc["2020-01-06", "degraded"] and dq.loc["2020-01-07", "degraded"]
