# Fase 0 — Inventario e dati

Script: `python python/scripts/phase0_data.py`. È deterministico e rigenera cache, statistiche e timeframe. I numeri completi sono in `output/phase0_stats.json`. Test: `tests/test_data_phase0.py` (79 test verdi in totale).

## 1. File ricevuti

| File | Contenuto | Periodo | Note |
|---|---|---|---|
| `data/raw/m1_new/XAU_1m_data.csv` (da `barre.part01-03.rar`) | M1, `Date;Open;High;Low;Close;Volume` | 2004-06-11 → 2026-01-30 | 6.789.606 barre; **niente spread**; Volume = volume tick |
| `data/raw/htf/XAU_30m.csv`, `XAU_4h.csv`, `XAU_1w.csv` | Stesso fornitore | 2004-06 → 2026-01-30 | Usati per la verifica incrociata |
| `data/raw/XAUUSD_M1.csv` (già presente) | M1 esportato da MT5, con spread | 2018-01-02 → 2026-10-09 | Usato per accodare 2026-02 → 2026-10 e per lo spread |

L'hash SHA-256 di ogni file è in `output/phase0_stats.json` e in `data/manifest/XAU_M1_2004_2026.manifest.json`.

## 2. Qualità del nuovo M1

- **Integrità:** 0 duplicati, 0 righe fuori ordine, 0 OHLC incoerenti, 0 prezzi ≤ 0.
- **Tick errati rimossi (4):** sono stati tolti, non interpolati.
  - 2004-10-04 23:47, 2006-04-03 01:07, 2006-10-02 01:21: tick singoli fuori livello di oltre l'1%, per esempio 578,1 dentro 598;
  - 2011-07-18 08:06: minimo a 1.495,75 con il prezzo a 1.597.
- **Movimenti veri, conservati:** il flash crash del 20 luglio 2015, il marzo 2020, il 9 agosto 2021 e il 29–30 gennaio 2026.
- **Copertura per anno** (barre presenti sui 1.380 minuti attesi al giorno):

| Anno | Copertura | Giorni sotto il 50% | Barre / giorno (mediana) |
|---|---|---|---|
| 2004 (da giugno) | 41% | 118 | 570 |
| **2005** | **41%** | **207 su 252** | **552** |
| **2006** | **48%** | **138** | **669** |
| 2007 | 68% | 12 | 922 |
| 2008 | 89% | 2 | 1.245 |
| 2009–2012 | 90–93% | 1–15 | 1.300–1.370 |
| 2013–2026 | 97–99% | 0–1 | circa 1.370 |

- **Copertura per ora:**
  - nel 2005 le ore asiatiche ed europee hanno solo il 25–40% dei minuti, contro l'85% del pomeriggio di New York;
  - nel 2008 si è già oltre l'80–99% in tutte le ore.

  I minuti mancanti sono minuti **senza scambi registrati** nel feed dell'epoca, non file tagliati: le barre a 30 minuti del fornitore sono complete.
- **Giorni "degradati"** (meno del 50% dei minuti):
  - salvati in `output/cache/day_quality.parquet`;
  - dopo il 2008 ne restano 45, per esempio dal 20 dicembre 2010 al 14 gennaio 2011, aprile 2011 e 6–20 marzo 2012;
  - in quei giorni il file ha barre quasi orarie: il 9 marzo 2012, per esempio, ha 22 barre;
  - **nessun segnale verrà generato in quei giorni.**

## 3. Fuso orario

- **Apertura settimanale lunedì 01:00, pausa giornaliera 00:00–01:00, ultima barra del venerdì alle 23 (alle 22 fino al 2010).** È identico in tutti gli anni dal 2004 al 2026 e identico al vecchio file MT5.
- **Fuso dichiarato: ora server = New York + 7 ore**, con l'ora legale USA. Tutte le serie sono già in questo fuso: nessuna conversione è necessaria.
- Le "08:00" del motore macro e le killzone ICT saranno calcolate da qui. Per esempio, l'apertura di New York alle 8:30 corrisponde alle 15:30 server.

## 4. Coerenza tra le fonti

| Confronto | Esito |
|---|---|
| Mio M30, H4, W1 (aggregati dal nuovo M1) contro i file 30m, 4h, 1w del fornitore | **Identici al 100%**: stesse barre, OHLC uguali al centesimo |
| Nuovo M1 contro vecchio M1 MT5, 2018 → 2026-01 (2,79 milioni di barre comuni) | Differenza mediana 0,05 $, 99,6% entro 0,50 $, 99° percentile circa 0,30 $. Sono due feed leggermente diversi ma lo stesso mercato e lo stesso orario |
| Barre presenti in una sola fonte | 16.149 solo nel nuovo, 54.431 solo nel vecchio, su 2,8 milioni |

