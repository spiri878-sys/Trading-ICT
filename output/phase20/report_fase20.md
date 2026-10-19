# Fase 20 — EA di terzi "Breakout Retest Pro v2.0" (mql5/Experts/ThirdParty/)

## Lettura del codice
- Entra A MERCATO dopo rottura (2 chiusure oltre la neckline) e retest; SL 1,5 ATR, TP 8 ATR ("4 x 2"); filtro SMA50.
- Swing confermati correttamente (nessun anticipo).
- Difetti: `current_bar_idx` = iBarShift della barra corrente = sempre 0 -> la scadenza del retest non scatta mai;
  l'uscita per "inversione" legge la barra appena aperta (open = close) -> engulfing/tre barre/movimento ATR quasi mai
  attivi; slippage massimo 2 punti + riempimento FOK -> sul reale ordini rifiutati/riquotati nei momenti veloci;
  con conti piccoli il rischio "1%" diventa il lotto minimo 0,01 (rischio vero molto più alto).

## Test (`python/scripts/phase20_brt_pro.py`, costi utente A 0,15 $ / B 0,27 $, 2010-15 e 2016-01/2026)
- M5: fortemente negativo in tutte le varianti (-0,09/-0,30 R, 530-615 trade/anno).
- H1: intorno a zero con l'uscita per inversione; senza, 0,00 R nel 2010-15 e +0,11 nel 2016-26 (2/6 anni positivi in sviluppo).
- M15 senza uscita per inversione: +0,055 R (2010-15) e +0,087 R (2016-26) con costi A; +0,01 / +0,04 con costi B.
  Ma: guadagnano solo gli acquisti (+0,13 R) mentre le vendite sono a zero (+0,02) -> è soprattutto il rialzo dell'oro;
  vinti 18%, serie peggiore 27 perdite di fila; conto da 116 $ a 0,01 lotti partendo nel 2022 -> AZZERATO.
- Conclusione: non è un bot profittevole in modo affidabile, e su 100 EUR è rovinoso.
