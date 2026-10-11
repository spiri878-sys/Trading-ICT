"""TG-01: audit of a Telegram XAUUSD signal channel (export result.json) against real M1 bars.

1. parse the signals; calibrate Telegram time -> server time (price at post time must match the quoted entry);
2. simulate a follower for every combination of entry method x latency x management x max hold x costs;
3. report totals, monthly results, drawdown, and the channel's own claims vs. what the market did.

usage: python scripts/tg01_signal_channel.py <result.json> [offset_minutes=60]
"""
import itertools
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from raptor.data import load_m1  # noqa: E402
from raptor.signals.follow import limit_fill, sim_signal  # noqa: E402
from raptor.signals.telegram_parse import parse_export  # noqa: E402

OUT = Path(__file__).resolve().parents[2] / "reports"
COMM_PER_OZ = 0.07  # 3.5 $/lot/side round trip = 7 $/lot = 0.07 $/oz
LOT = 0.10           # total size per signal for the $ figures (10 oz)


def mgmt_defs(K):
    """Management plans for a signal with K numbered TPs. Returns name -> (leg_tp, leg_w, be_k, step)."""
    d = {}
    one = lambda k: (np.array([k]), np.array([1.0]))  # noqa: E731
    for k in range(min(K, 6)):
        d[f"ALL_TP{k + 1}"] = (*one(k), -1, False)
        if k >= 1:
            d[f"ALL_TP{k + 1}_BE1"] = (*one(k), 0, False)
    eq = np.arange(K)
    d["CHAN_1perTP_BE1"] = (eq, np.full(K, 1.0 / K), 0, False)
    d["CHAN_1perTP_noBE"] = (eq, np.full(K, 1.0 / K), -1, False)
    d["CHAN_1perTP_BE1_step"] = (eq, np.full(K, 1.0 / K), 0, True)
    d["CHAN_1perTP_BE2"] = (eq, np.full(K, 1.0 / K), 1, False)
    run = np.append(eq, -1)
    d["CHAN_1perTP+runner_BE1"] = (run, np.full(K + 1, 1.0 / (K + 1)), 0, False)
    d["CHAN_1perTP+runner_BE1_step"] = (run, np.full(K + 1, 1.0 / (K + 1)), 0, True)
    d["HALF_TP1_HALF_lastTP_BE1"] = (np.array([0, K - 1]), np.array([0.5, 0.5]), 0, False)
    d["HALF_TP1_HALF_runner_BE1_step"] = (np.array([0, -1]), np.array([0.5, 0.5]), 0, True)
    if K >= 3:
        d["THIRDS_TP1_TP2_TP3_BE1"] = (np.array([0, 1, 2]), np.full(3, 1 / 3), 0, False)
        d["THIRDS_TP1_TP2_TP3_noBE"] = (np.array([0, 1, 2]), np.full(3, 1 / 3), -1, False)
        d["HALF_TP1_HALF_TP3_BE1"] = (np.array([0, 2]), np.array([0.5, 0.5]), 0, False)
    return d


def entries(s, t_idx, o, h, l, spread, slip, mode, lat, expiry):
    """Return list of (bar_index, fill_price, weight) for one signal under an entry mode."""
    side = s.side
    i_post = s.i_post + lat
    if mode == "MKT_POST":
        px = o[i_post] + (spread + slip if side == 1 else -slip)
        return [(i_post, px, 1.0)]
    if mode == "MKT_ALERT":
        i = (s.i_alert if s.i_alert >= 0 else s.i_post) + lat
        px = o[i] + (spread + slip if side == 1 else -slip)
        return [(i, px, 1.0)]
    if mode in ("LIM_Z1", "LIM_MID", "LIM_Z2"):
        p = {"LIM_Z1": s.z1, "LIM_MID": (s.z1 + s.z2) / 2, "LIM_Z2": s.z2}[mode]
        i, px = limit_fill(o, h, l, i_post, i_post + expiry, side, p, spread)
        return [(i, px, 1.0)] if i >= 0 else []
    if mode == "SPLIT_MKT_Z2":
        px = o[i_post] + (spread + slip if side == 1 else -slip)
        out = [(i_post, px, 0.5)]
        i, p2 = limit_fill(o, h, l, i_post, i_post + expiry, side, s.z2, spread)
        if i >= 0:
            out.append((i, p2, 0.5))
        return out
    raise ValueError(mode)


