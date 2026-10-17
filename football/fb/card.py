"""Scheda partita a 360 gradi (Fase F5): dalle partite future (casa, ospite, campionato, data, quote opzionali)
produce probabilità e quote giuste di tutti i mercati, usando i modelli finali addestrati su tutta la storia.

Le feature delle partite future sono calcolate aggiungendo righe senza risultato in coda all'archivio: tutti i
motori predicono PRIMA di aggiornare, quindi il calcolo è identico a quello del backtest.
"""
import json
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd
from scipy.stats import nbinom, poisson

from .data import COUNTRY, RAW, ROOT, matches
from .features import build
from .goals import MAXG, probs_vectorized, run_ratings

MODELS = ROOT / "models"
RHO = -0.05


def latest_elo(club, date):
    e = pd.read_csv(RAW / "EloRatings.csv", parse_dates=["date"])
    e = e[(e.club == club) & (e.date <= pd.Timestamp(date))]
    return float(e.elo.iloc[-1]) if len(e) else np.nan


def team_names(division=None):
    m = matches()
    if division:
        m = m[m.Division == division]
    return sorted(set(m.HomeTeam) | set(m.AwayTeam))


def fixtures_frame(fixtures):
    """fixtures: lista di dict {home, away, div, date, odds: {1,X,2,over25,under25} opzionale}."""
    m = matches().copy()
    rows = []
    for f in fixtures:
        d = pd.Timestamp(f["date"])
        o = f.get("odds") or {}
        rows.append(dict(Division=f["div"], date=d, MatchDate=d.strftime("%Y-%m-%d"), HomeTeam=f["home"],
                         AwayTeam=f["away"], HomeElo=latest_elo(f["home"], d), AwayElo=latest_elo(f["away"], d),
                         OddHome=o.get("1", np.nan), OddDraw=o.get("X", np.nan), OddAway=o.get("2", np.nan),
                         Over25=o.get("over25", np.nan), Under25=o.get("under25", np.nan),
                         HandiSize=o.get("ah_line", np.nan)))
    fx = pd.DataFrame(rows)
    fx["season"] = np.where(fx.date.dt.month >= 7, fx.date.dt.year, fx.date.dt.year - 1)
    fx["country"] = fx.Division.map(COUNTRY).fillna(fx.Division)
    fx["hg"] = np.nan
    fx["ag"] = np.nan
    # forma (punti nelle ultime 3/5) calcolata dallo storico
    for side, team in (("Home", "home"), ("Away", "away")):
        for n in (3, 5):
            vals = []
            for f in fixtures:
                t = f[team]
                g = m[((m.HomeTeam == t) | (m.AwayTeam == t)) & (m.date < pd.Timestamp(f["date"]))].tail(n)
                pts = np.where(g.HomeTeam == t, np.sign(g.hg - g.ag), np.sign(g.ag - g.hg))
                vals.append(float(np.where(pts > 0, 3, np.where(pts == 0, 1, 0)).sum()))
            fx[f"Form{n}{side}"] = vals
    m["hg"] = m.hg.astype(float)
    m["ag"] = m.ag.astype(float)
    allm = pd.concat([m, fx], ignore_index=True).sort_values(["date", "Division", "HomeTeam"], kind="stable")
    allm = allm.reset_index(drop=True)
    allm["mid"] = np.arange(len(allm))
    return allm, allm.index[allm.hg.isna()].values


