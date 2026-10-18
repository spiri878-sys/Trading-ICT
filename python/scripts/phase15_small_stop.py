"""FASE 15 — conto da 100 EUR sull'oro: strategie con STOP PICCOLO in dollari (0,01 lotti: 1 $ di movimento = 1 $).

Domanda: con stop fisso di 2-8 $ (rischio 2-7% di 116 $) esiste un ingresso che guadagna dopo i costi?
Ingressi (decisi sulla chiusura della barra, ingresso all'apertura della successiva, un trade alla volta, max 1 al giorno):
  T1 trend D1 (close > EMA50 D1) + rottura del massimo/minimo delle ultime 20 barre H1
  T2 trend D1 + ritracciamento: H1 chiude contro il trend dopo che H4 ha rotto il Donchian 20 nella direzione del trend
  T3 rottura del range asiatico (00-07 server) nella direzione del trend D1, alle 08-11
  R  ingresso casuale nella direzione del trend D1 (riferimento)
Uscita: stop fisso S $, target k*S, oppure chiusura dopo 24 ore. Se stop e target nella stessa barra M1: conta lo stop.
Costi: spread 0,30 + slippage 0,05 + commissione 0,035 = 0,385 $ a trade (scenario C1 del progetto).
Periodi: sviluppo 2010-2015, verifica 2016-2026/01. Una configurazione vale solo se positiva in ENTRAMBI.

usage: python python/scripts/phase15_small_stop.py
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
TF = ROOT / "output" / "cache" / "tf"
OUT = ROOT / "output" / "phase15"
COST = 0.385
STOPS = (2.0, 3.0, 5.0, 8.0)
KS = (1.0, 2.0, 3.0, 5.0)
HOLD = 24 * 60


def load():
    m1 = pd.read_parquet(ROOT / "output" / "cache" / "XAUUSD_M1_master.parquet")
    m1 = m1[m1.index >= "2009-06-01"]
    h1 = pd.read_parquet(TF / "XAUUSD_H1.parquet")
    h4 = pd.read_parquet(TF / "XAUUSD_H4.parquet")
    d1 = pd.read_parquet(TF / "XAUUSD_D1.parquet")
    return m1, h1[h1.index >= "2009-06-01"], h4, d1


def trend_on(idx, d1):
    """+1/-1: chiusura D1 precedente sopra/sotto la sua EMA50 (solo giorni chiusi)."""
    tr = np.sign(d1.close - d1.close.ewm(span=50).mean()).shift(1)
    tr.index = tr.index.normalize()
    return pd.Series(idx.normalize(), index=idx).map(tr).fillna(0).values


def signals(h1, h4, d1, rng):
    """Segnali sulla chiusura delle barre H1: DataFrame (time = apertura della barra successiva, side, rule)."""
    t = trend_on(h1.index, d1)
    out = []
    hi20, lo20 = h1.high.rolling(20).max().shift(1), h1.low.rolling(20).min().shift(1)
    s1 = np.where((t > 0) & (h1.close > hi20), 1, np.where((t < 0) & (h1.close < lo20), -1, 0))
    out.append(("T1", s1))
    dh, dl = h4.high.rolling(20).max().shift(1), h4.low.rolling(20).min().shift(1)
    brk = pd.Series(np.where(h4.close > dh, 1, np.where(h4.close < dl, -1, 0)), index=h4.index)
    brk = brk.replace(0, np.nan).ffill(limit=6).reindex(h1.index, method="ffill").fillna(0).values   # rottura recente
    up_bar = np.sign(h1.close - h1.open).values
    s2 = np.where((brk == t) & (t != 0) & (up_bar == -t), t, 0)
    out.append(("T2", s2))
    hr = h1.index.hour
    day = h1.index.normalize()
    asia = h1[(hr < 7)].groupby(h1[(hr < 7)].index.normalize()).agg({"high": "max", "low": "min"})
    ah, al = pd.Series(day).map(asia.high).values, pd.Series(day).map(asia.low).values
    win = (hr >= 8) & (hr <= 11)
    s3 = np.where(win & (t > 0) & (h1.close > ah), 1, np.where(win & (t < 0) & (h1.close < al), -1, 0))
    out.append(("T3", s3))
    s4 = np.where(rng.random(len(h1)) < 0.05, t, 0)
    out.append(("R", s4))
    rows = []
    for name, s in out:
        k = np.nonzero(s)[0]
        k = k[k + 1 < len(h1)]
        rows.append(pd.DataFrame({"time": h1.index[k + 1], "side": s[k].astype(int), "rule": name}))
    return pd.concat(rows, ignore_index=True)


def simulate(m1, sig, stop, k):
    o, h, l = m1.open.values, m1.high.values, m1.low.values
    idx = m1.index.values
    res = []
    busy_until = np.datetime64("1970-01-01")
    last_day = None
    for t, side in zip(sig.time.values, sig.side.values):
        if t < busy_until or (last_day is not None and t.astype("datetime64[D]") == last_day):
            continue
        i = np.searchsorted(idx, t)
        if i >= len(idx) - 2:
            break
        entry = o[i]
        j = min(i + HOLD, len(idx) - 1)
        hh, ll = h[i:j], l[i:j]
        if side > 0:
            hit_s = np.nonzero(ll <= entry - stop)[0]
            hit_t = np.nonzero(hh >= entry + k * stop)[0]
        else:
            hit_s = np.nonzero(hh >= entry + stop)[0]
            hit_t = np.nonzero(ll <= entry - k * stop)[0]
        fs = hit_s[0] if hit_s.size else 10**9
        ft = hit_t[0] if hit_t.size else 10**9
        if fs <= ft and fs < 10**9:
            pnl, e = -stop, i + fs
        elif ft < 10**9:
            pnl, e = k * stop, i + ft
        else:
            e = j
            pnl = (o[j] - entry) * side
        res.append((t, pnl - COST))
        busy_until = idx[e]
        last_day = t.astype("datetime64[D]")
    return pd.DataFrame(res, columns=["time", "usd"])


def summary(tr, stop):
    out = {}
    for name, (a, b) in (("sviluppo", ("2010-01-01", "2016-01-01")), ("verifica", ("2016-01-01", "2026-02-01"))):
        x = tr[(tr.time >= a) & (tr.time < b)]
        if not len(x):
            continue
        y = x.groupby(x.time.dt.year).usd.sum()
        out[name] = {"n": len(x), "anno": round(len(x) / (pd.Timestamp(b) - pd.Timestamp(a)).days * 365, 1),
                     "win": round(float((x.usd > 0).mean()), 3), "R_medio": round(float(x.usd.mean() / stop), 3),
                     "usd": round(float(x.usd.sum()), 1), "anni_pos": f"{int((y > 0).sum())}/{len(y)}"}
    return out


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    m1, h1, h4, d1 = load()
    sig = signals(h1, h4, d1, np.random.default_rng(7))
    rows = []
    for rule in ("T1", "T2", "T3", "R"):
        s = sig[sig.rule == rule].sort_values("time")
        for stop in STOPS:
            for k in KS:
                tr = simulate(m1, s, stop, k)
                sm = summary(tr, stop)
                row = {"rule": rule, "stop": stop, "k": k}
                for p, v in sm.items():
                    row.update({f"{p}_{a}": b for a, b in v.items()})
                rows.append(row)
                print(row, flush=True)
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "small_stop_grid.csv", index=False)
    ok = df[(df.sviluppo_R_medio > 0) & (df.verifica_R_medio > 0)]
    (OUT / "small_stop_summary.json").write_text(json.dumps({"configurazioni": len(df), "positive_entrambi": len(ok),
                                                             "elenco": ok.to_dict("records")}, indent=1))
    print("positive in entrambi i periodi:", len(ok), "su", len(df))


if __name__ == "__main__":
    main()
