"""Autoallenamento PRIME (Fase 11): memoria ombra, riaddestramento periodico, soglia, portafoglio a un trade.

Idea: l'EA simula in ombra OGNI segnale delle celle (anche quelli scartati) con la stessa gestione FOTO. Quando
l'esito di un segnale ombra è noto (uscita avvenuta) entra nella memoria. Dalla memoria derivano:

* feature di memoria: come sono andati di recente i segnali dello stesso tipo (cella x lato, cella x lato x
  sessione) negli ultimi N segnali chiusi / ultimi D giorni. "Questo trade l'ho scartato perché negli ultimi
  2 anni non andava bene";
* riaddestramento: a ogni data di riaddestramento il modello è rifatto SOLO sui segnali con uscita già avvenuta
  (nessun esito futuro), con finestra mobile e/o pesi che decadono con l'età (il mercato cambia).

Nessun lookahead: ogni grandezza al tempo t usa solo segnali con exit_time < t.
"""
import numpy as np
import pandas as pd

from .models import fit_lgbm

SESSIONS = ((0, 420, "asia"), (420, 900, "london"), (900, 1440, "ny"))  # minuti server (NY+7)


def session_of(times: pd.Series) -> np.ndarray:
    mod = (times.dt.hour * 60 + times.dt.minute).values
    out = np.empty(mod.size, dtype=object)
    for lo, hi, name in SESSIONS:
        out[(mod >= lo) & (mod < hi)] = name
    return out


def shadow_memory(df: pd.DataFrame, r_col: str, exit_col: str, keys: list, n_last=(30, 100), days=(90, 365, 730),
                  prefix="mem", min_n=10) -> pd.DataFrame:
    """Per ogni riga: media degli R dei segnali dello stesso gruppo (keys) con uscita PRIMA di known_at.
    n_last: ultimi N segnali chiusi; days: segnali chiusi negli ultimi D giorni. NaN se meno di min_n esiti."""
    out = {}
    t = df.known_at.values.astype("datetime64[ns]")
    ok = df[r_col].notna().values & df[exit_col].notna().values
    gkey = df[keys].astype(str).agg("|".join, axis=1).values if len(keys) else np.full(len(df), "all")
    cols = {f"{prefix}_n{n}": np.full(len(df), np.nan) for n in n_last}
    cols.update({f"{prefix}_d{d}": np.full(len(df), np.nan) for d in days})
    cols[f"{prefix}_cnt365"] = np.zeros(len(df))
    for g in np.unique(gkey):
        q = np.where(gkey == g)[0]
        src = q[ok[q]]
        if src.size == 0:
            continue
        ex = df[exit_col].values[src].astype("datetime64[ns]")
        o = np.argsort(ex, kind="stable")
        ex, r = ex[o], df[r_col].values[src][o].astype(float)
        cs = np.concatenate([[0.0], np.cumsum(r)])
        k = np.searchsorted(ex, t[q], side="left")          # esiti noti strettamente prima di t
        for n in n_last:
            k0 = np.maximum(k - n, 0)
            cnt = k - k0
            v = np.where(cnt >= min_n, (cs[k] - cs[k0]) / np.maximum(cnt, 1), np.nan)
            cols[f"{prefix}_n{n}"][q] = v
        for d in days:
            k0 = np.searchsorted(ex, t[q] - np.timedelta64(d, "D"), side="left")
            cnt = k - k0
            v = np.where(cnt >= min_n, (cs[k] - cs[k0]) / np.maximum(cnt, 1), np.nan)
            cols[f"{prefix}_d{d}"][q] = v
            if d == 365:
                cols[f"{prefix}_cnt365"][q] = cnt
    for kk, v in cols.items():
        out[kk] = v
    return pd.DataFrame(out, index=df.index)


def retrain_dates(start: str, end: str, every: str = "QS") -> pd.DatetimeIndex:
    return pd.date_range(start, end, freq=every)


