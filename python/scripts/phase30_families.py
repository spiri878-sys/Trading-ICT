"""FASE 30 — conto 5.000 USC, oro M1 2026: famiglie di bot diverse dal cesto classico.
A riduttore : cesto martingala (tendenza) che, da KR livelli, chiude insieme il primo ordine (perdita) e l'ultimo
              (guadagno) appena la loro somma è >= X $ (per 0,01): il cesto resta corto.
B piramide  : con la tendenza, aggiunge un ordine ogni D $ A FAVORE (lotto x M), chiude tutto quando il prezzo torna
              indietro di R $ dal massimo raggiunto (trailing del cesto).
C zone      : zone recovery: BUY; se scende di Z apre SELL più grande, se risale apre BUY più grande, ecc.; chiude
              tutto quando il prezzo esce dalla zona di T $ (lotti calcolati per chiudere in guadagno).
Unità: $ per 0,01 lotti; deposito 5.000; stop out al 50% del margine con leva 1:1000; commissione 0,04 per 0,01.
Nella barra M1 prima il movimento contrario. Mese per mese da capo, scelta gen-mag, verifica giu-ott.
usage: python python/scripts/phase30_families.py
"""
import itertools
from pathlib import Path

import numba
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DEP = 5000.0


@numba.njit(cache=True)
def sim_reducer(op, hi, lo, cl, sp, buy, sell, bal0, D, G, M, T, KR, X):
    bal = bal0; peak = bal0; mdd = 0.0; nord = 0; eq = bal0
    lots = np.zeros((2, 80)); px = np.zeros((2, 80)); n = np.zeros(2, np.int64); nxt = np.zeros(2)
    lev = np.zeros(2, np.int64)                       # livello raggiunto (per lotto e distanza), anche dopo i tagli
    for i in range(1, hi.size):
        flo = 0.0; marg = 0.0
        for s in range(2):
            d = 1.0 if s == 0 else -1.0
            if n[s] == 0:
                if not (buy[i - 1] if s == 0 else sell[i - 1]):
                    continue
                p0 = op[i] + (sp[i] if d > 0 else 0.0)
                lots[s, 0] = 1.0; px[s, 0] = p0; n[s] = 1; lev[s] = 1; nord += 1; nxt[s] = p0 - d * D
            added = False
            while n[s] < 79 and ((d > 0 and lo[i] <= nxt[s]) or (d < 0 and hi[i] + sp[i] >= nxt[s])):
                k = lev[s]
                lots[s, n[s]] = max(1.0, np.floor(M ** k + 1e-9)); px[s, n[s]] = nxt[s]
                n[s] += 1; lev[s] += 1; added = True; nord += 1
                nxt[s] = nxt[s] - d * D * G ** k
            L = 0.0; W = 0.0
            for k in range(n[s]):
                L += lots[s, k]; W += lots[s, k] * px[s, k]
            avg = W / L
            worst = (lo[i] - avg) * L if d > 0 else (avg - (hi[i] + sp[i])) * L
            if added:
                hit = (d > 0 and cl[i] >= avg + T) or (d < 0 and cl[i] + sp[i] <= avg - T)
            else:
                hit = (d > 0 and hi[i] >= avg + T) or (d < 0 and lo[i] + sp[i] <= avg - T)
            if hit:
                bal += T * L - 0.04 * L; n[s] = 0
                continue
            # riduttore sul prezzo di chiusura della barra
            if KR > 0 and n[s] >= KR:
                pc = cl[i] + (sp[i] if d < 0 else 0.0)
                pf = (pc - px[s, 0]) * d * lots[s, 0]
                pl = (pc - px[s, n[s] - 1]) * d * lots[s, n[s] - 1]
                if pf + pl >= X * lots[s, 0]:
                    bal += pf + pl - 0.04 * (lots[s, 0] + lots[s, n[s] - 1])
                    for k in range(n[s] - 2):
                        lots[s, k] = lots[s, k + 1]; px[s, k] = px[s, k + 1]
                    n[s] -= 2
                    if n[s] == 0:
                        continue
                    L = 0.0; W = 0.0
                    for k in range(n[s]):
                        L += lots[s, k]; W += lots[s, k] * px[s, k]
                    avg = W / L
                    worst = (lo[i] - avg) * L if d > 0 else (avg - (hi[i] + sp[i])) * L
            flo += min(worst, 0.0)
            marg += L * cl[i] / 1000.0
        eq = bal + flo
        if eq > peak:
            peak = eq
        if (peak - eq) / peak > mdd:
            mdd = (peak - eq) / peak
        if marg > 0 and eq < 0.5 * marg:
            return eq, 1.0, nord, 1
    return eq, mdd, nord, 0


