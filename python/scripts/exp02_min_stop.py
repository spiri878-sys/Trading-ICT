"""EXP-02 (dev only): minimum stop distance in ATR(M15) with cost model C1."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pandas as pd
from raptor import pipeline as P, metrics as M
from raptor.costs import C1, with_cost

CELLS = ["PPK", "OTEOF", "PO3", "UNIOF", "LS", "SILVER_BULLET", "WYCKOFF"]
rows = []
for tf, k in [("5min", 8), ("15min", 3)]:
    tfm = int(pd.Timedelta(tf).total_seconds() // 60)
    exp = {c: {"expiry": max(2, 60 // tfm)} for c in CELLS}
    for ms in [0, 1.5, 2.0, 3.0, 4.0]:
        with with_cost(C1) as prm:
            lab, X = P.labelled(exp, prm, tf=tf, swing_k=k, min_stop_m15=ms)
        d = P.in_period(lab, "dev")
        for s, x in d.groupby("strategy"):
            rows.append({"tf": tf, "k": k, "min_stop": ms, "cell": s, **M.r_stats(x.r)})
        rows.append({"tf": tf, "k": k, "min_stop": ms, "cell": "ALL", **M.r_stats(d.r)})
df = pd.DataFrame(rows)
df.to_csv(Path(__file__).resolve().parents[2] / "experiments" / "exp02_min_stop.csv", index=False)
pd.set_option("display.width", 220)
print(df.pivot_table(index="cell", columns=["tf", "min_stop"], values="mean_R").round(3).to_string())
print(df.pivot_table(index="cell", columns=["tf", "min_stop"], values="t_stat").round(1).to_string())
