# XauOcoBreakout: breakout OCO (buy stop + sell stop) su XAUUSD, report

**Stato:** simulazione Python su barre M1 2018-01 → 2026-10, con costi completi: spread 0,30 $, commissione 7 $ per lotto andata e ritorno, slippage 0,05 $, swap. Leva 1:100. L'EA (`mql5/Experts/XauOcoBreakout/XauOcoBreakout.mq5`) **non è stato compilato né testato in MT5**.

## Idea dell'utente

- Un buy stop sopra e un sell stop sotto un range.
- Quando uno si attiva, l'altro viene cancellato (OCO).
- Una sola operazione alla volta.
- Trailing che segue il prezzo, più lo stop loss.
- Ordini riposizionati dopo ogni trade.

## Ricerca (`python/scripts/oco01..04`)

| Passo | Risultato |
|---|---|
| OCO-01: 288 varianti, range {asiatico, PDH/PDL, mobile H1 N = 6/12/24, mobile compresso} × stop {lato opposto, 1 ATR, 2 ATR} × trailing {1, 2, 3 ATR} × TP {nessuno, 2R} × durata {24, 48 h}, entrambi i lati | Solo il **22,6%** è positivo; migliore t = 1,75. I buy stop guadagnano (+0,09R), i **sell stop perdono** |
| OCO-02: filtro di regime (D1 vs EMA50 e struttura H4): buy stop solo in regime rialzista, sell stop solo in regime ribassista | **48%** positive, migliore t = 3,3 (R per trade +0,078, PF 1,43, 660 trade) |
| OCO-02: walk-forward annidato (scelta annuale usando solo il passato) | **OOS 2020–2026: +0,038R/trade, t 3,24.** Annuale (somma R): −22 / +5,5 / −9 / 0 / +39,7 / +39,2 / +17,6. Dal 2021 sceglie sempre la configurazione finale |

### Configurazione finale ("perfezionata")

- **Range:** ogni ora, massimo e minimo delle ultime 24 barre H1, solo se compresso: altezza ≤ 1 × ATR14(H1) × √24, e fra 0,5 e 8 ATR.
- **Ordini:**
  - buy stop al massimo + 0,1 ATR, solo in regime rialzista;
  - sell stop al minimo − 0,1 ATR, solo in regime ribassista;
  - nessun ordine in regime misto.
- **Stop loss:** sul lato opposto del range.
- **Gestione:** TP a 2R, trailing a 2 ATR(H1) sulle chiusure M1, durata massima 24 h, chiusura il venerdì alle 23:00.
- **Ciclo degli ordini:** validi un'ora (poi vengono rinnovati); il riempimento di uno cancella l'altro; dopo la chiusura del trade la coppia viene riposizionata.

## Test richiesto: 1000 iniziali, lotto fisso 0,10, mese per mese (USD)

| Anno | Gen | Feb | Mar | Apr | Mag | Giu | Lug | Ago | Set | Ott | Nov | Dic | **Anno** | Saldo fine anno |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2018 | +113 | -128 | +121 | -203 | -96 | +91 | +138 | +115 | -78 | -46 | -84 | -132 | **-189** | 811 |
| 2019 | +7 | +18 | -107 | +44 | -19 | +508 | +108 | -76 | +56 | +124 | -105 | -69 | **+489** | 1,300 |
| 2020 | +336 | -147 | -634 | +825 | -44 | +73 | +526 | +607 | +82 | -274 | +666 | +125 | **+2141** | 3,441 |
| 2021 | +330 | +544 | -78 | -33 | +494 | -100 | -152 | -287 | +10 | +152 | +237 | -376 | **+741** | 4,182 |
| 2022 | -32 | +198 | -242 | -119 | +10 | -190 | +142 | -71 | -63 | +74 | -40 | +45 | **-288** | 3,894 |
| 2023 | +91 | -374 | +499 | 0 | +356 | -81 | -125 | -422 | -16 | +270 | +289 | +89 | **+576** | 4,470 |
| 2024 | -107 | -67 | +59 | +351 | +533 | +190 | +568 | +190 | +25 | +149 | +667 | +261 | **+2819** | 7,289 |
| 2025 | +485 | +836 | -129 | -112 | +972 | +94 | +324 | -726 | +1096 | +988 | +520 | +1594 | **+5942** | 13,231 |
| 2026 | +2399 | -1160 | +1519 | -158 | +623 | +364 | -473 | -188 | +964 | +11 | – | – | **+3901** | 17,132 |

Riepilogo:

- **Saldo finale:** circa 17.126.
- **DD massimo:** 55%, calcolato su equity, inclusa la perdita aperta peggiore.
- **Profit factor:** 1,59.
- **Trade:** 662 (≈ 6 al mese), 42,6% vincenti.
- **Mesi positivi:** 59%.
- **Rischio per trade:** medio circa 10% del conto, **massimo 71%**.
- **Short:** 238 trade, +1846 $. Con lotto fisso guadagnano; con rischio in percentuale sono quasi in pareggio.

**Perché i guadagni crescono così tanto nel 2024–2026:** con lotto fisso il guadagno in dollari è proporzionale al movimento del prezzo in dollari. L'oro è passato da 2000 a 4000–5000 $ e la volatilità in dollari è triplicata. Una parte della "esplosione" è quindi l'aumento dei movimenti del prezzo, non un miglioramento della strategia.

## Rischio di perdere il conto: "se fossi partito in un mese qualsiasi" (94 partenze, 12 mesi, 1000 nuovi)

| Lotto fisso | 2018 → 2026 | DD max | Dopo 12 mesi in utile | Mediana dopo 12 mesi | Partenze che hanno visto il conto sotto 500 | Peggiore |
|---|---|---|---|---|---|---|
| 0,02 | 4.225 | 17% | 80% | 1.168 | **0%** | 842 |
| 0,05 | 9.063 | 35% | 80% | 1.420 | 1% | 604 |
| **0,10** (richiesto) | 17.126 | **55%** | 75% | 1.624 | **28%** | **182** (partenza giugno 2023) |

**Idea originale senza filtro (entrambi i lati sempre), 1000 e lotto 0,10:** partendo nel 2018 arriva a **112 (−89%)**, e dopo i trade sono bloccati per margine insufficiente. Partendo nel 2021 arriva a 16.244, ma con DD 86%. È troppo dipendente dal punto di partenza.

## Limiti

- **Simulazione su barre M1 OHLC**, non a tick. Se buy stop e sell stop si attivano nella stessa candela M1 si contabilizza l'esito peggiore.
- **Leva:** con leva retail UE sull'oro (1:20) il lotto 0,10 su 1000 € non può essere aperto: servono circa 2000 $ di margine.
- **Valuta:** 1000 € sono circa 1150–1170 $. I risultati sono in dollari.
- **Fattori fuori controllo:** il vantaggio principale viene dai breakout rialzisti dell'oro nel 2024–2026, e il rendimento con lotto fisso dipende dall'aumento della volatilità in dollari.

## Preset (`mql5/Presets/`)

| Preset | Contenuto |
|---|---|
| `XauOcoBreakout_USER_1000_FIXED010.set` | Il test richiesto (aggressivo) |
| `XauOcoBreakout_1000_FIXED002_PRUDENT.set` | Lotto 0,02 con limiti di perdita |
| `XauOcoBreakout_DEMO_PRUDENT.set` | Lotto 0,01 per la prima prova demo |
| `XauOcoBreakout_ORIGINAL_BOTH_FIXED010.set` | Idea originale, solo per confronto |
