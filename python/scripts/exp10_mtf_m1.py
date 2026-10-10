"""EXP-10 (dev only): experimental multi-timeframe model with M1 execution (H4+H1 bias, M1 raid + MSS).
Variants: execution TF (1min/5min), min stop in ATR(M15), exit model. Costs: ZERO and C1."""
import sys
from dataclasses import replace
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pandas as pd
from raptor import pipeline as P, metrics as M
from raptor.costs import C1, ZERO, with_cost

EXITS = {"ladder": dict(tp_r=4.0, p1_r=0.7, p1_frac=0.2, p2_r=2.0, p2_frac=0.2, be_after_p1=True, mgmt_on_close=True, max_hold_min=1440),
         "tp2R_8h": dict(tp_r=2.0, p1_frac=0.0, p2_frac=0.0, be_after_p1=False, max_hold_min=480),
         "tp3R_24h": dict(tp_r=3.0, p1_frac=0.0, p2_frac=0.0, be_after_p1=False, max_hold_min=1440)}
rows = []
for tf, k in [("1min", 5), ("5min", 3)]:
    tfm = int(pd.Timedelta(tf).total_seconds() // 60)
    strat = {"MTF_M1": {"expiry": max(3, 30 // tfm), "min_r_atr": 0.5, "max_r_atr": 40.0}}
    for ms in (0.0, 1.0, 2.0, 3.0):
        for en, ex in EXITS.items():
            for cname, cm in [("zero", ZERO), ("C1", C1)]:
                with with_cost(cm) as prm:
                    lab, X = P.labelled(strat, replace(prm, **ex), tf=tf, swing_k=k, min_stop_m15=ms)
                d = P.in_period(lab, "dev"); d = d[d.filled]
                rows.append({"tf": tf, "min_stop": ms, "exit": en, "cost": cname, **M.r_stats(d.r),
                             "long_R": round(float(d[d.side == 1].r.mean()), 3), "short_R": round(float(d[d.side == -1].r.mean()), 3)})
df = pd.DataFrame(rows)
df.to_csv(Path(__file__).resolve().parents[2] / "experiments" / "exp10_mtf_m1.csv", index=False)
pd.set_option("display.width", 220)
print(df.to_string())
