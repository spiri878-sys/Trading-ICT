"""Unit tests of the execution simulator on synthetic M1 bars."""
from dataclasses import replace
import numpy as np
import pandas as pd
import pytest

from raptor.engine import Market, Params, run, label, STOP_FIXED, STOP_PERCENT, STOP_ATR, STOP_STRUCT, LOT_FIXED, LOT_RISK


def make_market(path, start="2024-01-02 10:00", spread_pts=0):
    """path: list of (open, high, low, close) M1 bid bars."""
    idx = pd.date_range(start, periods=len(path), freq="1min")
    df = pd.DataFrame(path, columns=["open", "high", "low", "close"], index=idx)
    df["spread"] = spread_pts
    return Market(df)


def sig(t, side=1, price=100.0, sl=99.0, otype="limit", expiry=10, atr=1.0):
    return pd.DataFrame({"bar_time": [pd.Timestamp(t)], "side": [side], "otype": [otype], "price": [price],
                         "sl_struct": [sl], "atr": [atr], "expiry_bars": [expiry], "strategy": ["T"]})


BASE = Params(spread_floor=0.0, slippage=0.0, commission_per_lot_side=0.0, p1_frac=0.0, p2_frac=0.0,
              be_after_p1=False, tp_r=2.0, fixed_lot=0.10, friday_close_min=24 * 60, max_spread=10)


def flat(n, px=101.0):
    return [(px, px + 0.1, px - 0.1, px)] * n


def test_limit_fill_then_tp_long():
    # signal bar 09:59 -> available 10:04 (tf=5); price dips to 100 then rallies to 102
    path = flat(4) + [(101, 101, 99.95, 100.2)] + [(100.2, 100.8, 100.1, 100.7)] + [(100.7, 102.5, 100.6, 102.4)]
    mk = make_market(path)
    tr, s = run(mk, sig("2024-01-02 09:59"), BASE)
    assert len(tr) == 1
    t = tr.iloc[0]
    assert t.entry == pytest.approx(100.0) and t.exit_reason == "TP"
    assert t.gross == pytest.approx(2.0 * 0.10 * 100)          # +2 USD/oz * 0.10 lot * 100 oz


def test_stop_wins_when_both_touched_same_bar():
    path = flat(4) + [(101, 101, 99.95, 100.2)] + [(100.2, 102.5, 98.5, 101)]
    tr, _ = run(make_market(path), sig("2024-01-02 09:59"), BASE)
    assert tr.iloc[0].exit_reason == "SL"
    assert tr.iloc[0].gross == pytest.approx(-1.0 * 10)


def test_stop_checked_on_fill_bar():
    path = flat(4) + [(101, 101, 98.9, 99.5)] + flat(3, 99.5)
    tr, _ = run(make_market(path), sig("2024-01-02 09:59"), BASE)
    assert tr.iloc[0].exit_reason == "SL"


def test_no_fill_before_signal_bar_closes():
    # price touches the limit during the signal bar itself (10:00-10:04 is bar 10:00 if tf=5) -> must not fill there
    path = [(100.0, 100.1, 99.9, 100.0)] + flat(10)
    tr, s = run(make_market(path), sig("2024-01-02 10:00", expiry=1), BASE)
    assert len(tr) == 0 and s.status.iloc[0] == "expired"


def test_short_uses_ask_for_exits():
    # short at bid 100, spread 0.5 -> stop at 101 triggers when bid high >= 100.5
    path = flat(4, 99) + [(99.5, 100.2, 99.4, 99.9)] + [(99.9, 100.55, 99.8, 100.4)]
    mk = make_market(path, spread_pts=50)
    tr, _ = run(mk, sig("2024-01-02 09:59", side=-1, price=100.0, sl=101.0), BASE)
    assert tr.iloc[0].exit_reason == "SL"
    assert tr.iloc[0].entry == pytest.approx(100.0)


@pytest.mark.parametrize("mode,kw,expected_sl", [
    (STOP_FIXED, dict(stop_fixed_usd=3.0), 97.0),
    (STOP_PERCENT, dict(stop_percent=1.0), 99.0),
    (STOP_ATR, dict(stop_atr_mult=2.0), 98.0),
    (STOP_STRUCT, dict(), 99.0),
])
def test_stop_selector(mode, kw, expected_sl):
    path = flat(4) + [(101, 101, 99.95, 100.2)] + flat(5, 100.2)
    tr, _ = run(make_market(path), sig("2024-01-02 09:59", atr=1.0), replace(BASE, stop_mode=mode, **kw))
    assert tr.iloc[0].sl0 == pytest.approx(expected_sl)


@pytest.mark.parametrize("stop_mode", [STOP_FIXED, STOP_PERCENT, STOP_ATR, STOP_STRUCT])
@pytest.mark.parametrize("lot_mode", [LOT_FIXED, LOT_RISK])
def test_all_stop_lot_combinations_run(stop_mode, lot_mode):
    path = flat(4) + [(101, 101, 99.95, 100.2)] + flat(5, 100.2) + [(100.2, 110, 100.1, 109)]
    prm = replace(BASE, stop_mode=stop_mode, lot_mode=lot_mode, risk_percent=1.0, initial_balance=10000)
    tr, s = run(make_market(path), sig("2024-01-02 09:59"), prm)
    assert len(tr) == 1
    if lot_mode == LOT_FIXED:
        assert tr.iloc[0].lot == pytest.approx(0.10)
    else:
        assert tr.iloc[0].risk_money <= 10000 * 0.01 + 1e-9


