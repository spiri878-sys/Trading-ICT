# XAUUSD: ricerca quantitativa ed EA "XauTrendRegime": rapporto finale

**Data:** 11/10/2026. **Dati:** barre M1 XAUUSD dal 2018-01-02 al 2026-10-09.

Questo rapporto distingue sempre quattro tipi di risultato:

1. simulazione teorica;
2. simulazione con costi;
3. Strategy Tester MT5;
4. forward su conto demo.

**Qui esistono solo i risultati 1 e 2.** Nessun test MT5 o demo è stato eseguito: l'ambiente non ha MetaTrader.

## In sintesi

- **Strategia selezionata: TREND-REGIME LONG.**
  - Ingresso: breakout del massimo delle 55 barre H4.
  - Filtro di regime: D1 sopra la EMA50 e struttura H4 rialzista.
  - Stop 3 ATR14(H4), trailing 3 ATR, durata massima 5 giorni di trading.
- **Al netto di spread, commissioni, slippage e swap**, con rischio 1% e capitale 10.000:
  - **+42,2%** sul periodo 2018 → ottobre 2026: PF 2,08, DD massimo 7,0% (equity peggiore dentro i trade), 139 trade;
  - **+23,0%** nel 2022–2026: PF 2,29, DD 2,7%.
- **Batte ingressi long casuali** con la stessa uscita: +0,341R contro +0,158R (p < 0,005). Il vantaggio non è solo la salita dell'oro.
- **Lo SHORT non ha vantaggio.** Lo specchio della strategia perde in 36 varianti su 36, e nessuna famiglia testata (8 famiglie, centinaia di varianti) ha uno short positivo e robusto. L'EA supporta gli short, ma li tiene **spenti** di default.
- **Rischi residui:**
  - dipende dai trend rialzisti dell'oro: 2018, 2021 e 2022 sono stati negativi;
  - i 5 trade migliori valgono il 54% del profitto;
  - circa 1,3 trade al mese.

## 1. Analisi dei dati storici (Fase A–B)

- **Dataset** (`data/manifest/XAUUSD_M1.manifest.json`, `docs/data_and_costs.md`):
  - 3.086.760 barre M1, prezzi BID in ora server (= New York + 7 h);
  - nessun duplicato né OHLC incoerente;
  - pausa giornaliera 23:55–01:01;
  - colonne disponibili: tick volume e spread; il volume reale è sempre 0.
- **Spread**:
  - 2018–2022: probabilmente in millesimi (sempre multipli di 10 e maggiori del range M1 nel 92% delle barre);
  - dal 2023 i valori sono quasi nulli;
  - per questo i costi sono modellati come scenari dichiarati (`reports/spread_diagnosis.json`).
- **Studio di mercato** (`reports/market_study.json`):
  - deriva rialzista: +5,1 bp al giorno, 53,8% di giorni positivi;
  - rendimenti annui: −2,7 / +18,5 / +23,9 / −6,0 / +1,3 / +12,2 / +27,5 / +62,8 / −3,2% (2018–2026);
  - code grasse: curtosi in eccesso 6 su D1 e 52 su M5; asimmetria negativa;
  - volatilità massima nella sessione NY mattina (6,1 bp per M5, contro circa 3,3 nelle altre sessioni);
  - H1 leggermente mean-reverting (variance ratio 0,98); H4 leggermente persistente (VR8 1,07);
  - dopo un breakout rialzista H1 il prezzo a 24 h sale di +0,39 ATR, contro +0,27 non condizionato;
  - **dopo un breakout ribassista non c'è prosecuzione** (−0,03);
  - il raid del minimo del giorno precedente si inverte (+0,07 ATR), il raid del massimo no.

## 2. Descrizione matematica della strategia selezionata

Notazione:

- barre H4 chiuse $t$, con $H_t, L_t, C_t$;
- $A_t$ = ATR di Wilder a 14 periodi su H4;
- $D_t$ = ultima chiusura D1 completata al tempo della decisione;
- $E^{50}_t$ = EMA50 delle chiusure D1;
- $S_t \in \{+1, -1\}$ = direzione dell'ultima rottura di struttura H4 (swing frattali con k = 2, rottura = chiusura oltre l'ultimo swing confermato e non ancora rotto).

**Ingresso LONG** all'apertura della prima barra M1 dopo la chiusura di $t$, se:

$$C_t > \max_{t-55 \le j < t} H_j \;\wedge\; C_{t-1} \le \max_{t-55 \le j < t} H_j \;\wedge\; D_t > E^{50}_t \;\wedge\; S_t = +1$$

**Stop iniziale:**

$$SL = C_t - 3A_t$$

**Trailing** su ogni barra M1 chiusa $i$ (bid):

$$SL \leftarrow \max\left(SL,\; C^{M1}_i - 3A_t\right)$$

Lo stop non si allarga mai.

