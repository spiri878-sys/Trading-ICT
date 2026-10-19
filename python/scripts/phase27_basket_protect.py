"""FASE 27 — cesto martingala M1: come non bruciare il conto restando aggressivi.
Base = set MacchinaDaGuerra (tendenza EMA200 H1 + niente strappi, distanza 1 $ x1,3, lotto x1,5, TP 3 $).
Protezioni provate (una per volta e insieme):
  LIV  : livelli massimi K; oltre l'ultimo livello, dopo un'altra distanza, il cesto si chiude (perdita del cesto,
         non del conto);
  GIRO : se il cesto ha almeno KF livelli e la tendenza H1 gira contro di lui, si chiude;
  COPRI: hedging: al livello KH apre una posizione opposta grande quanto tutto il cesto (blocca la perdita); la
         copertura si chiude quando il prezzo torna indietro di R $ dal suo estremo, poi il cesto riprende.
Mese per mese da capo (deposito 100.000 = conto sotto pressione, e 500.000), stop out al 50% del margine (1:1000).
usage: python python/scripts/phase27_basket_protect.py
"""
import itertools
from pathlib import Path

import numba
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]


@numba.njit(cache=True)
def sim(op, hi, lo, cl, sp, tr, buy, sell, bal0, D, G, T, M, KMAX, KF, KH, R):
    bal = bal0; peak = bal0; mdd = 0.0; nord = 0; nstop = 0
    lots = np.zeros((2, 64)); px = np.zeros((2, 64)); n = np.zeros(2, np.int64); nxt = np.zeros(2)
    hl = np.zeros(2); hp = np.zeros(2); hx = np.zeros(2)          # copertura: lotti, prezzo, estremo
    for i in range(1, hi.size):
        flo = 0.0; marg = 0.0
        for s in range(2):
            d = 1.0 if s == 0 else -1.0
            if n[s] == 0:
                if not (buy[i - 1] if s == 0 else sell[i - 1]):
                    continue
                p0 = op[i] + (sp[i] if d > 0 else 0.0)
                lots[s, 0] = 1.0; px[s, 0] = p0; n[s] = 1; nord += 1; nxt[s] = p0 - d * D
            L = 0.0; W = 0.0
            for k in range(n[s]):
                L += lots[s, k]; W += lots[s, k] * px[s, k]
            # copertura attiva: il cesto è congelato finché il prezzo non rimbalza di R dall'estremo
            if hl[s] > 0:
                hx[s] = min(hx[s], lo[i]) if d > 0 else max(hx[s], hi[i] + sp[i])
                back = (cl[i] - hx[s]) if d > 0 else (hx[s] - cl[i] - sp[i])
                if back >= R:                                       # chiude la copertura
                    exitp = cl[i] + (sp[i] if d > 0 else 0.0)
                    bal += (hp[s] - exitp) * d * hl[s] - 0.04 * hl[s]
                    hl[s] = 0.0
                    nxt[s] = cl[i] - d * D * G ** (n[s] - 1)        # la griglia riparte da qui
                else:
                    hv = (hp[s] - (hi[i] + sp[i])) * hl[s] if d > 0 else ((lo[i] + sp[i]) - hp[s]) * hl[s]
                    worst = (lo[i] - W / L) * L if d > 0 else (W / L - (hi[i] + sp[i])) * L
                    flo += min(worst + hv, 0.0)
                    marg += max(L, hl[s]) * cl[i] / 1000.0
                    continue
            added = False
            while (d > 0 and lo[i] <= nxt[s]) or (d < 0 and hi[i] + sp[i] >= nxt[s]):
                if n[s] >= KMAX:                                    # oltre l'ultimo livello: chiude il cesto
                    exitp = nxt[s]
                    bal += (exitp - W / L) * d * L - 0.04 * L
                    n[s] = 0; nstop += 1
                    break
                k = n[s]
                lots[s, k] = max(1.0, np.floor(M ** k + 1e-9)); px[s, k] = nxt[s]; n[s] += 1; added = True; nord += 1
                nxt[s] = nxt[s] - d * D * G ** k
                L += lots[s, k]; W += lots[s, k] * px[s, k]
                if KH > 0 and n[s] >= KH and hl[s] == 0:            # hedging: blocca tutto il cesto
                    hl[s] = L; hp[s] = px[s, k] - (sp[i] if d > 0 else -sp[i]) * 0.0
                    hx[s] = px[s, k]
                    break
            if n[s] == 0:
                continue
            avg = W / L
            if hl[s] > 0:
                worst = (lo[i] - avg) * L if d > 0 else (avg - (hi[i] + sp[i])) * L
                flo += min(worst, 0.0) + 0.0
                marg += L * cl[i] / 1000.0
                continue
            if KF > 0 and n[s] >= KF and ((d > 0 and not tr[i - 1]) or (d < 0 and tr[i - 1])):
                bal += (cl[i] - avg) * d * L - (sp[i] * L if d < 0 else 0.0) - 0.04 * L
                n[s] = 0; nstop += 1
                continue
            worst = (lo[i] - avg) * L if d > 0 else (avg - (hi[i] + sp[i])) * L
            if added:
                hit = (d > 0 and cl[i] >= avg + T) or (d < 0 and cl[i] + sp[i] <= avg - T)
            else:
                hit = (d > 0 and hi[i] >= avg + T) or (d < 0 and lo[i] + sp[i] <= avg - T)
            if hit:
                bal += T * L - 0.04 * L; n[s] = 0
                continue
            flo += min(worst, 0.0)
            marg += L * cl[i] / 1000.0
        eq = bal + flo
        if eq > peak:
            peak = eq
        if (peak - eq) / peak > mdd:
            mdd = (peak - eq) / peak
        if marg > 0 and eq < 0.5 * marg:
            return eq, 1.0, nord, nstop, 1
    for s in range(2):                                              # fine periodo: valuta le posizioni aperte
        if n[s] > 0:
            L = 0.0; W = 0.0
            for k in range(n[s]):
                L += lots[s, k]; W += lots[s, k] * px[s, k]
            d = 1.0 if s == 0 else -1.0
            bal += (cl[-1] - W / L) * d * L
            if hl[s] > 0:
                bal += (hp[s] - cl[-1]) * d * hl[s]
    return bal, mdd, nord, nstop, 0


