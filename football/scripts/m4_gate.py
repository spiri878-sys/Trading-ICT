"""Cancello di qualità (Fase M4). Legge le previsioni walk-forward (data/cache/m3) e per ogni statistica:
1) sceglie approccio, dispersione e rho sugli anni di SCELTA; 2) calcola tutte le selezioni; 3) calibra anno per
anno con i soli anni precedenti; 4) confronta con la media del campionato; 5) decide AMMESSO / NON AMMESSO.
Scrive output/m4_mercati.md, models/m4_config.json, models/m4_calib.pkl e data/cache/m4/<stat>.pkl.
Uso: python football/scripts/m4_gate.py [stat ...]
"""
import json
import pickle
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fb.data import CACHE, ROOT, matches  # noqa: E402
from fb.dist import fit_phi  # noqa: E402
from fb.gate import (RHOS, SEL_YEARS, VER_YEARS, brier, calibrator, ece, family, grid, kmax, logloss,  # noqa: E402
                     outcome, selections)
from fb.markets import prob  # noqa: E402
from fb.models import TARGETS, add_targets, poisson_dev  # noqa: E402

MODELS = ROOT / "models"
GATE = dict(ece=0.015, top_gap=0.02, stab=0.7, skill=0.002)   # skill: miglioramento minimo della log-loss


def choose(r, stat):
    sel = r.year.isin(SEL_YEARS)
    apps = sorted({c[:-2] for c in r.columns if c.endswith("_h") and c != "year"})
    dev = {a: poisson_dev(r.yh[sel], r[f"{a}_h"][sel]) + poisson_dev(r.ya[sel], r[f"{a}_a"][sel]) for a in apps}
    best = min(dev, key=dev.get)
    K = kmax(stat)
    ph, llh, llh_p = fit_phi(r.yh[sel].to_numpy(), r[f"{best}_h"][sel].to_numpy(), K)
    pa, lla, lla_p = fit_phi(r.ya[sel].to_numpy(), r[f"{best}_a"][sel].to_numpy(), K)
    rho = 0.0
    if stat in ("g", "ght", "g2h"):
        yh, ya = r.yh[sel].to_numpy(int).clip(0, K), r.ya[sel].to_numpy(int).clip(0, K)
        mh, ma = r[f"{best}_h"][sel].to_numpy(), r[f"{best}_a"][sel].to_numpy()

        def ll(rho_):
            M = grid(mh, ma, ph, pa, K, rho_)
            return float(np.mean(np.log(M[np.arange(len(yh)), yh, ya] + 1e-12)))
        rho = float(max(RHOS, key=ll))
    return dict(approach=best, deviance={k: round(v, 4) for k, v in dev.items()}, phi_h=ph, phi_a=pa, rho=rho,
                ll_gain_phi=round((llh - llh_p) + (lla - lla_p), 4))


def probs(r, cfg, stat, sels, chunk=15000):
    K, a = kmax(stat), cfg["approach"]
    P = np.zeros((len(r), len(sels)), np.float32)
    for i in range(0, len(r), chunk):
        s = slice(i, i + chunk)
        M = grid(r[f"{a}_h"].to_numpy()[s], r[f"{a}_a"].to_numpy()[s], cfg["phi_h"], cfg["phi_a"], K, cfg["rho"])
        for j, sl in enumerate(sels):
            P[s, j] = prob(M, sl)[0]
    return P


def baseline(m, stat, sels, years):
    """Media del campionato: frequenza dell'evento nella stessa divisione nei 3 anni prima di Y."""
    h, a = TARGETS[stat]
    mm = m[m[h].notna() & m[a].notna()]
    yr = np.where(mm.date.dt.month >= 7, mm.date.dt.year, mm.date.dt.year - 1)
    O = np.column_stack([outcome(s, mm[h].to_numpy(), mm[a].to_numpy(), kmax(stat)) for s in sels])
    df = pd.DataFrame(O, columns=range(len(sels)))
    df["div"], df["yr"] = mm.Division.to_numpy(), yr
    g = df.groupby(["div", "yr"])
    S, N = g.sum(), g.size()
    out = {}
    for y in years:
        w = [(d, t) for d, t in S.index if y - 3 <= t <= y - 1]
        s3, n3 = S.loc[w].groupby(level=0).sum(), N.loc[w].groupby(level=0).sum()
        out[y] = s3.div(n3, axis=0)
    glob = df[list(range(len(sels)))].mean()
    return out, glob


