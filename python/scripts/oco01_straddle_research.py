"""OCO-01: breakout straddle research (user idea): buy stop above / sell stop below a range, OCO, one trade at
a time, re-placed after each trade, trailing stop following the price. Range families x stop x exits.
Selection metric: per-trade R at 1% risk (sizing-independent); costs C1 + swap; nested walk-forward."""
import sys, json, itertools
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np, pandas as pd
from raptor import pipeline as P, metrics as M
from raptor.straddle import run
from raptor.straddle_setups import setups

ROOT = Path(__file__).resolve().parents[2]
mk = P.market()
SPREAD = np.full(len(mk.o), 0.30)          # C1 spread


GRID = []
for kind in ("ASIA", "PDHL"):
    for stop, sk in (("range", None), ("atr", 1.0), ("atr", 2.0)):
        GRID.append(dict(kind=kind, stop=stop, stop_k=sk or 1.5))
for kind, N in itertools.product(("ROLL", "SQZ"), (6, 12, 24)):
    for stop, sk in (("range", None), ("atr", 1.0), ("atr", 2.0)):
        GRID.append(dict(kind=kind, N=N, stop=stop, stop_k=sk or 1.5))
EXITS = [dict(trail_atr=t, tp_r=tp, max_hold_min=h) for t in (1.0, 2.0, 3.0) for tp in (100.0, 2.0) for h in (1440, 2880)]
rows, labs = [], []
for g in GRID:
    s, tfm = setups(**g)
    for ex in EXITS:
        tr, info = run(mk, s, tf_minutes=tfm, spread=SPREAD, init_bal=10000.0, lot_mode=1, risk_pct=1.0, **ex)
        cfg = ",".join(f"{k}={v}" for k, v in g.items()) + "|" + ",".join(f"{k}={v}" for k, v in ex.items())
        tr["cfg"] = cfg
        labs.append(tr[["entry_time", "exit_time", "side", "r_mult", "net", "cfg"]])
        st = M.r_stats(tr.r_mult)
        rows.append({"cfg": cfg, **st, "long_R": round(float(tr[tr.side == 1].r_mult.mean()), 3),
                     "short_R": round(float(tr[tr.side == -1].r_mult.mean()), 3),
                     "ties_pct": round(float(tr.same_bar_tie.mean() * 100), 2), "final_balance_1pct": round(float(tr.balance.iloc[-1]), 0)})
S = pd.DataFrame(rows).sort_values("t_stat", ascending=False)
S.to_csv(ROOT / "experiments" / "oco01_grid.csv", index=False)
L = pd.concat(labs, ignore_index=True)
L.to_parquet(ROOT / "experiments" / "oco01_trades.parquet")
pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 110)
print("configs:", len(S), " share mean_R>0:", round(float((S.mean_R > 0).mean()), 3))
print(S.head(12)[["cfg", "n", "mean_R", "pf", "t_stat", "win_pct", "long_R", "short_R", "final_balance_1pct"]].to_string())
print(S.groupby(S.cfg.str.split(",").str[0]).mean_R.describe()[["count", "mean", "50%", "max"]].round(3))
