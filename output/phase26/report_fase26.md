# Fase 26 — cesto martingala M1 "macchina da guerra": scelta su gen-mag 2026, verifica su giu-ott 2026

`python/scripts/phase26_basket_smart.py` (1.458 combinazioni, `prove.csv`). Lotti arrotondati come il broker, deposito
500.000 (5.000 EUR cent), stop out al 50% del margine, nella barra M1 prima il movimento contrario.

- Entrata con la tendenza (EMA200 H1) >> BUY+SELL insieme (che salta nella verifica).
- TP che scende con i livelli, distanza ATR, moltiplicatore che rallenta: nessun aiuto. Moltiplicatore x1,5 invariato.
- Migliore: distanza 1 $ che cresce x1,3, TP 3 $ sul prezzo medio, filtro strappo 6 ATR (4 era troppo severo).
  Gen-mag +145% (calo 27%), giu-ott +56% (calo 17%), ~7.500 ordini al mese. Con TP 2 $: +103% / +43%, ~10.100 ordini.
- EMA: 200 H1 (12.000 M1) è chiaramente la migliore per il calo (EMA più corte o più lunghe: cali 60-100%).
- Gen-ott di fila, TP 3 $: lotto fisso +202% (calo 27%); lotto 0,01 ogni 500.000 **+388%** (calo 27%);
  0,01 ogni 250.000 (parte da 0,02) +5.104% ma calo 64%.
- Mese per mese da capo: tutti i 10 mesi positivi (+4%...+41%), calo massimo 30%. Guadagno in calo da giugno.
Set: `mql5/Presets/CestoTopBottom_MacchinaDaGuerra.set`, `mql5/Presets/CestoTopBottom_Turbo.set`.
Limite: simulazione su candele M1, non tick; va confermata nel tester con tick reali e deposito 500000.
