# Fase 45-46 — correzione: capitale minimo dal punto più alto del conto

La fase 44 misurava il capitale minimo dall'inizio di ogni mese: i guadagni dei primi giorni coprivano i cali dopo, e il
capitale risultava troppo basso. La scala da 50 EUR (fase 45) è bruciata a gennaio. I set NoBrucia sono stati tolti.
`phase46b_true_capital_monthly.py` / `phase46c_scale_check.py`: capitale = calo massimo dal punto più alto
(+ 50% del margine), mese per mese, con i lotti veri dell'EA. Con margine di sicurezza 1,5 (EUR, gen - 16 ott 2026):
- 50 EUR: nessun set al sicuro (il meno esigente vuole ~52 EUR per 0,01 senza alcun margine).
- 100 EUR: set 255 (15 $ fissi, lotto x1,2 tetto 0,64, TP 0,5 $, copertura 70% al 4° livello, via 5 $), 0,01:
  +83 +95 +71 +25 +17 +28 +20 +20 +27 +10 = +397.
- 200 EUR: set 255, 0,02: +167 +190 +147 +54 +35 +56 +42 +40 +55 +22 = +808.
- 500 EUR: set 255, 0,04: +352 +403 +355 +108 +110 +113 +88 +82 +114 +39 = +1.763.
- 1.000 EUR: bot 1.61, 0,03: +663 +674 +766 +117 +177 +185 +173 +161 +157 +102 = +3.175 (set 1108 x0,02 +3.867 ma
  ottobre +6).
Set: `mql5/Presets/CestoTopBottom_Sicuro_*.set`.