def predict_fixtures(fixtures):
    allm, idx = fixtures_frame(fixtures)
    meta = json.loads((MODELS / "meta.json").read_text())
    lh, la = run_ratings(allm, **meta["f1_params"])
    f1 = pd.DataFrame({"lh": lh, "la": la})
    X = build(allm, f1)
    X["div_code"] = pd.Categorical(allm.Division, categories=meta["div_categories"]).codes
    XC = None
    if "cor6" in meta:   # modelli angoli F6
        from .corners import corner_feats, market_feats
        XC = pd.concat([X, corner_feats(allm), market_feats(allm, X)], axis=1)
    out = []
    for i in idx:
        has_mk = np.isfinite(X.loc[i, "mk_1"])
        v = "calcio_mercato" if has_mk else "calcio"
        feats = meta["features"][v]
        xi = X.loc[[i], feats]
        res = {"match": allm.loc[i, ["HomeTeam", "AwayTeam", "Division"]].to_dict(), "data": str(allm.loc[i, "date"].date()),
               "variante": v}
        import pickle
        cal = pickle.loads((MODELS / "calibratori.pkl").read_bytes())
        p1x2 = lgb.Booster(model_file=str(MODELS / f"{v}_1x2.txt")).predict(xi)[0]
        p1x2 = np.array([cal[f"{v}_{c}"].predict([p])[0] for c, p in zip(("p1", "pX", "p2"), p1x2)])
        p1x2 = p1x2 / p1x2.sum()
        res["p_1X2"] = dict(zip(("1", "X", "2"), map(float, p1x2)))
        po = lgb.Booster(model_file=str(MODELS / f"{v}_over.txt")).predict(xi)[0]
        res["p_over25_ai"] = float(cal[f"{v}_pover"].predict([po])[0])
        pg = lgb.Booster(model_file=str(MODELS / f"{v}_gg.txt")).predict(xi)[0]
        res["p_gg_ai"] = float(cal[f"{v}_pgg"].predict([pg])[0])
        mu_h = float(lgb.Booster(model_file=str(MODELS / f"{v}_mu_h.txt")).predict(xi)[0])
        mu_a = float(lgb.Booster(model_file=str(MODELS / f"{v}_mu_a.txt")).predict(xi)[0])
        res["gol_attesi"] = {"casa": mu_h, "ospite": mu_a}
        _, M = probs_vectorized([mu_h], [mu_a], RHO)
        res["matrice"] = M[0]
        xc = X.loc[[i], meta["features"]["calcio"]]
        for fam in ("cor", "yel"):
            mh = float(lgb.Booster(model_file=str(MODELS / f"{fam}_h.txt")).predict(xc)[0])
            ma = float(lgb.Booster(model_file=str(MODELS / f"{fam}_a.txt")).predict(xc)[0])
            res[f"{fam}_attesi"] = {"casa": mh, "ospite": ma, "k": meta["dispersion"][fam]}
        if XC is not None:
            xa = XC.loc[[i], meta["cor6"]["features"]]
            mh, ma, mt = (float(lgb.Booster(model_file=str(MODELS / f"cor6_{k}.txt")).predict(xa)[0])
                          for k in ("h", "a", "tot"))
            tot = (mh + ma + mt) / 2
            res["cor_attesi"] = {"casa": tot * mh / (mh + ma), "ospite": tot * ma / (mh + ma), "k": meta["cor6"]["k"]}
        res["contesto"] = {k: (None if not np.isfinite(X.loc[i, k]) else round(float(X.loc[i, k]), 2)) for k in
                           ("elo_h", "elo_a", "h_g_f_m5", "h_g_a_m5", "a_g_f_m5", "a_g_a_m5", "h_sot_f_m5", "a_sot_f_m5",
                            "h_cor_f_m5", "a_cor_f_m5", "h_pts_m5", "a_pts_m5", "h_rest_days", "a_rest_days",
                            "lh", "la")}
        res["quote_bookmaker"] = fixtures[list(idx).index(i)].get("odds") or {}
        out.append(res)
    return out


