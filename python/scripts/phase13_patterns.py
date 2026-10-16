"""FASE 13 — pattern mining delle sequenze di candele dell'oro.

Ogni barra chiusa diventa una lettera (18 possibili): direzione (su/giù) x corpo rispetto all'ATR14 (piccolo
<0,3 / medio 0,3-0,8 / grande >0,8) x posizione della chiusura nel range della barra (bassa / media / alta).
Una sequenza = le ultime L lettere (L = 1..4, fino a 104.976 sequenze). Per ogni sequenza e orizzonte h:
rendimento dall'apertura della barra successiva alla chiusura dopo h barre, in ATR, al netto di un costo fisso
(0,42 $ = spread 0,30 + commissione + slippage).

SCELTA solo su 2005-2015: sequenze con almeno 300 casi, t >= 4 (soglia severa per i tanti confronti), lato = segno.
CONTROLLO 2016-2026-01: stesso lato, stessa uscita; si conta quante restano positive e il risultato complessivo.

usage: python python/scripts/phase13_patterns.py
"""
import itertools
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from raptor.prime.data import ROOT  # noqa: E402

TF = ROOT / "output" / "cache" / "tf"
OUT = ROOT / "output" / "phase13"
COST = 0.42
SPLIT = np.datetime64("2016-01-01")


def letters(b):
    o, h, l, c = (b[k].values for k in ("open", "high", "low", "close"))
    pc = np.r_[c[0], c[:-1]]
    tr = np.maximum(h - l, np.maximum(np.abs(h - pc), np.abs(l - pc)))
    atr = pd.Series(tr).ewm(alpha=1 / 14, adjust=False).mean().shift(1).values   # ATR fino alla barra precedente
    body = np.abs(c - o) / atr
    size = np.where(body < 0.3, 0, np.where(body < 0.8, 1, 2))
    rng = np.where(h > l, h - l, np.nan)
    pos = (c - l) / rng
    cp = np.where(pos < 1 / 3, 0, np.where(pos < 2 / 3, 1, 2))
    up = (c >= o).astype(int)
    return up * 9 + size * 3 + cp, atr


def mine(tfname, Ls=(1, 2, 3, 4), hs=(1, 3, 6, 12)):
    b = pd.read_parquet(TF / f"XAUUSD_{tfname}.parquet")
    b = b[b.index >= "2005-01-01"]
    code, atr = letters(b)
    o, c = b.open.values, b.close.values
    t = b.index.values
    n = len(b)
    rows = []
    for L in Ls:
        pid = np.zeros(n, np.int64)
        valid = np.ones(n, bool)
        for k in range(L):
            sh = np.r_[np.full(k, -1), code[:n - k]] if k else code
            valid &= sh >= 0
            pid = pid * 18 + np.maximum(sh, 0)
        valid &= np.isfinite(atr) & (atr > 0)
        for h in hs:
            j0, j1 = np.arange(n) + 1, np.arange(n) + h
            ok = valid & (j1 < n)
            fwd = np.full(n, np.nan)
            fwd[ok] = (c[j1[ok]] - o[j0[ok]]) / atr[ok]
            cost = COST / atr
            for per, m in (("dev", ok & (t < SPLIT)), ("chk", ok & (t >= SPLIT))):
                p = pid[m]
                x = fwd[m]
                cnt = np.bincount(p, minlength=18 ** L)
                s1 = np.bincount(p, weights=x, minlength=18 ** L)
                s2 = np.bincount(p, weights=x * x, minlength=18 ** L)
                cs = np.bincount(p, weights=cost[m], minlength=18 ** L)
                rows.append((L, h, per, cnt, s1, s2, cs))
    return rows