**Uscite:** stop o trailing, oppure chiusura dopo 7200 barre M1 (circa 5 giorni di trading). Nessun take profit. Le posizioni restano aperte nel weekend, con swap addebitato.

**Lotto**, in modalità rischio:

$$lot = \left\lfloor \frac{base \times r\%}{\left|\text{profitto}(entry \rightarrow SL - slip)\right| + 2 \times comm} \right\rfloor_{step}$$

Se il risultato è sotto il lotto minimo, il trade viene saltato. In modalità FIXED il lotto non viene mai modificato.

**SHORT:** lo specchio esatto ($C_t < \min L$, $D_t < E^{50}$, $S_t = -1$) è disponibile ma disattivato.

## 3. Confronto fra le strategie testate

Valori in R per segnale isolato, costi C1 + swap; `experiments/fam01_stats.csv` e i report dei giri precedenti.

| Famiglia | Varianti | Long: quota > 0 | Long: R mediano | Short: quota > 0 | Short: R mediano |
|---|---|---|---|---|---|
| **Donchian / trend (H1, H4)** | 48 | **79%** | +0,030 | 0% | −0,054 |
| Squeeze di volatilità (M15, H1, H4) | 48 | 40% | −0,034 | 0% | −0,113 |
| RSI2 mean reversion (H1, H4) | 32 | 28% | −0,033 | 0% | −0,111 |
| Mean reversion Bollinger + regime laterale | 40 | 22% | −0,056 | 2% | −0,160 |
| Breakout del range asiatico (M15) | 24 | 17% | −0,045 | 0% | −0,105 |
| Pullback EMA in trend MTF (M15, H1) | 32 | 16% | −0,063 | 0% | −0,103 |
| ICT Unicorn (M15, stop H4) | 4 | 75% | +0,046 | 0% | −0,119 |
| ICT Liquidity Sweep | 4 | 0% | −0,220 | 0% | −0,269 |
| ICT (7 celle, 1° giro), Wyckoff semplice e MTF, filtro AI | centinaia | ≈ 0 o negativo fuori campione | | negativo | |

**Short in regime ribassista** (FAM-02): solo il 7,7% delle 222 configurazioni è positivo, mediana −0,097R.

**Semplice contro complessa:** il Donchian senza filtro rende +0,296R per trade (portafoglio +31%, DD 10%); con il filtro di regime +0,341R (+42%, DD 7%). Il filtro è stato tenuto perché migliora rendimento **e** rischio, ed è stato scelto in modo stabile dal walk-forward.

## 4. Risultati in-sample, out-of-sample e walk-forward

- **Periodi fissati:** dev 2018–2021, val 2022–2023, test 2024 → 09/10/2026. Questi periodi erano già stati usati nei giri di ricerca precedenti. Per questo la prova principale è il **walk-forward annidato**, che non dipende dalla divisione fissa.
- **Walk-forward annidato** (FAM-03): ogni anno sceglie, usando solo il passato, le 3 configurazioni migliori per lato (con t ≥ 2) fra 8 famiglie × filtro regime.

| Lato | Trade fuori campione | R medio | t | PF | Somma R per anno |
|---|---|---|---|---|---|
| Long | 1068 | **+0,063** | 2,12 | 1,18 | 2021: −20,0 · 2022: −41,4 · 2023: +11,2 · 2024: +48,1 · 2025: +26,9 · 2026: +42,3 |
| Short | 97 | −0,126 | −1,74 | 0,65 | quasi sempre nessuna configurazione idonea |

- **Convergenza:** dal 2021 la procedura sceglie quasi ogni anno Donchian H4-55 con regime, cioè la strategia selezionata.
- **Strategia selezionata per periodo** (R isolata, costi C1 + swap):

| Periodo | n | R medio | t |
|---|---|---|---|
| Dev | 206 | +0,503 | 4,4 |
| Val | 84 | +0,142 | 1,0 |
| Test | 266 | +0,278 | 4,0 |
| Tutto | 556 | +0,341 | 5,9 |

  R medio per anno: −0,18 / +0,83 / +0,93 / −0,29 / −0,19 / +0,39 / +0,28 / +0,23 / +0,45.

**Portafoglio** (rischio 1%, 1 posizione, capitale 10.000, costi C1 + swap; `reports/final_candidate.json`):

| Metrica | 2018 → ott. 2026 | 2022 → ott. 2026 |
|---|---|---|
| Capitale finale | 14.218 | 12.298 |
| Profitto netto | +4218 (+42,2%) | +2298 (+23,0%) |
| Profit factor | 2,08 | 2,29 |
| Trade (al mese) | 139 (1,32) | 81 (1,41) |
| Vincenti | 47,5% | 49,4% |
| Rapporto medio vincita / perdita | 2,30 | 2,35 |
| Aspettativa | +0,286R | +0,296R |
| DD massimo (equity dentro i trade) | 823 $ (7,0%) | 274 $ (2,7%) |
| Recovery factor | 5,1 | 8,4 |
| Serie massima di perdite | 7 | 4 |
| Mesi positivi | 59% | 63% |
| Esposizione | 17% del tempo | 19% |
| Sharpe mensile annualizzato | 0,92 | — |

