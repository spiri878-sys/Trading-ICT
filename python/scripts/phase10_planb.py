"""FASE 10 (anticipata) — Piano B: 10 celle (6 PRIME + SB, MSS, JUDAS, OB), Market Brain, portafoglio di celle.

Tutte le scelte (soglie per cella, celle ammesse, tabella del Market Brain) sono fatte SOLO sul fuori campione
2011-2017; la validazione 2018-2021 è applicata senza ritocchi. Test 2022+ non usato.
Criterio di "vantaggio solido" (dichiarato prima dei risultati): in validazione R medio >= +0,08 netto C1,
PF >= 1,15, >= 3/4 anni positivi, ancora positivo con costi C2.

usage: python python/scripts/phase10_planb.py
"""
import itertools
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from raptor.prime import cells as C  # noqa: E402
from raptor.prime import models as M  # noqa: E402
from raptor.prime.data import ROOT, config, degraded_days, master_m1  # noqa: E402
from raptor.prime.features import M1Context, prime_features  # noqa: E402
from raptor.prime.label import COSTS_C1, M1Arrays, label_signals  # noqa: E402

OUT = ROOT / "output"
CACHE = OUT / "cache"
OOF_YEARS = list(range(2011, 2018))
VAL = ("2018-01-01", "2022-01-01")
COSTS_C2 = dict(spread=0.60, comm_per_lot_side=7.0, slip=0.10, swap_long=-0.066, swap_short=0.029)
MIN_YEAR_CELL = 20
SOLID = dict(avg_r=0.08, pf=1.15, years_pos=3)


def log(msg, t0=[time.time()]):
    print(f"[{time.time() - t0[0]:6.0f}s] {msg}", flush=True)


STOP_MULT = float(sys.argv[1]) if len(sys.argv) > 1 else 3.0     # stop = STOP_MULT x ATR M15
MAX_HOLD = int(sys.argv[2]) if len(sys.argv) > 2 else 3 * 24 * 60
TAG = "" if STOP_MULT == 3.0 else f"_stop{int(STOP_MULT)}"


