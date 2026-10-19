"""FASE 22 — Breakout Retest su BITCOIN (BTCUSDT 1m, Binance data.binance.vision, 2018-01 -> 2026-09).

1. Prova fuori campione VERA: l'EA 'BRT Pro migliorato' scelto sull'oro (H1, solo acquisti in regime D1+H4 rialzista,
   swing 5, impulso 1,5, zona 1 ATR, SL 1 ATR, TP 8 ATR, 72 ore) applicato a Bitcoin senza modifiche,
   con confronto contro ingressi casuali (stesso filtro e stesse uscite).
2. Ricerca walk-forward come la Fase 21 (griglia identica), anni 2021-2026 scelti sui 3 precedenti.
Costi in percentuale del prezzo per trade: A 0,05% (spread+commissione), B 0,12% (+ slippage e swap per qualche giorno).

usage: python python/scripts/phase22_btc_breakout.py
"""
import itertools
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import phase18_sweep_pending as F18  # noqa: E402
import phase21_brt_walkforward as W  # noqa: E402

ROOT = W.ROOT
TF = ROOT / "output" / "cache" / "tf"
OUT = ROOT / "output" / "phase22"
COSTS = {"A": 0.0005, "B": 0.0012}
YEARS = list(range(2018, 2027))


def load():
    m1 = pd.read_parquet(ROOT / "output" / "cache" / "BTCUSD_M1.parquet")
    d1 = pd.read_parquet(TF / "BTCUSD_D1.parquet")
    h4 = pd.read_parquet(TF / "BTCUSD_H4.parquet")
    return m1, d1, h4


def prep(tfn, tfm, m1, d1, h4):
    b = pd.read_parquet(TF / f"BTCUSD_{tfn}.parquet")
    o, h, l, c = (b[x].values for x in ("open", "high", "low", "close"))
    pc = np.r_[c[0], c[:-1]]
    atr = pd.Series(np.maximum(h - l, np.maximum(abs(h - pc), abs(l - pc)))).ewm(alpha=1 / 14, adjust=False).mean().values
    sma = pd.Series(c).rolling(50).mean().values
    tclose = b.index + pd.Timedelta(minutes=tfm)
    reg = F18.htf_trend(tclose, d1, h4)
    eidx = np.searchsorted(m1.index.values, tclose.values).astype(np.int64)
    return o, h, l, c, atr, sma, reg, eidx, tclose


