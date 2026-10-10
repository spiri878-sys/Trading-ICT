"""EXP-05 (dev only): event study. Signed forward return after each cell's decision bar, in units of
ATR(H1), at horizons 1h/4h/24h - no management, no costs. Plus unconditional drift for reference."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np, pandas as pd
from raptor import pipeline as P

CELLS = ["PPK", "OTEOF", "PO3", "UNIOF", "LS", "SILVER_BULLET", "WYCKOFF"]
m1 = P.m1(); close = m1.close
rows = []
for tf, k in [("5min", 3), ("5min", 8), ("15min", 3), ("1h", 3)]:
    f = P.feats(tf, k)
    s = P.signals({c: {} for c in CELLS}, tf, k)
    s = P.in_period(s, "dev")
    tfm = int(pd.Timedelta(tf).total_seconds() // 60)
    t0 = s.bar_time + pd.Timedelta(minutes=tfm)
    i0 = np.searchsorted(m1.index.values, t0.values)
    a = f.h1_atr.values[s.bar_i.values]
    for hz in (60, 240, 1440):
        i1 = np.searchsorted(m1.index.values, (t0 + pd.Timedelta(minutes=hz)).values)
        ok = i1 < len(m1)
        fwd = (close.values[np.minimum(i1, len(m1) - 1)] - close.values[np.minimum(i0, len(m1) - 1)]) * s.side.values / a
        s[f"fwd_{hz}"] = np.where(ok, fwd, np.nan)
    for c, g in s.groupby("strategy"):
        r = {"tf": tf, "k": k, "cell": c, "n": len(g)}
        for hz in (60, 240, 1440):
            x = g[f"fwd_{hz}"].dropna()
            r[f"mean_{hz}"] = round(x.mean(), 3); r[f"t_{hz}"] = round(x.mean() / x.std() * np.sqrt(len(x)), 2)
        rows.append(r)
df = pd.DataFrame(rows)
pd.set_option("display.width", 220)
print(df.to_string())
# unconditional long drift in ATR(H1) units for reference
h1 = P.feats("1h", 3)
d = P.in_period(h1.assign(bar_time=h1.index), "dev")
fw = (d.close.shift(-24) - d.close) / d.h1_atr
print("unconditional long 24h drift (ATR H1):", round(fw.mean(), 3), "t=", round(fw.mean() / fw.std() * np.sqrt(len(fw) / 24), 2))
df.to_csv(Path(__file__).resolve().parents[2] / "experiments" / "exp05_event_study.csv", index=False)
