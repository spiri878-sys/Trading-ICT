"""FASE 18 — idea dell'utente: struttura + liquidity sweep + conferma con ORDINE PENDENTE + filtri.

Su barre M5 o M15 (decisione alla CHIUSURA della barra):
  struttura : swing high/low frattali (k=3), confermati 3 barre dopo (solo allora sono noti);
  sweep     : la barra va sotto l'ultimo swing low confermato e richiude sopra (stop presi, rifiuto) -> setup BUY;
              specchio sopra lo swing high -> setup SELL;
  pendente  : BUY STOP al massimo della barra dello sweep + 0,1 ATR (la conferma = il prezzo rompe in su),
              SL sotto il minimo dello sweep - 0,1 ATR, TP = R x rischio; ordine valido 4 barre, poi cancellato;
              un'operazione alla volta (gli altri setup aspettano).
Filtri: ATR (ATR14 della barra tra 0,7 e 2,0 volte la sua media a 100 barre), sessione (Londra+New York: NY 03-12),
  multi-timeframe (TREND: solo nella direzione di D1 chiusura>EMA50 del giorno prima E H4 chiusura>EMA50 dell'ultima H4
  chiusa; NESSUNO: entrambi i lati). Notizie: nessun calendario storico disponibile -> non testabili qui (l'EA può
  usare il calendario MT5 dal vivo).
Costi utente: A 0,15 $ a trade, B 0,27 $. Periodi: sviluppo 2010-2015, verifica 2016-01/2026.

usage: python python/scripts/phase18_sweep_pending.py
"""
import itertools
import json
from pathlib import Path

import numba
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
TF = ROOT / "output" / "cache" / "tf"
OUT = ROOT / "output" / "phase18"
COSTS = {"A": 0.15, "B": 0.27}
K = 3


@numba.njit(cache=True)
def run(h, l, c, s_i, s_exp, side, entry, sl, tp, hold):
    """Ordini stop pendenti, uno alla volta. Ritorna indice di ingresso, pnl in $ per oncia, rischio in $."""
    n = h.size
    m = s_i.size
    ent = np.full(m, -1, np.int64)
    pnl = np.zeros(m)
    risk = np.zeros(m)
    k = 0
    free = 0
    for q in range(m):
        i0 = s_i[q]
        if i0 < free or i0 >= n - 1:
            continue
        # attesa del riempimento
        e = -1
        for j in range(i0, min(s_exp[q], n - 1)):
            if (side[q] > 0 and h[j] >= entry[q]) or (side[q] < 0 and l[j] <= entry[q]):
                e = j
                break
        if e < 0:
            continue
        r = abs(entry[q] - sl[q])
        res = 0.0
        done = False
        end = min(e + hold, n - 1)
        j = e
        while j < end:
            if side[q] > 0:
                if l[j] <= sl[q]:
                    res = -r
                    done = True
                elif h[j] >= tp[q] and j > e:
                    res = tp[q] - entry[q]
                    done = True
            else:
                if h[j] >= sl[q]:
                    res = -r
                    done = True
                elif l[j] <= tp[q] and j > e:
                    res = entry[q] - tp[q]
                    done = True
            if done:
                break
            j += 1
        if not done:
            res = (c[end - 1] - entry[q]) * side[q]
            j = end - 1
        ent[k] = e
        pnl[k] = res
        risk[k] = r
        k += 1
        free = j + 1
    return ent[:k], pnl[:k], risk[:k]


def htf_trend(idx_close, d1, h4):
    """+1/-1/0 al momento idx_close: D1 del giorno prima vs EMA50 e ultima H4 CHIUSA vs EMA50."""
    d = np.sign(d1.close - d1.close.ewm(span=50).mean())
    d.index = d1.index + pd.Timedelta(days=1)                   # nota alla chiusura del giorno
    hh = np.sign(h4.close - h4.close.ewm(span=50).mean())
    hh.index = h4.index + pd.Timedelta(hours=4)                 # nota alla chiusura della H4
    dv = d.reindex(idx_close, method="ffill").fillna(0).values
    hv = hh.reindex(idx_close, method="ffill").fillna(0).values
    return np.where(dv == hv, dv, 0)