@numba.njit(cache=True)
def sim_pyramid(op, hi, lo, cl, sp, buy, sell, bal0, D, M, R, NMAX):
    bal = bal0; peak = bal0; mdd = 0.0; nord = 0; eq = bal0
    for_side = np.zeros(2)
    lots = np.zeros((2, 64)); px = np.zeros((2, 64)); n = np.zeros(2, np.int64); nxt = np.zeros(2); ext = np.zeros(2)
    for i in range(1, hi.size):
        flo = 0.0; marg = 0.0
        for s in range(2):
            d = 1.0 if s == 0 else -1.0
            if n[s] == 0:
                if not (buy[i - 1] if s == 0 else sell[i - 1]):
                    continue
                p0 = op[i] + (sp[i] if d > 0 else 0.0)
                lots[s, 0] = 1.0; px[s, 0] = p0; n[s] = 1; nord += 1; nxt[s] = p0 + d * D; ext[s] = p0
            # prima il ritorno contro (prudente): trailing dal massimo registrato fino alla barra prima
            back = (ext[s] - lo[i]) if d > 0 else ((hi[i] + sp[i]) - ext[s])
            L = 0.0; W = 0.0
            for k in range(n[s]):
                L += lots[s, k]; W += lots[s, k] * px[s, k]
            if back >= R:
                exitp = min(ext[s] - R, op[i]) if d > 0 else max(ext[s] + R, op[i] + sp[i])
                bal += (exitp - W / L) * d * L - 0.04 * L; n[s] = 0
                continue
            while n[s] < NMAX and ((d > 0 and hi[i] >= nxt[s]) or (d < 0 and lo[i] + sp[i] <= nxt[s])):
                k = n[s]
                lots[s, k] = max(1.0, np.floor(M ** k + 1e-9)); px[s, k] = nxt[s] + (sp[i] if d > 0 else -sp[i]); n[s] += 1; nord += 1
                L += lots[s, k]; W += lots[s, k] * px[s, k]
                nxt[s] = nxt[s] + d * D
            ext[s] = max(ext[s], hi[i]) if d > 0 else min(ext[s], lo[i] + sp[i])
            # prudente: se nella barra ha aggiunto livelli e il minimo (massimo per i SELL) è oltre il trailing,
            # si assume prima la salita e poi la discesa: esce al livello del trailing
            badd = (ext[s] - lo[i]) if d > 0 else ((hi[i] + sp[i]) - ext[s])
            if badd >= R:
                exitp = ext[s] - d * R
                bal += (exitp - W / L) * d * L - 0.04 * L; n[s] = 0
                continue
            v = (lo[i] - W / L) * L if d > 0 else (W / L - (hi[i] + sp[i])) * L
            flo += min(v, 0.0)
            marg += L * cl[i] / 1000.0
        eq = bal + flo
        if eq > peak:
            peak = eq
        if (peak - eq) / peak > mdd:
            mdd = (peak - eq) / peak
        if marg > 0 and eq < 0.5 * marg:
            return eq, 1.0, nord, 1
    return eq, mdd, nord, 0


