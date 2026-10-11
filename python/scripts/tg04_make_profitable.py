"""TG-04: can the channel be made profitable with filters (which signals to take) and different exits?

Per-signal outcomes are computed once per exit configuration (entry x management x max hold x stop multiplier,
standard costs); filters are causal masks (known at signal time). Everything is chosen on TRAIN (Mar-Jun 2026)
and judged on TEST (Jul-Sep 2026). A random-mask baseline of the same size tells how much a 'good' filter is luck.
usage: python scripts/tg04_make_profitable.py <result.json>
"""
import itertools
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from raptor.data import load_m1  # noqa: E402
from raptor.signals.follow import limit_fill, sim_signal  # noqa: E402
from raptor.signals.telegram_parse import parse_export  # noqa: E402
from scripts.tg01_signal_channel import COMM_PER_OZ, OUT, mgmt_defs  # noqa: E402

SPREAD, SLIP, OFF = 0.30, 0.05, 60
SPLIT = pd.Timestamp("2026-07-01")

sig = parse_export(sys.argv[1]).dropna(subset=["sl"])
sig = sig[sig.tps.str.len() > 0].sort_values("post_time").reset_index(drop=True)
m1 = load_m1().loc["2026-01-01":]
idx = m1.index.values
o, h, l, c = (m1[k].values for k in ("open", "high", "low", "close"))
sig["i_post"] = np.searchsorted(idx, (sig.post_time + pd.Timedelta(minutes=OFF)).values.astype("datetime64[ns]"),
                                side="right")
sig = sig[sig.i_post < len(idx) - 2].reset_index(drop=True)
ip = sig.i_post.values
side = sig.side.values

# ---------------- causal features (bars strictly before the entry bar) ----------------
cl = pd.Series(c, index=m1.index)
h1 = cl.resample("1h").last().dropna()
h4 = cl.resample("4h").last().dropna()
d1 = cl.resample("1D").last().dropna()


def last_closed(series, t, minutes):
    """value of the last bar of `series` (labelled by open time, length `minutes`) closed before t."""
    pos = np.searchsorted(series.index.values, (t - pd.Timedelta(minutes=minutes)).values, side="right") - 1
    return series.values[np.clip(pos, 0, None)]


t_entry = pd.Series(m1.index[ip])
f = pd.DataFrame(index=sig.index)
for name, ser, mins, span in [("h1", h1, 60, 50), ("h4", h4, 240, 50), ("d1", d1, 1440, 20)]:
    ema = ser.ewm(span=span, adjust=False).mean()
    f[f"trend_{name}"] = np.sign(last_closed(ser, t_entry, mins) - last_closed(ema, t_entry, mins)) * side
for n in (15, 60):
    f[f"mv{n}"] = (c[ip - 1] - c[ip - 1 - n]) * side
tr = pd.Series(h - l, index=m1.index).rolling(60).mean().values
f["atr60"] = tr[ip - 1]
f["hour"] = m1.index[ip].hour
gap = sig.post_time.diff().dt.total_seconds().fillna(1e9) / 60
f["first_in_60m"] = gap > 60
f["risk"] = (sig.z1 - sig.sl) * sig.side
train = (sig.post_time < SPLIT).values
atr_med = np.median(f.atr60[train])

FILTERS = {
    "all": np.ones(len(sig), bool),
    "short": side == -1, "long": side == 1,
    "with_H1": f.trend_h1 > 0, "with_H4": f.trend_h4 > 0, "with_D1": f.trend_d1 > 0,
    "against_H1": f.trend_h1 < 0, "against_H4": f.trend_h4 < 0,
    "fade15": f.mv15 < 0, "mom15": f.mv15 > 0, "fade60": f.mv60 < 0, "mom60": f.mv60 > 0,
    "lowvol": f.atr60 < atr_med, "highvol": f.atr60 >= atr_med,
    "morning": (f.hour >= 9) & (f.hour < 13), "afternoon": (f.hour >= 13) & (f.hour < 19),
    "first_in_60m": f.first_in_60m,
}
FILTERS = {k: np.asarray(v, bool) for k, v in FILTERS.items()}
combos = {"all": FILTERS["all"]}
names = [k for k in FILTERS if k != "all"]
for a in names:
    combos[a] = FILTERS[a]
for a, b in itertools.combinations(names, 2):
    combos[f"{a}+{b}"] = FILTERS[a] & FILTERS[b]

# ---------------- per-signal outcomes for each exit configuration ----------------
EXITS = []
for entry, mg, hold, slm in itertools.product(["MKT_POST1", "LIM_Z2"],
                                              ["ALL_TP1", "ALL_TP2", "ALL_TP3", "ALL_TP2_BE1", "ALL_TP3_BE1",
                                               "CHAN_1perTP_BE1", "CHAN_1perTP+runner_BE1",
                                               "HALF_TP1_HALF_lastTP_BE1", "THIRDS_TP1_TP2_TP3_BE1"],
                                              [30, 120, 1440], [0.5, 0.75, 1.0]):
    EXITS.append((entry, mg, hold, slm))

