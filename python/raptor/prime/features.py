"""Feature per segnale della ricostruzione PRIME (Fase 4). Elenco e formule: output/feature.md.

Regole: solo rapporti o misure in ATR (mai prezzi assoluti); le grandezze direzionali sono moltiplicate per il
lato del segnale (positivo = a favore del trade); tutto è noto alla chiusura dell'ultima barra prima di
`known_at` (barre del TF della cella: riga bar_i; HTF già uniti sull'orario di disponibilità; M1: ultima barra
chiusa prima di known_at).
"""
import numpy as np
import pandas as pd

from .cells import CELLS

SPREAD_C1 = 0.30
GROUPS = {}  # nome feature -> gruppo (riempito da prime_features)


def _runlen(sign):
    """Lunghezza della serie corrente di barre con lo stesso segno (con segno)."""
    out = np.zeros(sign.size)
    run = 0.0
    for i in range(sign.size):
        s = sign[i]
        if s == 0:
            run = 0.0
        elif run * s > 0:
            run += s
        else:
            run = s
        out[i] = run
    return out


class M1Context:
    """Serie M1 cumulative per feature 'all'istante' (rendimenti, volatilità realizzata, efficienza, volumi)."""

    def __init__(self, m1: pd.DataFrame):
        self.index = m1.index.values
        c = m1.close.values.astype(float)
        self.c = c
        d = np.r_[0.0, np.abs(np.diff(c))]
        self.cum_abs = np.cumsum(d)
        r = np.r_[0.0, np.diff(np.log(c))]
        self.cum_r2 = np.cumsum(r * r)
        tv = m1.tickvol.values.astype(float)
        self.cum_tv = np.cumsum(tv)
        wk = (m1.index - pd.to_timedelta((m1.index.dayofweek + 1) % 7, unit="D")).normalize()
        g = pd.DataFrame({"h": m1.high.values, "l": m1.low.values}, index=m1.index).groupby(wk)
        wh, wl = g.h.max(), g.l.min()
        self.week = wk.values
        self.pwh = wh.shift(1).reindex(wk).values
        self.pwl = wl.shift(1).reindex(wk).values
        self.wk_hi_run = pd.Series(m1.high.values).groupby(wk.values).cummax().values
        self.wk_lo_run = pd.Series(m1.low.values).groupby(wk.values).cummin().values

    def at(self, t):
        """indice dell'ultima M1 chiusa prima dell'istante t (barra con apertura < t - 0 e chiusura <= t)."""
        return np.searchsorted(self.index, np.asarray(t, dtype="datetime64[ns]") - np.timedelta64(1, "m"),
                               side="right") - 1

    def window(self, j, n):
        j0 = np.clip(j - n, 0, None)
        return j0


