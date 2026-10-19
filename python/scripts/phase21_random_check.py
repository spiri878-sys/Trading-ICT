"""FASE 21b — controllo: le varianti scelte dal walk-forward battono ingressi CASUALI con lo stesso filtro, gli stessi
lati, lo stesso SL/TP e lo stesso numero di trade? (200 estrazioni per configurazione, costi A)

usage: python python/scripts/phase21_random_check.py
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import phase18_sweep_pending as F18  # noqa: E402
import phase21_brt_walkforward as W  # noqa: E402

CHECK = [("H1", 5, 1.5, 0.5, "REGIME", "SOLO_BUY", 1.0, 8.0), ("H1", 5, 1.5, 1.0, "REGIME", "SOLO_BUY", 1.0, 8.0),
         ("M15", 20, 2.5, 0.5, "REGIME", "ENTRAMBI", 1.0, 8.0), ("H1", 20, 1.0, 1.0, "REGIME", "SOLO_BUY", 1.0, 8.0),
         ("M15", 20, 2.5, 1.0, "NESSUNO", "SOLO_BUY", 1.0, 8.0), ("H1", 10, 1.5, 0.5, "SMA50", "ENTRAMBI", 1.5, 8.0)]


def main():
    m1 = pd.read_parquet(W.ROOT / "output" / "cache" / "XAUUSD_M1_master.parquet")
    m1 = m1[m1.index >= "2009-10-01"]
    mo, mh, ml, mc = (m1[x].values.astype(float) for x in ("open", "high", "low", "close"))
    d1 = pd.read_parquet(W.TF / "XAUUSD_D1.parquet")
    h4 = pd.read_parquet(W.TF / "XAUUSD_H4.parquet")
    rng = np.random.default_rng(1)
    out = []
    cache = {}
    for tfn, L, imp, rz, filt, sides, slm, tpm in CHECK:
        tfm = 15 if tfn == "M15" else 60
        if tfn not in cache:
            b = pd.read_parquet(W.TF / f"XAUUSD_{tfn}.parquet")
            b = b[(b.index >= "2010-01-01")]
            o, h, l, c = (b[x].values for x in ("open", "high", "low", "close"))
            pc = np.r_[c[0], c[:-1]]
            atr = pd.Series(np.maximum(h - l, np.maximum(abs(h - pc), abs(l - pc)))).ewm(alpha=1 / 14, adjust=False).mean().values
            sma = pd.Series(c).rolling(50).mean().values
            tclose = b.index + pd.Timedelta(minutes=tfm)
            reg = F18.htf_trend(tclose, d1, h4)
            eidx = np.searchsorted(m1.index.values, tclose.values).astype(np.int64)
            cache[tfn] = (o, h, l, c, atr, sma, reg, eidx)
        o, h, l, c, atr, sma, reg, eidx = cache[tfn]
        sig = W.signals(o, h, l, c, atr, L, imp, rz)
        if filt == "SMA50":
            allow_b, allow_s = c > sma, c < sma
        elif filt == "REGIME":
            allow_b, allow_s = reg == 1, reg == -1
        else:
            allow_b = allow_s = np.ones(len(c), bool)
        ok = ((sig > 0) & allow_b) | ((sig < 0) & allow_s)
        if sides == "SOLO_BUY":
            ok &= sig > 0
        idx = np.flatnonzero(ok)

        def R_of(ix, sd):
            a = atr[ix]
            r, used = W.run(mo, mh, ml, mc, eidx[ix], sd.astype(np.int64), slm * a, tpm * a, 3 * 1440)
            return float(((r[used] - 0.15) / (slm * a[used])).mean()), int(used.sum())
        real, nreal = R_of(idx, sig[idx])
        pool_b = np.flatnonzero(allow_b)
        pool_s = np.flatnonzero(allow_s) if sides == "ENTRAMBI" else np.array([], int)
        nb, ns = int((sig[idx] > 0).sum()), int((sig[idx] < 0).sum())
        rand = []
        for _ in range(200):
            ix = np.r_[rng.choice(pool_b, nb, replace=False), rng.choice(pool_s, ns, replace=False) if ns else []].astype(int)
            sd = np.r_[np.ones(nb), -np.ones(ns)]
            order = np.argsort(ix)
            rand.append(R_of(ix[order], sd[order])[0])
        rand = np.array(rand)
        row = {"config": [tfn, L, imp, rz, filt, sides, slm, tpm], "trade": nreal, "R_bot": round(real, 3),
               "R_casuale_media": round(float(rand.mean()), 3), "R_casuale_p95": round(float(np.percentile(rand, 95)), 3),
               "p_valore": round(float((rand >= real).mean()), 3)}
        out.append(row)
        print(row, flush=True)
    (W.OUT / "random_check.json").write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