def main():
    m = pd.read_parquet(ROOT / "output" / "cache" / "XAUUSD_M1_axi_2026.parquet")
    op, hi, lo, cl = (m[c].values.astype(float) for c in ("open", "high", "low", "close"))
    sp = m.spread.values * 0.01
    h5, l5 = pd.Series(hi), pd.Series(lo)
    atr = (h5 - l5).rolling(14).mean().bfill()
    tr = cl > pd.Series(cl).ewm(span=12000, adjust=False).mean().values
    calm = ((h5.rolling(15).max() - l5.rolling(15).min()) < 6 * atr).values
    b, s = (tr & calm).astype(np.bool_), (~tr & calm).astype(np.bool_)
    mon = m.index.to_period("M").values
    cuts = [np.where(mon == p)[0] for p in pd.unique(mon)]
    split = 5                                                        # gen-mag scelta, giu-ott verifica
    rows = []
    variants = [("nessuna", 99, 0, 0, 0.0)]
    variants += [(f"LIV {k}", k, 0, 0, 0.0) for k in (8, 10, 12, 14, 16)]
    variants += [(f"GIRO da {k}", 99, k, 0, 0.0) for k in (4, 6, 8, 10)]
    variants += [(f"COPRI {k} R{r}", 99, 0, k, r) for k in (8, 10, 12) for r in (2.0, 5.0, 10.0)]
    variants += [(f"LIV {k} + GIRO da {f}", k, f, 0, 0.0) for k in (12, 14) for f in (6, 8)]
    for dep, T, (name, KMAX, KF, KH, R) in itertools.product((100000.0, 500000.0), (2.0, 3.0), variants):
        res = []
        for sel in cuts:
            a, z = sel[0], sel[-1] + 1
            bal, mdd, no, ns, dead = sim(op[a:z], hi[a:z], lo[a:z], cl[a:z], sp[a:z], tr[a:z], b[a:z], s[a:z], dep,
                                         1.0, 1.3, T, 1.5, KMAX, KF, KH, R)
            res.append((dead, -1.0 if dead else bal / dep - 1, mdd, no, ns))
        def part(rr):
            return sum(r[0] for r in rr), round(sum(r[1] for r in rr) * 100)
        sa, ra = part(res[:split]); sb, rb = part(res[split:])
        rows.append(dict(deposito=int(dep), tp=T, protezione=name, saltati_genmag=sa, resa_genmag=ra,
                         saltati_giuott=sb, resa_giuott=rb, calo_max=round(max(r[2] for r in res) * 100),
                         ordini_mese=round(np.mean([r[3] for r in res])), cesti_chiusi_in_perdita_mese=round(np.mean([r[4] for r in res]))))
    df = pd.DataFrame(rows)
    out = ROOT / "output" / "phase27"
    out.mkdir(parents=True, exist_ok=True)
    df.to_csv(out / "protezioni.csv", index=False)
    pd.set_option("display.width", 250)
    print(df.to_string(index=False))


if __name__ == "__main__":
    main()
