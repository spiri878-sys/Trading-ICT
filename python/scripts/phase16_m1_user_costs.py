"""FASE 16 — scalping M1 sull'oro con i COSTI DEL BROKER DELL'UTENTE (spread fisso 9 punti = 0,09 $, commissione
0,04 $ per 0,01 lotti). Nessuna griglia, nessuna martingala, un trade alla volta, stop e target sempre presenti.

Famiglie (segnale sulla barra M1 chiusa, ingresso all'apertura della successiva, solo Londra+New York, NY 03-16):
  IMP_F / IMP_R : candela con corpo > k*ATR14(M1) -> segui / contro
  BB_R          : chiusura fuori dalla banda media20 +- z*dev.st. -> contro (ritorno alla media)
  BRK_F / BRK_R : chiusura oltre il massimo/minimo delle 20 barre precedenti -> segui / contro
  ORB_F         : rottura del range dei primi 15 minuti di New York (09:30-09:45 NY) -> segui (1 al giorno)
Uscite: stop s*ATR, target t*ATR, chiusura dopo H minuti. Se stop e target nella stessa barra: conta lo stop.
Costi a trade (in $ per oncia = per 0,01 lotti): A utente 0,09+0,04+0,02 slippage = 0,15; B prudente 0,09+0,08+0,10 = 0,27.
Periodi: sviluppo 2010-2015, verifica 2016-01/2026. Vale solo se positiva in entrambi i periodi con costi A e B.

usage: python python/scripts/phase16_m1_user_costs.py [--larghi]
  --larghi: solo famiglie contro-movimento, stop 4-8 ATR, target 2-8 ATR, 60-240 minuti (prova aggiuntiva)
"""
import itertools
import json
from pathlib import Path

import numba
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "output" / "phase16"
COSTS = {"A": 0.15, "B": 0.27}


@numba.njit(cache=True)
def run(o, h, l, c, atr, sig, s, t, hold):
    n = o.size
    ent = np.full(n, -1, np.int64)
    pnl = np.zeros(n)
    risk = np.zeros(n)
    k = 0
    i = 0
    while i < n - 2:
        d = sig[i]
        if d == 0 or atr[i] <= 0:
            i += 1
            continue
        e = i + 1
        px = o[e]
        sl = s * atr[i]
        tp = t * atr[i]
        res = 0.0
        j = e
        end = min(e + hold, n - 1)
        done = False
        while j < end:
            if d > 0:
                if l[j] <= px - sl:
                    res = -sl
                    done = True
                elif h[j] >= px + tp:
                    res = tp
                    done = True
            else:
                if h[j] >= px + sl:
                    res = -sl
                    done = True
                elif l[j] <= px - tp:
                    res = tp
                    done = True
            if done:
                break
            j += 1
        if not done:
            res = (c[end - 1] - px) * d
            j = end - 1
        ent[k] = e
        pnl[k] = res
        risk[k] = sl
        k += 1
        i = j + 1
    return ent[:k], pnl[:k], risk[:k]


def main(wide=False):
    OUT.mkdir(parents=True, exist_ok=True)
    m1 = pd.read_parquet(ROOT / "output" / "cache" / "XAUUSD_M1_master.parquet")
    m1 = m1[m1.index >= "2009-12-01"]
    o, h, l, c = (m1[x].values.astype(float) for x in ("open", "high", "low", "close"))
    pc = np.r_[c[0], c[:-1]]
    tr = np.maximum(h - l, np.maximum(abs(h - pc), abs(l - pc)))
    atr = pd.Series(tr).rolling(14).mean().shift(0).fillna(0).values
    ny = m1.index - pd.Timedelta(hours=7)
    nyh, nym = ny.hour.values, ny.hour.values * 60 + ny.minute.values
    active = (nyh >= 3) & (nyh < 16)
    body = c - o
    s20 = pd.Series(c).rolling(20)
    mid, sd = s20.mean().values, s20.std(ddof=0).values
    hi20 = pd.Series(h).rolling(20).max().shift(1).values
    lo20 = pd.Series(l).rolling(20).min().shift(1).values
    day = ny.normalize()
    win = (nym >= 570) & (nym < 585)
    rng = pd.DataFrame({"d": day[win], "h": h[win], "l": l[win]}).groupby("d").agg({"h": "max", "l": "min"})
    oh, ol = pd.Series(day).map(rng.h).values, pd.Series(day).map(rng.l).values
    after = (nym >= 585) & (nym < 720)
    fams = {}
    for k in (1.5, 2.5):
        imp = np.where(body > k * atr, 1, np.where(body < -k * atr, -1, 0)) * active
        fams[f"IMP_F_k{k}"], fams[f"IMP_R_k{k}"] = imp, -imp
    for z in (2.0, 3.0):
        fams[f"BB_R_z{z}"] = np.where(c > mid + z * sd, -1, np.where(c < mid - z * sd, 1, 0)) * active
    brk = np.where(c > hi20, 1, np.where(c < lo20, -1, 0)) * active
    fams["BRK_F"], fams["BRK_R"] = brk, -brk
    orb = np.where(after & (c > oh), 1, np.where(after & (c < ol), -1, 0))
    first = pd.Series(orb != 0).groupby(day).cumsum().values == 1
    fams["ORB_F"] = np.where(first & (orb != 0), orb, 0)
    years = m1.index.year.values
    rows = []
    for name, sig in fams.items():
        sig = np.nan_to_num(sig).astype(np.int64)
        grid = itertools.product((4.0, 8.0), (2.0, 4.0, 8.0), (60, 240)) if wide else \
            itertools.product((1.0, 2.0), (1.0, 2.0, 3.0), (15, 60))
        if wide and not name.startswith(("IMP_R", "BB_R", "BRK_R")):
            continue
        for s, t, hold in grid:
            e, p, r = run(o, h, l, c, atr, sig, s, t, hold)
            yr = years[e]
            for cn, cost in COSTS.items():
                R = (p - cost) / r
                row = {"famiglia": name, "stop_atr": s, "target_atr": t, "hold": hold, "costi": cn,
                       "trade_giorno": round(len(e) / (16 * 260), 2), "stop_medio_usd": round(float(np.median(r)), 2)}
                for per, (a, b) in (("sviluppo", (2010, 2015)), ("verifica", (2016, 2026))):
                    mk = (yr >= a) & (yr <= b)
                    ys = pd.Series(R[mk]).groupby(yr[mk]).mean()
                    row[f"{per}_R"] = round(float(R[mk].mean()), 4)
                    row[f"{per}_lordo_R"] = round(float((p[mk] / r[mk]).mean()), 4)
                    row[f"{per}_anni_pos"] = f"{int((ys > 0).sum())}/{len(ys)}"
                rows.append(row)
        print(name, "fatto", flush=True)
    df = pd.DataFrame(rows)
    tag = "_larghi" if wide else ""
    df.to_csv(OUT / f"m1_user_costs{tag}.csv", index=False)
    a = df[df.costi == "A"]
    ok = a[(a.sviluppo_R > 0) & (a.verifica_R > 0)]
    summ = {"configurazioni": int(len(a)), "positive_entrambi_costi_A": int(len(ok)),
            "migliori_A": a.sort_values("verifica_R", ascending=False).head(10).to_dict("records"),
            "migliori_lordo": a.sort_values("verifica_lordo_R", ascending=False).head(5).to_dict("records")}
    (OUT / f"m1_user_costs{tag}_summary.json").write_text(json.dumps(summ, indent=1))
    print(json.dumps(summ, indent=1)[:4000])


if __name__ == "__main__":
    import sys
    main(wide="--larghi" in sys.argv)
