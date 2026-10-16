# Frequenza contro profitto, un trade alla volta (Fase 11)

Fonte: tutte le griglie della Fase 11 (`trend_exit_grid.csv`, `intraday_grid.csv`, `intraday_ai_grid.csv`, `selftrain_trail_grid.csv`): celle ICT, regime, AI autoallenata, uscite dinamiche e intraday, costi C1.

| Trade al giorno (sviluppo 2010-15) | Configurazioni | Positive in entrambi i periodi | 2016-26: R della migliore in sviluppo |
|---|---|---|---|
| fino a 0,05 | 28 | 17 | +0,231 |
| 0,05–0,1 | 5 | 3 | +0,395 |
| 0,1–0,25 | 133 | 85 | +0,107 |
| 0,25–0,5 | 427 | 105 | +0,077 |
| 0,5–1 | 424 | 14 | −0,060 |
| 1–2 | 443 | **0** | −0,045 |
| 2–3 | 322 | **0** | — |
| ≥ 3 | 739 | **0** | — |

**Conclusione:**
- Con un trade alla volta, oltre 1 trade al giorno nessuna delle circa 1.500 configurazioni è profittevole in entrambi i periodi.
- Su orizzonti di poche ore i segnali delle celle non hanno vantaggio lordo e i costi (circa 0,3–0,4 $ per oncia) lo rendono negativo.
- Il venditore dichiara 169 trade in circa 190 giorni nel 2026 (circa 0,9 al giorno), scartando circa il 90% dei segnali.
