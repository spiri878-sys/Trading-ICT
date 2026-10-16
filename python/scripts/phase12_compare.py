"""FASE 12 — ICT contro SMC contro WYCKOFF nella STESSA architettura: Market Brain (H4 + D1 allineati), AI
autoallenata (Huber, riaddestrata ogni 6 mesi su 4 anni, solo esiti chiusi, memoria ombra), uscita dinamica
(stop 1,5 ATR H4, trailing 5 ATR H4, 10 giorni), un trade alla volta. Confronto con selezioni casuali.
SVILUPPO 2010-2015, CONTROLLO 2016-2026-01.

usage: python python/scripts/phase12_compare.py
"""
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from phase11_robust import Base  # noqa: E402
from phase11_trend_exit import CACHE, OUT  # noqa: E402

FAMILIES = {
    "ICT (6 celle PRIME)": ["PPK", "OTEOF", "PO3", "UNIOF", "LS", "BB"],
    "SMC (BOS+FVG, CHoCH, OB, Breaker, Liquidity)": ["PPK", "MSS", "OB", "BB", "LS"],
    "WYCKOFF (Spring, SOS, LPS, H1)": ["WSPR", "WSOS", "WLPS", "WH1"],
    "TUTTE (14 celle)": None,
}
MGMT = {"swing_1.5_5_10g": (1.5, 5.0, 10), "swing_2_4_5g": (2.0, 4.0, 5)}


def log(msg, t0=[time.time()]):
    print(f"[{time.time() - t0[0]:6.0f}s] {msg}", flush=True)


def main():
    res = {}
    rng = np.random.default_rng(11)
    for fam, cells in FAMILIES.items():
        B = Base(path=CACHE / "phase12" / "dataset.parquet", cells=cells)
        for mn, (slm, trm, hold) in MGMT.items():
            r, et = B.label(slm, trm, hold)
            r2, _ = B.label(slm, trm, hold, spread=0.60, slip=0.10, comm=0.07)
            sc = B.scores(r, et)
            out = {"segnali": int(len(r))}
            for rule, take in (("solo trend", B.flt & np.isfinite(r)),
                               ("trend + AI", B.flt & (np.nan_to_num(sc, nan=-9) > 0))):
                take = take & (B.t >= np.datetime64("2010-01-01"))
                ev, op = B.evaluate(r, et, take)
                ev2, _ = B.evaluate(r2, et, op)
                out[rule] = {"dev": ev["dev"], "chk": ev["chk"], "chk_costi_x2_avg_r": ev2["chk"].get("avg_r")}
                if rule == "trend + AI":
                    half = pd.DatetimeIndex(B.t).year * 2 + (pd.DatetimeIndex(B.t).month > 6)
                    elig = B.flt & np.isfinite(r) & (B.t >= np.datetime64("2010-01-01"))
                    rand = []
                    for k in range(100):
                        tk = np.zeros(len(r), bool)
                        for hc in np.unique(half[take]):
                            pool = np.where(elig & (half == hc))[0]
                            n = int((take & (half == hc)).sum())
                            if len(pool) and n:
                                tk[rng.choice(pool, size=min(n, len(pool)), replace=False)] = True
                        e, _ = B.evaluate(r, et, tk)
                        rand.append(e["chk"].get("avg_r", np.nan))
                    rand = np.array(rand, float)
                    out[rule]["casuale_chk_media"] = round(float(np.nanmean(rand)), 3)
                    out[rule]["p_casuale_chk"] = round(float(np.nanmean(rand >= ev["chk"].get("avg_r", 9))), 3)
            res[f"{fam} | {mn}"] = out
            a = out["trend + AI"]
            log(f"{fam} | {mn}: segnali {out['segnali']}; trend+AI dev {a['dev'].get('avg_r')} ({a['dev'].get('per_year')}/anno) "
                f"chk {a['chk'].get('avg_r')} PF {a['chk'].get('pf')} anni {a['chk'].get('years_pos')} cagr1% "
                f"{a['chk'].get('cagr_1pct')} dd {a['chk'].get('maxdd_1pct')} | casuale {a['casuale_chk_media']} p={a['p_casuale_chk']}"
                f" | solo trend chk {out['solo trend']['chk'].get('avg_r')}")
        (OUT / "phase12_compare.json").write_text(json.dumps(res, indent=1, default=str))


if __name__ == "__main__":
    main()