def walk_forward_selftrain(df: pd.DataFrame, feats: list, target: str, exit_col: str, dates: pd.DatetimeIndex,
                           window_years=None, half_life_years=None, train_start="2005-01-01", objective=None,
                           params=None, rounds=300, seed=0, min_rows=2000, return_models=False):
    """Punteggi fuori campione con riaddestramento a ogni data di `dates`.

    Per il blocco [dates[i], dates[i+1]) il modello è addestrato sui segnali con known_at >= train_start (e
    >= dates[i] - window_years) la cui uscita (exit_col) è < dates[i]: solo esiti già noti in quel momento.
    half_life_years: peso 0.5**(età/half_life) sull'età del segnale al momento del riaddestramento."""
    score = pd.Series(np.nan, index=df.index)
    t = df.known_at
    ex = df[exit_col]
    y_all = df[target]
    models = {}
    for i, d in enumerate(dates):
        d_end = dates[i + 1] if i + 1 < len(dates) else t.max() + pd.Timedelta(days=1)
        te = (t >= d) & (t < d_end)
        if not te.any():
            continue
        tr = (t >= pd.Timestamp(train_start)) & ex.notna() & (ex < d) & y_all.notna()
        if window_years:
            tr &= t >= d - pd.DateOffset(years=window_years)
        if tr.sum() < min_rows:
            continue
        w = None
        if half_life_years:
            age = (d - t[tr]).dt.days.values / 365.25
            w = 0.5 ** (age / half_life_years)
        import lightgbm as lgb
        from .models import LGB_PARAMS
        p = {**LGB_PARAMS, **(params or {}), "seed": seed}
        if objective:
            p["objective"] = objective
        ds = lgb.Dataset(df.loc[tr, feats], label=y_all[tr].astype(float), weight=w)
        m = lgb.train(p, ds, num_boost_round=rounds)
        score[te] = m.predict(df.loc[te, feats])
        if return_models:
            models[d] = m
    return (score, models) if return_models else score


def one_at_a_time(fill_time, exit_time, take, r):
    """Esecuzione reale: una posizione per volta. Restituisce la maschera dei trade effettivamente aperti
    (ordine per fill_time; un segnale è saltato se il suo riempimento cade prima dell'uscita del trade aperto)."""
    ft = np.asarray(fill_time, "datetime64[ns]")
    et = np.asarray(exit_time, "datetime64[ns]")
    cand = np.where(np.asarray(take) & ~np.isnat(ft) & ~np.isnat(et) & np.isfinite(np.asarray(r, float)))[0]
    cand = cand[np.argsort(ft[cand], kind="stable")]
    opened = np.zeros(len(ft), bool)
    busy_until = np.datetime64("1900-01-01")
    for i in cand:
        if ft[i] >= busy_until:
            opened[i] = True
            busy_until = et[i]
    return opened


def equity(r, times, risk=0.01, start=10_000.0, dd_scale=None):
    """Capitale composto con rischio fisso (o 'rischio che respira' se dd_scale=(dd0, dd1, min_mult, recover_n)).
    Restituisce (serie del capitale, statistiche)."""
    r = np.asarray(r, float)
    o = np.argsort(np.asarray(times, "datetime64[ns]"), kind="stable")
    r = r[o]
    eq = np.empty(r.size)
    cap, peak, wins_since = start, start, 0
    mult = 1.0
    for i, x in enumerate(r):
        if dd_scale is not None:
            dd0, dd1, mmin, rec = dd_scale
            dd = 1 - cap / peak
            if dd <= dd0:
                mult = 1.0
            else:
                mult = max(mmin, 1 - (1 - mmin) * min(1.0, (dd - dd0) / (dd1 - dd0)))
            if wins_since >= rec:
                mult = 1.0
        cap *= 1 + risk * mult * x
        if cap >= peak:
            peak, wins_since = cap, 0
        elif x > 0:
            wins_since += 1
        eq[i] = cap
    s = pd.Series(eq, index=pd.DatetimeIndex(np.asarray(times, "datetime64[ns]")[o]))
    dd = 1 - s / s.cummax()
    years = max((s.index[-1] - s.index[0]).days / 365.25, 1e-9) if len(s) else 1
    cagr = (s.iloc[-1] / start) ** (1 / years) - 1 if len(s) else 0
    return s, dict(final=round(float(s.iloc[-1]), 0) if len(s) else start, cagr=round(100 * cagr, 2),
                   max_dd=round(100 * float(dd.max()), 2) if len(s) else 0.0)


