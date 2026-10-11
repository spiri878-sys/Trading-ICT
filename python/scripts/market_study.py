"""Phase B - quantitative market study of XAUUSD M1 2018-2026 (bid, server time = NY+7h).
Writes reports/market_study.json. All statistics are descriptive (no strategy selection here)."""
import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np, pandas as pd
from scipy import stats
from raptor import pipeline as P, data as D
from raptor.indicators import atr

ROOT = Path(__file__).resolve().parents[2]
m1 = P.m1()
out = {}
# 1) return distribution per timeframe (log returns of closes)
for tf in ["5min", "1h", "4h", "1D"]:
    b = D.resample(m1, tf)
    r = np.log(b.close).diff().dropna()
    per_year = b.close.groupby(b.index.year).agg(["first", "last"])
    out[f"returns_{tf}"] = {"n": int(len(r)), "mean_bp": round(r.mean() * 1e4, 3), "std_bp": round(r.std() * 1e4, 2),
                            "skew": round(float(stats.skew(r)), 3), "excess_kurtosis": round(float(stats.kurtosis(r)), 2),
                            "share_up": round(float((r > 0).mean()), 4)}
out["yearly_return_pct"] = {int(y): round(float(v["last"] / v["first"] * 100 - 100), 1) for y, v in
                            D.resample(m1, "1D").close.groupby(D.resample(m1, "1D").index.year).agg(["first", "last"]).iterrows()}
# 2) volatility by NY hour and session (mean M5 absolute log return, bp)
b5 = D.resample(m1, "5min")
r5 = np.log(b5.close).diff().abs() * 1e4
nyh = (b5.index - pd.Timedelta(hours=7)).hour
vol_h = r5.groupby(nyh).mean().round(2)
out["vol_by_ny_hour_abs_ret_bp_m5"] = vol_h.to_dict()
sess = pd.cut(nyh, [-1, 2, 7, 11, 16, 23], labels=["Asia(18-02NY)a", "London(03-07)", "NY_AM(08-11)", "NY_PM(12-16)", "late/Asia(17-23)"])
out["vol_by_session"] = r5.groupby(sess, observed=True).mean().round(2).to_dict()
# 3) trend persistence: autocorrelation and variance ratio
def vr(r, q):
    r = r - r.mean()
    rq = r.rolling(q).sum().dropna()
    return float(rq.var() / (q * r.var()))
for tf in ["1h", "4h", "1D"]:
    b = D.resample(m1, tf)
    r = np.log(b.close).diff().dropna()
    out[f"persistence_{tf}"] = {"acf1": round(float(r.autocorr(1)), 4), "acf2": round(float(r.autocorr(2)), 4),
                                "VR2": round(vr(r, 2), 3), "VR4": round(vr(r, 4), 3), "VR8": round(vr(r, 8), 3), "VR16": round(vr(r, 16), 3)}
# 4) breakout follow-through (H1 close beyond 20-bar high/low), forward return in ATR(H1) units, by direction
h1 = D.resample(m1, "1h")
a = atr(h1.high.values, h1.low.values, h1.close.values, 14)
c = h1.close.values
hi = pd.Series(h1.high.values).rolling(20).max().shift(1).values
lo = pd.Series(h1.low.values).rolling(20).min().shift(1).values
res = {}
for hz in (1, 4, 24):
    fwd = (pd.Series(c).shift(-hz).values - c) / a
    up, dn = c > hi, c < lo
    base = np.nanmean(fwd)
    res[f"{hz}h"] = {"after_up_breakout": round(float(np.nanmean(fwd[up])), 3), "after_down_breakout_signed": round(float(-np.nanmean(fwd[dn])), 3),
                     "unconditional_long": round(float(base), 3), "n_up": int(up.sum()), "n_dn": int(dn.sum())}
out["breakout_followthrough_ATR_H1"] = res
# 5) behaviour after the first raid of the previous-day high/low (M5), 1h/4h forward in ATR(H1)
f = P.feats("5min", 3) if (D.PROCESSED / "feat_5min_k3.parquet").exists() else P.feats("15min", 3)
cl = f.close.values
sw = {}
for name, m, sgn in [("after_PDH_raid_(short_signed)", (f.sweep_hi.values & (f.high.values > f.pdh.values)), -1),
                     ("after_PDL_raid_(long_signed)", (f.sweep_lo.values & (f.low.values < f.pdl.values)), 1)]:
    bars_h = int(60 / ((f.index[1] - f.index[0]).total_seconds() / 60))
    row = {"n": int(m.sum())}
    for hz in (1, 4):
        fwd = (pd.Series(cl).shift(-hz * bars_h).values - cl) / f.h1_atr.values * sgn
        row[f"{hz}h"] = round(float(np.nanmean(fwd[m])), 3)
    sw[name] = row
out["liquidity_raid_reversal_ATR_H1"] = sw
# 6) efficiency ratio regime (H1, 24 bars): share of trending vs ranging
er = (pd.Series(c).diff(24).abs() / pd.Series(c).diff().abs().rolling(24).sum())
out["efficiency_ratio_H1_24"] = {"median": round(float(er.median()), 3), "share_gt_0.4": round(float((er > 0.4).mean()), 3)}
(ROOT / "reports" / "market_study.json").write_text(json.dumps(out, indent=1, default=str))
print(json.dumps(out, indent=1, default=str))
