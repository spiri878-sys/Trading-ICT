"""FASE 2 — generatore di segnali delle 6 celle PRIME + confronto con i riferimenti del venditore.

1. feature causali per ogni (TF, k) necessario, dalla serie master (cache in output/cache/feat_prime_*.parquet);
2. segnali 2004 -> 2026-10 per le 6 celle (default), salvati in output/cache/signals/default.parquet;
3. statistiche SOLO 2008-2021 (addestramento + validazione): segnali/anno, ora, lato, rischio;
4. confronto di SOMIGLIANZA con i 18 riferimenti datati del 2026 (PPK/UNIOF): stesso lato e cella entro
   +-1 barra, offset orario 0 / +-60 min; griglia di varianti di definizione registrata in
   output/phase2_match_log.csv. Nessun esito/performance è calcolato o usato.

usage: python python/scripts/phase2_signals.py
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
from raptor.prime.data import ROOT, degraded_days, master_m1  # noqa: E402
from raptor.setups import build_features  # noqa: E402

OUT = ROOT / "output"
CACHE = OUT / "cache"
STATS_FROM, STATS_TO = "2008-01-01", "2022-01-01"


def feats(tf, k):
    p = CACHE / f"feat_prime_{tf}_k{k}.parquet"
    if p.exists():
        return pd.read_parquet(p)
    t = time.time()
    f = build_features(master_m1(), tf, k)
    f.to_parquet(p)
    print(f"features {tf} k={k}: {len(f)} barre in {time.time() - t:.0f}s")
    return f


def load_refs():
    r = pd.read_csv(OUT / "trade_riferimento.csv")
    r = r[r.cella.isin(["PPK", "UNIOF"]) & r.direzione.isin(["BUY", "SELL"])].copy()
    r["t"] = pd.to_datetime(r.data_ora, errors="coerce")
    r = r.dropna(subset=["t"])
    r["side"] = np.where(r.direzione == "BUY", 1, -1)
    return r.reset_index(drop=True)


def match(sig, refs, cell, offsets=(0, -60, 60), on="fill"):
    """Per ogni riferimento della cella: esiste un segnale stesso lato con bar_time o known_at entro una barra
    del riferimento (spostato di offset minuti)? Restituisce n trovati per offset e dettaglio."""
    s = sig[sig.cell == cell]
    rr = refs[refs.cella == cell]
    if rr.empty:
        return {}, []
    tfm = pd.Timedelta(C.TF_OF[cell])
    res, det = {}, []
    for off in offsets:
        hit = 0
        for r in rr.itertuples():
            t = r.t + pd.Timedelta(minutes=off)
            if on == "fill":
                c = s[(s.side == r.side) & ((s.fill_time - t).abs() <= pd.Timedelta("5min"))]
            else:
                c = s[(s.side == r.side) & (((s.bar_time - t).abs() <= tfm) | ((s.known_at - t).abs() <= tfm))]
            ok = len(c) > 0
            hit += ok
            if off == 0:
                det.append({"ref": str(r.t), "cella": cell, "dir": r.direzione, "tipo": r.tipo, "trovato": bool(ok),
                            "nostro_prezzo": float(c.price.iloc[0]) if ok else None,
                            "nostro_sl": float(c.sl_struct.iloc[0]) if ok else None})
        res[off] = hit
    return res, det


def per_year(sig):
    s = sig[(sig.known_at >= STATS_FROM) & (sig.known_at < STATS_TO)]
    return s.groupby(["cell", s.known_at.dt.year]).size().unstack(0).fillna(0).astype(int)


def main():
    t0 = time.time()
    deg = degraded_days()
    need = {(C.TF_OF[c], C.DEFAULTS[c]["k"]) for c in C.CELLS}
    need |= {("5min", 2), ("15min", 2), ("5min", 3), ("15min", 3), ("1h", 3)}
    F = {key: feats(*key) for key in sorted(need)}
    refs = load_refs()

    # ---------------- default signals
    sig = C.generate(F, degraded=deg)
    (CACHE / "signals").mkdir(exist_ok=True)
    sig.to_parquet(CACHE / "signals" / "default.parquet")
    py = per_year(sig)
    s = sig[(sig.known_at >= STATS_FROM) & (sig.known_at < STATS_TO)].copy()
    s["risk_usd"] = (s.price - s.sl_struct).abs()
    s["risk_atr"] = s.risk_usd / s.atr
    stats = {
        "signals_total": int(len(sig)),
        "per_year_2008_2021": {c: {int(y): int(v) for y, v in py[c].items()} for c in py.columns},
        "mean_per_year_2008_2021": {c: round(float(py[c].mean()), 1) for c in py.columns},
        "share_long": {c: round(float((g.side == 1).mean()), 3) for c, g in s.groupby("cell")},
        "risk_usd_median": {c: round(float(g.risk_usd.median()), 2) for c, g in s.groupby("cell")},
        "risk_atr_median": {c: round(float(g.risk_atr.median()), 2) for c, g in s.groupby("cell")},
        "hour_server_top3": {c: g.known_at.dt.hour.value_counts().head(3).to_dict() for c, g in s.groupby("cell")},
        "otype": {c: g.otype.iloc[0] for c, g in s.groupby("cell")},
    }
    # BB on alternative timeframes (TF undocumented)
    for tf in ("5min", "1h"):
        sb = C.generate(F, cells=["BB"], params={"BB": {"tf": tf}}, degraded=deg)
        stats[f"BB_{tf}_mean_per_year"] = round(float(per_year(sb)["BB"].mean()), 1)

    # ---------------- similarity with vendor references (2026, test period: similarity only)
    log = []
    M1 = master_m1()
    grids = {
        "PPK": dict(k=[2, 3], min_disp=[0.8, 1.2], min_fvg=[0.05, 0.15], max_entries=[3, 6],
                    entry_edge=["proximal", "ce", "distal"], expiry=[12, 24, 48], need_bos=[True, False]),
        "UNIOF": dict(k=[2, 3], sweep_bars=[12, 24], min_fvg=[0.05, 0.1], need_sweep=[True, False],
                      entry_edge=["proximal", "ce", "distal"], expiry=[12, 24]),
    }
    details = {}
    for cell, grid in grids.items():
        keys = list(grid)
        for vals in itertools.product(*(grid[k] for k in keys)):
            pr = dict(zip(keys, vals))
            tf = C.TF_OF[cell]
            if (tf, pr["k"]) not in F:
                F[(tf, pr["k"])] = feats(tf, pr["k"])
            sg = C.generate(F, cells=[cell], params={cell: pr}, degraded=deg)
            sg = sg[sg.known_at >= "2025-12-01"].copy()  # solo per il confronto: periodo dei riferimenti
            sg["fill_time"] = C.fill_times(sg, M1)
            res, det = match(sg, refs, cell)
            res_sig, _ = match(sg, refs, cell, on="signal")
            n2026 = int(((sg.known_at >= "2026-01-01") & (sg.known_at < "2026-10-01")).sum())
            log.append({"cell": cell, **pr, "match_off0": res.get(0), "match_off_m60": res.get(-60),
                        "match_off_p60": res.get(60), "match_on_signal_time": res_sig.get(0),
                        "n_refs": int((refs.cella == cell).sum()),
                        "signals_jan_sep_2026": n2026,
                        "is_default": all(C.DEFAULTS[cell][k] == v for k, v in pr.items())})
            if log[-1]["is_default"]:
                details[cell] = det
    lg = pd.DataFrame(log)
    lg.to_csv(OUT / "phase2_match_log.csv", index=False)
    # livello del caso: stessi segnali di default confrontati con i riferimenti spostati di 30..300 minuti
    null = {}
    for cell in grids:
        sg = C.generate(F, cells=[cell], degraded=deg)
        sg = sg[sg.known_at >= "2025-12-01"].copy()
        sg["fill_time"] = C.fill_times(sg, M1)
        offs = [o for o in range(-300, 301, 30) if abs(o) > 60]
        r, _ = match(sg, refs, cell, offsets=offs)
        null[cell] = {"mean": round(float(np.mean(list(r.values()))), 2), "max": int(max(r.values())),
                      "offsets": len(offs)}
    stats["match_chance_level"] = null
    stats["refs"] = {c: int((refs.cella == c).sum()) for c in ("PPK", "UNIOF")}
    stats["match_default"] = {c: lg[(lg.cell == c) & lg.is_default][["match_off0", "match_off_m60", "match_off_p60"]]
                              .iloc[0].to_dict() for c in grids}
    stats["match_best"] = {c: lg[lg.cell == c].assign(best=lambda d: d[["match_off0", "match_off_m60",
                                                                          "match_off_p60"]].max(axis=1))
                           .sort_values(["best", "is_default"], ascending=False).iloc[0].to_dict() for c in grids}
    stats["match_details_default"] = details
    # reference trade 08/01/2026 PPK BUY 4424.56, stop 21$
    ref_t = pd.Timestamp("2026-01-08 12:20")
    best_ppk = lg[lg.cell == "PPK"].sort_values(["match_off0", "is_default"], ascending=False).iloc[0]
    pr = {k: best_ppk[k] for k in grids["PPK"]}
    pr = {k: (int(v) if isinstance(v, (float, np.floating)) and float(v).is_integer() and k != "min_disp" and k != "min_fvg" else v) for k, v in pr.items()}
    sb = C.generate(F, cells=["PPK"], params={"PPK": {**pr, "stop_mode": "atr"}}, degraded=deg)
    sb = sb[sb.known_at >= "2026-01-07"].copy()
    sb["fill_time"] = C.fill_times(sb, M1)
    near = sb[(sb.side == 1) & ((sb.fill_time - ref_t).abs() <= pd.Timedelta("30min"))]
    stats["ref_trade_params_best_ppk"] = pr
    stats["ref_trade_2026_01_08"] = near[["bar_time", "known_at", "fill_time", "price", "sl_struct", "entry_n"]].assign(
        risk=lambda d: d.price - d.sl_struct).astype(str).to_dict("records")
    stats["runtime_s"] = round(time.time() - t0)
    (OUT / "phase2_stats.json").write_text(json.dumps(stats, indent=1, default=str))
    print(json.dumps({k: v for k, v in stats.items() if k != "match_details_default"}, indent=1, default=str))
    lg["best"] = lg[["match_off0", "match_off_m60", "match_off_p60"]].max(axis=1)
    print(lg.sort_values("best", ascending=False).groupby("cell").head(5).to_string())


if __name__ == "__main__":
    main()
