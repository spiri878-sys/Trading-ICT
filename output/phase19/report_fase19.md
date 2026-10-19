# Fase 19 — ricerca ampia (1.296 varianti) dell'idea struttura + sweep + pendente, con scelta walk-forward

Script `python/scripts/phase19_walkforward_search.py`. Griglia: M5/M15 x swing k 2/3/5 x validità ordine 2/4/8 barre x
target 1-3 R x multi-timeframe TREND/CONTRO/NESSUNO x sessione Londra+NY/NY/tutte x filtro ATR. Costi utente.

## Risultato
- 13 varianti su 1.296 (1%) risultano positive sia nel 2010-15 sia nel 2016-26: è quello che produce il caso
  con così tante prove. Prese singolarmente sembrerebbero "il bot profittevole".
- Prova vera (catena walk-forward: ogni anno si sceglie la migliore dei 3 anni prima e la si usa nell'anno dopo):
  2.050 trade 2013-2026, **R medio -0,009 (costi utente) e -0,052 (costi prudenti)**, 8 anni positivi su 14.
  Anni: 2013 +20,9 · 2014 +46,3 · 2015 -5,0 · 2016 +10,3 · 2017 +11,2 · 2018 -52,6 · 2019 +2,7 · 2020 -23,3 ·
  2021 +2,1 · 2022 -20,2 · 2023 -11,5 · 2024 -22,3 · 2025 +13,8 · 2026 (gen) +9,9 R.
- Il "migliore del passato" cambia quasi ogni anno e non ripete il risultato: nessun vantaggio stabile in questa famiglia.
