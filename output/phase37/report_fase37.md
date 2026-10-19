# Fase 37 — zero mesi in perdita? (tick per tick, ogni mese da capo)

Maggio 2026: oro con escursioni di 100-150 $ al giorno avanti e indietro; il cesto si copre, la copertura si toglie, il
prezzo riparte contro e il cesto cresce x2 a ogni giro finché salta.
- `phase37_smart_hedge.py` (216 set: copertura intelligente che usa il suo guadagno per chiudere gli ordini più vecchi,
  tetto al lotto 0,08/0,16, distanza 6-10 $, lotto x1,5/x2, copertura al 3°/4°/5°, rimbalzo 5/8 $): nessun set senza
  mesi in perdita a 5.000 USC; il migliore resta quello dell'EA 1.40 (+923 EUR, solo maggio -50).
- Stesso set con lotto 0,01 e più soldi sul conto: 75/100/150 EUR bruciano ancora a maggio; con 200 EUR (20.000 USC)
  maggio chiude +53 e nessun mese è in perdita: +233 +203 +262 +21 +53 +58 +56 +52 +49 +39 = +1.026 EUR.
