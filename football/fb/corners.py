"""Feature specifiche per gli angoli (Fase F6). Tutto calcolato solo dal passato."""
import numpy as np
import pandas as pd


def corner_feats(m):
    """Feature angoli, solo dal passato (shift di una partita)."""
    rows = []
    for side in ("h", "a"):
        d = pd.DataFrame({"mid": m.mid.values, "date": m.date.values, "season": m.season.values,
                          "team": (m.HomeTeam if side == "h" else m.AwayTeam).values, "country": m.country.values,
                          "side": side})
        d["cf"] = (m.HomeCorners if side == "h" else m.AwayCorners).values
        d["ca"] = (m.AwayCorners if side == "h" else m.HomeCorners).values
        d["sf"] = (m.HomeShots if side == "h" else m.AwayShots).values
        d["sa"] = (m.AwayShots if side == "h" else m.HomeShots).values
        rows.append(d)
    L = pd.concat(rows).sort_values(["date", "mid"]).reset_index(drop=True)
    L["ctot"] = L.cf + L.ca
    L["cshare"] = L.cf / L.ctot.replace(0, np.nan)
    L["sshare"] = L.sf / (L.sf + L.sa).replace(0, np.nan)
    out = pd.DataFrame({"mid": L.mid, "side": L.side})
    g = L.groupby(["country", "team"], sort=False)
    for c in ("cf", "ca", "ctot", "cshare", "sshare"):
        sh = g[c].shift(1)
        for span in (6, 20):
            out[f"{c}_ewm{span}"] = sh.groupby([L.country, L.team]).transform(
                lambda x: x.ewm(span=span, min_periods=2, ignore_na=True).mean()).values
    # per campo: stessa squadra, stesso lato (casa in casa, ospite fuori)
    gv = L.groupby(["country", "team", "side"], sort=False)
    for c in ("cf", "ca"):
        sh = gv[c].shift(1)
        out[f"{c}_venue8"] = sh.groupby([L.country, L.team, L.side]).transform(
            lambda x: x.rolling(8, min_periods=2).mean()).values
    # stagione in corso e stagione precedente
    gs = L.groupby(["country", "team", "season"], sort=False)
    for c in ("cf", "ca"):
        out[f"{c}_ssn"] = gs[c].transform(lambda x: x.shift(1).expanding(min_periods=1).mean()).values
        out[f"{c}_ssn_n"] = gs[c].transform(lambda x: x.shift(1).notna().cumsum()).values
        prev = L.groupby(["country", "team", "season"])[c].mean().rename("v").reset_index()
        prev["season"] += 1
        out[f"{c}_prev"] = L[["country", "team", "season"]].merge(prev, how="left").v.values
    wide = out.pivot(index="mid", columns="side")
    wide.columns = [f"{s}_{c}" for c, s in wide.columns]
    wide = wide.reindex(m.mid.values)
    wide.index = m.index
    # media angoli del campionato sulle ultime 300 partite (solo passato)
    tot = m.HomeCorners + m.AwayCorners
    wide["lg_cor300"] = tot.groupby(m.Division).transform(
        lambda x: x.shift(1).rolling(300, min_periods=50).mean()).values
    wide["lg_cor_home_share"] = (m.HomeCorners / tot.replace(0, np.nan)).groupby(m.Division).transform(
        lambda x: x.shift(1).rolling(300, min_periods=50).mean()).values
    # combinazioni attacco/difesa
    for a, b, n in (("h_cf_ewm20", "a_ca_ewm20", "x_home"), ("a_cf_ewm20", "h_ca_ewm20", "x_away")):
        wide[n] = wide[a] + wide[b]
    wide["x_tot"] = wide.x_home + wide.x_away
    return wide


def market_feats(m, X):
    F = pd.DataFrame(index=m.index)
    F["fav_gap"] = (X.mk_1 - X.mk_2).values
    F["fav_abs"] = F.fav_gap.abs()
    F["mk_max_over"] = np.where((m.MaxOver25 > 1) & (m.MaxUnder25 > 1),
                                (1 / m.MaxOver25) / (1 / m.MaxOver25 + 1 / m.MaxUnder25), np.nan)
    return F
