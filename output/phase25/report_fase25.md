# Fase 25 — cesto martingala: quali entrate fanno meno drawdown

`python/scripts/phase25_basket_entries.py`, barre M1 Axi gen-ott 2026. Griglia del set utente da 50 livelli
(distanza 2 $ x1,1, lotto 0,01 x1,5, TP cesto 2 $, nessuno stop, H24), un cesto BUY e uno SELL, stop out al 50% del
margine (leva 1:1000), nella barra prima il movimento contrario.

- Tutto il periodo di fila, deposito 100.000: quasi tutte le entrate saltano (livello 19-21, ~100 $ contro).
- Mese per mese da capo, deposito 500.000 (`entrate_mese_per_mese_500k.csv`):
  - entrata continua senza filtro: 5 mesi saltati su 10, +44% medio nei mesi buoni;
  - entrata continua solo dal lato della EMA200 H1 e non dopo uno strappo: **1 mese saltato su 10**, +14% medio,
    calo medio 18%;
  - RSI/stocastico con gli stessi filtri: 0 mesi saltati ma +0-4% al mese (pochissimi cesti).
- Conclusione: l'entrata non rende sicuro il cesto (salta su un movimento di ~100 $ senza ritorno, comunque entri), ma
  scegliere il lato della tendenza e aspettare la calma riduce molto i mesi saltati, al prezzo di meno guadagno.
  Aggiunto all'EA come `InpSmartEntry` (solo il primo ordine del cesto: i cesti aperti lavorano sempre).