def markets(res):
    """Tutti i mercati derivati: probabilità e quota giusta (1/p)."""
    M = res["matrice"]
    g = np.arange(MAXG + 1)
    tot = g[:, None] + g[None, :]
    dif = g[:, None] - g[None, :]
    P = {}
    p1, pX, p2 = res["p_1X2"]["1"], res["p_1X2"]["X"], res["p_1X2"]["2"]
    P["1"], P["X"], P["2"] = p1, pX, p2
    P["1X"], P["X2"], P["12"] = p1 + pX, pX + p2, p1 + p2
    for line in (0.5, 1.5, 2.5, 3.5, 4.5):
        P[f"Over {line}"] = float(M[tot > line].sum())
        P[f"Under {line}"] = 1 - P[f"Over {line}"]
    P["Over 2.5"] = res["p_over25_ai"]
    P["Under 2.5"] = 1 - res["p_over25_ai"]
    P["Gol"] = res["p_gg_ai"]
    P["NoGol"] = 1 - res["p_gg_ai"]
    P["Pari"] = float(M[tot % 2 == 0].sum())
    P["Dispari"] = 1 - P["Pari"]
    for a, b in ((0, 1), (1, 2), (1, 3), (2, 3), (2, 4), (3, 5)):
        P[f"Multigol {a}-{b}"] = float(M[(tot >= a) & (tot <= b)].sum())
    for line in (0.5, 1.5, 2.5):
        P[f"Casa Over {line}"] = float(M[g > line, :].sum())
        P[f"Ospite Over {line}"] = float(M[:, g > line].sum())
    # combo coerenti (dalla stessa matrice)
    P["1 + Over 1.5"] = float(M[(dif > 0) & (tot > 1.5)].sum())
    P["1 + Under 3.5"] = float(M[(dif > 0) & (tot < 3.5)].sum())
    P["2 + Over 1.5"] = float(M[(dif < 0) & (tot > 1.5)].sum())
    P["1X + Under 3.5"] = float(M[(dif >= 0) & (tot < 3.5)].sum())
    P["X2 + Under 3.5"] = float(M[(dif <= 0) & (tot < 3.5)].sum())
    P["Gol + Over 2.5"] = float(M[1:, 1:][(tot[1:, 1:] > 2.5)].sum())
    P["NoGol + Under 2.5"] = float(M[(tot < 2.5) & ~((g[:, None] > 0) & (g[None, :] > 0))].sum())
    for fam, lines, name in (("cor", (7.5, 8.5, 9.5, 10.5, 11.5), "Angoli"), ("yel", (2.5, 3.5, 4.5, 5.5), "Gialli")):
        e = res[f"{fam}_attesi"]
        mu, k = e["casa"] + e["ospite"], e["k"]
        for line in lines:
            P[f"{name} Over {line}"] = float(1 - nbinom.cdf(np.floor(line), k, k / (k + mu)))
            P[f"{name} Under {line}"] = 1 - P[f"{name} Over {line}"]
    exact = sorted(((float(M[i, j]), f"{i}-{j}") for i in range(6) for j in range(6)), reverse=True)[:8]
    return P, exact


def render(res):
    P, exact = markets(res)
    q = res["quote_bookmaker"]
    qmap = {"1": q.get("1"), "X": q.get("X"), "2": q.get("2"), "Over 2.5": q.get("over25"), "Under 2.5": q.get("under25")}
    h, a = res["match"]["HomeTeam"], res["match"]["AwayTeam"]
    L = [f"## {h} - {a} ({res['match']['Division']}, {res['data']})", "",
         f"Gol attesi: **{res['gol_attesi']['casa']:.2f} - {res['gol_attesi']['ospite']:.2f}** · angoli attesi "
         f"{res['cor_attesi']['casa']:.1f} - {res['cor_attesi']['ospite']:.1f} · gialli attesi "
         f"{res['yel_attesi']['casa']:.1f} - {res['yel_attesi']['ospite']:.1f} · modello: {res['variante']}", "",
         "| Mercato | Probabilità | Quota giusta | Quota bookmaker | Valore |", "|---|---|---|---|---|"]
    for k, p in P.items():
        qb = qmap.get(k)
        val = f"{100 * (p * qb - 1):+.1f}%" if qb else ""
        L.append(f"| {k} | {100 * p:.1f}% | {1 / max(p, 1e-6):.2f} | {qb or ''} | {val} |")
    last = matches().date.max().date()
    L += ["", f"Attenzione: l'archivio arriva al {last}; forma e forze non includono le partite successive. "
          "Il Valore è (probabilità x quota - 1): positivo = quota più alta del giusto secondo il modello.",
          "", "Risultati esatti più probabili: " + ", ".join(f"{s} ({100 * p:.1f}%)" for p, s in exact), "",
          "Contesto: " + ", ".join(f"{k}={v}" for k, v in res["contesto"].items())]
    return "\n".join(L)
