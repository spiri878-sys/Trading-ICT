# Selettori di stop e lotto: formule, unità, combinazioni

I due selettori sono **indipendenti**:

- **Stop**: `InpStopMode` (EA) e `Params.stop_mode` (Python).
- **Lotto**: `InpLotMode` (EA) e `Params.lot_mode` (Python).

La modalità scelta e la formula applicata vengono scritte in ogni riga di `<prefix>_signals.csv` (colonne `stop_mode`, `lot_mode`, `detail`).

## Stop

| Modalità | Formula (side = +1 long, −1 short) | Unità e base | Note |
|---|---|---|---|
| **FIXED** (obbligatoria) | `sl = entry − side × dist` | `dist` in **prezzo** (USD per oncia). XAUUSD a 2 decimali: 1,00 = 100 punti = 100 tick da 0,01 | Default 5,0 |
| **PERCENT** (obbligatoria) | `sl = entry × (1 − side × pct / 100)` | Percentuale del **prezzo di ingresso**, **non** del capitale | Default 0,25% (≈ $10 con l'oro a 4000) |
| STRUCTURAL (aggiuntiva, default) | Livello di invalidazione del setup ± 0,2 ATR | Prezzo | Opzionale `InpMinStopAtrM15` (E-12) |
| ATR (aggiuntiva) | `sl = entry − side × mult × ATR14(TF segnale)` | Prezzo | |

Per tutte le modalità valgono queste regole:

- **Prezzo di riferimento**:
  - ordine limit: il prezzo limite;
  - ordine a mercato: ASK per il long, BID per lo short;
  - nel simulatore: il prezzo di esecuzione effettivo.
- **Vincoli del broker**: se `|entry − sl|` < `SYMBOL_TRADE_STOPS_LEVEL × point`, il trade viene **rifiutato** (`rejected_stop_invalid`). Lo stop **non** viene mai allargato in silenzio.
- **Valori non validi** (≤ 0): `OnInit` restituisce `INIT_PARAMETERS_INCORRECT`.
- **Freeze level**: il break-even viene tentato e, se il broker lo rifiuta, l'errore va nel journal degli eventi.

## Lotto

| Modalità | Formula | Rifiuti |
|---|---|---|
| **FIXED** | `lot = InpFixedLot` (default **0,08**) | Fuori da min/max/step → `rejected_lot`; margine insufficiente → `rejected_margin`. **Mai ridotto** |
| **RISK_PERCENT** | `rischio = base × pct / 100 × moltiplicatore_respiro`, con `base` = BALANCE o EQUITY (`InpRiskBase`). `perdita_per_lotto = |OrderCalcProfit(entry → sl − side × slippage)| + 2 × commissione`. `lot = floor(rischio / perdita_per_lotto / step) × step` | Se `lot` < volume minimo → `rejected_lot`: **mai arrotondato per eccesso** |

- `OrderCalcProfit` usa tick size, tick value e la valuta del conto del broker, quindi è corretto anche per conti in EUR.
- **Tetto opzionale** `InpMaxRiskPctTrade` (default 2%): vale anche per il lotto fisso. Se il rischio stimato lo supera, il trade viene rifiutato.
- **Rischio effettivo**: può superare quello stimato per gap, slippage oltre la stima o commissioni diverse.

## Combinazioni verificate (`reports/stop_lot_combinations.csv`)

Set: le sei strategie del sito, M5, gestione a scala, costi C1, periodi dev e val.

| Capitale | Stop | Lotto | Rischio medio $ | Rischio medio % | Rischio max % | Osservazione |
|---|---|---|---|---|---|---|
| 1000 | FIXED $5 | FIXED 0,08 | 40,96 | 8–9% | 43% | Rischio insostenibile su 1000 |
| 1000 | FIXED $5 | RISK 1% | 5,12 | 0,7% | 1,00% | Fino a 2516 rifiuti per lotto minimo |
| 1000 | PERCENT 0,25% | FIXED 0,08 | 27,6–38,8 | 5,6–7,6% | 26% | |
| 1000 | PERCENT 0,25% | RISK 1% | 4,3–5,0 | 0,7% | 1,00% | |
| 10.000 | FIXED $5 | FIXED 0,08 | 40,96 | 0,7% | 1,3% | |
| 10.000 | FIXED $5 | RISK 1% | 37,7–45,5 | 0,92% | 1,00% | |
| 10.000 | PERCENT 0,25% | FIXED 0,08 | 32,8–38,2 | 0,6–1,5% | 7,4% (dopo il drawdown) | |
| 10.000 | PERCENT 0,25% | RISK 1% | 20,3–48,7 | 0,8–0,9% | 1,00% | |

Tutte le combinazioni hanno aspettativa negativa: è un effetto della strategia, non dei selettori. I test `test_all_stop_lot_combinations_run` (8 combinazioni) e `test_stop_selector` verificano le formule.

## Larghezza dello stop: lotto fisso contro rischio % (`reports/stop_width_vs_lot.csv`, dev, capitale 10.000)

| Stop minimo (ATR M15) | Stop mediano $ | Rischio medio $ con lotto 0,08 | Rischio medio $ con 1% | Aspettativa R |
|---|---|---|---|---|
| 0 | 1,32 | 15,7 | 20,7 | −0,33 / −0,48 |
| 2 | 3,06 | 32,3 | 19,9 | −0,18 / −0,17 |
| 3 | 4,82 | 48,4 | 31,1 | −0,13 / −0,13 |
| 4 | 6,37 | 64,3 | 53,6 | −0,07 / −0,07 |

Con il lotto fisso il rischio monetario cresce in proporzione alla distanza dello stop. Stop più larghi riducono il costo per R, ma l'aspettativa resta negativa.
