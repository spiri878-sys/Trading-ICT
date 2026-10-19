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

## Griglia con entrata continua (HFT) — `griglia_mese_per_mese_500k.csv`
Entrata continua (il cesto chiuso si riapre subito) "a caso" contro "con criterio" (lato EMA200 H1, niente strappi),
distanza 1,5/2/3 $, crescita della distanza x1,1/1,2/1,3, TP 1/2/3 $, lotto x1,5 e 50 livelli, mese per mese.
- Set attuale (2 $, x1,1, TP 2): a caso 5 mesi saltati su 10; con criterio 1 su 10, +14% nei mesi buoni.
- Migliore: **con criterio, 1,5 $, crescita x1,2, TP 3 $: 0 mesi saltati, +16,5% medio, calo medio 25%, ~1.650
  cesti al mese**. Vicini anche loro a 0 mesi saltati: 1,5/x1,2/TP 2 (+11%), 2/x1,2/TP 3 (+10%).
- La crescita x1,2 della distanza è il cambiamento che conta (livello 20 a ~232 $ di movimento contro, invece di ~102 $).
- Scelto sugli stessi dati: va confermato nel tester con tick reali. Trailing non simulato (nel set è spento).
Set: `mql5/Presets/CestoTopBottom_HFT_consigliato.set` (solo strategia 2: 5 strategie insieme = 5 cesti uguali = 5x
il rischio).

## Tante entrate senza saltare — `griglia_tante_entrate_500k.csv`
Ordini al mese (ogni livello conta), mese per mese da capo a 500.000; "calo max" = peggior mese.
| set | ordini/mese | cesti/mese | mesi saltati | guadagno medio | calo max |
|---|---|---|---|---|---|
| set utente a caso (2 $ x1,1 TP 2) | ~12.600 (si ferma quando salta) | ~4.900 | 5/10 | +44% | 100% |
| HFT a manetta: BUY+SELL dopo calma, 1 $ x1,25, TP 1 $ | ~21.400 | ~8.000 | 0/10 | +14,5% | 96% |
| HFT equilibrato: lato tendenza, 1 $ x1,25, TP 2 $ | ~8.100 | ~2.500 | 0/10 | +14,8% | 60% |
| precedente consigliato (1,5 $ x1,2 TP 3 $) | ~5.300 | ~1.650 | 0/10 | +16,5% | 87% |
Il "calo medio 25%" scritto sopra era la media: il peggior mese del set precedente è arrivato all'87%.
Set: `mql5/Presets/CestoTopBottom_HFT_manetta.set`, `mql5/Presets/CestoTopBottom_HFT_equilibrato.set`.
