"""Probabilità live sul tempo che resta (Fase M7, punto 7 del piano). NON verificato sul passato (mancano dati
minuto per minuto): le giocate live sono marcate 'non verificate'.

atteso_resto = atteso_prepartita * quota_tempo_resto * ritmo * punteggio * espulsioni
ritmo = (osservato + K * atteso_finora) / ((1 + K) * atteso_finora)   (peso moderato al ritmo osservato)
"""
import numpy as np

from .dist import pmf

K_PRIOR = 2.0                          # 2/3 pre-partita, 1/3 ritmo osservato
SECOND_HALF_GOALS = 0.55               # quota di gol nel 2° tempo se il campionato non la dà


def time_left_share(minute, stat, ht_share=None):
    """Quota del conteggio atteso che resta dopo il minuto (90' + recupero ~ 95')."""
    t = min(max(minute, 0), 94)
    h2 = 1 - (ht_share if ht_share else (1 - SECOND_HALF_GOALS)) if stat in ("g",) else 0.5
    if t <= 45:
        done = (1 - h2) * t / 45
    else:
        done = (1 - h2) + h2 * (t - 45) / 50
    return max(1 - done, 0.0)


def remaining(mu_h, mu_a, minute, obs_h, obs_a, stat, score=(0, 0), reds=(0, 0), ht_share=None):
    left = time_left_share(minute, stat, ht_share)
    done = 1 - left
    out = []
    for mu, obs, me, opp, r_me, r_opp in ((mu_h, obs_h, score[0], score[1], reds[0], reds[1]),
                                           (mu_a, obs_a, score[1], score[0], reds[1], reds[0])):
        exp_sofar = max(mu * done, 1e-6)
        pace = (obs + K_PRIOR * exp_sofar) / ((1 + K_PRIOR) * exp_sofar) if done > 0.05 else 1.0
        f = 1.0
        if stat in ("g", "cor", "sh", "sot") and minute >= 60:
            f *= 1.12 if me < opp else 0.92 if me > opp else 1.0     # chi perde spinge, chi vince gestisce
        f *= 0.75 ** r_me * 1.12 ** r_opp
        out.append(mu * left * pace * f)
    return out


def final_grid(mu_h, mu_a, minute, obs, stat, phi, K, score=(0, 0), reds=(0, 0), ht_share=None):
    """Griglia (1, K+1, K+1) del conteggio FINALE = osservato + resto (distribuzione del resto con la stessa
    dispersione del pre-partita)."""
    rh, ra = remaining(mu_h, mu_a, minute, obs[0], obs[1], stat, score, reds, ht_share)
    ph = pmf(np.array([rh]), phi[0], K)[0]
    pa = pmf(np.array([ra]), phi[1], K)[0]
    gh, ga = np.zeros(K + 1), np.zeros(K + 1)
    oh, oa = int(obs[0]), int(obs[1])
    for k in range(K + 1):
        gh[min(oh + k, K)] += ph[k]
        ga[min(oa + k, K)] += pa[k]
    return (gh[:, None] * ga[None, :])[None], (rh, ra)
