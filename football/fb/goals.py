"""Motore gol (Fase F1): forze di attacco/difesa dinamiche per squadra, aggiornate dopo OGNI partita (nessun
futuro), e distribuzione completa del punteggio (Poisson con correzione Dixon-Coles sui punteggi bassi).

lambda_casa  = exp(mu_div + home_div + att[casa] - dif[ospite])
lambda_ospite = exp(mu_div + att[ospite] - dif[casa])
Aggiornamento (discesa del gradiente sulla verosimiglianza di Poisson, passo lr):
att[casa] += lr*(gol_casa - lambda_casa), dif[ospite] -= lr*(gol_casa - lambda_casa) ... e simmetrico;
mu e home della divisione con passo più piccolo. Le squadre sono identificate per paese (una neopromossa porta
le sue forze dalla serie inferiore, corrette dalla differenza di livello stimata tra le divisioni).
"""
import numpy as np
import pandas as pd
from scipy.stats import poisson

MAXG = 10
TIER = {"E0": 1, "E1": 2, "E2": 3, "E3": 4, "EC": 5, "SC0": 1, "SC1": 2, "SC2": 3, "SC3": 4}


def tier(div):
    if div in TIER:
        return TIER[div]
    return int(div[-1]) if div[-1].isdigit() else 1


def dc_tau(x, y, lh, la, rho):
    if x == 0 and y == 0:
        return 1 - lh * la * rho
    if x == 0 and y == 1:
        return 1 + lh * rho
    if x == 1 and y == 0:
        return 1 + la * rho
    if x == 1 and y == 1:
        return 1 - rho
    return 1.0


def score_matrix(lh, la, rho=-0.05):
    ph = poisson.pmf(np.arange(MAXG + 1), lh)
    pa = poisson.pmf(np.arange(MAXG + 1), la)
    M = np.outer(ph, pa)
    for x in (0, 1):
        for y in (0, 1):
            M[x, y] *= dc_tau(x, y, lh, la, rho)
    return M / M.sum()


def run_ratings(m: pd.DataFrame, lr=0.05, lr_glob=0.005, decay=1.0, promo_pen=0.15, start_mu=0.25,
                start_home=0.25):
    """Scorre le partite in ordine di data e restituisce lambda_casa / lambda_ospite PRE-partita."""
    att, dif = {}, {}
    last_div = {}
    mu = {}
    home = {}
    div_level = {}
    lh_out = np.empty(len(m))
    la_out = np.empty(len(m))
    H, A, D, C = m.HomeTeam.values, m.AwayTeam.values, m.Division.values, m.country.values
    hg, ag = m.hg.values, m.ag.values
    for k in range(len(m)):
        d = D[k]
        mu.setdefault(d, start_mu)
        home.setdefault(d, start_home)
        keys = []
        for t in (H[k], A[k]):
            key = (C[k], t)
            if key not in att:
                att[key], dif[key] = -promo_pen * 0.5, -promo_pen * 0.5
            elif last_div.get(key) != d and last_div.get(key) is not None:
                # cambio di divisione: riparti più vicino alla media della nuova divisione
                att[key] *= 0.5
                dif[key] *= 0.5
                att[key] -= promo_pen * 0.5 if tier(d) < tier(last_div[key]) else -promo_pen * 0.25
            last_div[key] = d
            keys.append(key)
        h, a = keys
        lh = np.exp(mu[d] + home[d] + att[h] - dif[a])
        la = np.exp(mu[d] + att[a] - dif[h])
        lh_out[k], la_out[k] = lh, la
        if hg[k] != hg[k] or ag[k] != ag[k]:          # partita futura (risultato ignoto): niente aggiornamento
            continue
        eh, ea = hg[k] - lh, ag[k] - la
        att[h] += lr * eh
        dif[a] -= lr * eh
        att[a] += lr * ea
        dif[h] -= lr * ea
        mu[d] += lr_glob * (eh + ea) / 2
        home[d] += lr_glob * (eh - ea) / 2
    return lh_out, la_out


def market_probs(lh, la, rho=-0.05):
    """Probabilità dei principali mercati da una coppia di lambda."""
    M = score_matrix(lh, la, rho)
    g = np.arange(MAXG + 1)
    tot = g[:, None] + g[None, :]
    out = {"1": np.tril(M, -1).sum(), "X": np.trace(M), "2": np.triu(M, 1).sum()}
    for line in (0.5, 1.5, 2.5, 3.5, 4.5):
        out[f"over{line}"] = M[tot > line].sum()
    out["gg"] = M[1:, 1:].sum()
    out["pari"] = M[tot % 2 == 0].sum()
    return out


def probs_vectorized(lh, la, rho=-0.05):
    """Mercati per array di lambda (vettoriale)."""
    g = np.arange(MAXG + 1)
    ph = poisson.pmf(g[None, :], np.asarray(lh)[:, None])
    pa = poisson.pmf(g[None, :], np.asarray(la)[:, None])
    M = ph[:, :, None] * pa[:, None, :]
    lh_, la_ = np.asarray(lh), np.asarray(la)
    M[:, 0, 0] *= 1 - lh_ * la_ * rho
    M[:, 0, 1] *= 1 + lh_ * rho
    M[:, 1, 0] *= 1 + la_ * rho
    M[:, 1, 1] *= 1 - rho
    M /= M.sum(axis=(1, 2), keepdims=True)
    tot = g[:, None] + g[None, :]
    diff = g[:, None] - g[None, :]
    out = {"p1": (M * (diff > 0)).sum((1, 2)), "pX": (M * (diff == 0)).sum((1, 2)), "p2": (M * (diff < 0)).sum((1, 2))}
    for line in (0.5, 1.5, 2.5, 3.5, 4.5):
        out[f"over{line}"] = (M * (tot > line)).sum((1, 2))
    out["gg"] = M[:, 1:, 1:].sum((1, 2))
    out["pari"] = (M * (tot % 2 == 0)).sum((1, 2))
    return pd.DataFrame(out), M
