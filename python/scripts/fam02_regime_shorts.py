"""FAM-02: do SHORT signals work in a bearish higher-timeframe regime? Regime at decision time (closed bars):
bear = D1 close < D1 EMA50 AND H4 trend (last H4 structure break) down. Same for longs in bull regime."""
import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np, pandas as pd
from raptor import pipeline as P, metrics as M

ROOT = Path(__file__).resolve().parents[2]
L = pd.read_parquet(ROOT / "experiments" / "fam01_labels.parquet")
f = P.feats("15min", 3)[["d1_close", "d1_ema", "h4_trend"]]
# context available at decision: take the 15m feature row at/just before bar_time (higher TF already causal)
ctx = pd.merge_asof(L[["bar_time"]].reset_index().sort_values("bar_time"), f.rename_axis("bar_time").reset_index(),
                    on="bar_time", direction="backward").set_index("index").sort_index()
L["bear"] = (ctx.d1_close < ctx.d1_ema) & (ctx.h4_trend < 0)
L["bull"] = (ctx.d1_close > ctx.d1_ema) & (ctx.h4_trend > 0)
out = {}
for side, reg in [(-1, "bear"), (1, "bull")]:
    x = L[L.side == side]
    g = x.groupby("cfg").apply(lambda d: pd.Series({"in_regime": d[d[reg]].r.mean(), "n_in": int(d[reg].sum()),
                                                    "out_regime": d[~d[reg]].r.mean()}))
    g = g[g.n_in >= 40]
    out[f"{'short' if side < 0 else 'long'}_in_{reg}"] = {"configs": int(len(g)), "share_pos_in_regime": round(float((g.in_regime > 0).mean()), 3),
                                                          "median_R_in_regime": round(float(g.in_regime.median()), 3),
                                                          "median_R_out_regime": round(float(g.out_regime.median()), 3),
                                                          "best5": g.sort_values("in_regime", ascending=False).head(5).round(3).reset_index().to_dict("records")}
    yy = x[x[reg]]
    out[f"{'short' if side < 0 else 'long'}_in_{reg}"]["by_year_meanR_all_configs"] = yy.groupby(yy.bar_time.dt.year).r.mean().round(3).to_dict()
(ROOT / "experiments" / "fam02_regime.json").write_text(json.dumps(out, indent=1, default=str))
print(json.dumps(out, indent=1, default=str))
