# Fase 23 — AI Golden Life MT5 (EA commerciale, .ex5 chiuso): analisi del report del tester inviato dall'utente

Report: Axi, XAUUSD.p H1, 01-30/09/2026, "100% ticks reali", deposito 100, leva 1:1000, lotto 0,01.
Parametri: OrdersMax=1, TakeProfit=50, StopLoss=50 (= 5 $ di prezzo), OrdersStep=70 / OrdersProfit=50 (funzione
griglia presente ma spenta con OrdersMax=1), orari 08-22 (venerdì 20), filtro notizie 90'/90', AIFilter=true.

## Come opera (dal report)
- Entra SEMPRE a mercato al secondo 10 dell'apertura di una barra H1 (69/69 ingressi alle hh:00:10), una posizione alla volta.
- Stop e target simmetrici: +5 $ / -5 $ (1:1). Durata media 12 minuti, massima 56.
- Settembre 2026: 69 trade, 62 vinti (89,9%), buy 90% e sell 90%; TUTTI i 21 giorni di trading positivi; +281 $ su 100.

## Valutazione
- Con TP = SL = 5 $ la percentuale di vincita "normale" è ~50%: sull'oro 2025 (nostre barre M1, stesso schema: ingresso
  all'apertura H1 08-22 con TP/SL 5 $) segui-candela 48,2%, contro-candela 50,5%, sempre buy 50,6% (3.480 trade).
- 90% su 1:1 vorrebbe dire indovinare la direzione dei prossimi minuti 9 volte su 10: nessuna strategia nota ci arriva.
  Spiegazione più probabile: parametri/regole adattati proprio al periodo mostrato (settembre 2026, appena prima del
  lancio della v1.0), o un elenco di operazioni "imparato" sul passato. Va verificato su periodi diversi.
- Test richiesti all'utente (stesse impostazioni, tick reali): 01-17/10/2026 (dopo settembre), tutto il 2025, gen-ago 2026.
  Se la vincita crolla verso il 50% fuori da settembre: bot adattato al passato, da non comprare.
- Ricostruirlo: lo schema di ingresso/uscita è chiaro, ma la regola della direzione non si può ricavare da un solo mese
  (e se è adattata al passato non esiste una regola vera da copiare).

## Aggiornamento 19/10: barre M1 del broker dell'utente (Axi, 02/01 -> 19/10/2026)
- Le 69 operazioni di settembre simulate sulle barre dell'utente: 92,8% vinte (reale 89,9%): dati allineati.
- Direzione: SEMPRE contro la media. Compra se l'ultima H1 chiusa è sotto EMA10/EMA20/SMA20, vende se sopra: 69/69.
- Ma la stessa regola su TUTTE le ore in cui il bot poteva entrare (settembre, 08-22, 300 ore) vince solo il 45%
  (gen-ott 2026, mese per mese: 44-57%). Il 90% viene interamente da QUALI ore sceglie.
- Nessuna variabile visibile (distanza dalla media in ATR o z-score, RSI, corpo e ampiezza della candela, ATR)
  separa le ore scelte da quelle scartate: le distribuzioni si sovrappongono quasi del tutto.
- Ipotesi principale: scelte adattate ai dati di settembre (o elenco di orari memorizzato). Decisivo il report gen-ott.

## Aggiornamento: report del tester gen -> 19/10/2026 (1 minuto OHLC, OrdersMax=1, deposito 100, 0,01 lotti)
- 729 operazioni, 83,1% vinte (tester); ricalcolate sulle barre M1 Axi in modo prudente: 86,1%.
- Direzione contro EMA10 nel 98,6% dei casi. Stessa regola in tutte le ore: 44-57% al mese.
- Vincite per mese (tester): gen 83%, feb 88%, mar 87%, apr 82%, mag 84%, giu 86%, lug 82%, ago 83%, set 86%, ott 64%.
- Le ore scelte vincono il 74,6% anche entrando DOPO il primo minuto: la scelta "sa" più di quanto si possa sapere
  a hh:00:20 (conoscere l'intero primo minuto dà solo il 67% entrando all'apertura e il 50% entrando dopo).
- **Dal 13/10/2026 (uscita della v1.0 sul Market) in poi: 23 operazioni, 43,5% vinte (nostra simulazione 47,8%)**,
  contro ~85% fino al 12/10. Prima del lancio quasi perfetto, dopo il lancio una moneta lanciata: firma di un
  sistema costruito conoscendo già il passato (dati/segnali "imparati" fino alla data di costruzione).
- Conclusione: non c'è una regola vera da copiare. La parte visibile (contro la media all'apertura di ogni ora,
  TP = SL = 5 $) vince circa il 50% e con lo spread perde.
