"""FASE 20 — test dell'EA di terzi 'Breakout Retest Pro v2.0' (mql5/Experts/ThirdParty/), tradotto fedelmente.

Regole (input di default): swing high/low con 10 barre per lato (confermato), impulso >= 1,5 ATR14, rottura = 2 chiusure
oltre la neckline, retest = minimo (massimo) entro 0,5 ATR dalla neckline con candela nella direzione e chiusura oltre,
filtro trend chiusura vs SMA50 dello stesso timeframe. Ingresso A MERCATO all'apertura della barra successiva, SL 1,5 ATR,
TP 8 ATR (4 x 2 nel codice), una posizione alla volta. Uscita 'inversione': incrocio EMA8/EMA21 contro la posizione su
barre chiuse (nel codice originale gli altri criteri guardano la barra appena aperta e quasi non scattano).
Varianti: scadenza del retest COME NEL CODICE (mai: bars_since è sempre 0) o COME DICHIARATO (40 barre);
uscita per inversione sì/no. Costi utente A 0,15 $, B 0,27 $. Sviluppo 2010-15, verifica 2016-01/2026.

usage: python python/scripts/phase20_brt_pro.py
"""
import itertools
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
TF = ROOT / "output" / "cache" / "tf"
OUT = ROOT / "output" / "phase20"
L, IMP, CONF, RZ, RB, SLM, TPM = 10, 1.5, 2, 0.5, 40, 1.5, 8.0


def signals(b, expire):
    o, h, l, c = (b[x].values for x in ("open", "high", "low", "close"))
    n = len(b)
    pc = np.r_[c[0], c[:-1]]
    tr = np.maximum(h - l, np.maximum(abs(h - pc), abs(l - pc)))
    atr = pd.Series(tr).ewm(alpha=1 / 14, adjust=False).mean().values      # ATR di MT5 (Wilder)
    sma = pd.Series(c).rolling(50).mean().values
    out = np.zeros(n, np.int64)                                          # segnale alla chiusura della barra i
    bn = sn = 0.0
    bb = sb = False
    bw = sw = False
    bbar = sbar = 0
    for i in range(2 * L + 1, n):
        a = atr[i]
        if not np.isfinite(a) or not np.isfinite(sma[i]):
            continue
        p = i - L                                                        # pivot confermato alla chiusura di i
        if h[p] == h[p - L:p + L + 1].max() and h[p] - l[p] >= a * IMP:
            bn, bb, bw = h[p], False, False
        if l[p] == l[p - L:p + L + 1].min() and h[p] - l[p] >= a * IMP:
            sn, sb, sw = l[p], False, False
        if bn > 0 and not bb and (c[i - CONF + 1:i + 1] > bn).all():
            bb, bw, bbar = True, True, i
        if sn > 0 and not sb and (c[i - CONF + 1:i + 1] < sn).all():
            sb, sw, sbar = True, True, i
        if bw and bn > 0:
            if c[i] > sma[i] and bn - a * RZ <= l[i] <= bn + a * RZ and c[i] > bn and c[i] > o[i] \
                    and (not expire or i - bbar <= RB):
                out[i] = 1
                bw, bn = False, 0.0
            elif expire and i - bbar > RB:
                bw, bn = False, 0.0
        if sw and sn > 0:
            if c[i] < sma[i] and sn - a * RZ <= h[i] <= sn + a * RZ and c[i] < sn and c[i] < o[i] \
                    and (not expire or i - sbar <= RB):
                out[i] = -1 if out[i] == 0 else out[i]
                sw, sn = False, 0.0
            elif expire and i - sbar > RB:
                sw, sn = False, 0.0
    ef = pd.Series(c).ewm(span=8, adjust=False).mean().values
    es = pd.Series(c).ewm(span=21, adjust=False).mean().values
    return out, atr, np.sign(ef - es)


def simulate(b, m1, sig, atr, emad, rev, cost):
    mi = m1.index.values
    mh, ml, mo = m1.high.values, m1.low.values, m1.open.values
    bt = b.index.values
    step = bt[1] - bt[0]
    start = np.searchsorted(mi, bt)                                      # primo M1 di ogni barra
    trades = []
    i = 0
    n = len(b)
    while i < n - 2:
        d = sig[i]
        if d == 0:
            i += 1
            continue
        e_bar = i + 1
        k0 = start[e_bar]
        if k0 >= len(mo):
            break
        px = mo[k0]
        sl, tp = px - d * SLM * atr[i], px + d * TPM * atr[i]
        res, j = None, e_bar
        while j < n - 1 and res is None:
            for k in range(start[j], start[j + 1]):
                if (d > 0 and ml[k] <= sl) or (d < 0 and mh[k] >= sl):
                    res = sl - px if d > 0 else px - sl
                    break
                if (d > 0 and mh[k] >= tp) or (d < 0 and ml[k] <= tp):
                    res = tp - px if d > 0 else px - tp
                    break
            if res is None and rev and emad[j] == -d and emad[j - 1] == d:   # incrocio contro, a barra chiusa
                res = (mo[start[j + 1]] - px) * d
            j += 1
        if res is None:
            break
        trades.append((bt[i], d, (res - cost) / (SLM * atr[i]), res - cost))
        i = j
    return pd.DataFrame(trades, columns=["t", "side", "R", "usd"])


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    m1 = pd.read_parquet(ROOT / "output" / "cache" / "XAUUSD_M1_master.parquet")
    m1 = m1[m1.index >= "2009-10-01"]
    rows = []
    for tfn in ("M5", "M15", "H1"):
        b = pd.read_parquet(TF / f"XAUUSD_{tfn}.parquet")
        b = b[b.index >= "2009-10-01"]
        for expire, rev in itertools.product((False, True), (True, False)):
            sig, atr, emad = signals(b, expire)
            for cn, cost in (("A", 0.15), ("B", 0.27)):
                tr = simulate(b, m1, sig, atr, emad, rev, cost)
                y = pd.to_datetime(tr.t).dt.year
                row = {"tf": tfn, "scadenza_retest": "40 barre" if expire else "mai (come il codice)",
                       "uscita_inversione": rev, "costi": cn, "trade_anno": round(len(tr) / 16.1, 1)}
                for per, (a, bb) in (("sviluppo", (2010, 2015)), ("verifica", (2016, 2026))):
                    m = (y >= a) & (y <= bb)
                    ys = tr[m].groupby(y[m]).R.sum()
                    row.update({f"{per}_n": int(m.sum()), f"{per}_vinti": round(float((tr.usd[m] > 0).mean()), 3),
                                f"{per}_R": round(float(tr.R[m].mean()), 4), f"{per}_anni_pos": f"{int((ys > 0).sum())}/{len(ys)}"})
                rows.append(row)
                print(row, flush=True)
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "brt_pro.csv", index=False)
    (OUT / "brt_pro.json").write_text(json.dumps(rows, indent=1))


if __name__ == "__main__":
    main()
