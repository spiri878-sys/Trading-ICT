"""WF-01: nested walk-forward CONFIGURATION SELECTOR over ICT configurations (Wyckoff excluded).

The selection rule is fixed BEFORE looking at any result:
  for each year Y in 2020..2026: in-sample = signals with exit_time < Jan 1 of Y (from 2018);
  eligible configs: n_in >= 80 and mean_R_in > 0; pick the TOP_K=5 by in-sample t-stat;
  trade them in year Y (each config = one sleeve, isolated per-signal R, cost model C1).
The aggregated out-of-sample R over 2020-2026 is the honest estimate of what a systematic ICT search
can deliver. Grid: 7 cells x {M5,M15} x stop {struct, min2ATR15, H1 swing, H4 swing} x exits
{vendor ladder, tp3R_48h, tp2R_24h} x bias {none, H1 trend, H4 trend} x side {both, long only}."""
import sys, json, itertools
from dataclasses import replace
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np, pandas as pd
from raptor import pipeline as P, metrics as M
from raptor.costs import C1, with_cost

ROOT = Path(__file__).resolve().parents[2]
CELLS = ["PPK", "MSS", "OTEOF", "PO3", "UNIOF", "LS", "SILVER_BULLET"]
EXITS = {"ladder": dict(tp_r=4.0, p1_r=0.7, p1_frac=0.2, p2_r=2.0, p2_frac=0.2, be_after_p1=True, mgmt_on_close=True, max_hold_min=4320),
         "tp3R_48h": dict(tp_r=3.0, p1_frac=0.0, p2_frac=0.0, be_after_p1=False, max_hold_min=2880),
         "tp2R_24h": dict(tp_r=2.0, p1_frac=0.0, p2_frac=0.0, be_after_p1=False, max_hold_min=1440)}
STOPS = {"struct": dict(), "min2": dict(min_stop_m15=2.0), "h1": dict(htf_stop="h1"), "h4": dict(htf_stop="h4")}
TOP_K, MIN_N = 5, 80

frames = []
for (tf, k), (sn, skw), (en, ex) in itertools.product([("5min", 3), ("15min", 3)], STOPS.items(), EXITS.items()):
    tfm = int(pd.Timedelta(tf).total_seconds() // 60)
    strat = {c: {"expiry": max(3, 60 // tfm), "max_r_atr": 40.0} for c in CELLS}
    with with_cost(C1, replace(P.Params(), **ex)) as prm:
        lab, _ = P.labelled(strat, prm, tf=tf, swing_k=k, **skw)
    f = P.feats(tf, k)
    lab = lab[lab.filled].copy()
    i = lab.bar_i.values
    lab["h1_al"] = np.sign(f.h1_trend.values[i]) == lab.side
    lab["h4_al"] = np.sign(f.h4_trend.values[i]) == lab.side
    lab["pool"] = f"{tf}|{sn}|{en}"
    frames.append(lab[["bar_time", "exit_time", "side", "strategy", "r", "h1_al", "h4_al", "pool"]])
    print("labelled", tf, sn, en, len(lab), flush=True)
L = pd.concat(frames, ignore_index=True)
L.to_parquet(ROOT / "data" / "processed" / "wf01_labels.parquet")

# expand configurations as boolean filters
configs = []
for pool in L.pool.unique():
    for cell in CELLS:
        for bias in ["none", "h1", "h4"]:
            for side in ["both", "long"]:
                configs.append((pool, cell, bias, side))
def mask(df, cfg):
    pool, cell, bias, side = cfg
    m = (df.pool == pool) & (df.strategy == cell)
    if bias != "none": m &= df[f"{bias}_al"]
    if side == "long": m &= df.side == 1
    return m
masks = {c: mask(L, c).values for c in configs}
yr_exit = L.exit_time.dt.year.values; yr_bar = L.bar_time.dt.year.values
rows, oos = [], []
for Y in range(2020, 2027):
    ins = L.exit_time.values < np.datetime64(f"{Y}-01-01")
    stats = []
    for c in configs:
        r = L.r.values[masks[c] & ins]
        if len(r) >= MIN_N and r.mean() > 0:
            stats.append((r.mean() / (r.std(ddof=1) / np.sqrt(len(r))), c, r.mean(), len(r)))
    stats.sort(reverse=True, key=lambda x: x[0])
    chosen = stats[:TOP_K]
    for t, c, mu, n in chosen:
        r_oos = L.r.values[masks[c] & (yr_bar == Y)]
        rows.append({"year": Y, "config": "|".join(c), "t_in": round(t, 2), "meanR_in": round(mu, 3), "n_in": n,
                     "n_oos": len(r_oos), "meanR_oos": round(float(r_oos.mean()), 3) if len(r_oos) else None,
                     "sumR_oos": round(float(r_oos.sum()), 1)})
        oos.extend(r_oos.tolist())
    print(Y, "eligible configs:", len(stats), flush=True)
sel = pd.DataFrame(rows)
sel.to_csv(ROOT / "experiments" / "wf01_selector.csv", index=False)
pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 60)
print(sel.to_string())
o = pd.Series(oos)
print(json.dumps({"OOS_2020_2026": M.r_stats(o), "configs_in_grid": len(configs),
                  "yearly_sumR": sel.groupby("year").sumR_oos.sum().round(1).to_dict()}, indent=1))
