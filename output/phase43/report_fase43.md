# Fase 43 — ordini stop (tick per tick, ogni mese da 5.000 USC)

180 set: entrata a buy stop / sell stop a 1-2 $ (breakout) o a mercato, media con conferma (rimbalzo 0,5-3 $ prima di
aggiungere il livello), distanza 5/8 $, lotto x1,5/x2, copertura 0/4/5. `stop_*.csv`.
- Con l'entrata a stop 47 set non hanno mesi in perdita a 0,01, ma guadagnano pochissimo: il migliore +8.018 USC in 10
  mesi (~8 EUR al mese).
- `phase43b_scale.py`: con lotto di partenza 0,02 o più tutti hanno almeno un mese in perdita (in pratica brucia).
- Peggio del set costante della fase 41 (+46.800 USC, nessun mese in perdita) e del bot 1.61.
