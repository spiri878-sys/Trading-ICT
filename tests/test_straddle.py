"""OCO straddle simulator tests."""
import numpy as np
import pandas as pd
import pytest
from raptor.engine import Market
from raptor.straddle import run


def mk(path, start="2024-01-02 10:00"):
    idx = pd.date_range(start, periods=len(path), freq="1min")
    df = pd.DataFrame(path, columns=["open", "high", "low", "close"], index=idx)
    df["spread"] = 0
    return Market(df)


def setup(t, hi=101.0, lo=99.0, valid=1, atr=1.0):
    return pd.DataFrame({"bar_time": [pd.Timestamp(t)], "valid_bars": [valid], "p_hi": [hi], "p_lo": [lo],
                         "sl_hi": [lo], "sl_lo": [hi], "atr": [atr]})


KW = dict(spread=None, init_bal=10000.0, lot_mode=0, fixed_lot=0.10, tp_r=2.0, trail_atr=0.0, slip=0.0, comm=0.0,
          swap_long=0.0, swap_short=0.0, tf_minutes=60)


def go(path, s, **kw):
    m = mk(path)
    a = dict(KW, **kw); a["spread"] = np.zeros(len(m.o))
    return run(m, s, **a)


def test_buy_stop_fills_and_cancels_sell():
    flat = [(100, 100.2, 99.8, 100)] * 60
    path = flat + [(100, 101.5, 99.9, 101.4)] + [(101.4, 105.5, 101.3, 105)] + [(100, 100, 98, 98)] * 5
    tr, _ = go(path, setup("2024-01-02 10:00"))
    assert len(tr) == 1 and tr.iloc[0].side == 1 and tr.iloc[0].entry == pytest.approx(101.0)
    assert tr.iloc[0].exit_reason == "TP" and tr.iloc[0].net == pytest.approx(4.0 * 10)   # 2R = 4 USD x 0.1 x 100


def test_same_bar_tie_books_worse_outcome():
    flat = [(100, 100.2, 99.8, 100)] * 60
    path = flat + [(100, 101.5, 98.5, 100)] + [(100, 100.1, 98.0, 98.1)] * 3
    tr, _ = go(path, setup("2024-01-02 10:00"))
    assert len(tr) == 1 and bool(tr.iloc[0].same_bar_tie)
    assert tr.iloc[0].net < 0          # the long would be stopped (worse than the short)


def test_one_trade_at_a_time_and_replacement_after_close():
    flat = [(100, 100.2, 99.8, 100)] * 60
    # first setup fills long at 101 and hits SL at 99; a second setup (valid later) is re-placed after the close
    path = flat + [(100, 101.2, 99.9, 101.1), (101.1, 101.1, 98.9, 99.0)] + [(99.5, 99.6, 99.4, 99.5)] * 58 + \
           [(99.5, 101.3, 99.4, 101.2)] + [(101.2, 106, 101.1, 105.5)]
    s = pd.concat([setup("2024-01-02 10:00"), setup("2024-01-02 11:00", valid=2)], ignore_index=True)
    tr, _ = go(path, s)
    assert len(tr) == 2 and tr.iloc[0].exit_reason == "SL" and tr.iloc[1].exit_reason == "TP"
    assert tr.iloc[1].entry_time > tr.iloc[0].exit_time


def test_fixed_lot_margin_rejection():
    flat = [(100, 100.2, 99.8, 100)] * 60
    path = flat + [(100, 101.5, 99.9, 101.4)] + [(101.4, 105.5, 101.3, 105)]
    tr, info = go(path, setup("2024-01-02 10:00"), init_bal=50.0, fixed_lot=1.0, leverage=100.0)
    assert len(tr) == 0 and info["skipped_margin"] >= 1
