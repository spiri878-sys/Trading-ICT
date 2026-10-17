"""Previsioni per le partite del giorno (Fase M5).

fixtures: lista di dict {div, date, home, away (nomi archivio), arbitro, mk (colonne di mercato da market_inputs)}.
Le partite vengono messe in coda all'archivio con risultato vuoto: le feature usano solo il passato.
"""
import json
import pickle

import lightgbm as lgb
import numpy as np
import pandas as pd

from .data import COUNTRY, RAW, ROOT, matches
from .feats import build_features
from .gate import family, grid, kmax
from .markets import API_BETS, parse, prob
from .models import TARGETS, add_targets, candidates

MODELS = ROOT / "models"
KH = 6                                       # griglia dei due tempi


def _ref(name):
    """'Anthony Taylor' -> 'A Taylor' (formato football-data)."""
    w = name.replace(".", " ").split()
    return f"{w[0][0]} {w[-1]}" if len(w) >= 2 else name


def _elo(teams_dates):
    e = pd.read_csv(RAW / "EloRatings.csv", parse_dates=["date"]).sort_values("date")
    last = e.groupby("club").last()
    return [float(last.elo.get(t, np.nan)) for t, _ in teams_dates]


def fixture_frame(fixtures):
    rows = []
    elo_h = _elo([(f["home"], f["date"]) for f in fixtures])
    elo_a = _elo([(f["away"], f["date"]) for f in fixtures])
    for f, eh, ea in zip(fixtures, elo_h, elo_a):
        d = pd.Timestamp(f["date"])
        r = dict(Division=f["div"], MatchDate=d.strftime("%Y-%m-%d"), date=d, HomeTeam=f["home"], AwayTeam=f["away"],
                 HomeElo=eh, AwayElo=ea, Referee=_ref(f["arbitro"]) if f.get("arbitro") else np.nan)
        r.update(f.get("mk", {}))
        rows.append(r)
    fx = pd.DataFrame(rows)
    fx["season"] = np.where(fx.date.dt.month >= 7, fx.date.dt.year, fx.date.dt.year - 1)
    solar = ~fx.Division.isin(list(COUNTRY))
    fx.loc[solar, "season"] = fx.loc[solar, "date"].dt.year
    fx["country"] = fx.Division.map(COUNTRY).fillna(fx.Division)
    return fx


def team_counts(m, fx):
    """Partite con il dato (per statistica) di ogni squadra nelle ultime 2 stagioni: serve per escludere chi ha
    pochi dati."""
    recent = m[m.date >= m.date.max() - pd.Timedelta(days=730)]
    out = {}
    for stat, (h, a) in TARGETS.items():
        ok = recent[recent[h].notna()]
        cnt = pd.concat([ok.HomeTeam, ok.AwayTeam]).value_counts()
        out[stat] = (fx.HomeTeam.map(cnt).fillna(0).to_numpy(), fx.AwayTeam.map(cnt).fillna(0).to_numpy())
    return out


def predict(fixtures):
    m = add_targets(matches())
    fx = fixture_frame(fixtures)
    allm = pd.concat([m, fx], ignore_index=True).sort_values(["date", "Division", "HomeTeam"], kind="stable")
    allm = allm.reset_index(drop=True)
    is_fx = allm.hg.isna().to_numpy()
    X = build_features(allm)
    cols = json.loads((MODELS / "m5_features.json").read_text())
    Xf = X.loc[is_fx, cols]
    keys = allm.loc[is_fx, ["Division", "HomeTeam", "AwayTeam"]].apply(tuple, axis=1).tolist()
    order = [keys.index((f["div"], f["home"], f["away"])) for f in fixtures]
    Xf = Xf.iloc[order]
    conf = json.loads((MODELS / "m4_config.json").read_text())
    calib = pickle.load(open(MODELS / "m4_calib.pkl", "rb"))
    out = {"X": Xf.reset_index(drop=True), "conf": conf, "calib": calib, "mu": {}, "grid": {},
           "counts": team_counts(m, fx)}
    for stat in TARGETS:
        if stat not in conf["stats"] or not (MODELS / f"m5_{stat}_h.txt").exists():
            continue
        c = conf["stats"][stat]
        bh = lgb.Booster(model_file=str(MODELS / f"m5_{stat}_h.txt")).predict(Xf)
        ba = lgb.Booster(model_file=str(MODELS / f"m5_{stat}_a.txt")).predict(Xf)
        mh, ma = candidates(Xf, stat, bh, ba)[c["approach"]]
        out["mu"][stat] = (mh, ma)
        out["grid"][stat] = grid(mh, ma, c["phi_h"], c["phi_a"], kmax(stat), c["rho"])
    if "ght" in out["grid"] and "g2h" in out["grid"]:
        g1, g2 = conf["stats"]["ght"], conf["stats"]["g2h"]
        M1 = grid(*out["mu"]["ght"], g1["phi_h"], g1["phi_a"], KH, g1["rho"])
        M2 = grid(*out["mu"]["g2h"], g2["phi_h"], g2["phi_a"], KH, g2["rho"])
        out["grid"]["hh"] = M1[:, :, :, None, None] * M2[:, None, None, :, :]
    return out


def norm_sel(kind, sel):
    """Riporta alcune selezioni API alla famiglia verificata (es. 'Win to Nil' Home -> nil_home)."""
    if kind == "nil":
        return {"kind": "nil_home" if sel["o"] == "H" else "nil_away", "yes": True}
    if kind in ("hh_winboth_home", "hh_winboth_away") and sel.get("yes"):
        return {"kind": "hh_winboth", "o": "H" if kind.endswith("home") else "A"}
    if kind in ("hh_teamboth_home", "hh_teamboth_away") and sel.get("yes"):
        return {"kind": "hh_teamboth", "o": "H" if kind.endswith("home") else "A"}
    return dict(sel, kind=kind)


def evaluate_quote(pred, i, q):
    """Probabilità calibrata e valore di una quota API per la partita i. None se il mercato non è gestito."""
    if q["bet_id"] not in API_BETS or q.get("best") is None:      # mercato ignoto o non offerto dai suoi siti
        return None
    stat, kind = API_BETS[q["bet_id"]]
    if stat not in pred["grid"]:
        return None
    sel = parse(kind, q["value"])
    if sel is None:
        return None
    sel = norm_sel(kind, sel)
    M = pred["grid"][stat][i:i + 1]
    w, pu = prob(M, sel)
    fam = family(stat, sel)
    info = pred["conf"]["families"].get(fam)
    cal = pred["calib"].get(fam)
    pw = float(cal.predict(np.array([w[0]]))[0]) if cal is not None else float(w[0])
    pp = float(min(pu[0], 1 - pw))
    return {"stat": stat, "sel": sel, "famiglia": fam, "p_raw": float(w[0]), "p": pw, "p_push": pp,
            "valore": pw * q["best"] + pp - 1, "ammesso": bool(info and info["ammesso"]), "verificato": info is not None}
