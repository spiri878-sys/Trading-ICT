# Fase 44 — la combinazione migliore che NON BRUCIA MAI, per ogni capitale (tick per tick, gen - 16 ott 2026)

`phase44_capital_needed.py`: 2.003 set (con/senza hedging, trailing, tetti, filtro); per ognuno guadagno per 0,01 di lotto
e capitale minimo per 0,01 che regge tutti i mesi (conto enorme, punto più basso di equity - 50% margine).
380 set hanno tutti i mesi positivi con capitale sufficiente. `phase44b_verify.py`: i 40 migliori verificati con il lotto
vero (arrotondato come l'EA) e lotto = capitale / (1,5 x capitale minimo), ogni mese da capo. Risultati (USC, 10 mesi):
- 5.000 USC: set 503 (20 $ fissi, lotto x1,3 tetto 0,08, TP 2,5 $, trailing da 2 $ passo 0,2, copertura 70% al 4°
  livello, via 8 $, filtro 6), lotto 0,01: +37.118, peggior mese +768.
- 10.000 USC: set 503, lotto 0,02: +78.013, peggior +1.617.
- 20.000 USC: set 1726 (come 503 ma copertura 50% al 3°, tetto 0,16, trailing passo 0,5, senza filtro), lotto 0,03:
  +119.977, peggior +2.722.
- 50.000 USC: set 1830 (20 $ fissi, lotto x1,3 tetto 0,16, TP 1,5 $, copertura piena al 6°, via 8 $, filtro 6),
  lotto 0,07: +281.174, peggior +3.819.
- 100.000 USC: set 1830 lotto 0,14: +571.308, peggior +7.663 (set 1624 senza hedging x2,5 tetto 0,64: +634.968 ma
  agosto +413); bot 1.61 con lotto 0,04: +423.334.
Il capitale minimo è misurato sul 2026: il margine 1,5 serve per mesi peggiori. Set: `mql5/Presets/CestoTopBottom_NoBrucia_*`.
