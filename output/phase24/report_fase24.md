# Fase 24 — EA "TopBottom Martingale Basket": set dell'utente e simulazione di un cesto martingala sull'oro M1 2026

Simulazione generica (codice EA non disponibile): cesto BUY e SELL sempre attivi, livelli ogni D $ (x1,1), lotto x m,
max N livelli, chiusura a T $ oltre il prezzo medio, stop cesto S% del saldo. Barre M1 Axi gen-ott 2026, conto 5.000.
`python/scripts/phase24_basket_sim.py`.

- Versione ottimista (nella stessa barra M1 prima la chiusura): molti set sembrano moltiplicare il conto x20-60.
- Versione prudente (nella stessa barra prima il movimento contrario, commissione 0,04 $): **375 set su 384 azzerano
  il conto**; i 9 sopravvissuti hanno cali dal 70% al 92%. Il set dell'utente (x1,5, 20 livelli, 3 $) azzera il
  conto in tutte le varianti di stop.
- Con livelli di pochi dollari su M1 il risultato dipende dall'ordine dei prezzi dentro il minuto: serve il tester MT5
  con "Ogni tick basato su tick reali". Il set del file è "meno pericoloso", non "sicuro".

Set dell'utente: x1,5 e 20 livelli = ultimo livello ~22 lotti, cesto ~66 lotti; 300 punti tra i livelli; stop cesto 500%
(nessuno); SL/TP nascosti al broker; 5 strategie attive. Set consegnato (scelta utente: strategie aggressive invariate): output/phase24/set_basket_utente_migliorato.set
(richiesta finale utente: nessuno stop cesto, SL/TP nascosti come l originale; solo H24 e filtro notizie spento).

## Versione nostra: `mql5/Experts/CestoTopBottom/CestoTopBottom.mq5`
Scritta da zero con gli stessi nomi di input dell'originale (il .set dell'utente si carica direttamente; notizie e
licenza assenti). Cesti, livelli, lotti, distanze, TP del cesto, trailing e perdita massima seguono le impostazioni;
le ENTRATE delle 5 strategie sono nostre (codice originale chiuso): frattale, RSI 30/70, Bollinger, stocastico 20/80,
nuovo minimo/massimo di 20 barre con candela opposta. MaxTrades=0 = nessun limite. Non compilato qui: compilare in
MetaEditor e provare nel tester con tick reali, conto hedging.
