import json

import numpy as np

from raptor.signals.follow import sim_signal
from raptor.signals.telegram_parse import _repair, parse_export


def test_repair_single_digit_typo():
    assert _repair(4114.0, 4222.0, -1, 60)[0] == 4214.0
    assert _repair(4214.0, 4222.0, -1, 60) == (4214.0, False)


def test_parse_export(tmp_path):
    msgs = [{"id": 1, "type": "message", "date": "2026-03-10T08:13:49", "text": "Gold sell"},
            {"id": 2, "type": "message", "date": "2026-03-10T08:14:43",
             "text": "Gold sell 5174-5179\n\nSL 5185\n\nTP 5170\nTP 5166\nTP"}]
    p = tmp_path / "r.json"
    p.write_text(json.dumps({"messages": msgs}))
    s = parse_export(p)
    r = s.iloc[0]
    assert (r.side, r.z1, r.z2, r.sl, r.tps) == (-1, 5174.0, 5179.0, 5185.0, [5170.0, 5166.0])
    assert str(r.alert_time) == "2026-03-10 08:13:49"


def test_tp1_then_be_rest_closed_at_entry():
    # buy at 100, SL 88, TP1 103, TP2 106; bar1 hits TP1, bar2 comes back to 100 -> second leg at BE
    o = np.array([100.0, 101.0, 102.0, 101.0])
    h = np.array([100.5, 103.5, 102.5, 101.5])
    l = np.array([99.5, 100.5, 99.0, 98.0])
    c = o.copy()
    pnl, k, ei, mae, fsl = sim_signal(o, h, l, c, 0, 10, 1, 100.0, 88.0, np.array([103.0, 106.0]),
                                      np.array([0, 1], np.int64), np.array([0.5, 0.5]), 0, 0.0, False, 0.0, 0.0)
    assert k == 1 and ei == 2 and not fsl
    assert abs(pnl - 1.5) < 1e-9  # 0.5 * 3 + 0.5 * 0


def test_stop_checked_before_target_same_bar():
    o = np.array([100.0]); h = np.array([104.0]); l = np.array([87.0]); c = o.copy()
    pnl, k, *_ , fsl = sim_signal(o, h, l, c, 0, 5, 1, 100.0, 88.0, np.array([103.0]), np.array([0], np.int64),
                                  np.array([1.0]), 0, 0.0, False, 0.0, 0.0)
    assert k == 0 and fsl and abs(pnl + 12.0) < 1e-9
