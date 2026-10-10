"""Candidate C robustness: neighbourhood (k, TP, hold, HTF stop) and the SHORT mirror (drift check). C1."""
import sys, json, itertools
from dataclasses import replace
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pandas as pd
from raptor import pipeline as P, metrics as M
from raptor.costs import C1, with_cost

ROOT = Path(__file__).resolve().parents[2]
rows = []
for k, tp, hold, htf in itertools.product((2, 3, 4), (2.0, 3.0, 4.0), (24, 48, 96), ("h1", "h4")):
    ex = dict(tp_r=tp, p1_frac=0.0, p2_frac=0.0, be_after_p1=False, max_hold_min=hold * 60)
    with with_cost(C1, replace(P.Params(), **ex)) as prm:
        lab, _ = P.labelled({"UNIOF": {"expiry": 4, "max_r_atr": 40.0}}, prm, tf="15min", swing_k=k, htf_stop=htf)
    lab = lab[lab.filled]
    for side, g in lab.groupby("side"):
        o = g[g.bar_time >= "2022-01-01"]
        rows.append({"k": k, "tp": tp, "hold": hold, "htf_stop": htf, "side": "long" if side == 1 else "short",
                     "n": len(g), "meanR_all": round(g.r.mean(), 3), "meanR_2022_2026": round(o.r.mean(), 3)})
df = pd.DataFrame(rows)
df.to_csv(ROOT / "experiments" / "candidate_c_robustness.csv", index=False)
lg, sh = df[df.side == "long"], df[df.side == "short"]
out = {"long_share_positive_all": round((lg.meanR_all > 0).mean(), 3), "long_share_positive_2022_2026": round((lg.meanR_2022_2026 > 0).mean(), 3),
       "long_median_meanR": round(lg.meanR_all.median(), 3), "short_share_positive_all": round((sh.meanR_all > 0).mean(), 3),
       "short_median_meanR": round(sh.meanR_all.median(), 3), "grid_points_per_side": len(lg)}
print(json.dumps(out, indent=1))
print(lg.pivot_table(index=["k", "htf_stop"], columns=["tp", "hold"], values="meanR_all").round(2).to_string())