def run_variant(sig, bars, mode, lat, expiry, mg, hold, spread, slip):
    o, h, l, c = bars
    rows = []
    for s in sig.itertuples():
        K = len(s.tps)
        if K == 0 or np.isnan(s.sl):
            continue
        plans = mgmt_defs(K)
        if mg not in plans:
            continue
        leg_tp, leg_w, be_k, step = plans[mg]
        tps = np.array(s.tps, float)
        pnl = 0.0
        filled_w = 0.0
        k_hit = 0
        full_sl = False
        for i, px, w in entries(s, None, o, h, l, spread, slip, mode, lat, expiry):
            if (s.sl - px) * s.side >= 0:  # already beyond SL at fill
                continue
            pu, kh, ei, mae, fsl = sim_signal(o, h, l, c, i, hold, s.side, px, s.sl, tps, leg_tp.astype(np.int64),
                                               leg_w.astype(float), be_k, 0.0, step, spread, slip)
            pnl += w * (pu - COMM_PER_OZ)
            filled_w += w
            k_hit = max(k_hit, kh)
            full_sl |= fsl
        if filled_w == 0:
            continue
        rows.append((s.msg_id, s.post_time, s.side, pnl, (s.z1 - s.sl) * s.side, k_hit, full_sl, filled_w))
    return pd.DataFrame(rows, columns=["msg_id", "post_time", "side", "pnl_oz", "risk_oz", "tp_hit", "full_sl",
                                       "filled_w"])


def summarize(t):
    if t.empty:
        return {}
    usd = t.pnl_oz * LOT * 100
    eq = usd.cumsum()
    dd = (eq.cummax().clip(lower=0) - eq).max()
    mo = usd.groupby(t.post_time.dt.to_period("M")).sum()
    gp, gl = usd[usd > 0].sum(), -usd[usd < 0].sum()
    return dict(n=len(t), win_pct=round(100 * (usd > 0).mean(), 1), full_sl_pct=round(100 * t.full_sl.mean(), 1),
                total_usd_lot010=round(usd.sum(), 0), avg_usd=round(usd.mean(), 2), pf=round(gp / gl, 2) if gl else 99,
                max_dd_usd=round(dd, 0), avg_R=round((t.pnl_oz / t.risk_oz).mean(), 3),
                months_pos=f"{(mo > 0).sum()}/{len(mo)}", worst_month=round(mo.min(), 0), best_month=round(mo.max(), 0))


