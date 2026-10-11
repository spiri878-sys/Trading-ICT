"""FAM-03: nested walk-forward selector over ALL families (FAM-01 labels) x regime filter {none, aligned},
with SEPARATE long and short sleeves. Rule fixed in advance: each year Y (2020..2026), using only trades with
exit < Y-01-01, pick per side the top-3 configs by in-sample t-stat among those with n_in >= 60, mean > 0 and
t_in >= 2.0 (a side with no eligible config stays flat). Trade them in Y. Report OOS by side and year."""
import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np, pandas as pd
from raptor import pipeline as P, metrics as M

ROOT = Path(__file__).resolve().parents[2]
L = pd.read_parquet(ROOT / "experiments" / "fam01_labels.parquet")
f = P.feats("15min", 3)[["d1_close", "d1_ema", "h4_trend"]]
ctx = pd.merge_asof(L[["bar_time"]].reset_index().sort_values("bar_time"), f.rename_axis("bar_time").reset_index(),
                    on="bar_time", direction="backward").set_index("index").sort_index()
bull = ((ctx.d1_close > ctx.d1_ema) & (ctx.h4_trend > 0)).values
bear = ((ctx.d1_close < ctx.d1_ema) & (ctx.h4_trend < 0)).values
L["aligned"] = np.where(L.side == 1, bull, bear)
cfg_v, side_v, r_v = L.cfg.values, L.side.values, L.r.values
ex_v, yr_v = L.exit_time.values, L.bar_time.dt.year.values
configs = []
for cfg in np.unique(cfg_v):
    base = cfg_v == cfg
    for side in (1, -1):
        for reg in ("none", "aligned"):
            m = base & (side_v == side)
            if reg == "aligned":
                m = m & L.aligned.values
            configs.append(((cfg, side, reg), m))
rows, oos = [], {1: [], -1: []}
for Y in range(2020, 2027):
    ins = ex_v < np.datetime64(f"{Y}-01-01")
    for side in (1, -1):
        st = []
        for key, m in configs:
            if key[1] != side:
                continue
            r = r_v[m & ins]
            if len(r) >= 60 and r.mean() > 0:
                t = r.mean() / (r.std(ddof=1) / np.sqrt(len(r)))
                if t >= 2.0:
                    st.append((t, key, r.mean(), len(r), m))
        st.sort(key=lambda x: -x[0])
        for t, key, mu, n, m in st[:3]:
            ro = r_v[m & (yr_v == Y)]
            rows.append({"year": Y, "side": "long" if side == 1 else "short", "cfg": key[0], "regime": key[2],
                         "t_in": round(t, 2), "meanR_in": round(mu, 3), "n_in": n, "n_oos": len(ro),
                         "meanR_oos": round(float(ro.mean()), 3) if len(ro) else None, "sumR_oos": round(float(ro.sum()), 2)})
            oos[side].extend(ro.tolist())
        if not st:
            rows.append({"year": Y, "side": "long" if side == 1 else "short", "cfg": "(flat: no config with t_in>=2)"})
sel = pd.DataFrame(rows)
sel.to_csv(ROOT / "experiments" / "fam03_selector.csv", index=False)
pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 70)
print(sel.to_string())
res = {"OOS_long": M.r_stats(pd.Series(oos[1])), "OOS_short": M.r_stats(pd.Series(oos[-1])),
       "OOS_both": M.r_stats(pd.Series(oos[1] + oos[-1])),
       "yearly_sumR": sel.dropna(subset=["sumR_oos"]).groupby(["year", "side"]).sumR_oos.sum().round(1).unstack().to_dict()}
(ROOT / "experiments" / "fam03_walkforward.json").write_text(json.dumps(res, indent=1, default=str))
print(json.dumps(res, indent=1, default=str))
