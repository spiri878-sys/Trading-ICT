# Fase 15 — oro con conto da 100 EUR (0,01 lotti, leva 1:1000)

Vincolo: 0,01 lotti = 1 $ per $ di movimento. Lo stop del candidato Fase 11 (1,5 ATR H4 = 30-67 $ nel 2025-26) rischierebbe
il 25-60% del conto a trade: escluso. Cercata una regola con stop fisso di 2-8 $ (`phase15_small_stop.py`, 64 configurazioni,
costi 0,385 $ a trade, sviluppo 2010-15, verifica 2016-01/2026).

## Risultato
- T1 (rottura H1 nel trend), T3 (rottura range asiatico), R (casuale nel trend): negativi in media in entrambi i periodi.
- **T2 (ritracciamento nel trend: H4 ha rotto il Donchian 20 nella direzione del trend D1 nelle ultime 24 ore, la barra H1
  chiude contro il trend, ingresso all'apertura della successiva)**: positiva in tutte le 16 combinazioni stop/target in
  entrambi i periodi. R medio +0,10 (sviluppo) e +0,11 (verifica). Long e short entrambi positivi.

| stop / target | trade/anno | vinti | R verifica | anni + 2016-26 | serie perse max | costi doppi R | conto 116 $ dal 2016 (0,01 fisso) | DD max |
|---|---|---|---|---|---|---|---|---|
| 5 $ / 10 $ | ~112 | 41% | +0,095 | 9/11 | 12 | +0,03 | 657 $ | 28% (64% dal 2020) |
| 5 $ / 15 $ | ~112 | 36% | +0,135 | 9/11 | 14 | +0,04 | 883 $ | 25% (59% dal 2020) |
| 8 $ / 16 $ | ~107 | 45% | +0,116 | 10/11 | 10 | +0,06 | 1.140 $ | 26% (52% dal 2020) |
| 3 $ / 9 $ | ~116 | 33% | +0,113 | 8/11 | 15 | -0,005 | 508 $ | 25% |

## Avvertenze (oneste)
- Vantaggio piccolo (~0,1 R a trade): con costi doppi quasi sparisce. Spread e slippage reali del broker decidono tutto.
- Ultimi 6 mesi (ago 2025 - gen 2026, volatilità altissima, ATR H4 30-56 $): **negativi** (-65 $ stop 5/15, -60 $ stop 8/16).
  Gennaio 2026 negativo per tutte le varianti. Possibile che con l'oro così nervoso lo stop piccolo non regga più.
- Non è un test del tutto "mai visto": le idee (trend D1, Donchian H4) vengono dalle fasi precedenti su questi stessi anni.
- Prova vera: barre feb-ott 2026 (mai usate) e poi 2-3 mesi su conto demo con lo spread del broker dell'utente.
