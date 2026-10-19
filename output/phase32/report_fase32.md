# Fase 32 — cesto HFT con hedging, TICK PER TICK su tutto il 2026 (gen - 16 ott)

Tick HistData (~7-9 milioni al mese), spread fisso Axi 0,09 $, 5.000 USC, ogni mese da capo. 864 set
(`cesto_tick_mesi.csv`, `cesto_tick_tabella.csv`). Scelta su gen-mag, verifica su giu-ott.
- Nessun set senza mesi bruciati a gen-mag. Mesi bruciati su 10: 1 (un solo set), 2 (6 set), 3+ (tutti gli altri).
- Scelto su gen-mag: distanza 8 $ x1,3, lotto x2, TP 0,5 $, copertura al 4° livello, via dopo 8 $ di rimbalzo.
  Gen-mag: +415 +285 +462 +25, maggio BRUCIATO. Verifica giu-ott: +110 +112 +81 +117 +52 (ottobre a metà),
  0 bruciati. ~14.600 ordini al mese a gen-mag, ~6.100 a giu-ott. Calo massimo nei mesi buoni fino all'80%.
- Set precedente dell'utente (8 $ x1,2, lotto x1,3, TP 1 $, copertura 5, rimbalzo 5 $) coi tick: gennaio, febbraio e
  agosto bruciati; altri mesi +23...+253%.
- È un solo set su 864 con 1 mese bruciato (i vicini ne bruciano 2-3): fragile. Va confermato nel tester MT5.
Set: `mql5/Presets/CestoTopBottom_HFT_tick_5000USC.set` (anche predefinito nell'EA 1.20).

## Fase 33 — giro largo (1.296 set in più, anche senza hedging)
`python/scripts/phase33_basket_ticks_wide.py`, tabelle `cesto_tick_largo_*.csv`. Su 2.160 set in tutto, solo 2 bruciano
1 solo mese su 10, e sono della stessa famiglia del set scelto (8 $ x1,3, lotto x2, copertura al 4° livello, via a 8 $):
- TP 0,5 $: +415 +285 +462 +25 X(mag) +110 +112 +81 +117 +52; ~14.600 / ~6.100 ordini al mese.
- TP 0,3 $: +391 +289 +425 +4 X(mag) +94 +94 +72 +100 +43; ~19.300 / ~8.500 ordini al mese (più trade).
- Senza hedging il migliore brucia 2 mesi (gen, ago). Lotto x2,5 o distanza 12 $: 2-3 mesi bruciati.
Set "più trade": `mql5/Presets/CestoTopBottom_HFT_tick_5000USC_piuTrade.set`.
