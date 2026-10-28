"""FASE 46b — capitale minimo per 0,01 misurato DAL PUNTO PIÙ ALTO (non dall'inizio del mese), mese per mese
(la versione di fila, fase 46, superava le 2 ore). Il punto debole della fase 44 era proprio questo: i guadagni di
inizio mese coprivano i cali successivi. Set: 60 migliori della fase 44 + bot 1.61 + costante.
usage: python python/scripts/phase46b_true_capital_monthly.py
"""
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

from phase36_entries_ticks import signals
from phase46_true_capital import CAND, sim

ROOT = Path(__file__).resolve().parents[2]
ROWS = [r for _, r in CAND.iterrows()]


def run_month(m):
    fn = ROOT / "output" / "cache" / "ticks" / f"XAUUSD_ticks_2026_{m:02d}.parquet"
    sig = {k: signals(fn, 12000, k) for k in (0.0, 6.0)}
    out = []
    for r in ROWS:
        bid, ask, calm, trend = sig[r["CALM"]]
        month = np.full(bid.size, m, np.int64)
        me = np.zeros(13)
        p, need, no = sim(bid, ask, calm, trend, month, float(r["D"]), float(r["G"]), float(r["M"]), float(r["T"]),
                          int(r["KH"]), float(r["R"]), float(r["HR"]), float(r["LMAX"]), float(r["TRS"]), float(r["TRD"]), me)
        out.append(dict(cfg=int(r["cfg"]), mese=m, profitto=round(p), capitale_vero=round(need), ordini=no))
    print("fatto mese", m, flush=True)
    return out


def main():
    with Pool(5) as p:
        rows = [x for part in p.map(run_month, range(1, 11)) for x in part]
    df = pd.DataFrame(rows)
    out = ROOT / "output" / "phase46"
    out.mkdir(parents=True, exist_ok=True)
    df.to_csv(out / "capitale_vero_mesi.csv", index=False)
    g = df.groupby("cfg").agg(profitto=("profitto", "sum"), peggior=("profitto", "min"), capitale_vero=("capitale_vero", "max"))
    tab = pd.read_csv(ROOT / "output" / "phase44" / "capitale_tabella.csv").set_index("cfg")
    g = g.join(tab[["capitale", "D", "G", "M", "T", "KH", "R", "HR", "LMAX", "TRS", "TRD", "CALM"]])
    g["resa_su_capitale"] = g.profitto / g.capitale_vero
    g.to_csv(out / "capitale_vero_tabella.csv")
    pd.set_option("display.width", 300)
    print(g.sort_values("resa_su_capitale", ascending=False).to_string())


if __name__ == "__main__":
    main()
