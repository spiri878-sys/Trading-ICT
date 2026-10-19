# Fase 34 — gestione dei soldi, tick per tick, gen -> 16 ott 2026 di fila, partenza 50 EUR (5.000 USC)

Set fase 32 (8 $ x1,3, lotto x2, TP 0,5 $, copertura al 4° livello, via a 8 $). Se il conto brucia si ricaricano 50 EUR.
Netto = ritirato + saldo finale - versato. File: `gestione_soldi.csv`, `gestione_soldi_2.csv`.
- Lotto fisso 0,01, nessun prelievo: 0 volte bruciato, 50 -> 931 EUR (+881).
- Martingala più alta (lotto fisso, senza prelievi): x1,5 +62 (6 ricariche), x2 +881 (0), x2,5 -364 (12), x3 -603 (14).
- Lotto che cresce con il saldo (0,01 ogni X EUR): ogni 25 EUR sempre in perdita (28-31 ricariche); ogni 50 EUR +1.355
  ma 8 ricariche; ogni 100 EUR 5 ricariche; ogni 150 EUR 0-1; ogni 200 EUR senza prelievi +3.673 con 0 ricariche ma
  sensibile (150 e 200 con prelievi bruciano); ogni 300 EUR 0 ricariche in tutte e tre le varianti: senza prelievi
  +1.463 (saldo 1.513), con prelievi +881...+1.154.
- Scelta: 0,01 ogni 300 EUR (InpLotPerBalance = 30000 USC), EA 1.30 e set aggiornati.
