# XauTrendRegime: guida a input, installazione e verifica in MT5

> L'EA non è mai stato compilato né eseguito dall'autore: l'ambiente di sviluppo non ha MetaTrader. Segui la checklist della sezione 4 prima di qualunque uso, e usa solo un conto demo finché non è completata.

## 1. Installazione

1. In MT5 apri `File > Apri cartella dati` e copia:
   - `mql5/Experts/XauTrendRegime/XauTrendRegime.mq5` in `MQL5\Experts\XauTrendRegime\`;
   - **tutta** la cartella `mql5/Include/RaptorRecon/` in `MQL5\Include\RaptorRecon\` (contiene Logger, MarketModel, Risk, Defines);
   - `mql5/Presets/XauTrendRegime_*.set` in `MQL5\Presets\`.
2. Apri `XauTrendRegime.mq5` in MetaEditor e premi **F7**. Il risultato atteso è `0 errors`. Se ci sono errori, salva il log e mandalo.
3. Trascina l'EA su un grafico **XAUUSD**. Il timeframe del grafico è indifferente: l'EA legge da solo M1, H4 e D1. Abilita "Algo Trading".

## 2. Input

| Input | Default | Significato |
|---|---|---|
| `LotMode` | RISK_PERCENT | `FIXED` = lotto fisso; `RISK_PERCENT` = lotto calcolato dal rischio |
| `FixedLot` | 0,01 | Usato con FIXED. **Mai modificato**: se non rispetta min/max/step del broker o il margine, il trade viene rifiutato e registrato |
| `RiskPercent` | 1,0 | Percentuale della base rischiata allo stop (include commissione e slippage stimati). Se il lotto minimo supera il rischio, il trade viene **saltato** |
| `RiskBase` | Equity | Balance o equity |
| `MaxAggregateRiskPct` | 3,0 | Somma del rischio (distanza fino allo SL) di tutte le posizioni dell'EA più quella nuova |
| `MaxPositions` | 1 | La ricerca usa 1 |
| `MaxRiskPctTrade` | 2,0 | Tetto per singolo trade, valido anche con lotto fisso |
| `DailyLossPct` / `MaxDrawdownPct` | 3 / 20 | Al superamento si bloccano le nuove entrate. Le posizioni aperte restano gestite |
| `MaxConsecLosses` / `PauseHours` | 0 / 24 | Pausa dopo N perdite consecutive. **Non validato** nella ricerca, quindi spento |
| `MaxSpreadPrice` | 1,0 | Spread massimo, in dollari, per entrare |
| `AllowLong` / `AllowShort` | true / **false** | Lo short è lo specchio esatto, ma nella ricerca ha perso in 36 varianti su 36 |
| `DonchianBars`, `AtrPeriod`, `StopAtr`, `TrailAtr`, `MaxHoldM1Bars` | 55, 14, 3, 3, 7200 | Configurazione validata (vedi report) |
| `UseRegimeFilter`, `RegimeEmaD1`, `H4SwingK` | true, 50, 2 | Filtro di regime D1 EMA50 + struttura H4 |

- **Conti netting:** se sul simbolo esiste una posizione di un altro EA o manuale, l'EA non entra, perché si fonderebbe con la sua.
- **Conti hedging:** l'EA conta e gestisce solo le proprie posizioni, identificate dal magic number.

## 3. Configurazioni consigliate

| Uso | Preset |
|---|---|
| **Primo test demo** | `XauTrendRegime_DEMO_PRUDENT.set` (rischio 0,5%, tetto 1%, perdita giornaliera 1,5%, DD 10%) |
| Rischio percentuale standard | `XauTrendRegime_RISK_PERCENT_1pct.set` |
| Lotto fisso | `XauTrendRegime_FIXED_LOT_001.set` (con lotto 0,01, cioè 1 oncia, lo stop di 3 ATR H4 vale circa 30–120 $: verifica il rischio sul tuo conto) |
| Confronto con la ricerca | `XauTrendRegime_RESEARCH_PARITY.set` (protezioni spente) |

## 4. Checklist: il comportamento in MT5 corrisponde alla strategia testata?

1. **Compilazione:** 0 errori, e preferibilmente 0 avvisi rilevanti.
2. **Strategy Tester:**
   - simbolo XAUUSD, periodo 2018.01.01 → oggi;
   - **Every tick based on real ticks**, ritardo casuale;
   - preset `RESEARCH_PARITY`, deposito 10.000 USD.
3. **Journal:** la riga `INIT` riporta tick size, tick value, volume minimo, step, stops level e freeze level del broker. Verificali.
4. **Ora server:** controlla la pausa giornaliera dell'oro sul tuo broker. Le barre H4 e D1 devono seguire lo stesso calendario del feed analizzato (server = NY + 7 h, D1 che chiude alle 00:00 server). Se il broker usa un altro fuso, i livelli D1 e H4 cambiano e i risultati possono divergere.
5. **Numero di trade:** circa 1,3 al mese, 139 nel 2018–2026. Se è molto diverso, la logica o i dati non corrispondono.
6. **Ingressi:** solo all'apertura di una nuova barra H4, a mercato, con SL = chiusura H4 − 3 × ATR14. In `MQL5\Files\RaptorRecon\XTR_parity_signals.csv` ogni segnale rifiutato ha il suo motivo (regime, spread, rischio, margine…).
7. **Trailing:** lo SL si muove solo a favore, ogni minuto, a 3 × ATR dall'ultima chiusura M1. Chiusura forzata dopo circa 5 giorni di trading.
8. **Confronto trade per trade:**
   `python python/scripts/compare_ea_vs_python.py <...>/XTR_parity_trades.csv reports/trades_TREND_REGIME_long_only.csv 5`
   Le differenze vanno spiegate (spread reale, tick reali, swap del broker).
9. **Demo forward:** almeno 3 mesi con il preset prudente. Confronta il numero di trade e l'R medio con i valori attesi:
   - circa 1–2 trade al mese;
   - aspettativa circa +0,3R per trade, ma con grande variabilità: anche 6–7 perdite di fila sono normali.
