"""TG-03: what do the signals look like? Timing, side, move before the signal, and outcome by bucket
(follower at market +1 min, channel-style management, standard costs = tg01 'channel_style')."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from raptor.data import load_m1  # noqa: E402

OUT = Path(__file__).resolve().parents[2] / "reports"
t = pd.read_csv(OUT / "tg01_trades_channel_style.csv", parse_dates=["post_time"])
m1 = load_m1().loc["2026-02-25":]
c = m1.close
srv = t.post_time + pd.Timedelta(minutes=60)
i = np.searchsorted(m1.index.values, srv.values.astype("datetime64[ns]"))
for n in (5, 15, 60, 240):
    t[f"mv{n}"] = (c.values[i - 1] - c.values[i - 1 - n]) * t.side  # move before signal in trade direction
t["hour_srv"] = srv.dt.hour
t["usd"] = t.pnl_oz * 10
pd.set_option("display.width", 200)
out = []
out.append("side:\n" + t.groupby("side").usd.agg(["size", "sum", "mean"]).round(1).to_string())
out.append("hour (server):\n" + t.groupby("hour_srv").usd.agg(["size", "sum", "mean"]).round(1).to_string())
for n in (15, 60, 240):
    q = pd.qcut(t[f"mv{n}"], 4)
    out.append(f"move {n}m before, in trade direction (negative = fading):\n" +
               t.groupby(q, observed=True).usd.agg(["size", "sum", "mean"]).round(1).to_string())
out.append("median move before (trade direction): " + str(t[["mv5", "mv15", "mv60", "mv240"]].median().round(2).to_dict()))
out.append("share fading 15m move: %.2f" % (t.mv15 < 0).mean())
txt = "\n\n".join(out)
open(OUT / "tg03_profile.txt", "w").write(txt)
print(txt)
