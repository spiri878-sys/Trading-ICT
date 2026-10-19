"""FASE 17 — il bot a pendenti dell'utente (XauOcoBreakout, versione PERFEZIONATA: buy stop / sell stop sul range H1
compresso, uno alla volta, OCO, trailing 2 ATR H1, TP 2R, 24 h) su un CONTO DA 116 $ (100 EUR), 0,01 lotti, leva 1:1000,
costi del broker dell'utente.

Unica modifica provata: scartare i setup con stop troppo largo (distanza ingresso-stop > X $), perché a 0,01 lotti
1 $ di stop = 1 $ di rischio. X scelto sul 2018-2021 e verificato sul 2022-01/2026 (dati: XAU_1m_data.csv fino al 30/01/2026).
Costi: A spread 0,09 + commissione 0,04 $ per 0,01 lotti andata/ritorno + slippage 0,02; B prudente: commissione per lato
(0,08) + slippage 0,10.

usage: python python/scripts/phase17_oco_100eur.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from raptor import pipeline as P  # noqa: E402
from raptor.straddle import run  # noqa: E402
from raptor.straddle_setups import setups  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "output" / "phase17"
EX = dict(trail_atr=2.0, tp_r=2.0, max_hold_min=1440)
COSTS = {"A": dict(spread=0.09, comm=2.0, slip=0.02), "B": dict(spread=0.09, comm=4.0, slip=0.10)}
CAPS = (None, 30.0, 20.0, 15.0, 10.0)
PERIODS = {"sviluppo_2018_2021": ("2018-01-01", "2022-01-01"), "verifica_2022_2026": ("2022-01-01", "2026-02-01")}


def stats(tr, start_bal):
    if len(tr) == 0:
        return {"trade": 0}
    bal = tr.balance.values
    peak = np.maximum.accumulate(np.r_[start_bal, bal])[:-1]
    dd = np.maximum(peak - tr.equity_low.values, peak - bal) / peak * 100
    mon = tr.groupby(tr.exit_time.dt.to_period("M")).net.sum()
    risk = tr.risk_money / (tr.balance - tr.net) * 100
    return {"trade": int(len(tr)), "finale": round(float(bal[-1]), 1), "dd_max_pct": round(float(dd.max()), 1),
            "pf": round(float(tr.net[tr.net > 0].sum() / max(-tr.net[tr.net < 0].sum(), 1e-9)), 2),
            "vinti_pct": round(float((tr.net > 0).mean() * 100), 1), "mesi_pos_pct": round(float((mon > 0).mean() * 100), 1),
            "rischio_medio_pct": round(float(risk.mean()), 1), "rischio_max_pct": round(float(risk.max()), 1),
            "R_medio": round(float((tr.net / tr.risk_money).mean()), 3)}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    mk = P.market()
    s, tfm = setups(kind="SQZ", N=24, stop="range", stop_k=1.5, regime="filter")
    # distanza ingresso-stop: stop sul lato opposto del range = altezza del range con i buffer (sl_lo - sl_hi);
    # p_hi / p_lo non vanno usati: il filtro di regime mette 1e9 / -1e9 sul lato disattivato
    dist = s.sl_lo - s.sl_hi
    res = {}
    for cn, c in COSTS.items():
        spread = np.full(len(mk.o), c["spread"])
        for cap in CAPS:
            ss = s if cap is None else s[dist <= cap]
            key = f"costi{cn}_stopmax{cap or 'nessuno'}"
            res[key] = {}
            for pn, (a, b) in PERIODS.items():
                x = ss[(ss.bar_time >= a) & (ss.bar_time < b)]
                tr, info = run(mk, x, tf_minutes=tfm, spread=spread, init_bal=116.0, leverage=1000.0, lot_mode=0,
                               fixed_lot=0.01, comm=c["comm"], slip=c["slip"], **EX)
                res[key][pn] = {**stats(tr, 116.0), "conto_morto": bool(info.get("account_dead", False))}
            print(key, json.dumps(res[key]), flush=True)
    (OUT / "oco_100eur.json").write_text(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
