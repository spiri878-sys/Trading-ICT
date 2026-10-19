"""FASE 19 — ricerca ampia sull'idea dell'utente (struttura + sweep + ordine stop pendente + filtri) con SCELTA
WALK-FORWARD: ogni anno Y si sceglie la configurazione con il miglior R medio negli anni Y-3..Y-1 (almeno 60 trade,
costi A), e la si usa nell'anno Y, mai visto dalla scelta. Il risultato della catena 2013-2026 misura se il METODO di
ricerca trova un vantaggio vero (non il caso, che con ~1.300 varianti produce sempre un 'vincitore' sul passato).

Griglia: TF {M5, M15} x swing k {2,3,5} x validità ordine {2,4,8 barre} x target {1; 1,5; 2; 3 R} x
multi-timeframe {TREND, CONTRO, NESSUNO} x sessione {Londra+NY, solo NY 08-12, tutte} x filtro ATR {sì, no}.
Ingresso/stop/costi come la Fase 18 (`phase18_sweep_pending.py`).

usage: python python/scripts/phase19_walkforward_search.py
"""
import itertools
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import phase18_sweep_pending as F  # noqa: E402

OUT = F.ROOT / "output" / "phase19"
YEARS = list(range(2010, 2027))


def setups_k(b, tfm, d1, h4, k):
    F.K = k
    return F.make_setups(b, tfm, d1, h4)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    m1 = pd.read_parquet(F.ROOT / "output" / "cache" / "XAUUSD_M1_master.parquet")
    m1 = m1[m1.index >= "2009-10-01"]
    h, l, c = (m1[x].values.astype(float) for x in ("high", "low", "close"))
    d1 = pd.read_parquet(F.TF / "XAUUSD_D1.parquet")
    h4 = pd.read_parquet(F.TF / "XAUUSD_H4.parquet")
    years = m1.index.year.values
    ny_all = None
    recs = []           # per configurazione e anno: n, somma R (costi A e B)
    cfgs = []
    for tfname, tfm in (("M5", 5), ("M15", 15)):
        b = pd.read_parquet(F.TF / f"XAUUSD_{tfname}.parquet")
        b = b[b.index >= "2009-10-01"]
        for k in (2, 3, 5):
            S = setups_k(b, tfm, d1, h4, k)
            si = np.searchsorted(m1.index.values, S.t.values).astype(np.int64)
            nyh = (S.t - pd.Timedelta(hours=7)).dt.hour.values
            for valid, R, mtf, sess, atrf in itertools.product((2, 4, 8), (1.0, 1.5, 2.0, 3.0), ("TREND", "CONTRO", "NESSUNO"),
                                                                 ("LON_NY", "NY", "TUTTE"), ("ATR", "NO")):
                mk = np.ones(len(S), bool)
                if mtf == "TREND":
                    mk &= S.trend.values == S.side.values
                elif mtf == "CONTRO":
                    mk &= S.trend.values == -S.side.values
                if sess == "LON_NY":
                    mk &= S.sess.values
                elif sess == "NY":
                    mk &= (nyh >= 8) & (nyh < 12)
                if atrf == "ATR":
                    mk &= (S.rel.values >= 0.7) & (S.rel.values <= 2.0)
                x = S[mk]
                if len(x) < 100:
                    continue
                s_exp = np.searchsorted(m1.index.values, (x.t + pd.Timedelta(minutes=valid * tfm)).values).astype(np.int64)
                ent, sl = x.entry.values, x.sl.values
                e, p, r = F.run(h, l, c, si[mk], s_exp, x.side.values.astype(np.int64), ent, sl, ent + R * (ent - sl), 1440)
                ok = r > 0
                e, p, r = e[ok], p[ok], r[ok]
                yr = years[e]
                cid = len(cfgs)
                cfgs.append(dict(tf=tfname, k=k, valid=valid, R=R, mtf=mtf, sess=sess, atr=atrf))
                for y in YEARS:
                    m_ = yr == y
                    recs.append((cid, y, int(m_.sum()), float(((p[m_] - 0.15) / r[m_]).sum()),
                                 float(((p[m_] - 0.27) / r[m_]).sum())))
            print(tfname, "k", k, "configurazioni", len(cfgs), flush=True)
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
                      "R_medio_A": round(float(sa.loc[best, y] / max(n.loc[best, y], 1)), 4),
                      "somma_R_A": round(float(sa.loc[best, y]), 2), "somma_R_B": round(float(sb.loc[best, y]), 2)})
        print(chain[-1], flush=True)
    tot_n = sum(x["n"] for x in chain)
    tot_a = sum(x["somma_R_A"] for x in chain)
    tot_b = sum(x["somma_R_B"] for x in chain)
    # quante configurazioni sarebbero 'vincenti' sul passato per puro caso: positive in 2010-15 e 2016-26
    dev = sa[list(range(2010, 2016))].sum(axis=1) / n[list(range(2010, 2016))].sum(axis=1)
    chk = sa[list(range(2016, 2027))].sum(axis=1) / n[list(range(2016, 2027))].sum(axis=1)
    summ = {"configurazioni": len(cfgs), "positive_entrambi_periodi_A": int(((dev > 0) & (chk > 0)).sum()),
            "catena_walkforward": {"trade": tot_n, "R_medio_A": round(tot_a / max(tot_n, 1), 4),
                                   "R_medio_B": round(tot_b / max(tot_n, 1), 4),
                                   "anni_positivi_A": f"{sum(x['somma_R_A'] > 0 for x in chain)}/{len(chain)}"},
            "per_anno": chain}
    (OUT / "walkforward.json").write_text(json.dumps(summ, indent=1, default=str))
    print(json.dumps({k: v for k, v in summ.items() if k != "per_anno"}, indent=1))


if __name__ == "__main__":
    main()
