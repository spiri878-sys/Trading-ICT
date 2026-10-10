# Raptor Recon: ricerca ICT/SMC per XAUUSD (MT5)

Ricostruzione **indipendente** del comportamento pubblicamente descritto di *ICT RAPTOR AI PRIME* (AutoTrader Forex Club), solo per **XAUUSD**. Non è affiliata al prodotto commerciale e non ne è una copia: il suo codice e i suoi modelli non sono disponibili.

> **Profilo migliore trovato: C, Unicorn LONG (M15, stop H4, TP 3R / 48h).** Con rischio 1%: +58% nel 2018–2026 (PF 1,32, DD 15%) e +26% nel walk-forward 2022–2026. Robusto ai costi, ma dipende dal trend rialzista dell'oro: gli short perdono sempre. Preset `RaptorRecon_C_unicorn_long_risk1pct.set`.
>
> **Esito della ricerca** (`reports/FINAL_REPORT.md`): nessuna strategia testata (6 strategie del sito + PPK, combinazioni, profilo sperimentale, filtro AI, benchmark Wyckoff) mostra un vantaggio statistico robusto dopo i costi su XAUUSD M1 2018–2026. L'EA MQL5 non è stato compilato né testato in MT5. **Usare solo su conto demo.**

## Struttura

| Percorso | Contenuto |
|---|---|
| `mql5/Experts/RaptorRecon/RaptorRecon.mq5` | EA (profili A fedele, B sperimentale, W Wyckoff) |
| `mql5/Include/RaptorRecon/` | Moduli: `MarketModel` (struttura / FVG / liquidità / HTF), `Cells`, `Risk` (selettori stop e lotto, protezioni), `PositionManager`, `Logger`, `Telegram`, `Defines` |
| `mql5/Presets/` | Preset `.set` che riproducono i profili della ricerca |
| `python/raptor/` | Dati, feature causali, celle, simulatore M1, costi, metriche, ML, confronto EA ↔ Python |
| `python/scripts/` | Audit dei dati, esperimenti EXP-01..10, VAL-01, benchmark, report |
| `tests/` | 49 test pytest (motore, selettori, causalità, celle, confronto, controllo statico MQL5) |
| `tools/` | `mql5_static_check.py`, `unrar_multi.py` (estrazione RAR5 multivolume) |
| `data/manifest/` | Manifest e hash del dataset. I dati grezzi non sono versionati |
| `experiments/`, `reports/` | Tutti i risultati, inclusi i negativi |
| `models/` | Filtro LightGBM + ONNX (ricerca, **non usato** dall'EA) |
| `docs/` | `evidence_register`, `strategies` (con la matrice delle funzionalità), `data_and_costs`, `stop_and_lot`, `mt5_guide`, `limits` |

## Riprodurre

```bash
pip install pandas numpy numba pyarrow lightgbm scikit-learn onnxmltools onnxruntime pytest
# dati: estrai i due volumi RAR in data/raw/XAUUSD_M1.csv
python tools/unrar_multi.py <outdir> barre_xauusd_m1_2017.part1.rar barre_xauusd_m1_2017.part2.rar
python python/scripts/data_audit.py          # verifica + manifest + cache parquet
python -m pytest tests                        # 49 test
python python/scripts/research_report.py     # metriche per cella / costo / periodo
python python/scripts/benchmark_final.py     # ICT contro Wyckoff, profilo di riferimento
python python/scripts/ai_comparison.py       # AI contro casuale + parità ONNX
```

Per MT5 (installazione, compilazione, Strategy Tester, confronto trade per trade) vedi `docs/mt5_guide.md`.
