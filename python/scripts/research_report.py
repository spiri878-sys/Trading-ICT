"""Consolidated metrics (spec 13.2): every cell alone, the official-six combination, the faithful-5
combination and the Wyckoff benchmark; dev / val / test; costs ZERO, C1, C0R, C2; long/short; yearly;
duration. Isolated per-signal outcomes in R (sizing independent). No parameter is chosen here."""
import sys, json
from dataclasses import replace
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np, pandas as pd
from raptor import pipeline as P, metrics as M
from raptor.costs import C1, C0R, C2, ZERO, with_cost

ROOT = Path(__file__).resolve().parents[2]
LADDER = dict(tp_r=4.0, p1_r=0.7, p1_frac=0.2, p2_r=2.0, p2_frac=0.2, be_after_p1=True, mgmt_on_close=True, max_hold_min=4320)
CELLS = ["PPK", "MSS", "OTEOF", "PO3", "UNIOF", "LS", "SILVER_BULLET", "WYCKOFF"]
rows = []
for cname, cm in [("ZERO", ZERO), ("C1", C1), ("C0R", C0R), ("C2", C2)]:
    with with_cost(cm, replace(P.Params(), **LADDER)) as prm:
        lab, _ = P.labelled({c: {} for c in CELLS}, prm, tf="5min", swing_k=3)
    lab = lab[lab.filled].copy()
    lab["hold_h"] = (lab.exit_time - lab.fill_time).dt.total_seconds() / 3600
    groups = {c: lab[lab.strategy == c] for c in CELLS}
    groups["COMBO_SITE_SIX"] = lab[lab.strategy.isin(["UNIOF", "OTEOF", "SILVER_BULLET", "PO3", "MSS", "LS"])].drop_duplicates(["bar_time", "side"])
    groups["COMBO_FAITHFUL_5"] = lab[lab.strategy.isin(["PPK", "OTEOF", "PO3", "UNIOF", "LS"])].drop_duplicates(["bar_time", "side"])
    for gname, g in groups.items():
        for per in ["dev", "val", "test"]:
            d = P.in_period(g, per)
            r = {"cost": cname, "group": gname, "period": per, **M.r_stats(d.r),
                 "long_R": round(float(d[d.side == 1].r.mean()), 3) if (d.side == 1).any() else None,
                 "short_R": round(float(d[d.side == -1].r.mean()), 3) if (d.side == -1).any() else None,
                 "median_hold_h": round(float(d.hold_h.median()), 2) if len(d) else None,
                 "R_p05": round(float(d.r.quantile(0.05)), 2) if len(d) else None,
                 "R_p95": round(float(d.r.quantile(0.95)), 2) if len(d) else None}
            r["yearly_meanR"] = json.dumps({int(y): round(float(x.r.mean()), 3) for y, x in d.groupby(d.bar_time.dt.year)})
            rows.append(r)
df = pd.DataFrame(rows)
df.to_csv(ROOT / "reports" / "research_metrics.csv", index=False)
pd.set_option("display.width", 250)
print(df[df.cost == "C1"].pivot_table(index="group", columns="period", values=["n", "mean_R", "pf"]).round(3).to_string())
print(df.pivot_table(index="group", columns=["cost", "period"], values="mean_R").round(3).to_string())
