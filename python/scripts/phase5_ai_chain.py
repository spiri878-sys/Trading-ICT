"""FASE 5 — catena AI della PRIME (architetture V5 e SITO) + modalità di (auto)allenamento.

Periodi: addestramento 2008-2017 (OOF anno per anno 2011-2017, embargo 5 giorni), validazione 2018-2021
(scelta di soglie/livelli/modalità), test 2022+ NON usato. Stop 3 x ATR M15 (Fase 3). Esiti netti C1.

usage: python python/scripts/phase5_ai_chain.py
"""
import itertools
import json
import pickle
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from raptor.prime import models as M  # noqa: E402
from raptor.prime.data import ROOT, config  # noqa: E402

OUT = ROOT / "output"
CACHE = OUT / "cache"
MODELS = ROOT / "models" / "prime"
OOF_YEARS = list(range(2011, 2018))
VAL = ("2018-01-01", "2022-01-01")
MIN_PER_YEAR = 40
CTX_PREFIX = ("vol_", "atr_", "rvol_", "range_", "day_range", "m15_trend", "h1_trend", "h4_trend", "d1_trend",
              "dist_h1", "dist_h4", "dist_d1", "dist_m15", "pos_", "push_", "efficiency", "ny_", "dow", "kz_",
              "month_", "tv_60m", "side", "dist_pdh", "dist_pdl", "dist_pw", "asia_")


def log(msg, t0=[time.time()]):
    print(f"[{time.time() - t0[0]:6.0f}s] {msg}", flush=True)


# ------------------------------------------------------------------ auxiliary M5 models (supervisor, forecaster)
def m5_dataset():
    f = pd.read_parquet(CACHE / "feat_prime_5min_k3.parquet")
    c, a, a1h = f.close.values, f.atr.values, f.h1_atr.values
    X = pd.DataFrame(index=f.index)
    for nm in ("atr_rel", "m15_atr_rel", "h1_atr_rel", "h4_atr_rel", "d1_atr_rel", "tv_rel", "brk_up_48", "brk_dn_48"):
        X[nm] = f[nm].values
    for h in ("m15", "h1", "h4", "d1"):
        X[f"{h}_trend"] = np.sign(f[f"{h}_trend"].values)
        X[f"dist_{h}_ema"] = (f[f"{h}_close"].values - f[f"{h}_ema"].values) / f[f"{h}_atr"].values
        X[f"dist_{h}_hi"] = (f[f"{h}_swing_hi"].values - c) / f[f"{h}_atr"].values
        X[f"dist_{h}_lo"] = (c - f[f"{h}_swing_lo"].values) / f[f"{h}_atr"].values
    for hrs in (4, 24):
        hi, lo = f[f"rng_hi_{hrs}h"].values, f[f"rng_lo_{hrs}h"].values
        X[f"pos_{hrs}h"] = (c - lo) / np.where(hi - lo > 0, hi - lo, np.nan)
    X["ret_60m"] = f.ret_60m.values / a1h
    X["ret_3h"] = f.ret_3h.values / a1h
    X["body"] = (f.close.values - f.open.values) / a
    X["dist_ema_m5"] = (c - f.ema50.values) / a
    sw_hi = f.sweep_hi.values.astype(float); sw_lo = f.sweep_lo.values.astype(float)
    X["sweep_hi_12"] = pd.Series(sw_hi).rolling(12, min_periods=1).sum().values
    X["sweep_lo_12"] = pd.Series(sw_lo).rolling(12, min_periods=1).sum().values
    X["sweep_hi_48"] = pd.Series(sw_hi).rolling(48, min_periods=1).sum().values
    X["sweep_lo_48"] = pd.Series(sw_lo).rolling(48, min_periods=1).sum().values
    X["ny_sin"] = np.sin(2 * np.pi * f.ny_min.values / 1440); X["ny_cos"] = np.cos(2 * np.pi * f.ny_min.values / 1440)
    X = X.replace([np.inf, -np.inf], np.nan)
    fut12 = np.r_[c[12:], np.full(12, np.nan)] - c
    y_bias = np.where(fut12 > 0.5 * a, 1.0, np.where(fut12 < -0.5 * a, 0.0, np.nan))
    nxt = np.r_[c[1:], np.nan]
    y_next = np.where(np.isfinite(nxt), (nxt > c).astype(float), np.nan)
    return X, y_bias, y_next


