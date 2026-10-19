# Fase 18 — idea utente: struttura + liquidity sweep + conferma con ordine stop pendente + filtri

Script `python/scripts/phase18_sweep_pending.py`. Swing frattali k=3 (noti 3 barre dopo), sweep = la barra supera l'ultimo
swing confermato e richiude dentro; BUY STOP sopra il massimo della barra dello sweep (SELL STOP sotto il minimo), SL oltre
l'estremo dello sweep, TP 1,5/2/3 R, ordine valido 4 barre, un trade alla volta. Filtri: multi-timeframe (D1 + H4 vs EMA50,
solo barre chiuse), sessione Londra+NY, ATR relativo 0,7-2,0. Notizie: nessun calendario storico (non testabili).
M5 e M15, costi utente A (0,15 $) e B (0,27 $), sviluppo 2010-15, verifica 2016-01/2026.

## Risultato
- **0 configurazioni su 48 positive in entrambi i periodi** (costi A); M5 peggio di M15.
- Molte operazioni (200-700 all'anno su M15) ma R medio in verifica tra -0,01 e -0,05 nelle migliori; nessuna regola usabile.
- Le varianti migliori in sviluppo (M15, trend, Londra+NY, senza filtro ATR: +0,07/+0,10 R) diventano negative in verifica:
  tipico di una scelta fortunata sul passato.
- Coerente con le fasi 11-17: sull'oro, sotto l'ora, gli ingressi su sweep/rottura non hanno vantaggio dopo i costi.