def evaluate(stat, m):
    r = pickle.load(open(CACHE / "m3" / f"{stat}.pkl", "rb"))
    r = r[r.year.isin(SEL_YEARS + VER_YEARS)]
    cfg = choose(r, stat)
    print(stat, cfg, flush=True)
    sels = selections(stat)
    K = kmax(stat)
    P = probs(r, cfg, stat, sels)
    O = np.column_stack([outcome(s, r.yh.to_numpy(), r.ya.to_numpy(), K) for s in sels]).astype(np.float32)
    div = m.loc[r.index, "Division"].to_numpy()
    base, glob = baseline(m, stat, sels, VER_YEARS)
    B = np.zeros_like(P)
    for y in VER_YEARS:
        s = (r.year == y).to_numpy()
        bt = base[y].reindex(div[s])
        B[s] = bt.fillna(glob).to_numpy(np.float32) if len(bt) else glob.to_numpy()
    fams = {}
    for j, sl in enumerate(sels):
        fams.setdefault(family(stat, sl), []).append(j)
    yrs = r.year.to_numpy()
    PC = P.copy()
    rows, calib = [], {}
    for fam, js in fams.items():
        for y in VER_YEARS:
            tr, te = yrs < y, yrs == y
            if te.sum() == 0:
                continue
            ir = calibrator(P[tr][:, js].ravel(), O[tr][:, js].ravel())
            PC[np.ix_(te, js)] = ir.predict(P[te][:, js].ravel()).reshape(te.sum(), len(js))
        calib[fam] = calibrator(P[:, js].ravel(), O[:, js].ravel())     # per l'uso giornaliero: tutti gli anni
        v = np.isin(yrs, VER_YEARS)
        p, o, b, praw = PC[v][:, js].ravel(), O[v][:, js].ravel(), B[v][:, js].ravel(), P[v][:, js].ravel()
        yy = np.repeat(yrs[v], len(js))
        wins = [brier(p[yy == y], o[yy == y]) < brier(b[yy == y], o[yy == y]) for y in VER_YEARS if (yy == y).any()]
        top = p >= 0.7
        row = dict(famiglia=fam, n=len(p), ll=logloss(p, o), ll_media=logloss(b, o), brier=brier(p, o),
                   brier_media=brier(b, o), ece=ece(p, o), ece_grezza=ece(praw, o), stab=float(np.mean(wins)),
                   n70=int(top.sum()), p70=float(p[top].mean()) if top.any() else np.nan,
                   f70=float(o[top].mean()) if top.any() else np.nan)
        ok_top = row["n70"] < 200 or row["f70"] >= row["p70"] - GATE["top_gap"]
        row["skill"] = 1 - row["ll"] / row["ll_media"]
        row["ammesso"] = bool(row["ece"] <= GATE["ece"] and ok_top and row["skill"] >= GATE["skill"]
                              and row["brier"] < row["brier_media"] and row["stab"] >= GATE["stab"])
        rows.append(row)
    out = CACHE / "m4"
    out.mkdir(parents=True, exist_ok=True)
    pickle.dump(dict(index=r.index, year=yrs, sels=sels, P=P, PC=PC, O=O), open(out / f"{stat}.pkl", "wb"))
    return cfg, pd.DataFrame(rows), calib


def main(stats):
    m = add_targets(matches())
    MODELS.mkdir(exist_ok=True)
    cfg_path, cal_path = MODELS / "m4_config.json", MODELS / "m4_calib.pkl"
    conf = json.loads(cfg_path.read_text()) if cfg_path.exists() else {"stats": {}, "families": {}}
    cal = pickle.load(open(cal_path, "rb")) if cal_path.exists() else {}
    tabs = []
    for s in stats:
        cfg, tab, c = evaluate(s, m)
        conf["stats"][s] = cfg
        for _, row in tab.iterrows():
            conf["families"][row.famiglia] = {k: (round(v, 5) if isinstance(v, float) else v) for k, v in row.items()}
        cal.update(c)
        tabs.append(tab)
        print(tab[["famiglia", "ll", "ll_media", "ece", "stab", "n70", "p70", "f70", "ammesso"]].round(4).to_string(),
              flush=True)
    cfg_path.write_text(json.dumps(conf, indent=1, default=float))
    pickle.dump(cal, open(cal_path, "wb"))


if __name__ == "__main__":
    main(sys.argv[1:] or ["cor"])
