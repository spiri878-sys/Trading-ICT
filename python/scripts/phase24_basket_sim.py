"""FASE 24 — simulazione di un cesto martingala/griglia sull'oro M1 (barre Axi 2026 dell'utente), per scegliere un set.
Modello generico (il codice dell'EA 'TopBottom Martingale Basket' non è disponibile): un cesto BUY e uno SELL
indipendenti, sempre attivi (H24, nessun filtro notizie); primo ordine subito; livello successivo quando il prezzo va
contro di D $ (distanza x1,1 a ogni livello, come FixedDistMultiplier=1.1); lotto x m (m=1 lotto fisso); max N livelli;
il cesto chiude quando il prezzo torna T $ oltre il prezzo medio; stop di sicurezza se la perdita aperta del cesto supera
S% del saldo. Nella stessa barra M1 conta prima il movimento contrario (prudente); commissione 0,04 $
per 0,01 lotti. Spread dal file del broker. Conto 5.000 (USD), lotto iniziale 0,01 (1 $ per $ di movimento per 0,01 lotti).

usage: python python/scripts/phase24_basket_sim.py
"""
import itertools
import json
from pathlib import Path

import numba
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]


@numba.njit(cache=True)
def sim(hi, lo, cl, sp, D, mult, N, T, S, bal0):
    bal = bal0
    peak = bal0
    mdd = 0.0
    nclosed = 0
    nstop = 0
    for side in (1, -1):
        pass
    # stato dei due cesti
    lots = np.zeros((2, 64)); px = np.zeros((2, 64)); n = np.zeros(2, np.int64); nxt = np.zeros(2)
    dist = np.zeros(2)
    for i in range(hi.size):
        float_tot = 0.0
        for s in range(2):
            d = 1.0 if s == 0 else -1.0
            if n[s] == 0:                                   # apre il primo ordine
                p0 = cl[i] + (sp[i] if d > 0 else 0.0)
                lots[s, 0] = 1.0; px[s, 0] = p0; n[s] = 1; dist[s] = D; nxt[s] = p0 - d * D
                continue
            # nuovi livelli (prudente: nella barra prima il movimento contrario, poi l'eventuale chiusura)
            added = False
            while n[s] < N and ((d > 0 and lo[i] <= nxt[s]) or (d < 0 and hi[i] + sp[i] >= nxt[s])):
                k = n[s]
                lots[s, k] = lots[s, k - 1] * mult
                px[s, k] = nxt[s]
                n[s] += 1
                added = True
                dist[s] *= 1.1
                nxt[s] = nxt[s] - d * dist[s]
            L = 0.0; W = 0.0
            for k in range(n[s]):
                L += lots[s, k]; W += lots[s, k] * px[s, k]
            avg = W / L
            # perdita aperta al peggio della barra (unità: $ per 0,01 lotti)
            worst = (lo[i] - avg) * L if d > 0 else (avg - (hi[i] + sp[i])) * L
            if added:      # livello aggiunto in questa barra: chiude solo se ci arriva anche la chiusura della barra
                tp_hit = (d > 0 and cl[i] >= avg + T) or (d < 0 and cl[i] + sp[i] <= avg - T)
            else:
                tp_hit = (d > 0 and hi[i] >= avg + T) or (d < 0 and lo[i] + sp[i] <= avg - T)
            if worst < -S * bal:                            # stop di sicurezza
                bal += -S * bal - 0.04 * L; n[s] = 0; nstop += 1
                continue
            if tp_hit:
                bal += T * L - 0.04 * L; n[s] = 0; nclosed += 1      # commissione 0,04 $ per 0,01 lotti
                continue
            float_tot += min(worst, 0.0)
        eq = bal + float_tot
        if eq > peak:
            peak = eq
        if peak > 0 and (peak - eq) / peak > mdd:
            mdd = (peak - eq) / peak
        if eq <= 0:
            return bal, 1.0, nclosed, nstop, 1
    return bal, mdd, nclosed, nstop, 0


def main():
    m = pd.read_parquet(ROOT / "output" / "cache" / "XAUUSD_M1_axi_2026.parquet")
    hi, lo, cl = (m[c].values.astype(float) for c in ("high", "low", "close"))
    sp = m.spread.values * 0.01
    rows = []
    for D, mult, N, T, S in itertools.product((3.0, 10.0, 20.0, 30.0), (1.0, 1.2, 1.5), (5, 8, 12, 20), (2.0, 5.0),
                                             (0.10, 0.20, 0.30, 5.0)):
        bal, mdd, nc, ns, dead = sim(hi, lo, cl, sp, D, mult, N, T, S, 5000.0)
        rows.append(dict(distanza_usd=D, moltiplicatore=mult, max_livelli=N, tp_usd=T, stop_cesto_pct=S * 100,
                         saldo_finale=round(bal, 0), calo_max_pct=round(mdd * 100, 1), cesti_chiusi_tp=nc,
                         stop_scattati=ns, conto_azzerato=bool(dead)))
    df = pd.DataFrame(rows)
    out = ROOT / "output" / "phase24"
    out.mkdir(parents=True, exist_ok=True)
    df.to_csv(out / "basket_grid_2026.csv", index=False)
    ok = df[~df.conto_azzerato].copy()
    ok["profitto_su_calo"] = (ok.saldo_finale - 5000) / (ok.calo_max_pct.clip(lower=1) / 100 * 5000)
    print("azzerati:", int(df.conto_azzerato.sum()), "su", len(df))
    print(ok.sort_values("profitto_su_calo", ascending=False).head(15).to_string(index=False))
    print(df[(df.moltiplicatore == 1.5) & (df.distanza_usd == 3.0) & (df.max_livelli == 20)].to_string(index=False))


if __name__ == "__main__":
    main()
