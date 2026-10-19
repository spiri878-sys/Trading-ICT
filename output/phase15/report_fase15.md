# Fase 15 — oro con conto da 100 EUR (0,01 lotti, leva 1:1000)

Vincolo: 0,01 lotti = 1 $ per $ di movimento. Lo stop del candidato Fase 11 (1,5 ATR H4 = 30-67 $ nel 2025-26) rischierebbe
il 25-60% del conto a trade: escluso. Cercata una regola con stop fisso di 2-8 $ (`phase15_small_stop.py`, 64 configurazioni,
costi 0,385 $ a trade, sviluppo 2010-15, verifica 2016-01/2026).

## ERRORE TROVATO E CORRETTO (19/10/2026)
La prima versione di T2 leggeva la rottura del Donchian H4 con l'etichetta di APERTURA della barra H4: le barre H1 dentro
quella H4 conoscevano già la sua chiusura (fino a 3 ore di futuro). Con quel difetto T2 sembrava positiva in tutte le
16 combinazioni (+0,10 R). Corretto (rottura nota solo alla chiusura H4): **T2 negativa** (-0,10 R sviluppo, -0,05 R
verifica, 1-5 anni positivi su 11). I risultati della prima versione (tabella e t2_checks.json) NON valgono.

## Risultato corretto
- 3 configurazioni su 64 positive in entrambi i periodi (T1 8$/24$, T1 8$/40$, T3 8$/40$), tutte con R tra +0,006 e
  +0,067 e 2-3 anni positivi su 6 in sviluppo: compatibile con il caso (64 prove). Nessuna regola utilizzabile.
- Conferma le fasi precedenti: sull'oro, con stop piccoli e operatività intraday (M1/M5/H1), i costi (spread ~0,3-0,4 $)
  cancellano qualsiasi vantaggio. Fase 11: oltre 1 trade al giorno 0 configurazioni su ~1.500 positive in entrambi i
  periodi; hft01 (scalping M1): nessuna configurazione positiva con costi reali.