def prime_features(sig: pd.DataFrame, F: dict, ctx: M1Context, onehot=None) -> pd.DataFrame:
    """sig: segnali di cells.generate (colonne bar_i, known_at, cell, tf, side, price, sl_struct, atr_m15, ...).
    F: {(tf, k): feature del TF} usate per generare i segnali (k di default per cella)."""
    sig = sig.reset_index(drop=True)
    n = len(sig)
    s = sig.side.values.astype(float)
    X = {}
    grp = {}

    def put(name, val, group):
        X[name] = np.asarray(val, float)
        grp[name] = group

    # per-TF lookup of the signal bar row
    cols = {}
    for tf in sig.tf.unique():
        k = 3  # k di default di tutte le celle (cells.DEFAULTS)
        f = F[(tf, k)]
        m = (sig.tf == tf).values
        bi = sig.bar_i.values[m]
        if "runlen" not in f:
            f["runlen"] = _runlen(np.sign(f.close.values - f.open.values))
            f["fvg_any"] = (np.isfinite(f.fvg_bull_top.values) | np.isfinite(f.fvg_bear_top.values)).astype(float)
            f["fvg_cnt_24"] = pd.Series(f["fvg_any"].values).rolling(24, min_periods=1).sum().values
            sw = (f.sweep_hi.values | f.sweep_lo.values).astype(float)
            f["sweep_cnt_48"] = pd.Series(sw).rolling(48, min_periods=1).sum().values
        for col in f.columns:
            if col not in cols:
                cols[col] = np.full(n, np.nan)
            cols[col][m] = f[col].values[bi].astype(float)
    g = lambda k: cols[k]  # noqa: E731
    c, a = g("close"), g("atr")
    a15, a1h, a4h, a1d = g("m15_atr"), g("h1_atr"), g("h4_atr"), g("d1_atr")
    price = sig.price.values.astype(float)
    risk_s = (price - sig.sl_struct.values) * s
    risk_a = 3.0 * sig.atr_m15.values.astype(float)

    # ---------------- A. segnale
    put("side", s, "A")
    for cell in (onehot or CELLS):
        put(f"cell_{cell}", (sig.cell.values == cell).astype(float), "A")
    put("is_market", (sig.otype.values == "market").astype(float), "A")
    put("entry_n", sig["entry_n"].fillna(1).values if "entry_n" in sig else np.ones(n), "A")
    for nm, at in (("tf", a), ("m15", a15), ("h1", a1h), ("h4", a4h), ("d1", a1d)):
        put(f"stop_struct_atr_{nm}", risk_s / at, "A")
    put("stop_atr3_atr_h1", risk_a / a1h, "A")
    put("stop_struct_over_atr3", risk_s / risk_a, "A")
    put("entry_dist_atr", (c - price) * s / a, "A")
    put("zone_width_atr", (sig.zone_hi.values - sig.zone_lo.values) / a, "A")
    leg = sig.leg_hi.values - sig.leg_lo.values
    put("leg_atr", leg / a, "A")
    pos_leg = (price - sig.leg_lo.values) / np.where(leg > 0, leg, np.nan)
    put("entry_fib_in_leg", np.where(s > 0, 1 - pos_leg, pos_leg), "A")  # 0 = estremo della gamba, 1 = origine

    # ---------------- B. volatilità
    for nm in ("atr_rel", "m15_atr_rel", "h1_atr_rel", "h4_atr_rel", "d1_atr_rel"):
        put(f"vol_{nm}", g(nm), "B")
    put("atr_tf_over_h1", a / a1h, "B")
    put("atr_m15_over_h1", a15 / a1h, "B")
    put("atr_h1_over_d1", a1h / a1d, "B")
    put("atr_h4_over_d1", a4h / a1d, "B")
    j = ctx.at(sig.known_at.values)
    for mins in (30, 60, 240):
        j0 = np.clip(j - mins, 0, None)
        rv = np.sqrt(np.maximum(ctx.cum_r2[j] - ctx.cum_r2[j0], 0)) * ctx.c[j]
        put(f"rvol_{mins}m_over_atr_h1", rv / a1h, "B")
    for hrs in (4, 24):
        put(f"range_{hrs}h_atr_h1", (g(f"rng_hi_{hrs}h") - g(f"rng_lo_{hrs}h")) / a1h, "B")
    put("day_range_atr_d1", (g("day_hi") - g("day_lo")) / a1d, "B")
    put("bar_body_atr", g("body") / a, "B")
    put("bar_range_atr", (g("high") - g("low")) / a, "B")
    put("disp_atr", g("disp_body") / a, "B")

    # ---------------- C. struttura
    put("brk_favor_4h", np.where(s > 0, g("brk_up_48"), g("brk_dn_48")), "C")
    put("brk_against_4h", np.where(s > 0, g("brk_dn_48"), g("brk_up_48")), "C")
    put("brk_now_al", g("brk") * s, "C")
    put("is_mss", g("is_mss"), "C")
    for h in ("m15", "h1", "h4", "d1"):
        at = g(f"{h}_atr")
        put(f"{h}_trend_al", np.sign(g(f"{h}_trend")) * s, "C")
        put(f"dist_{h}_ema", (g(f"{h}_close") - g(f"{h}_ema")) * s / at, "C")
        put(f"dist_{h}_swing_fav", np.where(s > 0, g(f"{h}_swing_hi") - c, c - g(f"{h}_swing_lo")) / at, "C")
        put(f"dist_{h}_swing_adv", np.where(s > 0, c - g(f"{h}_swing_lo"), g(f"{h}_swing_hi") - c) / at, "C")
    put("dist_tf_ema", (c - g("ema50")) * s / a, "C")
    for hrs in (4, 24):
        hi, lo = g(f"rng_hi_{hrs}h"), g(f"rng_lo_{hrs}h")
        pos = (c - lo) / np.where(hi - lo > 0, hi - lo, np.nan)
        put(f"pos_range_{hrs}h", np.where(s > 0, pos, 1 - pos), "C")
    dh, dl = g("day_hi"), g("day_lo")
    put("pos_day", np.where(s > 0, c - dl, dh - c) / np.where(dh - dl > 0, dh - dl, np.nan), "C")
    wh, wl = ctx.wk_hi_run[j], ctx.wk_lo_run[j]
    put("pos_week", np.where(s > 0, c - wl, wh - c) / np.where(wh - wl > 0, wh - wl, np.nan), "C")
    put("dist_pdh_atr_h1", (g("pdh") - c) * s / a1h, "C")
    put("dist_pdl_atr_h1", (c - g("pdl")) * s / a1h, "C")
    put("dist_pwh_atr_d1", (ctx.pwh[j] - c) * s / a1d, "C")
    put("dist_pwl_atr_d1", (c - ctx.pwl[j]) * s / a1d, "C")
    put("dist_asia_hi_atr_h1", (g("asia_hi") - c) * s / a1h, "C")
    put("dist_asia_lo_atr_h1", (c - g("asia_lo")) * s / a1h, "C")
    put("asia_range_atr_h1", (g("asia_hi") - g("asia_lo")) / a1h, "C")
    put("asia_known", np.isfinite(g("asia_hi")).astype(float), "C")
    put("fvg_count_24bars", g("fvg_cnt_24"), "C")
    put("sweep_count_48bars", g("sweep_cnt_48"), "C")
    put("sweep_lo_now", g("sweep_lo") * 1.0, "C")
    put("sweep_hi_now", g("sweep_hi") * 1.0, "C")

    # ---------------- D. momentum / efficienza
    for mins in (15, 60, 180, 1440):
        j0 = np.clip(j - mins, 0, None)
        put(f"push_{mins}m_atr_h1", (ctx.c[j] - ctx.c[j0]) * s / a1h, "D")
    for mins in (240, 1440):
        j0 = np.clip(j - mins, 0, None)
        path = ctx.cum_abs[j] - ctx.cum_abs[j0]
        put(f"efficiency_{mins // 60}h", np.abs(ctx.c[j] - ctx.c[j0]) / np.where(path > 0, path, np.nan), "D")
        put(f"efficiency_{mins // 60}h_signed", (ctx.c[j] - ctx.c[j0]) * s / np.where(path > 0, path, np.nan), "D")
    put("run_bars_al", g("runlen") * s, "D")

    # ---------------- E. volumi
    put("tv_rel_tf", g("tv_rel"), "E")
    tv60 = ctx.cum_tv[j] - ctx.cum_tv[np.clip(j - 60, 0, None)]
    tv1d = (ctx.cum_tv[j] - ctx.cum_tv[np.clip(j - 1440, 0, None)]) / 24.0
    put("tv_60m_over_1d_hourly", tv60 / np.where(tv1d > 0, tv1d, np.nan), "E")

    # ---------------- F. sessione / tempo
    ny = g("ny_min")
    put("ny_sin", np.sin(2 * np.pi * ny / 1440), "F")
    put("ny_cos", np.cos(2 * np.pi * ny / 1440), "F")
    put("ny_hour", ny // 60, "F")
    put("dow", g("dow"), "F")
    put("kz_asia", (ny >= 20 * 60).astype(float), "F")
    put("kz_london", ((ny >= 120) & (ny < 300)).astype(float), "F")
    put("kz_ny", ((ny >= 420) & (ny < 600)).astype(float), "F")
    srv = sig.known_at.dt.hour.values * 60 + sig.known_at.dt.minute.values
    put("min_since_day_open", srv - 60, "F")
    mo = sig.known_at.dt.month.values
    put("month_sin", np.sin(2 * np.pi * mo / 12), "F")
    put("month_cos", np.cos(2 * np.pi * mo / 12), "F")

    # ---------------- G. costi
    put("spread_over_stop_struct", SPREAD_C1 / risk_s, "G")
    put("spread_over_stop_atr3", SPREAD_C1 / risk_a, "G")
    put("spread_over_atr_tf", SPREAD_C1 / a, "G")

    # ---------------- H. contesto delle celle (solo segnali PRECEDENTI)
    t = sig.known_at.values.astype("datetime64[ns]").astype(np.int64)
    order = np.argsort(t, kind="stable")
    ts = t[order]
    hour, day30, day = 3600 * 10 ** 9, 1800 * 10 ** 9, 86400 * 10 ** 9
    cnt = lambda arr, w: np.searchsorted(arr, t, side="left") - np.searchsorted(arr, t - w, side="left")  # noqa: E731
    put("sig_all_1h", cnt(ts, hour), "H")
    put("sig_all_24h", cnt(ts, day), "H")
    same1 = np.zeros(n); same24 = np.zeros(n)
    for cell in np.unique(sig.cell.values):
        m = sig.cell.values == cell
        tc = np.sort(t[m])
        same1[m] = (np.searchsorted(tc, t[m], side="left") - np.searchsorted(tc, t[m] - hour, side="left"))
        same24[m] = (np.searchsorted(tc, t[m], side="left") - np.searchsorted(tc, t[m] - day, side="left"))
    put("sig_same_cell_1h", same1, "H")
    put("sig_same_cell_24h", same24, "H")
    agree = np.zeros(n); disagree = np.zeros(n)
    for sd in (1, -1):
        tc = np.sort(t[sig.side.values == sd])
        k_ = np.searchsorted(tc, t, side="left") - np.searchsorted(tc, t - day30, side="left")
        agree += np.where(sig.side.values == sd, k_, 0)
        disagree += np.where(sig.side.values != sd, k_, 0)
    put("sig_agree_30m", agree, "H")
    put("sig_disagree_30m", disagree, "H")

    out = pd.DataFrame(X).replace([np.inf, -np.inf], np.nan)
    GROUPS.clear()
    GROUPS.update(grp)
    return out


# documentazione (output/feature.md): prefisso/nome -> (formula, timeframe, fonte)
DOC = [
    ("side", "lato del segnale (+1 buy, -1 sell)", "-", "nostra"),
    ("cell_", "one-hot della cella che ha generato il segnale", "-", "SITO: ogni cella col suo modello"),
    ("is_market", "1 se ingresso a mercato (LS), 0 se limit", "-", "nostra"),
    ("entry_n", "numero d'ingresso nella stessa gamba (PPK in sequenza)", "TF cella", "SITO: ingressi in sequenza"),
    ("stop_struct_atr_", "distanza ingresso-stop strutturale / ATR14 del TF indicato", "TF/M15/H1/H4/D1",
     "FOTO: stop in ATR M15/H1"),
    ("stop_atr3_atr_h1", "stop 3xATR M15 / ATR H1", "M15/H1", "Fase 2 (trade 08/01)"),
    ("stop_struct_over_atr3", "stop strutturale / stop 3xATR M15", "M15", "nostra"),
    ("entry_dist_atr", "(chiusura - prezzo d'ingresso) x lato / ATR TF: profondità del ritracciamento richiesto",
     "TF cella", "nostra"),
    ("zone_width_atr", "ampiezza della zona d'ingresso (FVG/OTE/breaker) / ATR TF", "TF cella", "nostra"),
    ("leg_atr", "ampiezza della gamba di riferimento / ATR TF", "TF cella", "nostra"),
    ("entry_fib_in_leg", "posizione dell'ingresso nella gamba (0 = estremo, 1 = origine)", "TF cella",
     "SITO Premium: Fibonacci"),
    ("vol_", "ATR14 / media 100 barre dello stesso TF (regime di volatilità)", "TF/M15/H1/H4/D1", "V5: volatilità"),
    ("atr_", "rapporti fra ATR di timeframe diversi", "multi-TF", "V5: contesto multi-timeframe"),
    ("rvol_", "volatilità realizzata M1 (radice somma rendimenti log^2) x prezzo / ATR H1", "M1", "nostra"),
    ("range_", "ampiezza massimo-minimo delle ultime 4h/24h / ATR H1", "TF cella", "FOTO: range 4h/24h"),
    ("day_range_atr_d1", "range del giorno server finora / ATR D1", "TF cella", "nostra"),
    ("bar_body_atr", "corpo della barra del segnale / ATR TF", "TF cella", "nostra"),
    ("bar_range_atr", "range della barra del segnale / ATR TF", "TF cella", "nostra"),
    ("disp_atr", "corpo massimo delle ultime 3 barre / ATR TF (displacement)", "TF cella", "V5/SITO: displacement"),
    ("brk_favor_4h", "rotture di struttura a favore nelle ultime 4h", "TF cella", "FOTO: rotture a favore"),
    ("brk_against_4h", "rotture di struttura contro nelle ultime 4h", "TF cella", "FOTO: rotture contro"),
    ("brk_now_al", "rottura sulla barra del segnale x lato", "TF cella", "nostra"),
    ("is_mss", "la rottura corrente è un cambio di struttura (MSS)", "TF cella", "PRES: MSS"),
    ("_trend_al", "direzione dell'ultima rottura HTF x lato", "M15/H1/H4/D1", "V5: multi-timeframe"),
    ("dist_", "distanze (con lato) da EMA50, swing, PDH/PDL, PWH/PWL, massimo/minimo asiatico in ATR",
     "multi-TF", "FOTO: distanza dalla media"),
    ("pos_", "posizione del prezzo nel range 4h/24h/giorno/settimana (0 = sconto per il lato)", "multi",
     "FOTO: posizione nel range"),
    ("asia_range_atr_h1", "ampiezza del range asiatico (03-07 server) / ATR H1", "TF cella", "nostra (PO3)"),
    ("asia_known", "1 se il range asiatico del giorno è già chiuso", "TF cella", "nostra"),
    ("fvg_count_24bars", "FVG formati nelle ultime 24 barre", "TF cella", "nostra"),
    ("sweep_count_48bars", "sweep di liquidità nelle ultime 48 barre", "TF cella", "SITO: liquidità"),
    ("sweep_", "sweep sulla barra del segnale", "TF cella", "nostra"),
    ("push_", "variazione del prezzo (x lato) negli ultimi N minuti / ATR H1", "M1", "FOTO: spinta 60 min / 3 h"),
    ("efficiency_", "|spostamento netto| / somma dei movimenti M1 (versione con segno x lato)", "M1",
     "FOTO: efficienza 4h"),
    ("run_bars_al", "barre consecutive nella stessa direzione x lato", "TF cella", "nostra"),
    ("tv_", "volume tick relativo (TF: / mediana 96 barre; M1: ultima ora / media oraria del giorno)",
     "TF/M1", "V5: volumi"),
    ("ny_", "ora di New York (sin/cos e ora intera)", "-", "FOTO: ora del giorno"),
    ("dow", "giorno della settimana", "-", "nostra"),
    ("kz_", "killzone Asia (NY 20-24), Londra (NY 02-05), New York (NY 07-10)", "-", "ICT"),
    ("min_since_day_open", "minuti dall'apertura del giorno server (01:00)", "-", "nostra"),
    ("month_", "mese (sin/cos)", "-", "nostra"),
    ("spread_", "spread dello scenario C1 / stop o / ATR", "-", "FOTO: spread rispetto alla volatilità"),
    ("sig_", "segnali precedenti (tutte le celle / stessa cella / concordi / discordi) in 30 min, 1 h, 24 h",
     "-", "FOTO: probabilità delle celle (contesto)"),
]


def doc_for(name):
    best = None
    for key, *rest in DOC:
        if name == key or name.startswith(key) or (key.startswith("_") and key in name):
            if best is None or len(key) > len(best[0]):
                best = (key, *rest)
    return best