def main():
    path = sys.argv[1]
    off = int(sys.argv[2]) if len(sys.argv) > 2 else 60
    sig = parse_export(path)
    m1 = load_m1().loc["2026-02-25":]
    idx = m1.index.values
    sig = sig.dropna(subset=["sl"]).copy()
    sig = sig[sig.tps.str.len() > 0]
    srv = sig.post_time + pd.Timedelta(minutes=off)
    sig["i_post"] = np.searchsorted(idx, srv.values.astype("datetime64[ns]"), side="right")  # first bar after msg
    al = sig.alert_time + pd.Timedelta(minutes=off)
    ia = np.searchsorted(idx, al.fillna(pd.Timestamp("2100-01-01")).values.astype("datetime64[ns]"), side="right")
    sig["i_alert"] = np.where(sig.alert_time.notna(), ia, -1)
    sig = sig[sig.i_post < len(idx) - 2].reset_index(drop=True)
    bars = (m1.open.values, m1.high.values, m1.low.values, m1.close.values)

    # ---------------- channel claims ----------------
    d = json.load(open(path, encoding="utf-8"))
    txt = lambda m: m["text"] if isinstance(m["text"], str) else "".join(  # noqa: E731
        x if isinstance(x, str) else x.get("text", "") for x in m["text"])
    msgs = [m for m in d["messages"] if m.get("type") == "message"]
    import re
    tp_claims = [m for m in msgs if re.match(r"^\s*TP\s*\d\s*✅", txt(m))]
    stop_claims = [m for m in msgs if re.match(r"^\s*stop\s*🛑", txt(m), re.I)]
    claims = dict(signals=len(sig), tp_announcements=len(tp_claims),
                  tp1_announcements=sum(1 for m in tp_claims if re.match(r"^\s*TP\s*1\s*✅", txt(m))),
                  stop_announcements=len(stop_claims))

    # ---------------- reference: the channel's own fill, perfect execution ----------------
    grid = []
    entries_modes = [("MKT_ALERT", 0, 0), ("MKT_POST", 0, 0), ("MKT_POST", 1, 0), ("MKT_POST", 3, 0),
                     ("LIM_Z1", 0, 60), ("LIM_MID", 0, 60), ("LIM_Z2", 0, 60), ("LIM_Z2", 0, 240),
                     ("SPLIT_MKT_Z2", 0, 120)]
    mgs = list(mgmt_defs(6).keys())
    holds = [60, 240, 1440]
    costs = [("RAW", 0.10, 0.02), ("STD", 0.30, 0.05)]
    for (mode, lat, exp), mg, hold, (cn, sp, sl) in itertools.product(entries_modes, mgs, holds, costs):
        t = run_variant(sig, bars, mode, lat, exp, mg, hold, sp, sl)
        r = summarize(t)
        if r:
            grid.append(dict(entry=mode, lat_min=lat, expiry=exp, mgmt=mg, max_hold_min=hold, cost=cn, **r))
    g = pd.DataFrame(grid).sort_values("total_usd_lot010", ascending=False)
    g.to_csv(OUT / "tg01_grid.csv", index=False)

    # main follower scenario: market at post (+1 min), channel-style management, 24h, standard costs
    main_cfgs = {
        "channel_style": ("MKT_POST", 1, 0, "CHAN_1perTP+runner_BE1", 1440, 0.30, 0.05),
        "best_grid_STD": None,
    }
    gs = g[g.cost == "STD"].iloc[0]
    main_cfgs["best_grid_STD"] = (gs.entry, int(gs.lat_min), int(gs.expiry), gs.mgmt, int(gs.max_hold_min), 0.30, 0.05)
    monthly = {}
    for name, (mode, lat, exp, mg, hold, sp, sl) in main_cfgs.items():
        t = run_variant(sig, bars, mode, lat, exp, mg, hold, sp, sl)
        usd = t.pnl_oz * LOT * 100
        mo = pd.DataFrame({"trades": usd.groupby(t.post_time.dt.to_period("M")).size(),
                           "usd_lot010": usd.groupby(t.post_time.dt.to_period("M")).sum().round(0)})
        monthly[name] = {"config": [mode, lat, exp, mg, hold, sp, sl], "summary": summarize(t),
                         "monthly": {str(k): v for k, v in mo.to_dict("index").items()}}
        t.to_csv(OUT / f"tg01_trades_{name}.csv", index=False)
    stats = dict(n_signals_parsed=int(len(sig)), offset_minutes=off,
                 risk_median=float(((sig.z1 - sig.sl) * sig.side).median()),
                 tp1_dist_median=float((sig.tps.str[0] - sig.z1).mul(sig.side).median()),
                 claims=claims, n_variants=len(g), share_variants_profitable_STD=round(
                     float((g[g.cost == "STD"].total_usd_lot010 > 0).mean()), 3),
                 share_variants_profitable_RAW=round(float((g[g.cost == "RAW"].total_usd_lot010 > 0).mean()), 3),
                 main=monthly)
    json.dump(stats, open(OUT / "tg01_summary.json", "w"), indent=1, default=str)
    print(json.dumps({k: v for k, v in stats.items() if k != "main"}, indent=1, default=str))
    for k, v in monthly.items():
        print(k, v["config"], v["summary"])
        print(pd.DataFrame(v["monthly"]).T)
    pd.set_option("display.width", 250)
    print(g.head(25).to_string())
    print(g[g.cost == "STD"].head(15).to_string())


if __name__ == "__main__":
    main()