Netto per anno: −21 / +292 / +1434 / −521 / −91 / +517 / +976 / +898 / +734 $.

## 5. Robustezza e rischi residui

| Test | Esito |
|---|---|
| Sensibilità: N {40, 55, 70} × stop/trailing {2, 2,5, 3, 3,5} × durata {3, 5, 10 g} | **36/36 positive** (da +0,17 a +0,34R) |
| Costi ×2 (spread 0,60, commissione 7 $/lato, slippage 0,10) | +0,318R; portafoglio +33,4%, PF 1,87 |
| Contro ingressi long casuali con la stessa uscita (200 estrazioni) | +0,341 contro +0,158 (p95 0,230, p99 0,262), **p < 0,005** |
| Monte Carlo a blocchi da 10 trade (5000 percorsi, 139 trade, rischio 1%) | Rendimento p5 / p50 / p95: +17,8 / +44,7 / +80,6%. DD p50 / p95 / p99: 5,1 / 9,3 / 12,2%. P(perdita) 0,1% |
| Concentrazione | I 5 trade migliori valgono il **54%** del netto |
| Lato short (specchio) | Negativo in tutte le 36 varianti e con costi ×2 |
| Parità EA ↔ ricerca (11.966 barre H4) | 0 differenze su segnale, regime D1 e trend H4; ATR entro l'1% |

**Rischi principali:**

1. Dipende da un mercato dell'oro con trend rialzisti. In fasi laterali o ribassiste prolungate perde: 2021 −5,2%, 2022 −0,9%, 2018 −0,2%.
2. Nessun dato prima del 2018. Il regime 2013–2015 (oro in calo) non è nel campione.
3. Lo swap usa i valori del 2026 (circa −6,6% annuo sui long), ricavati dagli screenshot; prima del 2022 i tassi erano più bassi, quindi lo stimato è probabilmente prudente.
4. Il campione di parametri e famiglie esplorati è ampio (rischio di selezione). Lo mitigano il walk-forward, la sensibilità e il confronto con il caso, ma non lo eliminano.

## 6–10. Codice, file e configurazioni

| Elemento | File |
|---|---|
| EA | `mql5/Experts/XauTrendRegime/XauTrendRegime.mq5` |
| Moduli condivisi | `mql5/Include/RaptorRecon/` (Logger, MarketModel, Risk, Defines) |
| Preset: rischio 1% (default validato) | `mql5/Presets/XauTrendRegime_RISK_PERCENT_1pct.set` |
| Preset: lotto fisso 0,01 | `mql5/Presets/XauTrendRegime_FIXED_LOT_001.set` |
| Preset: **demo prudente** | `mql5/Presets/XauTrendRegime_DEMO_PRUDENT.set` |
| Preset: parità con la ricerca | `mql5/Presets/XauTrendRegime_RESEARCH_PARITY.set` |
| Guida input, installazione, checklist | `docs/xau_trend_regime_guide.md` |
| Ricerca riproducibile | `python/scripts/market_study.py`, `fam01_compare.py`, `fam02_regime_shorts.py`, `fam03_walkforward.py`, `final_candidate.py`, `final_candidate_vs_random.py`, `ea_parity_trend_regime.py` |

Il preset demo prudente usa:

- rischio 0,5%;
- tetto per trade 1%;
- rischio aggregato massimo 1%;
- perdita giornaliera massima 1,5%;
- drawdown massimo 10%;
- short spenti.

## 13. Test eseguiti e test da eseguire

| Test | Stato |
|---|---|
| Audit dati, studio di mercato | ✅ eseguito |
| Backtest comparativi Python con costi e swap | ✅ eseguito (simulazione M1 OHLC, ordine intrabar conservativo) |
| Walk-forward annidato, sensibilità, costi ×2, Monte Carlo, controllo casuale | ✅ eseguito |
| Test automatici (pytest) | ✅ 66/66 |
| Controllo statico MQL5 | ✅ superato (non è una compilazione) |
| Parità della logica di decisione EA ↔ Python | ✅ 0 differenze (simulata in Python con le finestre dell'EA) |
| **Compilazione in MetaEditor** | ❌ da eseguire (MetaEditor non disponibile) |
| **Strategy Tester MT5 "Every tick based on real ticks"** | ❌ da eseguire |
| Confronto trade per trade tester ↔ Python (`compare_ea_vs_python.py`) | ❌ servono i log del tester |
| Forward su conto demo (almeno 3 mesi) | ❌ da eseguire |
| Conto reale | ❌ sconsigliato prima dei punti precedenti |
