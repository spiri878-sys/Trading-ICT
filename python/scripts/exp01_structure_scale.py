"""EXP-01 (dev only): does a larger structure scale (wider structural stops) create an edge?
Hypothesis H1 from the baseline diagnosis: M5/k=3 stops are ~0.9 ATR(M15): costs dominate and the
zero-cost edge is ~0. The Interstellar material shows stops of >= ~2 ATR(M15)."""
import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pandas as pd
from raptor import pipeline as P, metrics as M
from raptor.engine import Params

CELLS = ["PPK", "OTEOF", "PO3", "UNIOF", "LS", "SILVER_BULLET", "WYCKOFF"]
rows = []
for tf, k in [("5min", 3), ("5min", 8), ("5min", 15), ("15min", 3), ("15min", 6), ("1h", 3)]:
    tfm = int(pd.Timedelta(tf).total_seconds() // 60)
    exp = {c: {"expiry": max(2, 60 // tfm)} for c in CELLS}  # pending orders valid 1h
    exp["OTEOF"]["expiry"] = max(4, 120 // tfm)
    for cost, prm, zero in [("normalized_30pt", Params(max_spread=5.0, spread_floor=0.30), True),
                            ("recorded", Params(max_spread=5.0), False)]:
        mk = P.market(); raw = mk.sp_raw.copy()
        if zero:
            mk.sp_raw[:] = 0.0
        lab, X = P.labelled(exp, prm, tf=tf, swing_k=k)
        mk.sp_raw[:] = raw
        d = P.in_period(lab.join(X.drop(columns="side")), "dev")
        for s, x in d.groupby("strategy"):
            rows.append({"tf": tf, "k": k, "cost": cost, "cell": s, **M.r_stats(x.r),
                         "stop_m15_med": round(float(x.stop_atr_m15.median()), 2)})
df = pd.DataFrame(rows)
out = Path(__file__).resolve().parents[2] / "experiments" / "exp01_structure_scale.csv"
df.to_csv(out, index=False)
pd.set_option("display.width", 220)
print(df.pivot_table(index=["cell"], columns=["cost", "tf", "k"], values="mean_R").round(3).to_string())
print(df.pivot_table(index=["cell"], columns=["tf", "k"], values="n", aggfunc="max").to_string())
