"""Strumenti comuni per tradurre strategie TradingView (Pine) e simularle sull'oro (Fase 14).

Convenzioni (prudenti, uguali al resto del progetto):
* barre BID; un long entra all'ASK = BID + spread ed esce al BID; uno short entra al BID ed esce all'ASK;
* ordini 'a mercato' riempiti all'apertura della barra successiva (process_orders_on_close = false) oppure alla
  chiusura della barra del segnale quando la strategia usa process_orders_on_close = true;
* stop e target controllati sui massimi/minimi della barra, con lo STOP sempre per primo se entrambi toccati;
* slippage 0,05 $ su ingressi a mercato e stop; commissione 3,5 $ per lotto e lato (0,035 $/oncia per lato);
* R = P&L netto / rischio iniziale (distanza ingresso-stop); per le strategie senza stop si usa il rischio
  dichiarato (es. trailing 10%).
"""
import numpy as np
import pandas as pd

from ..prime.data import ROOT

TF_DIR = ROOT / "output" / "cache" / "tf"
import os
SPREAD, SLIP, COMM = (0.0, 0.0, 0.0) if os.environ.get("PINE_ZERO_COST") else (0.30, 0.05, 0.035)


def bars(tf):
    if tf == "M1":
        b = pd.read_parquet(ROOT / "output" / "cache" / "XAUUSD_M1_master.parquet")
    else:
        b = pd.read_parquet(TF_DIR / f"XAUUSD_{tf}.parquet")
    return b[b.index >= "2005-01-01"]


# ------------------------------------------------------------------ indicatori (stessa definizione di Pine)
def rma(x, n):
    x = np.asarray(x, float)
    out = np.full(x.size, np.nan)
    s, cnt, prev = 0.0, 0, np.nan
    for i in range(x.size):
        v = x[i]
        if np.isnan(v):
            out[i] = prev
            continue
        if cnt < n:
            s += v
            cnt += 1
            if cnt == n:
                prev = s / n
                out[i] = prev
        else:
            prev = (prev * (n - 1) + v) / n
            out[i] = prev
    return out


def ema(x, n):
    return pd.Series(x).ewm(span=n, adjust=False).mean().values


def sma(x, n):
    return pd.Series(x).rolling(n).mean().values


def wma(x, n):
    x = np.asarray(x, float)
    w = np.arange(n, 0, -1, dtype=float)          # peso n alla barra più recente
    out = np.convolve(np.nan_to_num(x), w, mode="full")[:x.size] / w.sum()
    bad = pd.Series(np.isnan(x).astype(float)).rolling(n, min_periods=1).max().values > 0
    out[:n - 1] = np.nan
    out[bad] = np.nan
    return out


def true_range(h, l, c):
    pc = np.r_[np.nan, c[:-1]]
    tr = np.maximum(h - l, np.maximum(np.abs(h - pc), np.abs(l - pc)))
    tr[0] = h[0] - l[0]
    return tr


def atr(h, l, c, n=14):
    return rma(true_range(h, l, c), n)


def rsi(c, n=14):
    d = np.diff(c, prepend=c[0])
    up, dn = rma(np.maximum(d, 0), n), rma(np.maximum(-d, 0), n)
    with np.errstate(divide="ignore", invalid="ignore"):
        rs = up / dn
    return np.where(dn == 0, 100.0, 100 - 100 / (1 + rs))


def dmi(h, l, c, n=14):
    up = np.diff(h, prepend=h[0])
    dn = -np.diff(l, prepend=l[0])
    pdm = np.where((up > dn) & (up > 0), up, 0.0)
    mdm = np.where((dn > up) & (dn > 0), dn, 0.0)
    tr = rma(true_range(h, l, c), n)
    with np.errstate(divide="ignore", invalid="ignore"):
        pdi = 100 * rma(pdm, n) / tr
        mdi = 100 * rma(mdm, n) / tr
        dx = 100 * np.abs(pdi - mdi) / (pdi + mdi)
    return pdi, mdi, rma(np.nan_to_num(dx), n)


def macd(c, f=12, s=26, sig=9):
    m = ema(c, f) - ema(c, s)
    sg = ema(m, sig)
    return m, sg, m - sg


def pivots(h, l, left, right):
    """ta.pivothigh/pivotlow: valore noto alla barra i per il pivot in i-right (None = nan)."""
    n = h.size
    ph = np.full(n, np.nan)
    pl = np.full(n, np.nan)
    hw = pd.Series(h).rolling(left + right + 1).max().values
    lw = pd.Series(l).rolling(left + right + 1).min().values
    for i in range(left + right, n):
        j = i - right
        if h[j] == hw[i] and (h[j] > h[j - left:j]).all() and (h[j] >= h[j + 1:i + 1]).all():
            ph[i] = h[j]
        if l[j] == lw[i] and (l[j] < l[j - left:j]).all() and (l[j] <= l[j + 1:i + 1]).all():
            pl[i] = l[j]
    return ph, pl


# ------------------------------------------------------------------ prezzi effettivi e statistiche
def entry_fill(px, side):
    """Prezzo pagato su BID px: long all'ASK + slippage, short al BID - slippage."""
    return px + SPREAD + SLIP if side == 1 else px - SLIP


def exit_bid_level(level, side):
    """Uscita su un livello: per i long il livello è sul BID; per gli short l'ordine si attiva quando l'ASK
    (BID + spread) lo raggiunge, quindi sul grafico BID scatta a level - spread."""
    return level


def trade_r(side, entry, exit_px, risk, nights=0):
    pnl = (exit_px - entry) * side - 2 * COMM
    pnl += (-0.066 if side == 1 else 0.029) * entry * nights / 365.0
    return pnl / max(risk, 1e-9)


def summarize(trades: pd.DataFrame, split="2016-01-01"):
    """trades: colonne time, r. Statistiche su tutto il periodo, sviluppo (< split) e controllo (>= split)."""
    out = {}
    if trades.empty:
        return {"tutto": {"n": 0}}
    for name, d in (("tutto", trades), ("2005-2015", trades[trades.time < split]),
                    ("2016-2026", trades[trades.time >= split])):
        r = d.r.values
        if r.size == 0:
            out[name] = {"n": 0}
            continue
        gp, gl = r[r > 0].sum(), -r[r < 0].sum()
        yrs = d.groupby(d.time.dt.year).r.sum()
        cap = 1.0
        peak, mdd = 1.0, 0.0
        for x in r:
            cap *= 1 + 0.01 * x
            peak = max(peak, cap)
            mdd = max(mdd, 1 - cap / peak)
        span = max((d.time.iloc[-1] - d.time.iloc[0]).days / 365.25, 0.5)
        out[name] = dict(n=int(r.size), per_anno=round(r.size / span, 1), win=round(float((r > 0).mean()), 3),
                         r_medio=round(float(r.mean()), 3), pf=round(float(gp / gl), 2) if gl > 0 else None,
                         anni_pos=f"{int((yrs > 0).sum())}/{len(yrs)}",
                         crescita_annua_rischio1=round(100 * (cap ** (1 / span) - 1), 2), dd_max=round(100 * mdd, 1))
    return out
