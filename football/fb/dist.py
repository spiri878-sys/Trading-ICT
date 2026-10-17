"""Distribuzioni dei conteggi (Fase M3): dal valore atteso alla distribuzione completa 0..K.

Forma scelta con un solo parametro di dispersione phi = varianza / media:
phi > 1 binomiale negativa, phi = 1 Poisson, phi < 1 binomiale (n = media / (1 - phi), arrotondato in modo continuo
mescolando i due interi vicini). phi si stima per massima verosimiglianza su previsioni fuori campione.
"""
import numpy as np
from scipy.stats import binom, nbinom, poisson

KMAX = {"g": 10, "ght": 7, "g2h": 8, "cor": 24, "fou": 45, "yel": 12, "red": 4, "crd": 16, "sh": 50, "sot": 25}
PHIS = np.r_[np.linspace(0.6, 0.98, 20), 1.0, np.linspace(1.02, 2.0, 50)]


def pmf(mu, phi, K):
    """mu: array (n,); restituisce (n, K+1). L'ultima colonna raccoglie la coda (>= K)."""
    mu = np.clip(np.asarray(mu, float), 1e-4, None)[:, None]
    k = np.arange(K + 1)[None, :]
    if phi > 1.0001:
        r = mu / (phi - 1)                                  # var = mu + mu^2 / r = phi * mu
        P = nbinom.pmf(k, r, r / (r + mu))
    elif phi < 0.9999:
        n = mu / (1 - phi)
        lo = np.floor(n)
        w = n - lo
        lo = np.maximum(lo, np.ceil(mu))                    # n >= mu
        P = (1 - w) * binom.pmf(k, lo, np.minimum(mu / lo, 1)) + w * binom.pmf(k, lo + 1, mu / (lo + 1))
    else:
        P = poisson.pmf(k, mu)
    P[:, -1] += np.clip(1 - P.sum(1), 0, None)
    return P


def loglik(y, mu, phi, K):
    y = np.minimum(np.asarray(y, int), K)
    P = pmf(mu, phi, K)
    return float(np.mean(np.log(np.clip(P[np.arange(len(y)), y], 1e-12, None))))


def fit_phi(y, mu, K):
    """phi migliore per massima verosimiglianza (griglia)."""
    ll = [loglik(y, mu, p, K) for p in PHIS]
    i = int(np.argmax(ll))
    return float(PHIS[i]), ll[i], ll[list(PHIS).index(1.0)]