def make_setups(b, tfm, d1, h4):
    o, h, l, c = (b[x].values for x in ("open", "high", "low", "close"))
    n = len(b)
    pc = np.r_[c[0], c[:-1]]
    atr = pd.Series(np.maximum(h - l, np.maximum(abs(h - pc), abs(l - pc)))).rolling(14).mean().values
    rel = atr / pd.Series(atr).rolling(100).mean().values
    # swing frattali: noti alla chiusura della barra j+K
    hs = pd.Series(h).rolling(2 * K + 1, center=True).max().values == h
    ls = pd.Series(l).rolling(2 * K + 1, center=True).min().values == l
    last_sh = np.full(n, np.nan)
    last_sl = np.full(n, np.nan)
    cur_h = cur_l = np.nan
    for i in range(n):
        j = i - K
        if j >= 0:
            if hs[j]:
                cur_h = h[j]
            if ls[j]:
                cur_l = l[j]
        last_sh[i], last_sl[i] = cur_h, cur_l
    # lo swing deve essere noto PRIMA della barra dello sweep
    psh, psl = np.r_[np.nan, last_sh[:-1]], np.r_[np.nan, last_sl[:-1]]
    bull = (l < psl) & (c > psl)
    bear = (h > psh) & (c < psh)
    t_close = b.index + pd.Timedelta(minutes=tfm)
    ny = t_close - pd.Timedelta(hours=7)
    sess = (ny.hour >= 3) & (ny.hour < 12)
    trend = htf_trend(t_close, d1, h4)
    df = pd.DataFrame({"t": t_close, "bull": bull, "bear": bear, "atr": atr, "rel": rel, "sess": sess, "trend": trend,
                       "h": h, "l": l})
    df = df[(df.bull ^ df.bear) & np.isfinite(df.atr) & np.isfinite(df.rel)]
    df["side"] = np.where(df.bull, 1, -1)
    df["entry"] = np.where(df.side > 0, df.h + 0.1 * df.atr, df.l - 0.1 * df.atr)
    df["sl"] = np.where(df.side > 0, df.l - 0.1 * df.atr, df.h + 0.1 * df.atr)
    return df


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    m1 = pd.read_parquet(ROOT / "output" / "cache" / "XAUUSD_M1_master.parquet")
    m1 = m1[m1.index >= "2009-10-01"]
    h, l, c = (m1[x].values.astype(float) for x in ("high", "low", "close"))
    d1 = pd.read_parquet(TF / "XAUUSD_D1.parquet")
    h4 = pd.read_parquet(TF / "XAUUSD_H4.parquet")
    years = m1.index.year.values
    rows = []
    for tfname, tfm in (("M5", 5), ("M15", 15)):
        b = pd.read_parquet(TF / f"XAUUSD_{tfname}.parquet")
        b = b[b.index >= "2009-10-01"]
        S = make_setups(b, tfm, d1, h4)
        si = np.searchsorted(m1.index.values, S.t.values).astype(np.int64)
        s_exp = np.searchsorted(m1.index.values, (S.t + pd.Timedelta(minutes=4 * tfm)).values).astype(np.int64)
        for mtf, sess, atrf, R in itertools.product(("TREND", "NESSUNO"), ("LON_NY", "TUTTE"), ("ATR", "NO"), (1.5, 2.0, 3.0)):
            mk = np.ones(len(S), bool)
            if mtf == "TREND":
                mk &= S.trend.values == S.side.values
            if sess == "LON_NY":
                mk &= S.sess.values
            if atrf == "ATR":
                mk &= (S.rel.values >= 0.7) & (S.rel.values <= 2.0)
            x = S[mk]
            ent, sl = x.entry.values, x.sl.values
            tp = ent + R * (ent - sl)
            e, p, r = run(h, l, c, si[mk], s_exp[mk], x.side.values.astype(np.int64), ent, sl, tp, 24 * 60)
            ok = r > 0
            e, p, r = e[ok], p[ok], r[ok]
            yr = years[e]
            for cn, cost in COSTS.items():
                Rv = (p - cost) / r
                row = {"tf": tfname, "mtf": mtf, "sessione": sess, "filtro_atr": atrf, "target_R": R, "costi": cn,
                       "trade_anno": round(len(e) / 16.1, 1), "stop_mediano_usd_2025": round(float(np.median(r[yr == 2025])), 2) if (yr == 2025).any() else None}
                for per, (a, bb) in (("sviluppo", (2010, 2015)), ("verifica", (2016, 2026))):
                    m_ = (yr >= a) & (yr <= bb)
                    ys = pd.Series(Rv[m_]).groupby(yr[m_]).mean()
                    row[f"{per}_n"] = int(m_.sum())
                    row[f"{per}_vinti"] = round(float((p[m_] > 0).mean()), 3)
                    row[f"{per}_R"] = round(float(Rv[m_].mean()), 4)
                    row[f"{per}_anni_pos"] = f"{int((ys > 0).sum())}/{len(ys)}"
                rows.append(row)
        print(tfname, "fatto", flush=True)
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "sweep_pending_grid.csv", index=False)
    a = df[df.costi == "A"]
    ok = a[(a.sviluppo_R > 0) & (a.verifica_R > 0)]
    print("positive in entrambi (costi A):", len(ok), "su", len(a))
    print(a.sort_values("verifica_R", ascending=False).head(12).to_string(index=False))


if __name__ == "__main__":
    main()
