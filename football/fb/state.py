"""Feature di squadra in un solo passaggio cronologico (Fase M2). Ogni riga usa SOLO partite precedenti:
lo stato viene letto prima della partita e aggiornato dopo. Partite future (risultato vuoto) non aggiornano nulla.

Per ogni statistica s (fatti = f, subiti = a): media esponenziale veloce e lenta, media nel campo (casa per chi
gioca in casa, fuori per chi gioca fuori), media della stagione e della stagione precedente, forza dinamica
(motore tipo Poisson online, errore relativo). Più: punti, classifica, riposo, partite ravvicinate, neopromosse.
Le medie partono dalla media del campionato (restringimento naturale per squadre con pochi dati).
"""
from collections import defaultdict, deque

import numpy as np
import pandas as pd

from .goals import tier

STATS = {"g": ("hg", "ag"), "ght": ("HTHome", "HTAway"), "sh": ("HomeShots", "AwayShots"),
         "sot": ("HomeTarget", "AwayTarget"), "cor": ("HomeCorners", "AwayCorners"),
         "fou": ("HomeFouls", "AwayFouls"), "yel": ("HomeYellow", "AwayYellow"), "red": ("HomeRed", "AwayRed")}
NS = len(STATS)
A_FAST, A_SLOW, A_VEN, A_LG, LR, LR_LG = 0.25, 0.08, 0.15, 0.005, 0.03, 0.002


class Team:
    def __init__(self, lg):
        self.ff, self.fa = lg.copy(), lg.copy()            # veloce fatti / subiti
        self.sf, self.sa = lg.copy(), lg.copy()            # lenta
        self.vf = [lg.copy(), lg.copy()]                   # campo: 0 = casa, 1 = fuori
        self.va = [lg.copy(), lg.copy()]
        self.att, self.dif = np.zeros(NS), np.zeros(NS)    # forze dinamiche (log)
        self.ssn, self.div = None, None
        self.cs_f, self.cs_a, self.cs_n = np.zeros(NS), np.zeros(NS), np.zeros(NS)
        self.prev_f, self.prev_a = np.full(NS, np.nan), np.full(NS, np.nan)
        self.n, self.pts_ew, self.last = 0, 1.35, None
        self.dates = deque(maxlen=8)
        self.prev_tier = None
        self.nobs = np.zeros(NS)                           # partite con il dato, per statistica


