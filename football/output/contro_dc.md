# Contropronostico doppia chance sulla sfavorita (backtest 2019-2026)

Dati: football-data.co.uk, 22 campionati europei, 54.747 partite con linea asiatica di apertura e di chiusura e quote
Bet365. Giocata: doppia chance della sfavorita (1X se è la casa, X2 se è l'ospite), 1 unità. Quota DC ricavata dall'1X2
Bet365 (1/(1/q sfavorita + 1/q pareggio)): la DC vera di Bet365 paga un po' meno (~2-3%) -> togliere ~2-3 punti di ROI.

## A. Segnale linea asiatica (apertura -> chiusura) verso la sfavorita

| filtro | giocate | vinte | quota media | ROI apertura | ROI chiusura | stagioni in utile |
|---|---|---|---|---|---|---|
| tutte le DC sfavorita (nessun segnale) | 54.745 | 50% | 2.01 | -8.5% | | 0/8 |
| linea mossa >= 0.25 | 9.588 | 52% | 2.11 | 0.0% | -8.3% | 5/8 |
| linea mossa >= 0.5 | 555 | 51% | 2.55 | +8.5% | -11.2% | 7/8 |
| >= 0.5 + AI d'accordo | 220 | 59% | 2.15 | +10.7% | -8.7% | 6/8 |
| >= 0.5 + AI + sfavorita leggera (linea 0.25-0.75) | 160 | 67% | 1.76 | +13.5% | | 7/8 |

Campione piccolo (~25 giocate a stagione), stagioni recenti più deboli.

## B. Segnale probabilità 1X2 (Pinnacle apertura -> chiusura): più giocate, più stabile

| probabilità DC sfavorita sale di | giocate | vinte | quota | ROI apertura Bet365 | a metà movimento | chiusura | stagioni + |
|---|---|---|---|---|---|---|---|
| >= 3 punti | 8.393 | 55% | 1.97 | +1.9% | | | 6/7 |
| >= 5 punti | 3.470 | 57% | 1.97 | +6.0% | -0.3% | -6.6% | 6/7 |
| **>= 7 punti (REGOLA)** | **1.329** | **58%** | **2.01** | **+10.6%** | +2.2% | -6.1% | **7/7** |
| >= 10 punti | 284 | 56% | 2.07 | +9.8% | | | 5/7 |

Regola >= 7 punti per stagione: 19/20 +18.7%, 20/21 +16.8%, 21/22 +9.6%, 22/23 +4.6%, 23/24 +0.9%, 24/25 +12.7%,
25/26 +2.4%. Sfavorita ospite +11.0% (862), casa +9.8% (467). Con l'AI d'accordo: 587 giocate +11.3% (non serve).

## Conclusione onesta
- Il valore c'è SOLO alla quota vecchia: se Bet365 ha già abbassato la quota, la stessa giocata perde (-6%).
- Per questo `scripts/contro_dc.py` dà la QUOTA MINIMA (probabilità attuale senza margine, +5% di valore): sotto
  quella quota non si gioca.
- Il riferimento attuale gratis è DraftKings (ESPN), non Pinnacle: muove meno e più tardi -> segnale più debole del
  backtest. È un limite superiore: va giudicato sul registro reale.
