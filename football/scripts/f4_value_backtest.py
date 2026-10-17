"""F4 — cacciatore di valore: scommesse simulate alle quote REALI del passato.

Si scommette 1 unità quando valore atteso = p_modello x quota - 1 >= soglia. Mercati: 1X2 e Over/Under 2,5,
a quota Bet365 e alla quota MASSIMA fra circa 17 bookmaker (migliore prezzo disponibile).
Scelte (fonte di probabilità, soglia, quote massime) SOLO su 2013-2018; verifica 2019-2026 senza ritocchi.
Output: output/f4_value_backtest.json, output/f4_grid.csv

usage: python football/scripts/f4_value_backtest.py
"""
import itertools
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fb.data import CACHE, ROOT, matches  # noqa: E402

DEV, CHK = (2013, 2018), (2019, 2026)


def bets_table(m, pr, f1):
    """Una riga per ogni possibile scommessa (partita x esito) con probabilità delle fonti e quote."""
    rows = []
    res = m.FTResult.values
    over = ((m.hg + m.ag) > 2.5).values
    for out, ob, omax, win in (("1", "OddHome", "MaxHome", res == "H"), ("X", "OddDraw", "MaxDraw", res == "D"),
                               ("2", "OddAway", "MaxAway", res == "A"), ("over", "Over25", "MaxOver25", over),
                               ("under", "Under25", "MaxUnder25", ~over)):
        d = pd.DataFrame({"mid": m.mid, "season": m.season, "div": m.Division, "esito": out,
                          "q_b365": m[ob], "q_max": m[omax], "vinta": win})
        key = {"1": "p1", "X": "pX", "2": "p2", "over": "pover", "under": "pover"}[out]
        for v in ("calcio", "calcio_mercato"):
            p = pr[f"{v}_{key}"].values
            d[f"p_{v}"] = 1 - p if out == "under" else p
        fk = {"1": "p1", "X": "pX", "2": "p2", "over": "over2.5", "under": "over2.5"}[out]
        d["p_F1"] = 1 - f1[fk].values if out == "under" else f1[fk].values
        rows.append(d)
    return pd.concat(rows, ignore_index=True)


def evaluate(b, src, qcol, thr, qmax, markets):
    d = b[(b.esito.isin(markets)) & (b[qcol] > 1) & b[f"p_{src}"].notna()]
    ev = d[f"p_{src}"] * d[qcol] - 1
    s = d[(ev >= thr) & (d[qcol] <= qmax)]
    # al massimo una scommessa per partita e mercato (la più conveniente)
    s = s.assign(ev=ev[s.index], fam=np.where(s.esito.isin(["over", "under"]), "ou", "1x2"))
    s = s.sort_values("ev", ascending=False).drop_duplicates(["mid", "fam"])
    pnl = np.where(s.vinta, s[qcol] - 1, -1.0)
    return s.assign(pnl=pnl, q_used=s[qcol])


def stats(s):
    if len(s) == 0:
        return dict(n=0)
    by = s.groupby("season").pnl.agg(["sum", "count"])
    return dict(n=int(len(s)), roi_pct=round(100 * s.pnl.mean(), 2), utile_unita=round(float(s.pnl.sum()), 1),
                quota_media=round(float(s.q_used.mean()), 2),
                stagioni_positive=f"{int((by['sum'] > 0).sum())}/{len(by)}",
                vinte_pct=round(100 * float(s.vinta.mean()), 1))


def main():
    m = matches()
    pr = pd.read_parquet(CACHE / "f2_preds.parquet")
    f1 = pd.read_parquet(CACHE / "f1_goals.parquet")
    b = bets_table(m, pr, f1)
    b = b[b.season >= DEV[0]]
    rows = []
    for src, qcol, thr, qmax, mk in itertools.product(["calcio", "calcio_mercato", "F1"], ["q_b365", "q_max"],
                                                      [0.0, 0.03, 0.05, 0.08, 0.12, 0.2], [2.5, 4.0, 10.0],
                                                      ["1x2", "ou", "tutti"]):
        markets = {"1x2": ["1", "X", "2"], "ou": ["over", "under"], "tutti": ["1", "X", "2", "over", "under"]}[mk]
        s = evaluate(b, src, qcol, thr, qmax, markets)
        for per, (a, z) in (("dev", DEV), ("chk", CHK)):
            st = stats(s[(s.season >= a) & (s.season <= z)])
            rows.append(dict(fonte=src, quote=qcol, soglia=thr, quota_max=qmax, mercati=mk, periodo=per, **st))
    G = pd.DataFrame(rows)
    G.to_csv(ROOT / "output" / "f4_grid.csv", index=False)
    D = G[G.periodo == "dev"].set_index(["fonte", "quote", "soglia", "quota_max", "mercati"])
    C = G[G.periodo == "chk"].set_index(["fonte", "quote", "soglia", "quota_max", "mercati"])
    J = D.join(C, lsuffix="_dev", rsuffix="_chk")
    J = J[J.n_dev >= 300]
    top = J.sort_values("roi_pct_dev", ascending=False).head(25)
    pd.set_option("display.width", 250)
    cols = ["n_dev", "roi_pct_dev", "stagioni_positive_dev", "n_chk", "roi_pct_chk", "utile_unita_chk", "stagioni_positive_chk"]
    print(top[cols].to_string())
    rep = {"migliori_scelte_2013_2018": top[cols].reset_index().to_dict("records"),
           "quota_configurazioni_positive_2013_2018": round(float((J.roi_pct_dev > 0).mean()), 3),
           "quota_configurazioni_positive_2019_2026": round(float((J.roi_pct_chk > 0).mean()), 3),
           "positive_in_entrambi": int(((J.roi_pct_dev > 0) & (J.roi_pct_chk > 0)).sum()), "totale": int(len(J))}
    (ROOT / "output" / "f4_value_backtest.json").write_text(json.dumps(rep, indent=1, default=str))
    print({k: v for k, v in rep.items() if k != "migliori_scelte_2013_2018"})


if __name__ == "__main__":
    main()
