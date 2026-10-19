# Fase 28 — conto vero dell'utente: 5.000 USC (50 $)

Il conto è 5.000 USC = 50 $ (nel tester: deposito 5.000 con 0,01 lotti). I set delle fasi 25-27 erano pensati per
500.000: con 5.000 bruciano tutti i mesi (mese per mese, `phase28_basket_5000usc.py`, 400 combinazioni: nessuna
senza mesi bruciati a gen-mag).
- Migliore senza protezioni: tendenza EMA200 H1, distanza 8 $ x1,2, lotto x1,3, TP 1 $: 2 mesi bruciati su 10
  (gen, ago), negli altri +4%...+129%.
- Con hedging al livello 5 (copertura grande quanto il cesto, tolta quando il prezzo rimbalza di 5 $): 1 mese
  bruciato su 10 (feb), negli altri +16%...+143%. Livelli massimi con chiusura del cesto: niente mesi bruciati ma
  in perdita. Scelta fatta su tutti i 10 mesi (non c'è un periodo di verifica separato): ottimista.
- Stesso set senza bruciature: 20.000 USC (200 $) da 0 mesi bruciati, +4%...+32% al mese.
Set: `mql5/Presets/CestoTopBottom_5000USC_hedging.set`.