def test_risk_lot_rounds_down_and_never_exceeds_risk():
    path = flat(4) + [(101, 101, 99.95, 100.2)] + flat(5, 100.2)
    prm = replace(BASE, lot_mode=LOT_RISK, risk_percent=1.0, initial_balance=1000, commission_per_lot_side=3.5, slippage=0.05)
    tr, _ = run(make_market(path), sig("2024-01-02 09:59", sl=99.0), prm)
    # loss per lot = (1.00 + 0.05) * 100 + 7 = 112 -> 10 USD / 112 = 0.089 -> 0.08
    assert tr.iloc[0].lot == pytest.approx(0.08)
    assert tr.iloc[0].risk_money <= 10.0


def test_risk_lot_below_min_is_rejected_not_forced():
    path = flat(4) + [(101, 101, 99.95, 100.2)] + flat(5, 100.2)
    prm = replace(BASE, lot_mode=LOT_RISK, risk_percent=0.1, initial_balance=100)
    tr, s = run(make_market(path), sig("2024-01-02 09:59"), prm)
    assert len(tr) == 0 and s.status.iloc[0] == "rejected_risk_too_high_for_min_lot"


def test_fixed_lot_not_reduced_on_margin_shortfall():
    path = flat(4) + [(101, 101, 99.95, 100.2)] + flat(5, 100.2)
    prm = replace(BASE, lot_mode=LOT_FIXED, fixed_lot=5.0, initial_balance=100, leverage=100)
    tr, s = run(make_market(path), sig("2024-01-02 09:59"), prm)
    assert len(tr) == 0 and s.status.iloc[0] == "rejected_margin"


def test_invalid_fixed_lot_step_rejected():
    path = flat(4) + [(101, 101, 99.95, 100.2)] + flat(5, 100.2)
    tr, s = run(make_market(path), sig("2024-01-02 09:59"), replace(BASE, fixed_lot=0.085))
    assert s.status.iloc[0] == "rejected_fixed_lot_invalid"


def test_ladder_partials_and_breakeven():
    # entry 100, R=1. close crosses 100.7 (p1 20% + BE), then 102 (p2 20%), then price returns to entry -> BE
    path = (flat(4) + [(101, 101, 99.95, 100.2)] + [(100.2, 100.8, 100.2, 100.75)]
            + [(100.75, 102.1, 100.7, 102.05)] + [(102.05, 102.1, 99.9, 100.0)])
    prm = replace(BASE, tp_r=4.0, p1_r=0.7, p1_frac=0.2, p2_r=2.0, p2_frac=0.2, be_after_p1=True, mgmt_on_close=True)
    tr, _ = run(make_market(path), sig("2024-01-02 09:59"), prm)
    t = tr.iloc[0]
    assert t.partials == 2 and t.exit_reason == "BE"
    # 0.2*0.75 + 0.2*2.05 + 0.6*0 = 0.56 USD/oz
    assert t.gross == pytest.approx(0.56 * 0.10 * 100)


def test_one_position_at_a_time_and_duplicates_skipped():
    path = flat(4) + [(101, 101, 99.95, 100.2)] + flat(30, 100.2)
    s = pd.concat([sig("2024-01-02 09:59"), sig("2024-01-02 10:00")], ignore_index=True)
    tr, st = run(make_market(path), s, BASE)
    assert len(tr) == 1 and st.status.iloc[1] == "skipped_busy"


def test_label_matches_portfolio_single_trade():
    path = flat(4) + [(101, 101, 99.95, 100.2)] + [(100.2, 102.5, 100.1, 102.4)]
    mk = make_market(path)
    s = sig("2024-01-02 09:59")
    lab = label(mk, s, BASE)
    tr, _ = run(mk, s, BASE)
    assert lab.r.iloc[0] == pytest.approx(tr.r_mult.iloc[0], rel=1e-6)


def test_friday_cutoff_blocks_entries():
    idx_start = "2024-01-05 22:55"  # Friday
    path = flat(4) + [(101, 101, 99.95, 100.2)] + flat(10, 100.2)
    mk = make_market(path, start=idx_start)
    # available 22:59 -> fills before the cutoff, must be flattened at 23:00
    tr, s = run(mk, sig("2024-01-05 22:54"), replace(BASE, friday_close_min=23 * 60))
    assert len(tr) == 1 and tr.iloc[0].exit_reason == "FRIDAY"
    assert tr.iloc[0].exit_time == pd.Timestamp("2024-01-05 23:00")
    # available 23:01 -> after the cutoff: no entry
    tr, s = run(mk, sig("2024-01-05 22:56"), replace(BASE, friday_close_min=23 * 60))
    assert len(tr) == 0


def test_breathing_risk_reduces_after_drawdown_and_never_exceeds_base():
    # 12 consecutive losing trades of 1R each at 2% risk: DD passes 5% -> multiplier < 1, never > 1
    seg = [(101, 101, 99.95, 100.2), (100.2, 100.2, 98.5, 98.6)] + flat(3, 101.0)
    path = flat(4) + seg * 12
    mk = make_market(path)
    starts = [mk.index[4 + 5 * j] - pd.Timedelta(minutes=5) for j in range(12)]
    s = pd.concat([sig(t) for t in starts], ignore_index=True)
    prm = replace(BASE, lot_mode=LOT_RISK, risk_percent=2.0, initial_balance=100000, breathe=True,
                  breathe_dd_full=5.0, breathe_dd_min=23.75, breathe_mult_min=0.25, breathe_recover_wins=20)
    tr, _ = run(mk, s, prm)
    assert len(tr) == 12 and (tr.net < 0).all()
    assert (tr.risk_mult <= 1.0).all() and tr.risk_mult.iloc[0] == 1.0
    assert tr.risk_mult.iloc[-1] < 1.0 and tr.risk_mult.iloc[-1] >= 0.25
    assert (tr.risk_money.diff().dropna() <= 1e-9).all()   # risk never increases after losses (no martingale)
