"""EXP-07 (dev only): parameter neighbourhood of the H1 continuation candidate (robustness, not tuning)."""
import sys
from dataclasses import replace
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np, pandas as pd
from raptor import pipeline as P, metrics as M
from raptor.costs import C1, C2, with_cost

rows = []
for k in (2, 3, 4):
    for disp in (0.8, 1.2, 1.6):
        strat = {c: {"expiry": 4, "max_r_atr": 30.0, "min_r_atr": 0.3, "market_entry": True, "min_disp": disp}
                 for c in ["PPK", "UNIOF"]}
        for tp in (2.0, 3.0, 4.0):
            for hold in (24, 48, 96):
                ex = dict(tp_r=tp, p1_frac=0.0, p2_frac=0.0, be_after_p1=False, max_hold_min=hold * 60)
                for cname, cm in [("C1", C1), ("C2", C2)]:
                    with with_cost(cm) as prm:
                        lab, X = P.labelled(strat, replace(prm, **ex), tf="1h", swing_k=k)
                    d = P.in_period(lab, "dev"); d = d[d.filled].drop_duplicates(["bar_time", "side"])
                    rows.append({"k": k, "disp": disp, "tp": tp, "hold": hold, "cost": cname, **M.r_stats(d.r)})
df = pd.DataFrame(rows)
df.to_csv(Path(__file__).resolve().parents[2] / "experiments" / "exp07_neighbourhood.csv", index=False)
pd.set_option("display.width", 250)
print(df[df.cost == "C1"].pivot_table(index=["k", "disp"], columns=["tp", "hold"], values="mean_R").round(3).to_string())
print(df[df.cost == "C1"].pivot_table(index=["k", "disp"], columns=["tp", "hold"], values="n").to_string())
print("share of C1 cells > 0:", round((df[df.cost == 'C1'].mean_R > 0).mean(), 3), " C2:", round((df[df.cost == 'C2'].mean_R > 0).mean(), 3))
