# Guida MT5: installazione, compilazione, backtest, configurazione

> **Stato**: l'EA **non è mai stato compilato** né eseguito in MT5. L'ambiente di sviluppo (container Linux) non dispone di MetaEditor, Wine o Strategy Tester. È stato verificato solo con `tools/mql5_static_check.py` (bilanciamento, include, input usati, parità con Python), che **non** sostituisce il compilatore. La prima compilazione su Windows potrebbe segnalare errori da correggere.

## 1. Installazione (Windows, MT5 build recente)

1. In MT5 apri `File > Apri cartella dati`.
2. Copia `mql5/Experts/RaptorRecon/RaptorRecon.mq5` in `MQL5\Experts\RaptorRecon\`.
3. Copia `mql5/Include/RaptorRecon/*.mqh` in `MQL5\Include\RaptorRecon\`.
4. Copia `mql5/Presets/*.set` in `MQL5\Presets\` (oppure caricali dalla scheda Inputs del tester).

## 2. Compilazione

- **Da MetaEditor**: apri `RaptorRecon.mq5` e premi F7. Il risultato deve essere `0 errors`. Salva il log di compilazione in `reports/mt5/compile_log.txt`.
- **Da riga di comando** (PowerShell):

  ```
  & "C:\Program Files\MetaTrader 5\MetaEditor64.exe" /compile:"<DataFolder>\MQL5\Experts\RaptorRecon\RaptorRecon.mq5" /log:"<DataFolder>\compile.log"
  ```

Se compaiono errori, inviameli: il log verrà analizzato e corretto.

## 3. Backtest nello Strategy Tester

| Impostazione | Valore consigliato | Perché |
|---|---|---|
| Expert | RaptorRecon | |
| Simbolo | XAUUSD del broker (l'EA rifiuta ogni altro simbolo) | Guard `IsXauUsd` |
| Timeframe del grafico | M1 (l'EA legge da solo M5, M15, H1) | Gestione su barre M1 chiuse |
| Periodo | 2018.01.01–2021.12.31 (dev), 2022.01.01–2023.12.31 (val), 2024.01.01–oggi (test) | Stessi periodi della ricerca |
| **Modelling** | **Every tick based on real ticks** | Il video del venditore usava "1 minute OHLC" (E-14), troppo ottimistico per stop di pochi dollari |
| Delays | Random delay, oppure 50–200 ms | **Non** "Zero latency, ideal execution" |
| Deposito / leva | 10.000 USD, 1:100 (anche 1.000 per vedere i rifiuti per lotto minimo) | |
| Preset | `RaptorRecon_C_unicorn_long_risk1pct.set` (profilo C, il migliore), `RaptorRecon_A_faithful_risk1pct.set` (profilo A), poi `…_fixed008`, `…_W_wyckoff_benchmark`, `…_B_experimental_H1` | |

Durante e dopo il test raccogli:

- il report del tester (tasto destro > Report > HTML, oppure "Open XML");
- i file CSV dell'EA in `<Agent>\MQL5\Files\RaptorRecon\`: `RR_*_signals.csv`, `RR_*_trades.csv`, `RR_*_events.csv`. Il percorso dell'agente è indicato nella scheda Journal.

## 4. Confronto EA ↔ simulatore Python (trade per trade)

```
cd python
python scripts/benchmark_final.py            # genera reports/trades_<profilo>_<periodo>_C1.csv
python scripts/compare_ea_vs_python.py <...>/RR_A_faithful_fixed008_trades.csv ../reports/trades_ICT_FAITHFUL_val_C1.csv 2
```

Il report `reports/ea_vs_python_*.csv` elenca i trade abbinati, quelli presenti solo nell'EA e quelli presenti solo in Python, con le differenze su:

- prezzo d'ingresso;
- stop;
- lotto;
- risultato netto;
- parziali.

Differenze attese, da spiegare caso per caso:

- **Spread e costi**: il tester usa lo spread reale; il simulatore usa C1 fisso a 0,30.
- **Ordine intrabar**: tick reali nel tester, assunzione pessimistica nel simulatore.
- **Inizializzazione della struttura**: l'EA ricalcola la struttura sulle ultime 1000 barre, il simulatore su tutto lo storico.
- **Profondità storica**: l'orario NY e i livelli di liquidità dipendono dalla storia caricata dal broker.

## 5. Configurazione: input principali

| Gruppo | Input | Default | Note |
|---|---|---|---|
| Generale | `InpProfile` | FAITHFUL_M5 | A / B (sperimentale, fallito in validazione) / Wyckoff / **C Unicorn long** (consigliato per i test) |
| | `InpAllowRealAccount` | false | Su un conto reale l'EA non parte |
| | `InpNyOffsetHours` | 7 | Ora server − ora New York: **va verificato sul proprio broker** |
| Stop | `InpStopMode` | STRUCTURAL | FIXED / PERCENT obbligatorie, STRUCTURAL / ATR aggiuntive (vedi `stop_and_lot.md`) |
| Lotto | `InpLotMode`, `InpFixedLot` | FIXED, 0,08 | RISK_PERCENT con `InpRiskPercent` e `InpRiskBase` |
| | `InpMaxRiskPctTrade` | 2,0 | Tetto di rischio per trade, anche con lotto fisso: **rifiuta, non riduce** |
| Gestione | `InpTpR`, `InpP1R`, `InpP1Frac`, `InpP2R`, `InpP2Frac`, `InpBreakEven` | 4 / 0,7 / 0,2 / 2 / 0,2 / true | Da E-25 |
| Protezioni | `InpMaxPositions`, `InpMaxTradesPerDay`, `InpDailyLossPct`, `InpMaxDdPct`, `InpMaxSpreadPrice` | 1, 3, 3%, 25%, 1,0 | |
| | `InpBreathe*` | off | Rischio che respira (E-27), solo in modalità rischio % |
| | `InpNewsFilter` | off | Calendario MT5: solo live, **non disponibile nel tester** |
| Celle | `InpCellUnicorn/OTE/SilverBullet/PO3/MSS/LS/PPK` | | Ogni cella è abilitabile e testabile singolarmente |
| Telegram | `InpTelegram`, `InpTelegramToken`, `InpTelegramChat` | off | Abilita `https://api.telegram.org` in Strumenti > Opzioni > Expert Advisor > WebRequest. Non funziona nel tester. **Non testato** |

### Ciclo di vita del trade (macchina a stati)

```
SEGNALE --(controlli: duplicato, esposizione, trade/giorno, kill switch, perdita giornaliera,
           spread, notizie, stop valido, lotto, tetto rischio, margine)--> RIFIUTATO (motivo nel CSV)
   └--> PENDENTE (limit) --scadenza / venerdi'--> SCADUTO
          └--> APERTO (SL+TP dal broker) --chiusura M1 >= P1--> P1 FATTO (+BE)
                 --chiusura M1 >= P2--> P2 FATTO --TP / SL / BE / durata massima / venerdi'--> CHIUSO
```

Gli stati (R iniziale, volume iniziale, fase dei parziali) e i contatori (picco, trade del giorno, segnali già processati) sono salvati nelle GlobalVariables del terminale. Dopo un riavvio vengono ripresi e lo stesso segnale non viene inviato due volte.
