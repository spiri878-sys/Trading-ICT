"""FASE 21 — 'migliorare finché è profittevole' l'EA Breakout Retest Pro, in modo onesto: ampia griglia di varianti e
SCELTA WALK-FORWARD (ogni anno la variante migliore dei 3 anni precedenti, almeno 60 trade, usata nell'anno dopo).

Griglia: TF {M15, H1} x swing {5, 10, 20} x impulso {1; 1,5; 2,5 ATR} x zona retest {0,3; 0,5; 1 ATR}
x filtro {SMA50 del TF, regime D1+H4 (EMA50, barre chiuse), nessuno} x lati {entrambi, solo acquisti}
x SL {1; 1,5; 2,5 ATR} x TP {2; 4; 8 ATR}. Ingresso a mercato all'apertura della barra dopo il segnale, una posizione
alla volta, chiusura dopo 3 giorni se né SL né TP. Retest valido 40 barre (come dichiarato dall'EA). Costi utente A/B.

usage: python python/scripts/phase21_brt_walkforward.py
"""
import itertools
import json
import sys
from pathlib import Path

import numba
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import phase18_sweep_pending as F18  # noqa: E402  (htf_trend: regime D1+H4 su barre chiuse)

ROOT = Path(__file__).resolve().parents[2]
TF = ROOT / "output" / "cache" / "tf"
OUT = ROOT / "output" / "phase21"
YEARS = list(range(2010, 2027))


def signals(o, h, l, c, atr, L, imp, rz, rb=40, conf=2):
    """Segnali grezzi breakout+retest (senza filtro trend): +1/-1 alla chiusura della barra."""
    n = len(c)
    out = np.zeros(n, np.int64)
    hmax = pd.Series(h).rolling(2 * L + 1).max().values           # finestra [p-L, p+L] che termina in i
    lmin = pd.Series(l).rolling(2 * L + 1).min().values
    bn = sn = 0.0
    bb = sb = bw = sw = False
    bbar = sbar = 0
    for i in range(2 * L + 1, n):
        a = atr[i]
        p = i - L
        if h[p] == hmax[i] and h[p] - l[p] >= a * imp:
            bn, bb, bw = h[p], False, False
        if l[p] == lmin[i] and h[p] - l[p] >= a * imp:
            sn, sb, sw = l[p], False, False
        if bn > 0 and not bb and c[i] > bn and c[i - 1] > bn:
            bb, bw, bbar = True, True, i
        if sn > 0 and not sb and c[i] < sn and c[i - 1] < sn:
            sb, sw, sbar = True, True, i
        if bw:
            if i - bbar > rb:
                bw, bn = False, 0.0
            elif bn - a * rz <= l[i] <= bn + a * rz and c[i] > bn and c[i] > o[i]:
                out[i] = 1
                bw, bn = False, 0.0
        if sw:
            if i - sbar > rb:
                sw, sn = False, 0.0
            elif sn - a * rz <= h[i] <= sn + a * rz and c[i] < sn and c[i] < o[i] and out[i] == 0:
                out[i] = -1
                sw, sn = False, 0.0
    return out


