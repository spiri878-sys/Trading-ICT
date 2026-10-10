# Dati, simulatore e modelli di costo

## Dataset (manifest: `data/manifest/XAUUSD_M1.manifest.json`)

| Voce | Valore |
|---|---|
| File | `barre xauusd m1 2017.csv`, da RAR5 multivolume, estratto con libarchive (`tools`: vedi README) |
| SHA-256 | `a0388a0e669da5fc5397f3036392184b04525055a0e400f79323bb658c17961a` (190.479.345 byte) |
| Formato | MT5 "Export Bars", separato da TAB, CRLF: `<DATE> <TIME> <OPEN> <HIGH> <LOW> <CLOSE> <TICKVOL> <VOL> <SPREAD>` |
| Prezzi | BID (convenzione dei grafici MT5), 2 decimali |
| Periodo | 2018-01-02 10:00 → 2026-10-09 23:54 (ora server). Il nome dice "2017", ma i dati partono dal 2018 |
| Righe | 3.086.760, circa 350 k all'anno, mediana 1375 barre al giorno |
| Duplicati / ordine / OHLC incoerenti / prezzi ≤ 0 | 0 / 0 / 0 / 0. Nessuna riga rimossa né interpolata |
| Lacune intrasettimanali > 10 min | 1835: quasi tutte la pausa giornaliera 23:55 → 01:01 (66 min) |
| Salti > 2% in 1 minuto | 4 (2021-08-09 01:58, flash crash reale; 2026-01-29 17:27; 2026-02-02 01:00) |
| Fuso | Server = NY + 7 h (apertura settimanale alle 01:00, pausa 23:55–01:01): **INFERITO** |
| Dati mancanti rispetto alle attese | **Barre M5 dal 2005 non fornite**; nessun tick reale; nessun dato ask |

I timeframe superiori si ottengono per aggregazione (`data.resample`):

- **open**: apertura della prima M1 del periodo;
- **high**: massimo dei massimi;
- **low**: minimo dei minimi;
- **close**: chiusura dell'ultima M1;
- **etichetta**: orario di apertura;
- nessuna barra sintetica nei vuoti.

Il contesto HTF viene unito ai segnali sull'orario di **disponibilità** (apertura + durata della barra), mai su quello di apertura. Il test `test_features_truncation_invariant` lo verifica.

## Diagnosi dello spread (`reports/spread_diagnosis.json`, `reports/spread_monthly.csv`)

- **Colonna**: `<SPREAD>`, intera, nelle unità "punti" dell'esportazione.
- **2018 → gennaio 2023**:
  - valori fra 80 e 240, **sempre multipli di 10**;
  - mediana 140, cioè $1,40 se 1 punto = 0,01;
  - in questa ipotesi lo spread supera l'**intero range** della barra M1 nel **92%** delle barre (range mediano $0,22), cosa implausibile per l'oro.
- **Da febbraio 2023**:
  - valori 0–40 e solo il 77% multipli di 10;
  - 43–55% di barre a 0 nel 2023–2024 (feed raw / ECN);
  - spread maggiore del range M1 solo nel 10% dei casi.
- **Conclusione (INFERITA, non verificabile senza il broker)**: fino al 2022 lo spread è con ogni probabilità espresso in millesimi (punti a 3 cifre). Lo spread reale sarebbe quindi intorno a $0,10–0,16.
  - I due regimi provengono da feed diversi e non sono confrontabili.
  - Nessuno spread è stato inventato: si usano scenari dichiarati.

## Modelli di costo (`python/raptor/costs.py`)

| Scenario | Spread | Commissione | Slippage | Uso |
|---|---|---|---|---|
| **C1** (decisioni) | 0,30 $ fisso, tutti gli anni | 3,5 $ / lotto / lato | 0,05 $ su stop e mercato | Selezione e confronto |
| C0R | Registrato; fino al 2022 diviso per 10 (inferito); minimo 0,05 | idem | idem | Sensibilità |
| C0 | Registrato, unità a 0,01 (minimo 0,05) | idem | idem | Stress (molto punitivo nel 2018–22) |
| C2 | 0,60 $ | 7 $ / lotto / lato | 0,10 $ | Stress ×2 |
| ZERO | 0 | 0 | 0 | Misura dell'edge lordo |

Lo **swap** (−79,48 / +34,41 $ per lotto e notte, E-28) **non** è modellato: le posizioni durano in genere meno di un giorno, e l'omissione è favorevole alle strategie.

## Simulatore (`python/raptor/engine.py`): approssimazione OHLC, non tick

- Prezzi BID; ASK = BID + spread della barra.
  - Long: entra all'ASK, esce al BID.
  - Short: entra al BID, esce all'ASK.
- **Ordini**:
  - limit eseguito al prezzo limite, o all'apertura se la barra apre già oltre;
  - mercato all'apertura della M1 successiva + slippage;
  - stop con slippage.
- **Stessa barra**: se stop e target sono toccati entrambi, **vince lo stop**. Sulla barra di esecuzione si controlla solo lo stop.
- **Parziali e break-even** decisi sulla chiusura M1 ed eseguiti al close. Il TP finale è un limit intrabar.
- **Esposizione**: una posizione e un ordine pendente alla volta; i segnali sovrapposti vengono registrati come `skipped_busy`.
- **Selettori indipendenti**:
  - stop: STRUCTURAL / FIXED / PERCENT / ATR;
  - lotto: FIXED / RISK_PERCENT.
- **Rifiuti espliciti**: lotto non valido, margine insufficiente, lotto minimo troppo rischioso, stop invalido, limite giornaliero, kill switch.
- **Etichette per il ML**: stessa routine `_manage` del backtest, quindi etichette e backtest sono coerenti per costruzione (test `test_label_matches_portfolio_single_trade`).
- **Limiti noti**:
  - nessun tick reale: con stop di pochi dollari l'ordine intrabar è incerto;
  - nessuna latenza;
  - nessuno swap;
  - nessuna conversione EUR (i conti sono trattati in USD).