@numba.njit(cache=True)
def sim_zone(op, hi, lo, cl, sp, buy, sell, bal0, Z, T, NMAX):
    """Una sola sequenza alla volta. BUY a p0 (o SELL se il segnale è sell). Zona [p0-Z, p0]; uscita a p0+T (sopra) o
    p0-Z-T (sotto). Lotti scelti perché all'uscita il netto sia +T x lotto iniziale."""
    bal = bal0; peak = bal0; mdd = 0.0; nord = 0; eq = bal0
    active = False
    nb = 0; ns = 0
    lb = 0.0; ls = 0.0; wb = 0.0; ws = 0.0
    top = 0.0; bot = 0.0; last = 0
    for i in range(1, hi.size):
        if not active:
            if buy[i - 1] or sell[i - 1]:
                p0 = op[i]
                active = True
                if buy[i - 1]:
                    top = p0 + sp[i]; bot = top - Z
                    lb = 1.0; wb = top; ls = 0.0; ws = 0.0; last = 1
                else:
                    bot = p0; top = bot + Z
                    ls = 1.0; ws = bot; lb = 0.0; wb = 0.0; last = -1
                nb = 1; nord += 1
        if active:
            # uscita sopra (BUY vincono) o sotto (SELL vincono): prima il lato contrario all'ultima posizione
            up = top + T; dn = bot - T
            done = False
            for side in (0, 1):
                first_dn = last == 1
                if (side == 0) == first_dn:
                    if lo[i] + sp[i] <= dn:
                        pnl = (0.0 if lb == 0 else (dn - wb / lb) * lb) + (0.0 if ls == 0 else (ws / ls - (dn + sp[i])) * ls)
                        bal += pnl - 0.04 * (lb + ls); done = True; break
                else:
                    if hi[i] >= up:
                        pnl = (0.0 if lb == 0 else (up - wb / lb) * lb) + (0.0 if ls == 0 else (ws / ls - (up + sp[i])) * ls)
                        bal += pnl - 0.04 * (lb + ls); done = True; break
            if done:
                active = False
                lb = 0.0; ls = 0.0; wb = 0.0; ws = 0.0
            else:
                # inversione: se il prezzo attraversa l'altro bordo, apre il lato opposto con il lotto che porta in
                # guadagno all'uscita da quel lato
                if last == 1 and lo[i] <= bot and nb < NMAX:
                    # serve: (ws+ x*bot)/... => profitto sotto: ls*(ws/ls - dn) + x*(bot - dn) - lb*(wb/lb - dn) >= T
                    need = T + lb * (wb / lb - (bot - T)) - (0.0 if ls == 0 else ls * (ws / ls - (bot - T)))
                    x = max(1.0, np.ceil(need / T))
                    ls += x; ws += x * bot; last = -1; nb += 1; nord += 1
                elif last == -1 and hi[i] + sp[i] >= top and nb < NMAX:
                    need = T + ls * ((top + T) - ws / ls) - (0.0 if lb == 0 else lb * ((top + T) - wb / lb))
                    x = max(1.0, np.ceil(need / T))
                    lb += x; wb += x * top; last = 1; nb += 1; nord += 1
        flo = 0.0; marg = 0.0
        if active:
            vb = 0.0 if lb == 0 else min((lo[i] - wb / lb) * lb, (hi[i] - wb / lb) * lb)
            vs = 0.0 if ls == 0 else min((ws / ls - (hi[i] + sp[i])) * ls, (ws / ls - (lo[i] + sp[i])) * ls)
            flo = min(vb + vs, 0.0)
            marg = max(lb, ls) * cl[i] / 1000.0
        eq = bal + flo
        if eq > peak:
            peak = eq
        if (peak - eq) / peak > mdd:
            mdd = (peak - eq) / peak
        if marg > 0 and eq < 0.5 * marg:
            return eq, 1.0, nord, 1
    return eq, mdd, nord, 0


