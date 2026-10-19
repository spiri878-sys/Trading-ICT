# Fase 29 — 5.000 USC con hedging: più operazioni e più profitto?

`python/scripts/phase29_hedge_search.py`: 9.216 combinazioni (entrata tendenza o BUY+SELL, distanza 2-8 $, crescita
x1-1,3, lotto x1,1-1,5, TP 0,5-2 $, copertura al livello 3-6, rimbalzo 2-8 $), mese per mese da capo a 5.000.
- Nessuna combinazione senza mesi bruciati a gen-mag. Mesi bruciati su 10: 1 (9 combinazioni), 2 (93), 3+ (tutte le
  altre). Tutte le combinazioni con BUY+SELL o distanza sotto 6 $ bruciano 2+ mesi.
- La migliore resta il set della fase 28 (tendenza, 8 $ x1,2, lotto x1,3, TP 1 $, copertura al 5° livello, rimbalzo
  5 $): 1 mese bruciato, ~2.800 ordini al mese.
- Più operazioni con 1 mese bruciato: TP 0,5 $ e copertura al 4° livello, rimbalzo 3 $: ~4.650 ordini al mese ma
  guadagno totale ~40% più basso.
- Conclusione: con 50 $ il limite è il capitale; più operazioni o lotti più grandi = più mesi bruciati.
