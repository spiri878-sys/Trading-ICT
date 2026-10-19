# Fase 30 — conto 5.000 USC: famiglie di bot diverse dal cesto

`python/scripts/phase30_families.py` (3.392 prove, `famiglie.csv`), mese per mese da capo a 5.000, equity finale con le
posizioni aperte valutate, scelta gen-mag e verifica giu-ott.
- A riduttore (chiude insieme il primo ordine in perdita e l'ultimo in guadagno): il migliore brucia 3 mesi su 10
  (D8 x1,2, lotto x1,5, TP 2, da 4 livelli): peggio del cesto con hedging (1 mese).
- B piramide (aggiunge a favore, trailing): numeri enormi solo con passi e trailing di 0,5-2 $, più piccoli di una
  candela M1 (in media 2 $; 5.534 candele oltre 10 $): la simulazione su candele li inventa. Con passi/trailing da
  3-8 $ (dove la simulazione è credibile) perde in tutti i mesi.
- C zone recovery: con zona 1 $ e uscita 8 $ tutti i 10 mesi positivi (+3...+137%), ~6.300 ordini al mese; ma con
  zona da 2 $ in su (credibile) perde. Zona 1 $ < candela M1: risultato non affidabile, va giudicato coi tick reali.
  EA per il tester: `mql5/Experts/ZonaRecupero/ZonaRecupero.mq5`.
- Nota: la simulazione della fase 26 (usata anche nella 28) a fine mese contava solo il saldo, non i cesti aperti
  (leggermente ottimista); le fasi 27, 29 e 30 valutano anche le posizioni aperte.