res = np.full((len(EXITS), len(sig)), np.nan)
for e, (entry, mg, hold, slm) in enumerate(EXITS):
    for j, s in enumerate(sig.itertuples()):
        K = len(s.tps)
        plans = mgmt_defs(K)
        if mg not in plans:
            continue
        leg_tp, leg_w, be_k, step = plans[mg]
        if entry == "MKT_POST1":
            i = s.i_post + 1
            px = o[i] + (SPREAD + SLIP if s.side == 1 else -SLIP)
        else:
            i, px = limit_fill(o, h, l, s.i_post, s.i_post + 60, s.side, s.z2, SPREAD)
            if i < 0:
                continue
        sl = px - s.side * (s.z1 - s.sl) * s.side * slm
        tps = np.array(s.tps, float)
        pu = sim_signal(o, h, l, c, i, hold, s.side, px, sl, tps, leg_tp.astype(np.int64), leg_w.astype(float),
                        be_k, 0.0, step, SPREAD, SLIP)[0]
        res[e, j] = pu - COMM_PER_OZ

USD = 10.0  # 0.10 lot
rows = []
for e, ex in enumerate(EXITS):
    r = res[e]
    for fn, mask in combos.items():
        mtr = mask & train & ~np.isnan(r)
        mte = mask & ~train & ~np.isnan(r)
        if mtr.sum() < 40 or mte.sum() < 15:
            continue
        a, b = r[mtr], r[mte]
        mo_tr = pd.Series(a, index=sig.post_time[mtr]).groupby(lambda t: t.month).sum()
        rows.append(dict(entry=ex[0], mgmt=ex[1], hold=ex[2], sl_mult=ex[3], filt=fn,
                         n_tr=int(mtr.sum()), usd_tr=a.sum() * USD, pf_tr=a[a > 0].sum() / max(-a[a < 0].sum(), 1e-9),
                         mpos_tr=int((mo_tr > 0).sum()),
                         n_te=int(mte.sum()), usd_te=b.sum() * USD, pf_te=b[b > 0].sum() / max(-b[b < 0].sum(), 1e-9)))
g = pd.DataFrame(rows)
g.to_csv(OUT / "tg04_search.csv.gz", index=False, compression="gzip")

# selection on TRAIN only: robust = all 4 train months positive, PF>1.2, >=40 trades; rank by train $
sel = g[(g.mpos_tr == 4) & (g.pf_tr > 1.2)].sort_values("usd_tr", ascending=False)
top = sel.head(50)

# random-mask baseline for the #1 pick: same exit, random subsets of the same size (train and test)
best = sel.iloc[0] if len(sel) else g.sort_values("usd_tr", ascending=False).iloc[0]
e_best = EXITS.index((best.entry, best.mgmt, int(best.hold), float(best.sl_mult)))
r = res[e_best]
rng = np.random.default_rng(3)
valid_tr = np.where(train & ~np.isnan(r))[0]
valid_te = np.where(~train & ~np.isnan(r))[0]
rand_tr = [r[rng.choice(valid_tr, int(best.n_tr), replace=False)].sum() * USD for _ in range(2000)]
rand_te = [r[rng.choice(valid_te, int(best.n_te), replace=False)].sum() * USD for _ in range(2000)]

out = dict(
    n_strategies=len(g), n_exits=len(EXITS), n_filters=len(combos),
    share_profitable_train=round(float((g.usd_tr > 0).mean()), 3),
    share_profitable_test=round(float((g.usd_te > 0).mean()), 3),
    n_selected_robust_train=len(sel),
    selected_top50_test=dict(share_profitable=round(float((top.usd_te > 0).mean()), 3),
                             median_usd=round(float(top.usd_te.median())), mean_usd=round(float(top.usd_te.mean()))),
    selected_all_test=dict(share_profitable=round(float((sel.usd_te > 0).mean()), 3),
                           median_usd=round(float(sel.usd_te.median())) if len(sel) else None),
    corr_train_test_usd=round(float(g[["usd_tr", "usd_te"]].corr().iloc[0, 1]), 3),
    best_pick=best.to_dict(),
    best_pick_random_pctile_train=round(float((np.array(rand_tr) < best.usd_tr).mean()), 3),
    best_pick_random_pctile_test=round(float((np.array(rand_te) < best.usd_te).mean()), 3),
)
# what a single simple idea does (no search): shorts only with the channel's own management
for k in ["short", "with_H4", "with_D1", "short+with_H4", "lowvol", "first_in_60m"]:
    ex = EXITS.index(("MKT_POST1", "CHAN_1perTP+runner_BE1", 1440, 1.0))
    rr = res[ex]
    m = combos[k] & ~np.isnan(rr)
    out[f"simple_{k}"] = dict(train_usd=round(float(np.nansum(rr[m & train]) * USD)),
                              test_usd=round(float(np.nansum(rr[m & ~train]) * USD)), n=int(m.sum()))
json.dump(out, open(OUT / "tg04_make_profitable.json", "w"), indent=1, default=str)
print(json.dumps(out, indent=1, default=str))
pd.set_option("display.width", 250)
print(top.head(20).round(2).to_string())