def main():
    seed = config()["seed"]
    m1 = master_m1()
    F = {(tf, 3): pd.read_parquet(CACHE / f"feat_prime_{tf}_k3.parquet") for tf in set(C.TF_OF.values())}
    cells = list(C.ALL_CELLS)
    sig = C.generate(F, cells=cells, degraded=degraded_days())
    sig = sig[(sig.known_at >= "2005-01-01") & (sig.known_at < VAL[1])].reset_index(drop=True)  # niente test
    log(f"segnali 2005-2021: {len(sig)}; per cella {sig.cell.value_counts().to_dict()}")
    f5 = F[("5min", 3)]
    A1 = M1Arrays(m1, f5)
    A2 = M1Arrays(m1, f5, spread=COSTS_C2["spread"])
    L1 = label_signals(sig, A1, stop="atr", atr_mult=STOP_MULT, profiles=("FOTO",), max_hold_min=MAX_HOLD)
    L2 = label_signals(sig, A2, stop="atr", atr_mult=STOP_MULT, profiles=("FOTO",), costs=COSTS_C2,
                       max_hold_min=MAX_HOLD)
    X = prime_features(sig, F, M1Context(m1), onehot=cells)
    df = pd.concat([L1.reset_index(drop=True), X.add_prefix("f_")], axis=1)
    df["r_c2"] = L2.r_foto.values
    df = df[df.filled].reset_index(drop=True)
    df["year"] = df.known_at.dt.year
    feats = [c for c in df.columns if c.startswith("f_")]
    log(f"etichette e feature pronte: {len(df)} riempiti, {len(feats)} feature")

    is_oof = df.year.between(2011, 2017).values
    is_val = ((df.known_at >= VAL[0]) & (df.known_at < VAL[1])).values
    tr_final = M.train_mask(df.known_at, VAL[0], 5, "2008-01-01")

    scores = {}
    for name, tgt in (("sel", "big_runner"), ("gate", "clean_entry")):
        d = df[df[tgt].notna()]
        oof = M.walk_forward_oof(df, feats, tgt, OOF_YEARS, seed=seed)
        mdl = M.fit_lgbm(df.loc[tr_final, feats], df.loc[tr_final, tgt].astype(float), seed=seed)
        val = pd.Series(np.nan, index=df.index)
        val[is_val] = mdl.predict(df.loc[is_val, feats])
        trs = mdl.predict(df.loc[tr_final, feats])
        # percentili per cella: OOF rispetto ai punteggi OOF della cella; val rispetto ai punteggi di training
        pct = pd.Series(np.nan, index=df.index)
        for cell in cells:
            mc = (df.cell == cell).values
            if (is_oof & mc).sum():
                pct[is_oof & mc] = M.pct_rank(oof[is_oof & mc].values, oof[is_oof & mc].values)
            ref = trs[(df.loc[tr_final, "cell"] == cell).values]
            if (is_val & mc).sum() and ref.size:
                pct[is_val & mc] = M.pct_rank(ref, val[is_val & mc].values)
        scores[name] = pct
        log(f"modello {name}: pronto")

    # ---------------- Market Brain: fase di mercato (terzili sul training 2008-2017)
    tr_rows = df.year.between(2008, 2017).values
    v_cut = np.nanquantile(df.loc[tr_rows, "f_vol_h1_atr_rel"], [1 / 3, 2 / 3])
    e_cut = np.nanquantile(df.loc[tr_rows, "f_efficiency_24h"], [1 / 3, 2 / 3])
    df["phase"] = (np.digitize(df.f_vol_h1_atr_rel.fillna(1.0), v_cut) * 3
                   + np.digitize(df.f_efficiency_24h.fillna(0.0), e_cut))

    def perf(mask, col="r_foto"):
        return M.perf(df.loc[mask, col].values, df.loc[mask, "year"].values)

    # ---------------- per-cell thresholds chosen on OOF 2011-2017
    grid = list(itertools.product((0, 0.5, 0.7, 0.8, 0.9), (0, 0.5, 0.7)))
    per_cell, admitted, rows = {}, {}, []
    for cell in cells:
        mc = (df.cell == cell).values
        best = None
        for s_thr, g_thr in grid:
            m = is_oof & mc & (scores["sel"].values >= s_thr) & (scores["gate"].values >= g_thr)
            p = perf(m)
            rows.append({"cell": cell, "sel": s_thr, "gate": g_thr, "period": "oof",
                         **{k: v for k, v in p.items() if k != "r_by_year"}})
            if p.get("n", 0) < MIN_YEAR_CELL * 7:
                continue
            pos = int(p["years_pos"].split("/")[0])
            if p["avg_r"] > 0 and pos >= 5 and (best is None or p["avg_r"] > best[2]["avg_r"]):
                best = (s_thr, g_thr, p)
        base_oof = perf(is_oof & mc)
        base_val = perf(is_val & mc)
        d = {"baseline_oof": base_oof, "baseline_val": base_val}
        if best:
            s_thr, g_thr, p = best
            mv = is_val & mc & (scores["sel"].values >= s_thr) & (scores["gate"].values >= g_thr)
            d.update({"thr": {"sel": s_thr, "gate": g_thr}, "oof": p, "val": perf(mv), "val_c2": perf(mv, "r_c2")})
            admitted[cell] = (s_thr, g_thr)
        per_cell[cell] = d
    pd.DataFrame(rows).to_csv(OUT / f"phase10_cell_grid_oof{TAG}.csv", index=False)
    log(f"celle ammesse (scelte sul 2011-2017): {admitted}")

    def portfolio_mask(period_mask, brain=None):
        m = np.zeros(len(df), bool)
        for cell, (s_thr, g_thr) in admitted.items():
            mc = (df.cell == cell).values & period_mask & (scores["sel"].values >= s_thr) & \
                (scores["gate"].values >= g_thr)
            if brain is not None:
                mc &= np.isin(df.phase.values, brain.get(cell, []))
            m |= mc
        return m

    # ---------------- Market Brain table on OOF (filtered signals), phases with avg R > 0 and >= 30 trades
    brain = {}
    brain_tab = []
    for cell, (s_thr, g_thr) in admitted.items():
        mc = is_oof & (df.cell == cell).values & (scores["sel"].values >= s_thr) & (scores["gate"].values >= g_thr)
        ok_ph = []
        for ph, g in df[mc].groupby("phase"):
            brain_tab.append({"cell": cell, "phase": int(ph), "n": len(g), "avg_r": round(float(g.r_foto.mean()), 4)})
            if len(g) >= 30 and g.r_foto.mean() > 0:
                ok_ph.append(int(ph))
        brain[cell] = ok_ph
    # Market Brain without AI filters (pure "choose the strategy for the phase") on all 10 cells
    brain_raw = {}
    for cell in cells:
        mc = is_oof & (df.cell == cell).values
        brain_raw[cell] = [int(ph) for ph, g in df[mc].groupby("phase") if len(g) >= 60 and g.r_foto.mean() > 0]

    res = {"admitted_cells_thresholds_oof": {k: {"sel": v[0], "gate": v[1]} for k, v in admitted.items()},
           "per_cell": per_cell, "brain_on_portfolio": brain, "brain_raw": brain_raw,
           "brain_table_oof": brain_tab, "phase_cuts": {"vol_h1_atr_rel": v_cut.tolist(),
                                                        "efficiency_24h": e_cut.tolist()}}
    out = {}
    for name, mk in (("portfolio", lambda pm: portfolio_mask(pm)),
                     ("portfolio+brain", lambda pm: portfolio_mask(pm, brain)),
                     ("brain_only_no_ai", lambda pm: pm & np.array([ph in brain_raw.get(c, []) for c, ph in
                                                                     zip(df.cell.values, df.phase.values)]))):
        mo, mv = mk(is_oof), mk(is_val)
        out[name] = {"oof": perf(mo), "val": perf(mv), "val_c2": perf(mv, "r_c2"),
                     "val_trades_per_year": round(int(mv.sum()) / 4, 1)}
    out["all_signals_baseline"] = {"oof": perf(is_oof), "val": perf(is_val), "val_c2": perf(is_val, "r_c2")}
    res["portfolios"] = out

    # random benchmark for the portfolio on validation
    rng = np.random.default_rng(seed)
    pv = out["portfolio"]["val"]
    if pv.get("n", 0):
        pool = df.loc[is_val, "r_foto"].values
        sims = np.array([rng.choice(pool, pv["n"], replace=False).mean() for _ in range(1000)])
        res["random_benchmark_portfolio_val"] = {"selected": pv["avg_r"], "random_mean": round(float(sims.mean()), 4),
                                                 "share_random_ge": float((sims >= pv["avg_r"]).mean())}
    # criterion
    verdict = {}
    for name in ("portfolio", "portfolio+brain", "brain_only_no_ai"):
        v, v2 = out[name]["val"], out[name]["val_c2"]
        if not v.get("n"):
            verdict[name] = False
            continue
        verdict[name] = bool(v["avg_r"] >= SOLID["avg_r"] and (v["pf"] or 0) >= SOLID["pf"]
                             and int(v["years_pos"].split("/")[0]) >= SOLID["years_pos"] and v2["avg_r"] > 0)
    res["solid_edge_criterion"] = SOLID
    res["verdict"] = verdict
    (OUT / f"phase10_results{TAG}.json").write_text(json.dumps(res, indent=1, default=str))
    log("fatto")
    show = {k: res[k] for k in ("admitted_cells_thresholds_oof", "brain_on_portfolio", "brain_raw", "portfolios",
                                "verdict")}
    print(json.dumps(show, indent=1, default=str)[:15000])
    for cell, d in per_cell.items():
        print(cell, "base_oof", d["baseline_oof"].get("avg_r"), "base_val", d["baseline_val"].get("avg_r"),
              "| thr", d.get("thr"), "oof", d.get("oof", {}).get("avg_r"), "val", d.get("val", {}).get("avg_r"),
              d.get("val", {}).get("n"), d.get("val", {}).get("years_pos"), "val_c2", d.get("val_c2", {}).get("avg_r"))


if __name__ == "__main__":
    main()