@numba.njit(cache=True)
def run(mo, mh, ml, mc, e_idx, side, sld, tpd, hold):
    m = e_idx.size
    res = np.zeros(m)
    used = np.zeros(m, np.bool_)
    free = 0
    for q in range(m):
        e = e_idx[q]
        if e < free or e >= mo.size - 1:
            continue
        px = mo[e]
        sl = px - side[q] * sld[q]
        tp = px + side[q] * tpd[q]
        end = min(e + hold, mo.size - 1)
        r = 0.0
        done = False
        j = e
        while j < end:
            if side[q] > 0:
                if ml[j] <= sl:
                    r, done = -sld[q], True
                elif mh[j] >= tp:
                    r, done = tpd[q], True
            else:
                if mh[j] >= sl:
                    r, done = -sld[q], True
                elif ml[j] <= tp:
                    r, done = tpd[q], True
            if done:
                break
            j += 1
        if not done:
            r = (mc[end - 1] - px) * side[q]
            j = end - 1
        res[q] = r
        used[q] = True
        free = j + 1
    return res, used


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    m1 = pd.read_parquet(ROOT / "output" / "cache" / "XAUUSD_M1_master.parquet")
    m1 = m1[m1.index >= "2009-10-01"]
    mo, mh, ml, mc = (m1[x].values.astype(float) for x in ("open", "high", "low", "close"))
    myear = m1.index.year.values
    d1 = pd.read_parquet(TF / "XAUUSD_D1.parquet")
    h4 = pd.read_parquet(TF / "XAUUSD_H4.parquet")
    cfgs, recs = [], []
    for tfn, tfm in (("M15", 15), ("H1", 60)):
        b = pd.read_parquet(TF / f"XAUUSD_{tfn}.parquet")
        b = b[b.index >= "2009-10-01"]
        o, h, l, c = (b[x].values for x in ("open", "high", "low", "close"))
        pc = np.r_[c[0], c[:-1]]
        atr = pd.Series(np.maximum(h - l, np.maximum(abs(h - pc), abs(l - pc)))).ewm(alpha=1 / 14, adjust=False).mean().values
        sma = pd.Series(c).rolling(50).mean().values
        tclose = b.index + pd.Timedelta(minutes=tfm)
        reg = F18.htf_trend(tclose, d1, h4)
        eidx_all = np.searchsorted(m1.index.values, tclose.values).astype(np.int64)   # ingresso: apertura barra dopo
        for L, imp, rz in itertools.product((5, 10, 20), (1.0, 1.5, 2.5), (0.3, 0.5, 1.0)):
            sig = signals(o, h, l, c, atr, L, imp, rz)
            for filt, sides in itertools.product(("SMA50", "REGIME", "NESSUNO"), ("ENTRAMBI", "SOLO_BUY")):
                ok = sig != 0
                if filt == "SMA50":
                    ok &= np.where(sig > 0, c > sma, c < sma)
                elif filt == "REGIME":
                    ok &= reg == sig
                if sides == "SOLO_BUY":
                    ok &= sig > 0
                idx = np.flatnonzero(ok)
                if len(idx) < 150:
                    continue
                for slm, tpm in itertools.product((1.0, 1.5, 2.5), (2.0, 4.0, 8.0)):
                    a = atr[idx]
                    r, used = run(mo, mh, ml, mc, eidx_all[idx], sig[idx].astype(np.int64), slm * a, tpm * a, 3 * 1440)
                    r, a2 = r[used], (slm * a)[used]
                    yr = myear[np.minimum(eidx_all[idx][used], len(myear) - 1)]
                    cid = len(cfgs)
                    cfgs.append(dict(tf=tfn, swing=L, impulso=imp, zona=rz, filtro=filt, lati=sides, sl=slm, tp=tpm))
                    for y in YEARS:
                        mk = yr == y
                        recs.append((cid, y, int(mk.sum()), float(((r[mk] - 0.15) / a2[mk]).sum()),
                                     float(((r[mk] - 0.27) / a2[mk]).sum())))
            print(tfn, L, imp, rz, "configurazioni", len(cfgs), flush=True)
    rec = pd.DataFrame(recs, columns=["cfg", "anno", "n", "sumR_A", "sumR_B"])
    rec.to_parquet(OUT / "per_anno.parquet")
    pd.DataFrame(cfgs).to_csv(OUT / "configurazioni.csv", index_label="cfg")
    n = rec.pivot(index="cfg", columns="anno", values="n").fillna(0)
    sa = rec.pivot(index="cfg", columns="anno", values="sumR_A").fillna(0)
    sb = rec.pivot(index="cfg", columns="anno", values="sumR_B").fillna(0)
    chain = []
    for y in range(2013, 2027):
        past = [y - 3, y - 2, y - 1]
        npast = n[past].sum(axis=1)
        score = sa[past].sum(axis=1) / npast.replace(0, np.nan)
        score[npast < 60] = np.nan
        best = score.idxmax()
        chain.append({"anno": y, "scelta": cfgs[best], "R_passato": round(float(score[best]), 3), "n": int(n.loc[best, y]),
                      "somma_R_A": round(float(sa.loc[best, y]), 2), "somma_R_B": round(float(sb.loc[best, y]), 2)})
        print(chain[-1], flush=True)
    tn = sum(x["n"] for x in chain)
    dev = sa[list(range(2010, 2016))].sum(axis=1) / n[list(range(2010, 2016))].sum(axis=1)
    chk = sa[list(range(2016, 2027))].sum(axis=1) / n[list(range(2016, 2027))].sum(axis=1)
    summ = {"configurazioni": len(cfgs), "positive_entrambi_periodi_A": int(((dev > 0) & (chk > 0)).sum()),
            "catena": {"trade": tn, "R_medio_A": round(sum(x["somma_R_A"] for x in chain) / max(tn, 1), 4),
                       "R_medio_B": round(sum(x["somma_R_B"] for x in chain) / max(tn, 1), 4),
                       "anni_pos_A": f"{sum(x['somma_R_A'] > 0 for x in chain)}/{len(chain)}"}, "per_anno": chain}
    (OUT / "walkforward.json").write_text(json.dumps(summ, indent=1, default=str))
    print(json.dumps({k: v for k, v in summ.items() if k != "per_anno"}, indent=1))


if __name__ == "__main__":
    main()
