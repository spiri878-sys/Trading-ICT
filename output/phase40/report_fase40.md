# Fase 40 — martingala con tetto al lotto (0,01 -> ... -> tetto, poi sempre al tetto), tick per tick, mese da 5.000 USC

`phase40_lot_cap.py`, `tetto_lotto.csv`. Distanza 6/8 $ x1,3, lotto x2, TP 0,7 $, via a 8 $, copertura piena.
- Copertura al 4° livello: tetto 0,64 +941 EUR (1 mese bruciato), nessun tetto +923, tetto 0,32 +675 (2), 0,16 +194 (4).
- Senza hedging: 6-8 mesi bruciati in ogni variante. Copertura al 5°-8° livello: 4-8 mesi bruciati.
- Con 50 EUR il cesto non arriva quasi mai a 0,64 (la copertura al 4° livello lo ferma a 0,08): il tetto cambia poco.
