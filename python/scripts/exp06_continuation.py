"""EXP-06 (dev only): H8 - continuation cells on 15m/1h structure, entry and exit variants."""
import sys
from dataclasses import replace
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np, pandas as pd
from raptor import pipeline as P, metrics as M
from raptor.costs import C1, ZERO, with_cost

EXITS = {
    "ladder_0.7/2/4R": dict(tp_r=4.0, p1_r=0.7, p1_frac=0.2, p2_r=2.0, p2_frac=0.2, be_after_p1=True, mgmt_on_close=True, max_hold_min=3 * 1440),
    "tp2R_hold24h": dict(tp_r=2.0, p1_frac=0.0, p2_frac=0.0, be_after_p1=False, max_hold_min=1440),
    "tp3R_hold48h": dict(tp_r=3.0, p1_frac=0.0, p2_frac=0.0, be_after_p1=False, max_hold_min=2880),
    "time24h_only": dict(tp_r=50.0, p1_frac=0.0, p2_frac=0.0, be_after_p1=False, max_hold_min=1440),
    "p1@1R_be_tp3R": dict(tp_r=3.0, p1_r=1.0, p1_frac=0.5, p2_frac=0.0, be_after_p1=True, mgmt_on_close=True, max_hold_min=2880),
}
rows = []
for tf, k in [("15min", 3), ("15min", 6), ("1h", 2), ("1h", 3)]:
    tfm = int(pd.Timedelta(tf).total_seconds() // 60)
    for entry in ["retrace", "market"]:
        strat = {c: {"expiry": max(2, 240 // tfm), "max_r_atr": 30.0, "min_r_atr": 0.3, "market_entry": entry == "market"}
                 for c in ["PPK", "UNIOF", "OTEOF"]}
        if entry == "market":
            strat.pop("OTEOF")  # OTE is by definition a retracement entry
        for ename, ex in EXITS.items():
            for cname, cm in [("zero", ZERO), ("C1", C1)]:
                with with_cost(cm) as prm:
                    lab, X = P.labelled(strat, replace(prm, **ex), tf=tf, swing_k=k)
                d = P.in_period(lab, "dev"); d = d[d.filled]
                for s, g in d.groupby("strategy"):
                    rows.append({"tf": tf, "k": k, "entry": entry, "exit": ename, "cost": cname, "cell": s, **M.r_stats(g.r)})
df = pd.DataFrame(rows)
df.to_csv(Path(__file__).resolve().parents[2] / "experiments" / "exp06_continuation.csv", index=False)
pd.set_option("display.width", 250)
c1 = df[df.cost == "C1"]
print(c1.pivot_table(index=["cell", "entry", "exit"], columns=["tf", "k"], values="mean_R").round(3).to_string())
print(c1.pivot_table(index=["cell", "entry", "exit"], columns=["tf", "k"], values="t_stat").round(1).to_string())
print(c1.pivot_table(index=["cell", "entry"], columns=["tf", "k"], values="n", aggfunc="max").to_string())
print("configurations tested:", len(c1))
