"""Tabella completa delle feature pre-partita (Fase M2): squadra (fb.state) + arbitro + Elo + mercato + motore gol.

Mercato: probabilità implicite senza margine, prima Pinnacle pre-partita, se manca Bet365 (o media per i campionati
extra). Le stesse colonne si riempiono dal giorno della partita con le quote dell'API (fb.apifootball).
"""
import numpy as np
import pandas as pd

from .goals import run_ratings, tier
from .state import build_state

REF_A = 0.1


def referee_feats(m):
    """Media esponenziale (solo passato) di gialli, rossi e falli per arbitro; n = partite dirette."""
    ref = m.Referee.fillna("").str.strip().str.replace(r"\s+", " ", regex=True).to_numpy() \
        if "Referee" in m else np.full(len(m), "")
    y = (m.HomeYellow + m.AwayYellow).to_numpy(float)
    r = (m.HomeRed + m.AwayRed).to_numpy(float)
    f = (m.HomeFouls + m.AwayFouls).to_numpy(float)
    st, out = {}, np.full((len(m), 4), np.nan, dtype=np.float32)
    for k, name in enumerate(ref):
        if not name:
            continue
        s = st.get(name)
        if s is not None:
            out[k] = s
        if np.isnan(y[k]):
            continue
        if s is None:
            st[name] = np.array([y[k], r[k], f[k] if f[k] == f[k] else np.nan, 1.0])
        else:
            for i, x in enumerate((y[k], r[k], f[k])):
                if x == x:
                    s[i] = x if s[i] != s[i] else s[i] + REF_A * (x - s[i])
            s[3] += 1
    return pd.DataFrame(out, columns=["ref_yel", "ref_red", "ref_fou", "ref_n"], index=m.index)


def _devig(cols, m):
    o = m[cols].apply(pd.to_numeric, errors="coerce")
    o = o.where(o > 1)
    inv = 1 / o
    return inv.div(inv.sum(axis=1), axis=0), inv.sum(axis=1) - 1


def market_feats(m):
    F = pd.DataFrame(index=m.index)
    pin, pin_mg = _devig(["PinH", "PinD", "PinA"], m) if "PinH" in m else (None, None)
    b365, b_mg = _devig(["OddHome", "OddDraw", "OddAway"], m)
    for i, c in enumerate(("mk_1", "mk_X", "mk_2")):
        F[c] = pin.iloc[:, i].fillna(b365.iloc[:, i]) if pin is not None else b365.iloc[:, i]
    F["mk_src_pin"] = pin.iloc[:, 0].notna().astype(float) if pin is not None else 0.0
    F["mk_margin"] = b_mg
    o25p, _ = _devig(["PinO25", "PinU25"], m) if "PinO25" in m else (None, None)
    o25b, _ = _devig(["Over25", "Under25"], m)
    F["mk_o25"] = o25p.iloc[:, 0].fillna(o25b.iloc[:, 0]) if o25p is not None else o25b.iloc[:, 0]
    F["mk_ah"] = pd.to_numeric(m.HandiSize, errors="coerce")
    F["mk_fav"] = F.mk_1 - F.mk_2
    return F


def build_features(m):
    """m ordinato per data (anche con partite future in coda). Restituisce X (solo passato) allineato a m."""
    st = build_state(m)
    lh, la = run_ratings(m)
    X = pd.concat([st, referee_feats(m), market_feats(m)], axis=1)
    X["f1_lh"], X["f1_la"] = lh, la
    X["elo_h"], X["elo_a"] = m.HomeElo.to_numpy(float), m.AwayElo.to_numpy(float)
    X["elo_diff"] = X.elo_h - X.elo_a
    X["tier"] = m.Division.map(tier).to_numpy()
    X["month"] = m.date.dt.month.to_numpy()
    X["div_code"] = m.Division.astype("category").cat.codes.astype(int).to_numpy()
    return X.astype(np.float32)