**Serie master** (`output/cache/XAUUSD_M1_master.parquet`):
- **nuovo M1 dal 2004-06-11 al 2026-01-30**;
- **vecchio M1 dal 2026-02-02 al 2026-10-09**, 244.845 barre accodate.

La giunzione cade nel fine settimana:
- la differenza tra le due fonti nell'ultimo giorno comune è di 0,25 $;
- il salto da venerdì 30 gennaio (4.889) a lunedì 2 febbraio (apertura 4.779) è il gap reale del fine settimana dopo il crollo del 29–30 gennaio 2026.

Totale: **7.034.447 barre M1**.

## 5. Spread

- **Il nuovo file non ha lo spread.** Nella serie master lo spread registrato da MT5 è presente dal 2018, con unità diverse prima e dopo febbraio 2023 (vedi `docs/data_and_costs.md`); prima del 2018 vale −1 (sconosciuto).
- **Profilo per ora** (vecchio M1, regime affidabile da febbraio 2023, feed raw):
  - mediana 0,05–0,10 $ nelle ore centrali, 0,20 $ all'apertura e prima della pausa;
  - 90° percentile 0,3–1,4 $;
  - salvato in `output/cache/spread_profile_by_hour.csv`.
- **Scenari di costo** (in `configs/config.yaml`):

| Scenario | Spread | Commissione | Slittamento | Uso |
|---|---|---|---|---|
| C1 | 0,30 $ fisso | 3,5 $ / lotto / lato | 0,05 $ | Decisioni |
| C1H | Profilo per ora, minimo 0,20 $ | 3,5 $ / lotto / lato | 0,05 $ | Variante |
| C2 | 0,60 $ | 7 $ / lotto / lato | 0,10 $ | Stress ×2 |

  Per il 2005–2017 non esiste uno spread registrato: uso gli stessi scenari in dollari, ed è un'**ipotesi dichiarata**. Con l'oro a 400–1.300 $, 0,30 $ era in proporzione uno spread più largo di oggi, quindi l'ipotesi è prudente.

## 6. Timeframe costruiti (`output/cache/tf/`)

| TF | Barre | Note |
|---|---|---|
| M3 | 2.454.536 | ancorato all'ora (:00, :03, …) — Liquidity Sweep |
| M5 | 1.492.426 | PO3, Raptor Mode, supervisore LiqBias |
| M12 | 636.303 | ancorato all'ora (:00, :12, :24, :36, :48) — OTE |
| M15 | 510.618 | Unicorn |
| M30, H1, H4 | 257.106 / 129.303 / 34.029 | contesto; H4 su 00/04/08/… come il fornitore |
| D1 | 5.710 | giorno server |
| W1 | 1.162 | da domenica, come il fornitore |

- Ogni barra è etichettata con l'orario di **apertura** e sarà usata solo dopo la sua **chiusura**, per evitare lookahead.
- Non ci sono barre sintetiche nei vuoti.

## 7. Divisione dei dati (`configs/config.yaml`)

- **Addestramento:** 2005–2017.
- **Validazione:** 2018–2021.
- **Test:** 2022 → 2026-10-09, **bloccato** fino alla Fase 9.
- **Dichiarazione onesta:** il 2022–2026 è già stato esaminato nel lavoro precedente su questo stesso repository (strategie ICT, Wyckoff, trend, OCO). Non lo userò per scegliere nulla, ma non è più un dato "mai visto". La prova davvero pulita sarà il **forward su demo**, più i mesi che arriveranno dopo il 9 ottobre 2026.

## 8. Decisioni che ti chiedo

1. **Da quando partire con l'addestramento.**
   - Nel 2005–2006 circa il 60% dei minuti non ha scambi registrati e più di metà dei giorni sono degradati. Sui timeframe M3–M15 delle celle questo produce swing, FVG e sweep falsi o mancanti: con la serie a buchi, i segnali di quegli anni non sono affidabili.
   - **La mia proposta:** addestrare sul **2008–2017** (10 anni, copertura 89–98%) e usare 2005–2007 solo per il contesto H4, D1 e W1.
   - In alternativa si resta sul 2005–2017 come da specifica, escludendo solo i giorni degradati.
2. **Spread del 2005–2017:** confermi gli scenari fissi in dollari (C1 e C2)? Oppure, se conosci lo spread tipico del tuo broker sul conto che userai (PU Prime, Vantage o Fusion; standard o raw più commissione), lo uso come C1.

## 9. Cosa manca ancora per le fasi successive

- **Fase 1:**
  - le 4 pagine guida del sito e la seconda app (Lovable);
  - altre foto o video dei backtest con le operazioni leggibili, se ne hai;
  - la tua replica precedente (`ea/*.mq5`), se esiste.
- **Fase 6:** lo storico del calendario economico. Ti preparerò lo script MQL5 per esportarlo.

**Fine Fase 0. Attendo il tuo ok (e le due decisioni del punto 8) per passare alla Fase 1.**
