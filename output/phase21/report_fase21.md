# Fase 21 — "migliorare finché è profittevole" Breakout Retest Pro, con scelta walk-forward

Script `python/scripts/phase21_brt_walkforward.py` (2.817 varianti: M15/H1, swing, impulso, zona di retest, filtro
SMA50/regime D1+H4/nessuno, entrambi i lati o solo acquisti, SL 1-2,5 ATR, TP 2-8 ATR) e `phase21_random_check.py`.

## Risultati
- Catena walk-forward 2013-2026 (scelta ogni anno sui 3 anni prima): 330 trade, +0,33 R (costi utente), +0,28 R (prudenti), 7/13 anni positivi.
- MA 799 varianti su 2.817 sono positive in entrambi i periodi: segno che il vantaggio viene in gran parte dal rialzo
  dell'oro. Controllo con ingressi CASUALI (stesso filtro, stessi lati, stesso SL/TP): solo acquisti in regime rialzista
  con TP 8 ATR fa già circa +0,2 R a caso.
- Le varianti H1 "solo acquisti + regime D1/H4 + SL 1 ATR + TP 8 ATR" battono il caso: +0,55/+0,59 R contro +0,19/+0,22
  (p = 0,000-0,015 su 200 estrazioni; ottimistico perché scelte tra molte varianti).
- Variante scelta per l'EA (swing 5, impulso 1,5, zona 1 ATR): 393 trade 2010-01/2026, vinti 21%, +0,56 R; ma
  2010-2015 circa -12 R in totale (oro in calo/laterale) e 2016-2025 +224 R (oro in rialzo). Serie peggiore 18 perdite.
  Conto 116 $ a 0,01 lotti: da 2022 -> 960 $ (calo max 43%), da 2025 -> 630 $ (calo 28%). Stop mediano 2025: 8,4 $ (7% del conto).
- EA: `mql5/Experts/ThirdParty/BRT_Pro_Migliorato.mq5` (non compilato dall'autore, blocco sul conto reale di default).

## Avvertenze
- È di fatto un sistema "compra le rotture nel trend rialzista": se l'oro smette di salire, il filtro lo ferma (nessuna
  vendita) ma nel 2010-2015 ha perso un poco.
- Scelto dopo molte prove: il risultato futuro atteso è più basso di quello storico.