def main():
    m = pd.read_parquet(ROOT / "output" / "cache" / "XAUUSD_M1_axi_2026.parquet")
    op, hi, lo, cl = (m[c].values.astype(float) for c in ("open", "high", "low", "close"))
    sp = m.spread.values * 0.01
    h5, l5 = pd.Series(hi), pd.Series(lo)
    atr = (h5 - l5).rolling(14).mean().bfill()
    tr = cl > pd.Series(cl).ewm(span=12000, adjust=False).mean().values
    calm = ((h5.rolling(15).max() - l5.rolling(15).min()) < 6 * atr).values
    entries = {"tendenza": ((tr & calm).astype(np.bool_), (~tr & calm).astype(np.bool_)),
               "BUY+SELL": (calm.astype(np.bool_), calm.astype(np.bool_))}
    mon = m.index.to_period("M").values
    cuts = [np.where(mon == p)[0] for p in pd.unique(mon)]

    def evaluate(fn, b, s, args):
        res = []
        for sel in cuts:
            a, z = sel[0], sel[-1] + 1
            r = fn(op[a:z], hi[a:z], lo[a:z], cl[a:z], sp[a:z], b[a:z], s[a:z], DEP, *args)
            res.append((r[3], -1.0 if r[3] else r[0] / DEP - 1, r[1], r[2]))
        return dict(saltati_A=sum(x[0] for x in res[:5]), resa_A=round(sum(x[1] for x in res[:5]) * 100),
                    saltati_B=sum(x[0] for x in res[5:]), resa_B=round(sum(x[1] for x in res[5:]) * 100),
                    mesi=" ".join("X" if x[0] else f"{x[1] * 100:+.0f}" for x in res),
                    ordini_mese=round(np.mean([x[3] for x in res])))

    rows = []
    for en, D, G, M, T, KR, X in itertools.product(entries, (2.0, 3.0, 5.0, 8.0), (1.0, 1.2, 1.3), (1.3, 1.5, 2.0),
                                                   (0.5, 1.0, 2.0), (3, 4, 5, 6), (0.0, 1.0, 3.0)):
        b, s = entries[en]
        rows.append(dict(famiglia="A riduttore", entrata=en, impostazioni=f"D{D} G{G} M{M} TP{T} da{KR} X{X}",
                         **evaluate(sim_reducer, b, s, (D, G, M, T, KR, X))))
    for en, D, M, R, N in itertools.product(entries, (0.5, 1.0, 2.0, 3.0, 5.0), (1.0, 1.2, 1.5), (1.0, 2.0, 3.0, 5.0, 8.0),
                                            (3, 5, 10, 20)):
        b, s = entries[en]
        rows.append(dict(famiglia="B piramide", entrata=en, impostazioni=f"D{D} M{M} R{R} max{N}",
                         **evaluate(sim_pyramid, b, s, (D, M, R, N))))
    for en, Z, T, N in itertools.product(entries, (1.0, 2.0, 3.0, 5.0, 8.0), (1.0, 2.0, 3.0, 5.0, 8.0), (4, 6, 8, 12)):
        b, s = entries[en]
        rows.append(dict(famiglia="C zone recovery", entrata=en, impostazioni=f"Z{Z} T{T} max{N}",
                         **evaluate(sim_zone, b, s, (Z, T, N))))
    df = pd.DataFrame(rows)
    out = ROOT / "output" / "phase30"
    out.mkdir(parents=True, exist_ok=True)
    df.to_csv(out / "famiglie.csv", index=False)
    pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 80)
    df["saltati"] = df.saltati_A + df.saltati_B
    df["resa"] = df.resa_A + df.resa_B
    for f, g in df.groupby("famiglia"):
        print(f"\n== {f}: {len(g)} prove; scelta su gen-mag (meno mesi bruciati, poi più resa), poi verifica giu-ott")
        print(g.sort_values(["saltati_A", "resa_A"], ascending=[True, False]).head(8).to_string(index=False))


if __name__ == "__main__":
    main()
