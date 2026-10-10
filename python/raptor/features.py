"""Per-signal features for the ML filter: ratios only, never raw prices (as in the Interstellar
material: "struttura, volatilità, sessione, spread, stop, probabilità delle celle: solo rapporti").
All values are known at the close of the decision bar.
"""
import numpy as np
import pandas as pd

CELLS = ["PPK", "MSS", "MTF_M1", "OTEOF", "PO3", "UNIOF", "LS", "SILVER_BULLET", "WYCKOFF", "WYCKOFF_MTF"]


def signal_features(f: pd.DataFrame, sig: pd.DataFrame) -> pd.DataFrame:
    i = sig.bar_i.values
    s = sig.side.values.astype(float)
    g = lambda k: f[k].values[i]
    c, a = g("close"), g("atr")
    risk = (sig.price.values - sig.sl_struct.values) * s
    X = pd.DataFrame(index=sig.index)
    X["side"] = s
    for cell in CELLS:
        X["cell_" + cell] = (sig.strategy.values == cell).astype(float)
    X["stop_atr_m5"] = risk / a
    X["stop_atr_m15"] = risk / g("m15_atr")
    X["stop_atr_h1"] = risk / g("h1_atr")
    X["stop_atr_d1"] = risk / g("d1_atr")
    X["spread_over_stop"] = g("spread_px") / risk
    X["spread_over_atr"] = g("spread_px") / a
    X["entry_dist_atr"] = (c - sig.price.values) * s / a
    X["vol_m5_rel"] = g("atr_rel")
    X["vol_m15_rel"] = g("m15_atr_rel")
    X["vol_h1_rel"] = g("h1_atr_rel")
    X["vol_d1_rel"] = g("d1_atr_rel")
    X["atr_m5_over_h1"] = a / g("h1_atr")
    for hrs in (4, 24):
        hi, lo = g(f"rng_hi_{hrs}h"), g(f"rng_lo_{hrs}h")
        pos = (c - lo) / np.where(hi - lo > 0, hi - lo, np.nan)
        X[f"pos_range_{hrs}h"] = np.where(s > 0, pos, 1 - pos)  # 0 = discount for the trade side
        X[f"range_{hrs}h_atr"] = (hi - lo) / g("h1_atr")
    X["dist_ema_m5"] = (c - g("ema50")) * s / a
    X["dist_ema_h1"] = (g("h1_close") - g("h1_ema")) * s / g("h1_atr")
    X["dist_ema_h4"] = (g("h4_close") - g("h4_ema")) * s / g("h4_atr")
    X["dist_ema_d1"] = (g("d1_close") - g("d1_ema")) * s / g("d1_atr")
    X["push_60m"] = g("ret_60m") * s / g("h1_atr")
    X["push_3h"] = g("ret_3h") * s / g("h1_atr")
    X["brk_favor_4h"] = np.where(s > 0, g("brk_up_48"), g("brk_dn_48"))
    X["brk_against_4h"] = np.where(s > 0, g("brk_dn_48"), g("brk_up_48"))
    X["is_mss"] = g("is_mss").astype(float)
    X["disp_atr"] = g("disp_body") / a
    X["day_range_d1atr"] = (g("day_hi") - g("day_lo")) / g("d1_atr")
    X["pos_day"] = np.where(s > 0, (c - g("day_lo")), (g("day_hi") - c)) / np.maximum(g("day_hi") - g("day_lo"), 1e-9)
    X["dist_pdh_atr"] = (g("pdh") - c) / g("h1_atr")
    X["dist_pdl_atr"] = (c - g("pdl")) / g("h1_atr")
    for h in ("h1", "h4"):
        X[f"{h}_trend_al"] = np.sign(g(f"{h}_trend")) * s
        X[f"dist_{h}_swing_lo"] = (c - g(f"{h}_swing_lo")) / g(f"{h}_atr")
        X[f"dist_{h}_swing_hi"] = (g(f"{h}_swing_hi") - c) / g(f"{h}_atr")
    X["stop_atr_h4"] = risk / g("h4_atr")
    X["tv_rel"] = g("tv_rel")
    X["tp_r_sig"] = sig["tp_r"].values if "tp_r" in sig.columns else 0.0
    ny = g("ny_min")
    X["ny_sin"] = np.sin(2 * np.pi * ny / 1440); X["ny_cos"] = np.cos(2 * np.pi * ny / 1440)
    X["ny_hour"] = ny // 60
    X["dow"] = g("dow")
    return X.replace([np.inf, -np.inf], np.nan)
