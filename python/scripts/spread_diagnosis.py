"""Spread diagnosis (spec 6.1). Writes reports/spread_diagnosis.json."""
import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np, pandas as pd
from raptor import data as D

m1 = D.load_m1()
out = {}
# 1) column identity / units: header and digits of prices
hdr = open(D.RAW / "XAUUSD_M1.csv", "rb").readline().decode().strip()
out["header"] = hdr
dec = m1.close.head(200000).map(lambda x: len(f"{x:.5f}".rstrip("0").split(".")[1]) if "." in f"{x:.5f}".rstrip("0") else 0)
out["max_price_decimals_sample"] = int(dec.max())
# 2) monthly spread statistics + tick volume + M1 range (to see feed changes)
g = m1.groupby(m1.index.to_period("M"))
mon = pd.DataFrame({"spread_med_pts": g.spread.median(), "spread_zero_share": g.spread.apply(lambda s: (s == 0).mean()),
                    "tickvol_med": g.tickvol.median(), "range_med_usd": g.apply(lambda x: (x.high - x.low).median()),
                    "close_med": g.close.median()})
mon["spread_over_range"] = mon.spread_med_pts * 0.01 / mon.range_med_usd
mon.index = mon.index.astype(str)
mon.round(4).to_csv(D.ROOT / "reports" / "spread_monthly.csv")
# 3) change point: first month where median spread < 50 points
cp = mon.index[(mon.spread_med_pts < 50).values]
out["first_month_median_spread_below_50pts"] = cp[0] if len(cp) else None
# 4) values distribution: are spreads multiples of 10 (typical of a 3-digit -> 2-digit conversion)?
for a, b, name in [("2018", "2023", "2018_2022"), ("2023", "2027", "2023_2026")]:
    s = m1.spread[(m1.index >= a) & (m1.index < b)]
    out[f"{name}_share_multiple_of_10"] = round(float((s % 10 == 0).mean()), 4)
    out[f"{name}_top_values"] = {int(k): int(v) for k, v in s.value_counts().head(8).items()}
    out[f"{name}_spread_over_median_m1_range"] = round(float(s.median() * 0.01 / (m1.high - m1.low)[s.index].median()), 3)
# 5) plausibility: is the spread larger than the whole M1 bar range very often?
rng = (m1.high - m1.low)
for a, b, name in [("2018", "2023", "2018_2022"), ("2023", "2027", "2023_2026")]:
    m = (m1.index >= a) & (m1.index < b)
    out[f"{name}_share_bars_spread_gt_range"] = round(float((m1.spread[m] * 0.01 > rng[m]).mean()), 4)
print(json.dumps(out, indent=1))
(D.ROOT / "reports" / "spread_diagnosis.json").write_text(json.dumps(out, indent=1))
print(mon[["spread_med_pts", "spread_zero_share", "tickvol_med", "range_med_usd"]].iloc[::6].to_string())
