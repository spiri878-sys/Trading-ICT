"""TG-02: ideal execution of the channel (its own entry price, zero costs), side-flipped and random-time baselines,
and channel claims vs. market outcome (TP1 before SL)."""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.tg01_signal_channel import OUT, mgmt_defs, run_variant, summarize  # noqa: E402
from raptor.data import load_m1  # noqa: E402
from raptor.signals.follow import sim_signal  # noqa: E402
from raptor.signals.telegram_parse import parse_export  # noqa: E402

path = sys.argv[1]
sig = parse_export(path).dropna(subset=["sl"])
sig = sig[sig.tps.str.len() > 0].copy()
m1 = load_m1().loc["2026-02-25":]
idx = m1.index.values
o, h, l, c = m1.open.values, m1.high.values, m1.low.values, m1.close.values
srv = sig.post_time + pd.Timedelta(minutes=60)
sig["i_post"] = np.searchsorted(idx, srv.values.astype("datetime64[ns]"), side="right")
al = (sig.alert_time.fillna(sig.post_time) + pd.Timedelta(minutes=60))
sig["i_alert"] = np.searchsorted(idx, al.values.astype("datetime64[ns]"), side="right")
sig = sig[sig.i_post < len(idx) - 2].reset_index(drop=True)
MG = "CHAN_1perTP+runner_BE1"


def one(s, i, side, entry, sl, tps, mg=MG, hold=1440, spread=0.0, slip=0.0):
    leg_tp, leg_w, be_k, step = mgmt_defs(len(tps))[mg]
    return sim_signal(o, h, l, c, i, hold, side, entry, sl, np.asarray(tps, float), leg_tp.astype(np.int64),
                      leg_w.astype(float), be_k, 0.0, step, spread, slip)


res = {}
# 1) ideal: the channel's own quoted entry (z1) filled at the alert bar, zero spread/commission
rows = []
for s in sig.itertuples():
    pu, kh, ei, mae, fsl = one(s, s.i_alert, s.side, s.z1, s.sl, s.tps)
    pu1, kh1, *_ = one(s, s.i_alert, s.side, s.z1, s.sl, s.tps, mg="ALL_TP1")
    rows.append((s.post_time, pu, kh, fsl, pu1, kh1, (s.z1 - s.sl) * s.side))
ideal = pd.DataFrame(rows, columns=["post_time", "pnl", "k", "fsl", "pnl_tp1", "k1", "risk"])
res["ideal_zero_cost"] = dict(
    n=len(ideal), tp1_reached_pct=round(100 * (ideal.k >= 1).mean(), 1), full_sl_pct=round(100 * ideal.fsl.mean(), 1),
    chan_style_usd_lot010=round(ideal.pnl.sum() * 10, 0), tp1_only_usd_lot010=round(ideal.pnl_tp1.sum() * 10, 0),
    chan_style_months={str(k): round(v * 10) for k, v in ideal.pnl.groupby(ideal.post_time.dt.to_period("M")).sum().items()})

# 2) flipped side, same geometry mirrored, ideal execution
rows = []
for s in sig.itertuples():
    side = -s.side
    sl = s.z1 + (s.z1 - s.sl)
    tps = [s.z1 - (tp - s.z1) for tp in s.tps]
    rows.append(one(s, s.i_alert, side, s.z1, sl, tps)[0])
res["flipped_side_ideal_usd_lot010"] = round(float(np.sum(rows) * 10), 0)

# 3) random entries: same geometry, random minute (weekday 01:00-22:00 server) in the same period, random side
rng = np.random.default_rng(7)
ok = np.where((m1.index.dayofweek < 5) & (m1.index.hour >= 1) & (m1.index.hour < 22))[0]
ok = ok[(ok > sig.i_post.min()) & (ok < len(idx) - 1500)]
tot = []
for rep in range(300):
    acc = 0.0
    for s in sig.itertuples():
        i = rng.choice(ok)
        side = rng.choice([-1, 1])
        e = o[i]
        d_sl = (s.z1 - s.sl) * s.side
        tps = [e + side * (tp - s.z1) * s.side for tp in s.tps]
        acc += one(s, i, side, e, e - side * d_sl, tps)[0]
    tot.append(acc * 10)
tot = np.array(tot)
res["random_ideal_usd_lot010"] = dict(mean=round(tot.mean()), p5=round(np.percentile(tot, 5)),
                                      p95=round(np.percentile(tot, 95)),
                                      share_above_channel=round(float((tot >= res["ideal_zero_cost"]["chan_style_usd_lot010"]).mean()), 3))

# 4) claims
d = json.load(open(path, encoding="utf-8"))
import re  # noqa: E402
txt = lambda m: m["text"] if isinstance(m["text"], str) else "".join(  # noqa: E731
    x if isinstance(x, str) else x.get("text", "") for x in m["text"])
msgs = [m for m in d["messages"] if m.get("type") == "message"]
pips = 0
for m in msgs:
    mm = re.match(r"^\s*TP\s*\d\s*✅+\s*\+\s*(\d+)", txt(m))
    if mm:
        pips += int(mm.group(1))
res["claims"] = dict(tp1_msgs=sum(1 for m in msgs if re.match(r"^\s*TP\s*1\s*✅", txt(m))),
                     stop_msgs=sum(1 for m in msgs if re.match(r"^\s*stop\s*🛑", txt(m), re.I)),
                     sum_of_announced_pips=pips, signals=len(sig))
json.dump(res, open(OUT / "tg02_baselines.json", "w"), indent=1)
print(json.dumps(res, indent=1))
