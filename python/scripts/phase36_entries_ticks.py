"""FASE 36 — entrate diverse sul set migliore (8 $ x1,3, lotto x2, TP 0,7 $, copertura 4, via a 8 $), TICK PER TICK,
ogni mese da 5.000 USC: BUY+SELL insieme contro solo il lato della tendenza, EMA della tendenza (M1: 3.000 / 12.000 /
24.000 ~ EMA 50 / 200 / 400 H1), filtro anti-strappo (4 / 6 ATR / nessuno).
usage: python python/scripts/phase36_entries_ticks.py
"""
import itertools
from pathlib import Path

import numpy as np
import pandas as pd

from phase31_ticks import DEP, SPREAD, tick_basket

ROOT = Path(__file__).resolve().parents[2]
SET = (8.0, 1.3, 2.0, 0.7, 4, 8.0)


def signals(fn, span, k):
    t = pd.read_parquet(fn)
    t = t[t.bid > 0].reset_index(drop=True)
    bid = t.bid.values.astype(np.float64)
    minute = t.time.values.astype("datetime64[m]")
    s = pd.Series(bid, index=pd.DatetimeIndex(minute))
    o = s.groupby(level=0).agg(["max", "min", "last"])
    o.columns = ["high", "low", "close"]
    atr = (o.high - o.low).rolling(14).mean()
    calm = ((o.high.rolling(15).max() - o.low.rolling(15).min()) < k * atr) if k else pd.Series(True, index=o.index)
    trend = o.close > o.close.ewm(span=span, adjust=False).mean()
    idx = np.searchsorted(o.index.values, minute) - 1
    ok = idx >= 0
    c = np.zeros(bid.size, np.bool_); tr = np.zeros(bid.size, np.bool_)
    c[ok] = calm.values[idx[ok]]; tr[ok] = trend.values[idx[ok]]
    return bid, bid + SPREAD, c, tr


def main():
    rows = []
    for m in range(1, 11):
        fn = ROOT / "output" / "cache" / "ticks" / f"XAUUSD_ticks_2026_{m:02d}.parquet"
        for span, k in itertools.product((3000, 12000, 24000), (4.0, 6.0, 0.0)):
            bid, ask, calm, trend = signals(fn, span, k)
            for lab, both in (("tendenza", False), ("BUY+SELL", True)):
                if both and span != 12000:
                    continue                                  # con BUY+SELL la tendenza non conta
                r1 = tick_basket(bid, ask, calm, trend, DEP, *SET, both)
                rows.append(dict(mese=m, ema=span, strappo=k, entrata=lab, saltato=bool(r1[4]),
                                 eur=-50 if r1[4] else round((r1[0] - DEP) / 100), ordini=r1[2]))
        print("mese", m, flush=True)
    df = pd.DataFrame(rows)
    out = ROOT / "output" / "phase36"
    out.mkdir(parents=True, exist_ok=True)
    df.to_csv(out / "entrate_tick.csv", index=False)
    piv = df.pivot_table(index=["entrata", "ema", "strappo"], columns="mese", values="eur", aggfunc="first")
    piv["totale"] = piv.sum(axis=1); piv["bruciati"] = (piv[list(range(1, 11))] == -50).sum(axis=1)
    pd.set_option("display.width", 250)
    print(piv.sort_values("totale", ascending=False).to_string())


if __name__ == "__main__":
    main()
