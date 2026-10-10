"""EXP-04 (dev only): cells executed on H1/H4 structure (H2), with/without D1 trend alignment (H3)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np, pandas as pd
from raptor import pipeline as P, metrics as M
from raptor.costs import C1, ZERO, with_cost

CELLS = ["PPK", "OTEOF", "PO3", "UNIOF", "LS", "SILVER_BULLET", "WYCKOFF"]
rows = []
for tf, k in [("15min", 6), ("30min", 3), ("1h", 2), ("1h", 3), ("4h", 2)]:
    tfm = int(pd.Timedelta(tf).total_seconds() // 60)
    strat = {c: {"expiry": max(2, 240 // tfm), "max_r_atr": 30.0, "min_r_atr": 0.3} for c in CELLS}
    for cname, cm in [("zero", ZERO), ("C1", C1)]:
        with with_cost(cm) as prm:
            lab, X = P.labelled(strat, prm, tf=tf, swing_k=k)
        d = P.in_period(lab.join(X.drop(columns="side")), "dev")
        d = d[d.filled]
        for filt in ["none", "d1_aligned", "d1_against"]:
            x = d if filt == "none" else d[(np.sign(d.dist_ema_d1) > 0) == (filt == "d1_aligned")]
            for s, g in x.groupby("strategy"):
                rows.append({"tf": tf, "k": k, "cost": cname, "filter": filt, "cell": s, **M.r_stats(g.r)})
            rows.append({"tf": tf, "k": k, "cost": cname, "filter": filt, "cell": "ALL", **M.r_stats(x.r)})
df = pd.DataFrame(rows)
df.to_csv(Path(__file__).resolve().parents[2] / "experiments" / "exp04_htf_cells.csv", index=False)
pd.set_option("display.width", 250)
for c in ["zero", "C1"]:
    print("==", c)
    print(df[df.cost == c].pivot_table(index="cell", columns=["tf", "k", "filter"], values="mean_R").round(2).to_string())
print(df[df.cost == "C1"].pivot_table(index="cell", columns=["tf", "k", "filter"], values="n").to_string())
