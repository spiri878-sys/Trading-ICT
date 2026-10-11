"""FAM-01: comparative study of strategy families on XAUUSD, long and short evaluated SEPARATELY.
Costs: C1 (spread 0.30, commission 3.5/lot/side, slippage 0.05) + overnight swap (long -6.6%/yr, short +2.9%/yr).
Isolated per-signal R. Outputs:
  experiments/fam01_labels.parquet  - every labelled signal (for walk-forward / Monte Carlo)
  experiments/fam01_stats.csv       - per config x side x period statistics"""
import sys, json, itertools
from dataclasses import replace
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np, pandas as pd
from raptor import pipeline as P, metrics as M
from raptor.engine import label
from raptor.strategies import REGISTRY
from raptor.costs import C1, with_cost

ROOT = Path(__file__).resolve().parents[2]
EXITS = {
    "tp1.5R_8h": dict(tp_r=1.5, p1_frac=0.0, p2_frac=0.0, be_after_p1=False, max_hold_min=480),
    "tp2R_24h": dict(tp_r=2.0, p1_frac=0.0, p2_frac=0.0, be_after_p1=False, max_hold_min=1440),
    "tp3R_48h": dict(tp_r=3.0, p1_frac=0.0, p2_frac=0.0, be_after_p1=False, max_hold_min=2880),
    "trail_5d": dict(tp_r=50.0, p1_frac=0.0, p2_frac=0.0, be_after_p1=False, trail_atr=2.5, max_hold_min=5 * 1440),
    "native": None,   # per-signal tp_r (MR_BB middle band); else skipped
}
GRID = {
    ("ASIA_BO", "15min", 3): [dict(window=w, stop=s) for w in [(9, 13), (15, 19), (9, 19)] for s in ["range", "atr"]],
    ("EMA_PB", "15min", 3): [dict(touch=t, fast=fa) for t in (4, 8) for fa in (20, 50)],
    ("EMA_PB", "1h", 3): [dict(touch=t, fast=fa) for t in (4, 8) for fa in (20, 50)],
    ("SQUEEZE", "15min", 3): [dict(pct=q, atr_k=k) for q in (0.1, 0.2) for k in (1.5, 2.5)],
    ("SQUEEZE", "1h", 3): [dict(pct=q, atr_k=k) for q in (0.1, 0.2) for k in (1.5, 2.5)],
    ("SQUEEZE", "4h", 2): [dict(pct=q, atr_k=k) for q in (0.1, 0.2) for k in (1.5, 2.5)],
    ("DONCHIAN", "1h", 3): [dict(n=n, atr_k=k) for n in (20, 55, 100) for k in (2.0, 3.0)],
    ("DONCHIAN", "4h", 2): [dict(n=n, atr_k=k) for n in (20, 55, 100) for k in (2.0, 3.0)],
    ("MR_BB", "15min", 3): [dict(k=k, rsi_lo=r, max_er=e) for k in (2.0, 2.5) for r in (30,) for e in (0.3, 0.45)],
    ("MR_BB", "1h", 3): [dict(k=k, rsi_lo=r, max_er=e) for k in (2.0, 2.5) for r in (30,) for e in (0.3, 0.45)],
    ("RSI2", "1h", 3): [dict(lo=lo, atr_k=k) for lo in (5, 10) for k in (1.5, 2.5)],
    ("RSI2", "4h", 2): [dict(lo=lo, atr_k=k) for lo in (5, 10) for k in (1.5, 2.5)],
    ("UNIOF", "15min", 3): [dict(expiry=4, max_r_atr=40.0, _htf="h4")],
    ("LS", "15min", 3): [dict(expiry=4)],
}
frames = []
for (fam, tf, k), plist in GRID.items():
    f = P.feats(tf, k)
    tfm = int(pd.Timedelta(tf).total_seconds() // 60)
    for prm_s in plist:
        q = {kk: v for kk, v in prm_s.items() if not kk.startswith("_")}
        s = REGISTRY[fam](f, q)
        if prm_s.get("_htf"):
            s = P.apply_htf_stop(s, f, prm_s["_htf"])
        if len(s) < 20:
            continue
        s = s.sort_values("bar_time").reset_index(drop=True)
        for en, ex in EXITS.items():
            if en == "native":
                if "tp_r" not in s.columns:
                    continue
                ex = dict(p1_frac=0.0, p2_frac=0.0, be_after_p1=False, max_hold_min=1440)
                ss = s
            else:
                ss = s.drop(columns="tp_r", errors="ignore")
            with with_cost(C1, replace(P.Params(), **ex)) as prm:
                lab = label(P.market(), ss, prm, tfm)
            lab = lab[lab.filled]
            lab["cfg"] = f"{fam}|{tf}|" + ",".join(f"{a}={b}" for a, b in prm_s.items()) + f"|{en}"
            lab["family"] = fam
            lab["hold_h"] = (lab.exit_time - lab.fill_time).dt.total_seconds() / 3600
            frames.append(lab[["bar_time", "exit_time", "side", "r", "cfg", "family", "hold_h"]])
    print("done", fam, tf, flush=True)
L = pd.concat(frames, ignore_index=True)
L.to_parquet(ROOT / "experiments" / "fam01_labels.parquet")
rows = []
for (cfg, side), g in L.groupby(["cfg", "side"]):
    r = {"cfg": cfg, "family": g.family.iloc[0], "side": "long" if side == 1 else "short"}
    for per, (a, b) in {"all": ("2018", "2027"), **P.PERIODS}.items():
        x = g[(g.bar_time >= a) & (g.bar_time < b)].r
        st = M.r_stats(x)
        r[f"{per}_n"] = st.get("n"); r[f"{per}_R"] = st.get("mean_R"); r[f"{per}_t"] = st.get("t_stat")
    r["median_hold_h"] = round(float(g.hold_h.median()), 1)
    r["years_positive"] = int((g.groupby(g.bar_time.dt.year).r.mean() > 0).sum())
    rows.append(r)
S = pd.DataFrame(rows)
S.to_csv(ROOT / "experiments" / "fam01_stats.csv", index=False)
pd.set_option("display.width", 250)
summ = S.groupby(["family", "side"]).agg(configs=("cfg", "count"), share_pos=("all_R", lambda x: round((x > 0).mean(), 2)),
                                         median_R=("all_R", "median"), best_R=("all_R", "max"),
                                         dev_med=("dev_R", "median"), val_med=("val_R", "median"), test_med=("test_R", "median"))
print(summ.round(3).to_string())