def analyse(tfname, tmin=4.0, use_cost=True):
    rows = mine(tfname)
    out = []
    by = {}
    for L, h, per, cnt, s1, s2, cs in rows:
        by[(L, h, per)] = (cnt, s1, s2, cs)
    for (L, h, per), (cnt, s1, s2, cs) in by.items():
        if per != "dev":
            continue
        with np.errstate(invalid="ignore", divide="ignore"):
            mean = s1 / cnt
            sd = np.sqrt(np.maximum(s2 / cnt - mean ** 2, 0))
            tstat = mean / (sd / np.sqrt(cnt))
            mcost = cs / cnt
        side = np.sign(mean)
        net = np.abs(mean) - (mcost if use_cost else 0)                      # rendimento netto medio per trade, in ATR
        pick = (cnt >= 300) & (np.abs(tstat) >= tmin) & (net > 0)
        c2, s12, _, cs2 = by[(L, h, "chk")]
        with np.errstate(invalid="ignore", divide="ignore"):
            mean2 = s12 / c2
            net2 = side * mean2 - (cs2 / c2 if use_cost else 0)
        for pidx in np.flatnonzero(pick):
            out.append(dict(tf=tfname, L=L, h=h, pattern=int(pidx), side=int(side[pidx]), n_dev=int(cnt[pidx]),
                            t_dev=round(float(tstat[pidx]), 2), net_atr_dev=round(float(net[pidx]), 4),
                            n_chk=int(c2[pidx]), net_atr_chk=round(float(net2[pidx]), 4) if c2[pidx] else None))
        # quante sequenze sono state provate (per la correzione dei confronti multipli)
        out.append(dict(tf=tfname, L=L, h=h, pattern=-1, tested=int((cnt >= 300).sum())))
    return out


def decode(pidx, L):
    names = []
    for _ in range(L):
        x = pidx % 18
        pidx //= 18
        up, size, cp = x // 9, (x % 9) // 3, x % 3
        names.append(f"{'SU' if up else 'GIU'}-{['piccola', 'media', 'grande'][size]}-chiude{['bassa', 'metà', 'alta'][cp]}")
    return " > ".join(reversed(names[::-1])[::-1]) if False else " > ".join(names[::-1][::-1])


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    summ_all = {}
    for tier, tmin, use_cost in (("severa_t4_netto", 4.0, True), ("larga_t3_netto", 3.0, True),
                                 ("lorda_t4_senza_costi", 4.0, False)):
        allr = []
        for tfname in ("M5", "M15", "H1"):
            allr += analyse(tfname, tmin, use_cost)
        summ_all[tier] = report(pd.DataFrame(allr), tier)
    (OUT / "patterns_summary.json").write_text(json.dumps(summ_all, indent=1))
    print(json.dumps(summ_all, indent=1))


def report(R, tier):
    tested = R[R.pattern == -1].groupby("tf").tested.sum().to_dict()
    S = R[R.pattern >= 0].copy() if "net_atr_dev" in R else pd.DataFrame()
    if S.empty:
        return {"sequenze_provate": tested, "scelte_su_2005_2015": 0}
    S["sequenza"] = [decode(p, L) for p, L in zip(S.pattern, S.L)]
    S.to_csv(OUT / f"patterns_selected_{tier}.csv", index=False)
    summ = {"sequenze_provate_con_almeno_300_casi": tested,
            "scelte_su_2005_2015": int(len(S)),
            "positive_anche_2016_2026": int((S.net_atr_chk > 0).sum()),
            "netto_medio_2016_2026_ATR": round(float(np.average(S.net_atr_chk.fillna(0), weights=S.n_chk.clip(lower=1))), 4)
            if len(S) else None}
    for tfname, g in S.groupby("tf"):
        summ[tfname] = {"scelte": int(len(g)), "positive_controllo": int((g.net_atr_chk > 0).sum()),
                        "netto_medio_dev": round(float(g.net_atr_dev.mean()), 4),
                        "netto_medio_chk": round(float(g.net_atr_chk.mean()), 4)}
    pd.set_option("display.width", 250)
    print(S.sort_values("t_dev", key=np.abs, ascending=False)[["tf", "L", "h", "side", "n_dev", "t_dev", "net_atr_dev",
                                                              "n_chk", "net_atr_chk", "sequenza"]].head(12).to_string())
    return summ


if __name__ == "__main__":
    main()
