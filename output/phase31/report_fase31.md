# Fase 31 — prime prove TICK PER TICK (gennaio e giugno 2026)

Tick reali XAUUSD da HistData.com (gratis, ~9 milioni al mese), spread fisso Axi 0,09 $, conto 5.000 USC.
`python/scripts/phase31_ticks.py` (tabella: `tick_tabella.csv`).
- Zone recovery: perde in tutte le varianti (con le candele M1 sembrava perfetta: era un errore della simulazione).
- Piramide: perde o quasi (anche lei gonfiata dalle candele).
- Cesto HFT con hedging: positivo in entrambi i mesi in molte varianti (es. distanza 5 $ x1,2, lotto x1,5, TP 2 $,
  copertura al 4° livello, rimbalzo 5 $: gennaio +670%, giugno +162%; cali 72% e 47%). Da verificare su tutti i mesi
  (fase 32).