def trades(m, eidx, idx, side, a, slm, tpm, cost):
    mo, mh, ml, mc = m
    r, used = W.run(mo, mh, ml, mc, eidx[idx], side.astype(np.int64), slm * a, tpm * a, 3 * 1440)
    px = mo[np.minimum(eidx[idx], len(mo) - 1)]
    R = (r - cost * px) / (slm * a)
    return R[used], used, r[used] - cost * px[used]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    m1, d1, h4 = load()
    m = tuple(m1[x].values.astype(float) for x in ("open", "high", "low", "close"))
    myear = m1.index.year.values
    res = {}
    # 1. EA dell'oro, invariato
    o, h, l, c, atr, sma, reg, eidx, tclose = prep("H1", 60, m1, d1, h4)
    sig = W.signals(o, h, l, c, atr, 5, 1.5, 1.0)
    idx = np.flatnonzero((sig > 0) & (reg == 1))
    rng = np.random.default_rng(3)
    pool = np.flatnonzero(reg == 1)
    for cn, cost in COSTS.items():
        R, used, usd = trades(m, eidx, idx, np.ones(len(idx)), atr[idx], 1.0, 8.0, cost)
        yr = myear[np.minimum(eidx[idx][used], len(myear) - 1)]
        rand = []
        for _ in range(100):
            ix = np.sort(rng.choice(pool, len(idx), replace=False))
            rand.append(trades(m, eidx, ix, np.ones(len(ix)), atr[ix], 1.0, 8.0, cost)[0].mean())
        s = 0
        mx = 0
        for v in R < 0:
            s = s + 1 if v else 0
            mx = max(mx, s)
        res[f"ea_oro_invariato_costi{cn}"] = {
            "trade": int(len(R)), "vinti": round(float((R > 0).mean()), 3), "R_medio": round(float(R.mean()), 3),
            "R_per_anno": {int(y): round(float(R[yr == y].sum()), 1) for y in np.unique(yr)},
            "casuale_media": round(float(np.mean(rand)), 3), "casuale_p95": round(float(np.percentile(rand, 95)), 3),
            "p_valore": round(float((np.array(rand) >= R.mean()).mean()), 3), "serie_perse_max": mx,
            "stop_mediano_2025_usd": round(float(np.median(atr[idx][used][yr == 2025])), 0) if (yr == 2025).any() else None}
        print(cn, res[f"ea_oro_invariato_costi{cn}"], flush=True)
    # 2. ricerca walk-forward
    cfgs, recs = [], []
    for tfn, tfm in (("M15", 15), ("H1", 60)):
        o, h, l, c, atr, sma, reg, eidx, tclose = prep(tfn, tfm, m1, d1, h4)
        for L, imp, rz in itertools.product((5, 10, 20), (1.0, 1.5, 2.5), (0.3, 0.5, 1.0)):
            sig = W.signals(o, h, l, c, atr, L, imp, rz)
            for filt, sides in itertools.product(("SMA50", "REGIME", "NESSUNO"), ("ENTRAMBI", "SOLO_BUY")):
                ok = sig != 0
                if filt == "SMA50":
                    ok &= np.where(sig > 0, c > sma, c < sma)
                elif filt == "REGIME":
                    ok &= reg == sig
                if sides == "SOLO_BUY":
                    ok &= sig > 0
                idx = np.flatnonzero(ok)
                if len(idx) < 100:
                    continue
                for slm, tpm in itertools.product((1.0, 1.5, 2.5), (2.0, 4.0, 8.0)):
                    RA, used, _ = trades(m, eidx, idx, sig[idx], atr[idx], slm, tpm, COSTS["A"])
                    RB, _, _ = trades(m, eidx, idx, sig[idx], atr[idx], slm, tpm, COSTS["B"])
                    yr = myear[np.minimum(eidx[idx][used], len(myear) - 1)]
                    cid = len(cfgs)
                    cfgs.append(dict(tf=tfn, swing=L, impulso=imp, zona=rz, filtro=filt, lati=sides, sl=slm, tp=tpm))
                    for y in YEARS:
                        k = yr == y
                        recs.append((cid, y, int(k.sum()), float(RA[k].sum()), float(RB[k].sum())))
        print(tfn, "configurazioni", len(cfgs), flush=True)
    rec = pd.DataFrame(recs, columns=["cfg", "anno", "n", "sumR_A", "sumR_B"])
    n = rec.pivot(index="cfg", columns="anno", values="n").fillna(0)
    sa = rec.pivot(index="cfg", columns="anno", values="sumR_A").fillna(0)
    sb = rec.pivot(index="cfg", columns="anno", values="sumR_B").fillna(0)
    chain = []
    for y in range(2021, 2027):
        past = [y - 3, y - 2, y - 1]
        npast = n[past].sum(axis=1)
        score = sa[past].sum(axis=1) / npast.replace(0, np.nan)
        score[npast < 60] = np.nan
        best = score.idxmax()
        chain.append({"anno": y, "scelta": cfgs[best], "R_passato": round(float(score[best]), 3), "n": int(n.loc[best, y]),
                      "somma_R_A": round(float(sa.loc[best, y]), 2), "somma_R_B": round(float(sb.loc[best, y]), 2)})
        print(chain[-1], flush=True)
    tn = sum(x["n"] for x in chain)
    dev = sa[[2018, 2019, 2020, 2021]].sum(axis=1) / n[[2018, 2019, 2020, 2021]].sum(axis=1)
    chk = sa[[2022, 2023, 2024, 2025, 2026]].sum(axis=1) / n[[2022, 2023, 2024, 2025, 2026]].sum(axis=1)
    res["ricerca"] = {"configurazioni": len(cfgs), "positive_2018_21_e_2022_26_A": int(((dev > 0) & (chk > 0)).sum()),
                      "catena": {"trade": tn, "R_medio_A": round(sum(x["somma_R_A"] for x in chain) / max(tn, 1), 4),
                                 "R_medio_B": round(sum(x["somma_R_B"] for x in chain) / max(tn, 1), 4),
                                 "anni_pos_A": f"{sum(x['somma_R_A'] > 0 for x in chain)}/{len(chain)}"}, "per_anno": chain}
    (OUT / "btc.json").write_text(json.dumps(res, indent=1, default=str))
    print(json.dumps(res["ricerca"]["catena"], indent=1), res["ricerca"]["positive_2018_21_e_2022_26_A"])


if __name__ == "__main__":
    main()