def adaptive_set(s: pd.DataFrame, group_cols=("cell", "side"), lookback_years=3, qs=(0.0, 0.5, 0.7, 0.8, 0.9),
                 min_n=40, margin=0.03, every="QS", start=None, r_col="r"):
    """'Set' che si ricalcola da solo: a ogni data (trimestre), per ogni gruppo (cella x lato) guarda i segnali
    PASSATI con punteggio fuori campione ed esito già chiuso negli ultimi lookback_years; sceglie la soglia
    (quantile del punteggio del gruppo) con il miglior R medio, purché R medio > margin e n >= min_n.
    Se nessuna soglia supera il margine, il gruppo è spento per il trimestre. Restituisce (take, log)."""
    s = s.reset_index(drop=True)
    take = np.zeros(len(s), bool)
    key = s[list(group_cols)].astype(str).agg("|".join, axis=1).values
    t = s.known_at
    first = pd.Timestamp(start) if start else t.min() + pd.DateOffset(years=lookback_years)
    dates = pd.date_range(first.normalize(), t.max() + pd.Timedelta(days=92), freq=every)
    log = []
    for i, d in enumerate(dates[:-1]):
        te = ((t >= d) & (t < dates[i + 1])).values
        if not te.any():
            continue
        past = ((t >= d - pd.DateOffset(years=lookback_years)) & (s.exit_time < d) & s.score.notna()).values
        for g in np.unique(key[te]):
            pg = past & (key == g)
            if pg.sum() < min_n:
                continue
            sc, rr = s.score.values[pg], s[r_col].values[pg]
            best = None
            for q in qs:
                thr = np.quantile(sc, q) if q > 0 else -np.inf
                sel = sc >= thr
                if sel.sum() < min_n:
                    continue
                m = np.nanmean(rr[sel])
                if m > margin and (best is None or m > best[1]):
                    best = (thr, m, q, int(sel.sum()))
            if best is not None:
                cur = te & (key == g)
                take |= cur & (s.score.values >= best[0])
                log.append(dict(date=d, group=g, q=best[2], thr=best[0], past_avg_r=round(best[1], 3), past_n=best[3]))
    return take, pd.DataFrame(log)


def k_slots(fill_time, exit_time, take, r, k=5):
    """Fino a k posizioni aperte insieme: un segnale approvato apre se c'è uno slot libero al suo riempimento."""
    ft = np.asarray(fill_time, "datetime64[ns]")
    et = np.asarray(exit_time, "datetime64[ns]")
    cand = np.where(np.asarray(take) & ~np.isnat(ft) & ~np.isnat(et) & np.isfinite(np.asarray(r, float)))[0]
    cand = cand[np.argsort(ft[cand], kind="stable")]
    opened = np.zeros(len(ft), bool)
    busy = []
    for i in cand:
        busy = [x for x in busy if x > ft[i]]
        if len(busy) < k:
            opened[i] = True
            busy.append(et[i])
    return opened


def equity_events(r, fill_time, exit_time, risk, start=10_000.0):
    """Capitale con posizioni sovrapposte: il rischio di ogni trade è risk x capitale al RIEMPIMENTO; il P&L
    si realizza all'uscita. Restituisce (serie del capitale alle uscite, cagr %, max dd % sul realizzato)."""
    r = np.asarray(r, float)
    ft = np.asarray(fill_time, "datetime64[ns]")
    et = np.asarray(exit_time, "datetime64[ns]")
    ev = sorted([(ft[i], 0, i) for i in range(r.size)] + [(et[i], 1, i) for i in range(r.size)])
    cap = start
    stake = np.zeros(r.size)
    times, caps = [], []
    for tm, kind, i in ev:
        if kind == 0:
            stake[i] = cap * risk
        else:
            cap += stake[i] * r[i]
            times.append(tm)
            caps.append(cap)
    s = pd.Series(caps, index=pd.DatetimeIndex(times)).sort_index()
    if s.empty:
        return s, 0.0, 0.0
    yrs = max((s.index[-1] - s.index[0]).days / 365.25, 0.5)
    cagr = 100 * ((max(s.iloc[-1], 1e-9) / start) ** (1 / yrs) - 1)
    dd = 100 * float((1 - s / s.cummax()).max())
    return s, round(cagr, 2), round(dd, 2)