def m5_predictions(X, y, seed):
    """Previsioni per ogni barra M5 dal 2015: barre 2015-2017 con modello addestrato fino al 2014 (fuori campione),
    barre dal 2018 con modello addestrato fino al 2017. Il campione di training prende una barra ogni 3."""
    idx = X.index
    p = pd.Series(np.nan, index=idx)
    models = {}
    for start, end, train_end in (("2015-01-01", "2018-01-01", "2014-12-25"), ("2018-01-01", "2100-01-01", "2017-12-25")):
        tr = (idx >= "2008-01-01") & (idx < train_end) & np.isfinite(y)
        tr &= (np.arange(len(idx)) % 3 == 0)
        m = M.fit_lgbm(X[tr], y[tr], seed=seed, rounds=200)
        te = (idx >= start) & (idx < end)
        p[te] = m.predict(X[te])
        models[train_end] = m
    return p, models


def map_m5(p: pd.Series, known_at):
    avail = (p.index + pd.Timedelta("5min")).values
    j = np.searchsorted(avail, known_at.values.astype("datetime64[ns]"), side="right") - 1
    return np.where(j >= 0, p.values[np.clip(j, 0, None)], np.nan)


# ------------------------------------------------------------------ evaluation helpers
def sel_perf(r, mask, years, mult=None):
    rr = r[mask] * (mult[mask] if mult is not None else 1.0)
    return M.perf(rr.values, years[mask].values)


def ok(p, n_years, min_pos):
    if p.get("n", 0) < MIN_PER_YEAR * n_years or p.get("avg_r") is None:
        return False
    pos = int(p["years_pos"].split("/")[0])
    return pos >= min_pos


