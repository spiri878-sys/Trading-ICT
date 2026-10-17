"""Feature pre-partita a 360 gradi (Fase F2). Tutto è calcolato SOLO con partite precedenti.

Gruppi:
A. forze dinamiche (motore F1) per gol, tiri in porta, tiri, angoli, cartellini, falli (lambda attesi);
B. medie mobili per squadra sulle ultime 5 e 10 partite (fatti/subiti) e giorni di riposo;
C. Elo pre-partita, forma (fonte), punti stagione per partita, giornata;
D. mercato: probabilità implicite Bet365 (1X2, O/U 2,5), linea di handicap asiatico, margine.
"""
import numpy as np
import pandas as pd

from .data import implied
from .goals import tier


def online_rates(m, hcol, acol, lr=0.02, lr_glob=0.002):
    """Come il motore gol ma per un conteggio qualsiasi (tiri, angoli, ...). Partite senza dato: si predice e
    non si aggiorna. Restituisce i valori attesi PRE-partita per casa e ospite."""
    att, dif, mu, home, last = {}, {}, {}, {}, {}
    H, A, D, C = m.HomeTeam.values, m.AwayTeam.values, m.Division.values, m.country.values
    xh, xa = m[hcol].values.astype(float), m[acol].values.astype(float)
    base = np.nanmean(np.r_[xh, xa])
    oh, oa = np.full(len(m), np.nan), np.full(len(m), np.nan)
    for k in range(len(m)):
        d = D[k]
        if d not in mu:
            mu[d], home[d] = np.log(max(base, 0.1)), 0.05
        ks = []
        for t in (H[k], A[k]):
            key = (C[k], t)
            if key not in att:
                att[key] = dif[key] = 0.0
            elif last.get(key) not in (None, d):
                att[key] *= 0.5
                dif[key] *= 0.5
            last[key] = d
            ks.append(key)
        h, a = ks
        eh = np.exp(mu[d] + home[d] + att[h] - dif[a])
        ea = np.exp(mu[d] + att[a] - dif[h])
        oh[k], oa[k] = eh, ea
        if np.isnan(xh[k]) or np.isnan(xa[k]):
            continue
        rh, ra = (xh[k] - eh) / max(eh, 1e-6), (xa[k] - ea) / max(ea, 1e-6)   # errore relativo (scala comune)
        att[h] += lr * rh
        dif[a] -= lr * rh
        att[a] += lr * ra
        dif[h] -= lr * ra
        mu[d] += lr_glob * (rh + ra) / 2
        home[d] += lr_glob * (rh - ra) / 2
    return oh, oa


def team_rolling(m):
    """Medie mobili per squadra (fatti/subiti) sulle ultime 5/10 partite PRIMA della partita, riposo."""
    stats = {"g": ("hg", "ag"), "sot": ("HomeTarget", "AwayTarget"), "sh": ("HomeShots", "AwayShots"),
             "cor": ("HomeCorners", "AwayCorners"), "yel": ("HomeYellow", "AwayYellow"),
             "fou": ("HomeFouls", "AwayFouls")}
    rows = []
    for side in ("h", "a"):
        d = pd.DataFrame({"mid": m.mid, "date": m.date, "team": m.HomeTeam if side == "h" else m.AwayTeam,
                          "country": m.country, "side": side})
        for s, (hc, ac) in stats.items():
            d[f"{s}_f"] = m[hc] if side == "h" else m[ac]
            d[f"{s}_a"] = m[ac] if side == "h" else m[hc]
        res = np.sign(m.hg - m.ag) * (1 if side == "h" else -1)
        d["pts"] = np.where(res > 0, 3, np.where(res == 0, 1, 0))
        rows.append(d)
    L = pd.concat(rows).sort_values(["date", "mid"]).reset_index(drop=True)
    g = L.groupby(["country", "team"], sort=False)
    out = pd.DataFrame({"mid": L.mid, "side": L.side})
    cols = [c for c in L.columns if c.endswith("_f") or c.endswith("_a")] + ["pts"]
    for w in (5, 10):
        r = g[cols].transform(lambda x: x.shift(1).rolling(w, min_periods=2).mean())
        for c in cols:
            out[f"{c}_m{w}"] = r[c].values
    out["rest_days"] = g["date"].transform(lambda x: x.diff().dt.days).values
    wide = out.pivot(index="mid", columns="side")
    wide.columns = [f"{s}_{c}" for c, s in wide.columns]
    return wide


def build(m, f1):
    """m: partite (fb.data.matches); f1: DataFrame con lh, la (motore gol)."""
    X = pd.DataFrame(index=m.index)
    X["lh"], X["la"] = f1.lh.values, f1.la.values
    for name, (hc, ac) in {"sot": ("HomeTarget", "AwayTarget"), "sh": ("HomeShots", "AwayShots"),
                           "cor": ("HomeCorners", "AwayCorners"), "yel": ("HomeYellow", "AwayYellow"),
                           "fou": ("HomeFouls", "AwayFouls")}.items():
        eh, ea = online_rates(m, hc, ac)
        X[f"exp_{name}_h"], X[f"exp_{name}_a"] = eh, ea
    roll = team_rolling(m).reindex(m.mid.values)
    roll.index = m.index
    X = pd.concat([X, roll], axis=1)
    X["elo_h"], X["elo_a"] = m.HomeElo.values, m.AwayElo.values
    X["elo_diff"] = X.elo_h - X.elo_a
    for c in ("Form3Home", "Form5Home", "Form3Away", "Form5Away"):
        X[c] = m[c].values
    X["tier"] = m.Division.map(tier).values
    X["month"] = m.date.dt.month.values
    X["matchday"] = m.groupby(["Division", "season"]).cumcount().values
    ok = (m.OddHome > 1) & (m.OddDraw > 1) & (m.OddAway > 1)
    imp = implied(m.loc[ok, ["OddHome", "OddDraw", "OddAway"]])
    for i, c in enumerate(("mk_1", "mk_X", "mk_2")):
        X[c] = np.nan
        X.loc[ok, c] = imp.iloc[:, i].values
    X["mk_margin"] = np.where(ok, 1 / m.OddHome + 1 / m.OddDraw + 1 / m.OddAway - 1, np.nan)
    ok2 = (m.Over25 > 1) & (m.Under25 > 1)
    X["mk_over25"] = np.nan
    X.loc[ok2, "mk_over25"] = implied(m.loc[ok2, ["Over25", "Under25"]]).iloc[:, 0].values
    X["ah_line"] = m.HandiSize.values
    return X
