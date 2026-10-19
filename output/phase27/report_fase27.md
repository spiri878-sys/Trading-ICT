# Fase 27 — protezioni contro le bruciature del cesto (livelli massimi, giro di tendenza, hedging)

`python/scripts/phase27_basket_protect.py`, base MacchinaDaGuerra, mese per mese da capo, deposito 100.000 (sotto
pressione) e 500.000 (= 5.000 EUR cent). Scelta gen-mag, verifica giu-ott. Tabella completa: `protezioni.csv`.

- Senza protezioni, 500.000: 0 mesi saltati, gen-mag +133%, giu-ott +54% (TP 3 $), calo massimo 30%.
- Senza protezioni, 100.000: 3 mesi saltati su 10.
- Livelli massimi (8-16, poi chiusura del cesto): niente più conto bruciato a 100.000 con 14 livelli, ma i soldi
  persi nei cesti chiusi mangiano tutto il guadagno (gen-mag -78%, giu-ott +77% a 100.000; -16% / +15% a 500.000).
- Chiusura quando la tendenza gira: peggio in tutti i casi.
- Hedging (copertura al livello 8-12): risultati instabili, spesso brucia lo stesso; bloccare la perdita è uno stop
  rimandato e la copertura va tolta al momento giusto: non funziona in modo stabile.
- Conclusione: nessuna protezione migliora il set; quello che decide è il capitale. L'utente nel tester usava 5.000
  (= 50 EUR su un conto cent): con 0,01 lotti servono 500.000 nel tester per simulare 5.000 EUR cent.
