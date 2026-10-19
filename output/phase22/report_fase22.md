# Fase 22 — Breakout Retest su Bitcoin (BTCUSDT 1m Binance, 2018-01 -> 2026-09)

Dati: archivio pubblico data.binance.vision (105 file mensili, 4,59 milioni di barre M1; non nel repository).
Costi per trade in % del prezzo: A 0,05%, B 0,12%. Script `python/scripts/phase22_btc_breakout.py`.

## 1. EA "BRT Pro migliorato" scelto sull'oro, INVARIATO su Bitcoin (prova fuori campione vera)
- 270 trade, vinti 16%, R medio +0,14 (A) / +0,04 (B); serie peggiore 17 perdite; stop mediano 2025 circa 540 $ di prezzo.
- Ingressi CASUALI con lo stesso filtro e le stesse uscite: +0,14 (A) / +0,04 (B). p = 0,46-0,51.
- **Su Bitcoin la logica breakout-retest non aggiunge niente al caso.** Indebolisce anche il risultato sull'oro
  (Fase 21): il vantaggio sopra il caso trovato lì è probabilmente in buona parte fortuna della scelta tra ~2.800 varianti.

## 2. Ricerca walk-forward su Bitcoin (2.871 varianti, scelta annuale sui 3 anni precedenti)
- 400 varianti positive sia nel 2018-21 sia nel 2022-26 (costi A): effetto del rialzo di Bitcoin.
- Catena 2021-2026: 131 trade, +0,10 R (A), -0,01 R (B), 3 anni positivi su 6. Non convincente.

## Conclusione
Nessun bot breakout profittevole in modo affidabile su Bitcoin. I guadagni storici vengono dal rialzo del prezzo (le
stesse uscite con ingressi casuali guadagnano uguale).
