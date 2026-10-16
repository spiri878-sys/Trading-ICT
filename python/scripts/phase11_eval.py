"""FASE 11 — valutazione dei punteggi dell'autoallenamento: soglie, memoria ombra, un trade alla volta.

Periodi: SVILUPPO 2010-2019 (qui si sceglie), CONTROLLO 2020-2026-01 (solo lettura, mai usato per scegliere).

usage: python python/scripts/phase11_eval.py
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from raptor.prime.data import ROOT  # noqa: E402
from raptor.prime.models import living_threshold  # noqa: E402
from raptor.prime.selftrain import adaptive_set, equity, one_at_a_time  # noqa: E402

D = ROOT / "output" / "cache" / "phase11"
OUT = ROOT / "output" / "phase11"
DEV = ("2012-01-01", "2020-01-01")
CHK = ("2020-01-01", "2026-02-01")


def stats(r, t):
    r = np.asarray(r, float)
    ok = np.isfinite(r)
    r, t = r[ok], np.asarray(t)[ok]
    if r.size == 0:
        return dict(n=0)
    gp, gl = r[r > 0].sum(), -r[r < 0].sum()
    yrs = pd.Series(r, index=pd.DatetimeIndex(t).year).groupby(level=0).sum()
    span = max((pd.Timestamp(max(t)) - pd.Timestamp(min(t))).days / 365.25, 0.5)
    return dict(n=int(r.size), per_year=round(r.size / span, 1), avg_r=round(float(r.mean()), 4),
                pf=round(float(gp / gl), 3) if gl > 0 else None, years_pos=f"{int((yrs > 0).sum())}/{len(yrs)}",
                t=round(float(r.mean() / (r.std(ddof=1) / np.sqrt(r.size))), 2) if r.size > 2 else None)


def rules(s):
    """Regole di presa candidate. Restituisce {nome: maschera}."""
    sc = s.score.values
    out = {}
    is_reg = "_reg_" in s.attrs["name"]
    if is_reg:
        for th in (0.0, 0.05, 0.1, 0.15, 0.2):
            out[f"abs{th}"] = sc > th
    else:
        for th in (0.45, 0.5, 0.55):
            out[f"abs{th}"] = sc > th
    for q in (0.8, 0.9, 0.95):
        thr = living_threshold(sc, s.known_at.values, window=1000, q=q)
        out[f"live{q}"] = sc > np.nan_to_num(thr, nan=np.inf)
    for lb in (2, 3):
        for mg in (0.0, 0.05):
            for gc in (("cell", "side"), ("side",)):
                tk, _ = adaptive_set(s, group_cols=gc, lookback_years=lb, margin=mg, start="2012-01-01")
                out[f"aset_{'_'.join(gc)}_lb{lb}_m{mg}"] = tk
    if "mem_cs_d730" in s:
        for k in list(out):
            out[k + "+mem730"] = out[k] & (np.nan_to_num(s.mem_cs_d730.values, nan=-1) > 0)
    return out


def evaluate(path):
    s = pd.read_parquet(path)
    s = s[s.score.notna()].sort_values("known_at").reset_index(drop=True)
    s.attrs["name"] = path.stem.replace("scores_", "")
    rows = []
    for rn, take in rules(s).items():
        op = one_at_a_time(s.fill_time.values, s.exit_time.values, take, s.r.values)
        for per, (a, b) in (("dev", DEV), ("chk", CHK)):
            m = ((s.known_at >= a) & (s.known_at < b)).values
            iso = stats(s.r.values[m & take], s.known_at.values[m & take])
            one = stats(s.r.values[m & op], s.known_at.values[m & op])
            c2 = stats(s.r_c2.values[m & op], s.known_at.values[m & op])
            rows.append(dict(cfg=s.attrs["name"], rule=rn, period=per, **{f"iso_{k}": v for k, v in iso.items()},
                             **{f"one_{k}": v for k, v in one.items()}, one_c2_avg_r=c2.get("avg_r")))
    return rows


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rows = []
    for p in sorted(D.glob("scores_*.parquet")):
        rows += evaluate(p)
    R = pd.DataFrame(rows)
    R.to_csv(OUT / "eval_grid.csv", index=False)
    dev = R[R.period == "dev"].set_index(["cfg", "rule"])
    chk = R[R.period == "chk"].set_index(["cfg", "rule"])
    J = dev.join(chk, lsuffix="_dev", rsuffix="_chk")
    J = J[J.one_per_year_dev >= 40]
    cols = ["one_n_dev", "one_per_year_dev", "one_avg_r_dev", "one_pf_dev", "one_years_pos_dev", "one_c2_avg_r_dev",
            "one_n_chk", "one_avg_r_chk", "one_pf_chk", "one_years_pos_chk", "one_c2_avg_r_chk"]
    top = J.sort_values("one_avg_r_dev", ascending=False)[cols].head(40)
    pd.set_option("display.width", 250)
    print(top.to_string())
    top.to_csv(OUT / "eval_top_dev.csv")


if __name__ == "__main__":
    main()