def main():
    t0 = time.time()
    seed = config()["seed"]
    df = pd.read_parquet(CACHE / "features" / "default.parquet")
    df = df[df.filled_atr == True].reset_index(drop=True)  # noqa: E712
    df = df[df.known_at < VAL[1]].reset_index(drop=True)  # il test (2022+) non entra in questa fase
    df["year"] = df.known_at.dt.year
    df["mfe2_atr"] = (df.mfe_r_atr >= 2.0).astype(float)
    feats = [c for c in df.columns if c.startswith("f_")]
    ctx = [c for c in feats if c[2:].startswith(CTX_PREFIX)]
    log(f"segnali riempiti 2005-2021: {len(df)}, feature {len(feats)}, contesto {len(ctx)}")
    is_tr = (df.known_at >= "2008-01-01") & (df.known_at < "2018-01-01")
    is_oof = df.year.between(2011, 2017)
    is_val = (df.known_at >= VAL[0]) & (df.known_at < VAL[1])
    tr_final = M.train_mask(df.known_at, VAL[0], 5, "2008-01-01")

    def oof_and_val(target, cols, fit=M.fit_lgbm, s=seed, objective=None):
        fitf = (lambda X, y, seed: M.fit_lgbm(X, y, seed=seed, objective=objective)) if fit is M.fit_lgbm else fit
        oof = M.walk_forward_oof(df, cols, target, OOF_YEARS, fit=fitf, seed=s)
        m = fitf(df.loc[tr_final & df[target].notna(), cols], df.loc[tr_final & df[target].notna(), target], seed=s)
        val = pd.Series(np.nan, index=df.index)
        val[is_val] = M.predict(m, df.loc[is_val, cols])
        trs = M.predict(m, df.loc[tr_final, cols])  # punteggi del training (riferimento per i percentili)
        return oof, val, m, trs

    # ---------------- core models
    S = {}
    for name, target, cols, obj in (("sel", "big_runner_atr", feats, None), ("gate", "clean_entry_atr", feats, None),
                                    ("regime", "big_runner_atr", ctx, None),
                                    ("sem_r", "r_foto_atr", feats, "regression"),
                                    ("sem_p2", "mfe2_atr", feats, None)):
        oof, val, m, trs = oof_and_val(target, cols, objective=obj)
        S[name] = dict(oof=oof, val=val, model=m, train_scores=trs, cols=cols)
        log(f"modello {name} pronto")
    # Occhio: 4 LightGBM (semi/sottocampioni diversi) + 4 MLP
    eye = []
    for k in range(4):
        prm = dict(feature_fraction=0.5 + 0.1 * k, bagging_fraction=0.6 + 0.05 * k)
        fit = (lambda X, y, seed, prm=prm: M.fit_lgbm(X, y, seed=seed, params=prm))
        oof, val, m, trs = oof_and_val("big_runner_atr", feats, fit=fit, s=seed + k)
        eye.append(dict(oof=oof, val=val, model=m, train_scores=trs, kind="lgbm"))
    for k in range(4):
        oof, val, m, trs = oof_and_val("big_runner_atr", feats, fit=M.fit_mlp, s=seed + 10 + k)
        eye.append(dict(oof=oof, val=val, model=m, train_scores=trs, kind="mlp"))
    log("Occhio (8 modelli) pronto")
    # aux M5 models
    X5, yb, yn = m5_dataset()
    pb, mb = m5_predictions(X5, yb, seed)
    pn, mn = m5_predictions(X5, yn, seed)
    df["p_up_bias"] = map_m5(pb, df.known_at)
    df["p_up_next"] = map_m5(pn, df.known_at)
    log("supervisore LiqBias e forecaster M5 pronti")

    # ---------------- per-signal scores -> percentiles (reference = training-score distribution of the model)
    def pcts(d, which):
        """percentile del punteggio: OOF -> rispetto a tutti i punteggi OOF 2011-2017 (usa solo la distribuzione
        dei punteggi, non gli esiti); val -> rispetto ai punteggi di training del modello finale (solo passato)."""
        if which == "val":
            return pd.Series(M.pct_rank(d["train_scores"], d["val"].values), index=df.index)
        ref = d["oof"][is_oof].values
        return pd.Series(M.pct_rank(ref, d["oof"].values), index=df.index)

    side = df.f_side.values
    out_rows = []

    def evaluate(which):
        mask_per = is_oof if which == "oof" else is_val
        n_years = 7 if which == "oof" else 4
        min_pos = 5 if which == "oof" else 3
        P = {k: pcts(S[k], which) for k in ("sel", "gate", "regime", "sem_r", "sem_p2")}
        # per-cell percentile for the selectors (SITO: "ogni cella col suo modello e le sue soglie")
        sel_cell = pd.Series(np.nan, index=df.index)
        raw = S["sel"]["val" if which == "val" else "oof"]
        for cell in df.cell.unique():
            m = (df.cell == cell).values
            ref = (S["sel"]["train_scores"][(df.loc[tr_final, "cell"] == cell).values] if which == "val"
                   else S["sel"]["oof"][is_oof & (df.cell == cell)].values)
            sel_cell[m] = M.pct_rank(ref, raw[m].values)
        eyes = np.vstack([pcts(e, which).values for e in eye])
        pb_ = df.p_up_bias.values; pn_ = df.p_up_next.values
        bias_against = lambda thr: ((side > 0) & (pb_ <= 1 - thr)) | ((side < 0) & (pb_ >= thr))  # noqa: E731
        fc_against = lambda thr: ((side > 0) & (pn_ <= 1 - thr)) | ((side < 0) & (pn_ >= thr))  # noqa: E731
        fc_favor = lambda thr: ((side > 0) & (pn_ >= thr)) | ((side < 0) & (pn_ <= 1 - thr))  # noqa: E731
        res = {}
        for prof in ("foto", "v5"):
            r = df[f"r_{prof}_atr"]
            yrs = df.year
            base = mask_per & r.notna()
            res[f"baseline_{prof}"] = sel_perf(r, base.values, yrs)
            # ---------- V5 architecture
            best, grid = None, []
            for a_, b_, c_, sup, fc in itertools.product((0, 0.3, 0.5), (0, 0.5, 0.7, 0.8, 0.9), (0, 0.5, 0.7),
                                                         (None, 0.6, 0.7), (None, 0.55, 0.6)):
                m = base.values & (P["regime"].values >= a_) & (P["sel"].values >= b_) & (P["gate"].values >= c_)
                if sup is not None:
                    m &= ~(np.nan_to_num(bias_against(sup)) > 0)
                mult = np.ones(len(df))
                if fc is not None:
                    m &= ~(np.nan_to_num(fc_against(fc)) > 0)
                    mult = np.where(fc_favor(fc), 1.5, 1.0)
                p = sel_perf(r, m, yrs, pd.Series(mult, index=df.index))
                cfg = dict(arch="V5", prof=prof, regime=a_, sel=b_, gate=c_, sup=sup, fc=fc)
                grid.append({**cfg, **{k: v for k, v in p.items() if k != "r_by_year"}})
                if ok(p, n_years, min_pos) and (best is None or p["avg_r"] > best[1]["avg_r"]):
                    best = (cfg, p)
            res[f"V5_{prof}_best"] = best
            out_rows.extend([{**g, "period": which} for g in grid])
            # ---------- SITO architecture
            best_s = None
            for ey, sl, sup, sem in itertools.product((0, 0.6, 0.65, 0.7), (0, 0.78, 0.85, 0.92), (None, 0.70, 0.72),
                                                     (False, True)):
                m = base.values.copy()
                if ey > 0:
                    m &= M.majority_vote(eyes, ey)
                if sl > 0:
                    m &= sel_cell.values >= sl
                if sup is not None:
                    m &= ~(np.nan_to_num(bias_against(sup)) > 0)
                mult = np.where(P["sem_r"].values < 0.33, 0.5, np.where(P["sem_r"].values > 0.67, 1.5, 1.0)) \
                    if sem else np.ones(len(df))
                p = sel_perf(r, m, yrs, pd.Series(mult, index=df.index))
                cfg = dict(arch="SITO", prof=prof, eye=ey, sel=sl, sup=sup, sem=sem)
                out_rows.append({**cfg, **{k: v for k, v in p.items() if k != "r_by_year"}, "period": which})
                if ok(p, n_years, min_pos) and (best_s is None or p["avg_r"] > best_s[1]["avg_r"]):
                    best_s = (cfg, p)
            res[f"SITO_{prof}_best"] = best_s
        return res, P, sel_cell, eyes, bias_against, fc_against, fc_favor

    res_oof, *_ = evaluate("oof")
    log("valutazione OOF 2011-2017 fatta")
    res_val, Pv, sel_cell_v, eyes_v, bias_v, fca_v, fcf_v = evaluate("val")
    log("valutazione validazione 2018-2021 fatta")

    # honest check: thresholds chosen on OOF applied unchanged to validation
    honest = {}
    grid = pd.DataFrame(out_rows)
    for key, best in res_oof.items():
        if not key.endswith("_best") or best is None:
            honest[key] = None
            continue
        cfg = best[0]
        g = grid[(grid.period == "val") & (grid.arch == cfg["arch"]) & (grid.prof == cfg["prof"])]
        for k, v in cfg.items():
            if k in ("arch", "prof"):
                continue
            g = g[g[k].isna()] if v is None else g[g[k] == v]
        honest[key] = {"cfg": cfg, "oof": {k: v for k, v in best[1].items()},
                       "val_same_thresholds": g.drop(columns=["period"]).to_dict("records")[0] if len(g) else None}
    grid.to_csv(OUT / "phase5_grid.csv", index=False)

    # ---------------- level-by-level table for the validation-chosen V5 / SITO configs
    levels = []
    for key in ("V5_foto_best", "V5_v5_best", "SITO_foto_best", "SITO_v5_best"):
        best = res_val.get(key)
        if best is None:
            continue
        cfg = best[0]
        r = df[f"r_{cfg['prof']}_atr"]
        base = is_val.values & r.notna().values
        m = base.copy()
        steps = [("baseline", m.copy(), None)]
        if cfg["arch"] == "V5":
            m &= Pv["regime"].values >= cfg["regime"]; steps.append((f"+regime>={cfg['regime']}", m.copy(), None))
            m &= Pv["sel"].values >= cfg["sel"]; steps.append((f"+selettore>={cfg['sel']}", m.copy(), None))
            m &= Pv["gate"].values >= cfg["gate"]; steps.append((f"+gate>={cfg['gate']}", m.copy(), None))
            if cfg["sup"] is not None:
                m &= ~(np.nan_to_num(bias_v(cfg["sup"])) > 0); steps.append((f"+supervisore {cfg['sup']}", m.copy(), None))
            if cfg["fc"] is not None:
                m &= ~(np.nan_to_num(fca_v(cfg["fc"])) > 0)
                steps.append((f"+forecaster {cfg['fc']}", m.copy(), np.where(fcf_v(cfg["fc"]), 1.5, 1.0)))
        else:
            if cfg["eye"] > 0:
                m &= M.majority_vote(eyes_v, cfg["eye"]); steps.append((f"+occhio {cfg['eye']}", m.copy(), None))
            if cfg["sel"] > 0:
                m &= sel_cell_v.values >= cfg["sel"]; steps.append((f"+selettori {cfg['sel']}", m.copy(), None))
            if cfg["sup"] is not None:
                m &= ~(np.nan_to_num(bias_v(cfg["sup"])) > 0); steps.append((f"+LiqBias {cfg['sup']}", m.copy(), None))
            if cfg["sem"]:
                mult = np.where(Pv["sem_r"].values < 0.33, 0.5, np.where(Pv["sem_r"].values > 0.67, 1.5, 1.0))
                steps.append(("+semaforo", m.copy(), mult))
        for name, mm, mult in steps:
            p = sel_perf(r, mm, df.year, pd.Series(mult, index=df.index) if mult is not None else None)
            levels.append({"config": key, "level": name, **{k: v for k, v in p.items() if k != "r_by_year"},
                           "per_year": round(p.get("n", 0) / 4, 1)})
    pd.DataFrame(levels).to_csv(OUT / "phase5_levels.csv", index=False)

    # ---------------- training modes on the selector (V5 best on validation, or plain selector >= 0.8)
    modes = {}
    best_v5 = res_val.get("V5_foto_best")
    sel_thr = best_v5[0]["sel"] if best_v5 and best_v5[0]["sel"] > 0 else 0.8
    r = df.r_foto_atr
    base = is_val.values & r.notna().values
    modes["CONGELATO"] = sel_perf(r, base & (Pv["sel"].values >= sel_thr), df.year)
    tr_scores = S["sel"]["train_scores"]
    vi = np.flatnonzero(is_val.values)
    for q in (0.7, 0.8, 0.9):
        thr = np.full(len(df), np.inf)
        thr[vi] = M.living_threshold(S["sel"]["val"].values[vi], df.known_at.values[vi], window=1000, q=q,
                                     warm=tr_scores[-1000:])
        modes[f"SOGLIA_VIVA_q{q}"] = sel_perf(r, base & (np.nan_to_num(S["sel"]["val"].values, nan=-1) >= thr),
                                               df.year)
    retrain = pd.Series(np.nan, index=df.index)
    pct_re = pd.Series(np.nan, index=df.index)
    for y in range(2018, 2022):
        trm = M.train_mask(df.known_at, f"{y}-01-01", 5, "2008-01-01") & df.big_runner_atr.notna()
        te = (df.year == y).values
        m = M.fit_lgbm(df.loc[trm, feats], df.loc[trm, "big_runner_atr"], seed=seed)
        retrain[te] = m.predict(df.loc[te, feats])
        pct_re[te] = M.pct_rank(m.predict(df.loc[trm, feats]), retrain[te].values)
    modes["RIADDESTRAMENTO_ANNUALE"] = sel_perf(r, base & (pct_re.values >= sel_thr), df.year)
    modes["selector_threshold_pct"] = sel_thr

    # ---------------- random benchmark for each validation-chosen config
    rng = np.random.default_rng(seed)
    bench = {}
    for key in ("V5_foto_best", "V5_v5_best", "SITO_foto_best", "SITO_v5_best"):
        best = res_val.get(key)
        if best is None:
            continue
        cfg, p = best
        rr = df.loc[is_val & df[f"r_{cfg['prof']}_atr"].notna(), f"r_{cfg['prof']}_atr"].values
        sims = np.array([rng.choice(rr, size=p["n"], replace=False).mean() for _ in range(1000)])
        bench[key] = {"selected_avg_r": p["avg_r"], "random_mean": round(float(sims.mean()), 4),
                      "random_p95": round(float(np.percentile(sims, 95)), 4),
                      "share_random_ge": round(float((sims >= p["avg_r"]).mean()), 4)}

    # ---------------- save models
    MODELS.mkdir(parents=True, exist_ok=True)
    for k, d in S.items():
        d["model"].save_model(str(MODELS / f"{k}.txt"))
    for i, e in enumerate(eye):
        if e["kind"] == "lgbm":
            e["model"].save_model(str(MODELS / f"eye_{i}.txt"))
        else:
            pickle.dump(e["model"], open(MODELS / f"eye_{i}.pkl", "wb"))
    mb["2017-12-25"].save_model(str(MODELS / "liqbias_m5.txt"))
    mn["2017-12-25"].save_model(str(MODELS / "forecaster_m5.txt"))
    json.dump({"features": feats, "context_features": ctx, "m5_features": list(X5.columns)},
              open(MODELS / "features.json", "w"), indent=1)

    clean = lambda b: None if b is None else {"cfg": b[0], **b[1]}  # noqa: E731
    results = {"oof_2011_2017": {k: (clean(v) if k.endswith("_best") else v) for k, v in res_oof.items()},
               "val_2018_2021": {k: (clean(v) if k.endswith("_best") else v) for k, v in res_val.items()},
               "honest_oof_thresholds_on_val": honest, "training_modes_val": modes, "random_benchmark_val": bench,
               "auc": {}, "runtime_s": round(time.time() - t0)}
    from sklearn.metrics import roc_auc_score
    for k, tgt in (("sel", "big_runner_atr"), ("gate", "clean_entry_atr"), ("regime", "big_runner_atr"),
                   ("sem_p2", "mfe2_atr")):
        for per, msk, col in (("oof", is_oof, "oof"), ("val", is_val, "val")):
            y = df.loc[msk, tgt].values; s = S[k][col][msk].values; ok_ = np.isfinite(s) & np.isfinite(y)
            results["auc"][f"{k}_{per}"] = round(float(roc_auc_score(y[ok_], s[ok_])), 4)
    for nm, p, y in (("liqbias", pb, yb), ("forecaster", pn, yn)):
        msk = (p.index >= "2018-01-01") & (p.index < VAL[1]) & np.isfinite(y) & p.notna().values
        results["auc"][f"{nm}_val"] = round(float(roc_auc_score(y[msk], p[msk])), 4)
    (OUT / "phase5_results.json").write_text(json.dumps(results, indent=1, default=str))
    sel_cfg = {k: clean(v) for k, v in res_val.items() if k.endswith("_best")}
    (OUT / "phase5_selected_config.json").write_text(json.dumps(sel_cfg, indent=1, default=str))
    log("fatto")
    print(json.dumps({k: v for k, v in results.items()}, indent=1, default=str)[:12000])


if __name__ == "__main__":
    main()