def build_state(m: pd.DataFrame) -> pd.DataFrame:
    """m ordinato per data (fb.data.matches, eventualmente con partite future in coda per data)."""
    X = np.column_stack([m[h].to_numpy(float) for h, _ in STATS.values()]), \
        np.column_stack([m[a].to_numpy(float) for _, a in STATS.values()])
    XH, XA = X
    H, A, D, C = m.HomeTeam.to_numpy(), m.AwayTeam.to_numpy(), m.Division.to_numpy(), m.country.to_numpy()
    S, T = m.season.to_numpy(), m.date.to_numpy()
    teams, lgh, lga, lmu, lhome, lgn = {}, {}, {}, {}, {}, {}
    table = defaultdict(lambda: defaultdict(lambda: [0, 0, 0]))       # (div, season) -> team -> [pts, gp, gd]
    names = list(STATS)
    cols = []
    for p in ("h", "a"):
        for k in ("ff", "fa", "sf", "sa", "vf", "va", "cf", "ca", "pf", "pa"):
            cols += [f"{p}_{s}_{k}" for s in names]
        cols += [f"{p}_{k}" for k in ("n", "pts_ew", "ppg", "rank", "gap_top", "gap_safe", "rest", "busy14",
                                      "new_div", "cs_n")]
    cols += [f"lg_h_{s}" for s in names] + [f"lg_a_{s}" for s in names]
    cols += [f"exp_h_{s}" for s in names] + [f"exp_a_{s}" for s in names] + ["ssn_prog"]
    out = np.full((len(m), len(cols)), np.nan, dtype=np.float32)

    def flush(items):
        """Aggiornamenti condivisi (campionato, classifica): applicati solo a giorno finito, così una partita non
        vede partite dello stesso giorno giocate magari più tardi."""
        for d, ssn, h, a, xh, xa, ok, rh, ra in items:
            for team, gf, ga in ((h, xh[0], xa[0]), (a, xa[0], xh[0])):
                r = table[(d, ssn)][team]
                r[0] += 3 if gf > ga else 1 if gf == ga else 0
                r[1] += 1
                r[2] += gf - ga
            first = ok & (lgn[d] == 0)                    # primo dato del campionato per questa statistica
            lgh[d][first], lga[d][first] = xh[first], xa[first]
            lmu[d][first] = np.log(np.maximum((xh[first] + xa[first]) / 2, 0.1))
            lmu[d] = np.clip(lmu[d] + LR_LG * (rh + ra) / 2, -3, 4)
            lhome[d] += LR_LG * (rh - ra) / 2
            lgn[d][ok] += 1
            a_lg = np.maximum(A_LG, 1 / (lgn[d] + 1))[ok]   # all'inizio media semplice, poi esponenziale
            lgh[d][ok] += a_lg * (xh[ok] - lgh[d][ok])
            lga[d][ok] += a_lg * (xa[ok] - lga[d][ok])
        items.clear()

    pending, cur_t = [], None
    for k in range(len(m)):
        d, c, ssn, t = D[k], C[k], S[k], T[k]
        if t != cur_t:
            flush(pending)
            cur_t = t
        if d not in lgh:
            lgh[d] = np.where(np.isnan(XH[k]), 1.0, XH[k])
            lga[d] = np.where(np.isnan(XA[k]), 1.0, XA[k])
            lmu[d], lhome[d] = np.log(np.maximum((lgh[d] + lga[d]) / 2, 0.1)), np.full(NS, 0.05)
            lgn[d] = np.zeros(NS)
        lg_all = (lgh[d] + lga[d]) / 2
        tab = table[(d, ssn)]
        row = []
        tm = []
        for side, name in ((0, H[k]), (1, A[k])):
            key = (c, name)
            if key not in teams:
                teams[key] = Team(lg_all)
            tt = teams[key]
            if tt.ssn != ssn:                              # nuova stagione: archivia la media della precedente
                if tt.ssn is not None:
                    with np.errstate(invalid="ignore", divide="ignore"):
                        tt.prev_f, tt.prev_a = tt.cs_f / tt.cs_n, tt.cs_a / tt.cs_n
                    tt.prev_tier = tier(tt.div)
                tt.cs_f, tt.cs_a, tt.cs_n, tt.ssn = np.zeros(NS), np.zeros(NS), np.zeros(NS), ssn
            if tt.div is not None and tt.div != d:         # cambio di divisione: forze a metà
                tt.att *= 0.5
                tt.dif *= 0.5
            tt.div = d
            tm.append(tt)
            with np.errstate(invalid="ignore", divide="ignore"):
                cf, ca = tt.cs_f / tt.cs_n, tt.cs_a / tt.cs_n
            ranks = sorted(tab, key=lambda x: (-tab[x][0], -tab[x][2]))
            n_t = max(len(ranks), 1)
            me = tab[name] if name in tab else [0, 0, 0]
            rank = (ranks.index(name) + 1) / n_t if name in tab else np.nan
            top = tab[ranks[0]][0] if ranks else 0
            safe = tab[ranks[-4]][0] if len(ranks) >= 6 else 0
            rest = (t - tt.last) / np.timedelta64(1, "D") if tt.last is not None else np.nan
            busy = sum((t - x) / np.timedelta64(1, "D") <= 14 for x in tt.dates)
            new_div = np.nan if tt.prev_tier is None else np.sign(tt.prev_tier - tier(d))
            row += [*tt.ff, *tt.fa, *tt.sf, *tt.sa, *tt.vf[side], *tt.va[side], *cf, *ca, *tt.prev_f, *tt.prev_a,
                    tt.n, tt.pts_ew, me[0] / me[1] if me[1] else np.nan, rank, top - me[0], me[0] - safe, rest, busy,
                    new_div, tt.cs_n[0]]
        th, ta = tm
        eh = np.exp(lmu[d] + lhome[d] + th.att - ta.dif)
        ea = np.exp(lmu[d] - lhome[d] + ta.att - th.dif)
        gp = np.mean([v[1] for v in tab.values()]) if tab else 0
        row += [*lgh[d], *lga[d], *eh, *ea, gp / max(2 * (len(tab) - 1), 1)]
        out[k] = row

        xh, xa = XH[k], XA[k]
        if np.isnan(xh[0]) or np.isnan(xa[0]):            # partita futura: niente aggiornamento
            continue
        ok = ~np.isnan(xh) & ~np.isnan(xa)
        for side, tt, xf, xg in ((0, th, xh, xa), (1, ta, xa, xh)):
            okf, oka = ~np.isnan(xf), ~np.isnan(xg)
            new = okf & (tt.nobs == 0)                     # primo dato della squadra: parte dalla media campionato
            if new.any():
                base = np.where(lgn[d] > 0, (lgh[d] + lga[d]) / 2, (xf + xg) / 2)[new]
                for arr in (tt.ff, tt.fa, tt.sf, tt.sa, tt.vf[0], tt.vf[1], tt.va[0], tt.va[1]):
                    arr[new] = base
            tt.nobs[okf] += 1
            for arr, x, ok, a in ((tt.ff, xf, okf, A_FAST), (tt.fa, xg, oka, A_FAST), (tt.sf, xf, okf, A_SLOW),
                                  (tt.sa, xg, oka, A_SLOW), (tt.vf[side], xf, okf, A_VEN), (tt.va[side], xg, oka, A_VEN)):
                arr[ok] += a * (x[ok] - arr[ok])
            tt.cs_f[okf] += xf[okf]
            tt.cs_a[oka] += xg[oka]
            tt.cs_n[okf & oka] += 1
            res = np.sign(xf[0] - xg[0])
            pts = 3 if res > 0 else 1 if res == 0 else 0
            tt.pts_ew += 0.15 * (pts - tt.pts_ew)
            tt.n += 1
            tt.last = t
            tt.dates.append(t)
        # errore in unità della media del campionato (stabile anche per eventi rari come i rossi)
        scale = np.maximum((lgh[d] + lga[d]) / 2, 0.3)
        rh = np.where(ok, (np.nan_to_num(xh) - eh) / scale, 0)
        ra = np.where(ok, (np.nan_to_num(xa) - ea) / scale, 0)
        for tt_, arr, sgn, r_ in ((th, "att", 1, rh), (ta, "dif", -1, rh), (ta, "att", 1, ra), (th, "dif", -1, ra)):
            v = getattr(tt_, arr)
            v += sgn * LR * r_
            np.clip(v, -1.5, 1.5, out=v)
        pending.append((d, ssn, H[k], A[k], xh, xa, ok, rh, ra))
    return pd.DataFrame(out, columns=cols, index=m.index)
