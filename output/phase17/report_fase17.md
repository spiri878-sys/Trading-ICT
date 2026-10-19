# Fase 17 — bot a pendenti (XauOcoBreakout perfezionato) su conto da 116 $ a 0,01 lotti

Costi A: spread 0,09 + commissione 0,04 $ per 0,01 lotti + slippage 0,02. B: commissione per lato + slippage 0,10.
Partenza 116 $ in ciascun periodo. Dati fino al 30/01/2026. Script `python/scripts/phase17_oco_100eur.py`.

| variante | periodo | trade | finale $ | calo max | PF | vinti | mesi + | rischio medio | rischio max |
|---|---|---|---|---|---|---|---|---|---|
| costiA_stopmaxnessuno | sviluppo_2018_2021 | 297 | 540.7 | 29.0% | 1.61 | 43.1% | 51.0% | 5.5% | 30.6% |
| costiA_stopmaxnessuno | verifica_2022_2026 | 297 | 1222.0 | 50.4% | 2.1 | 43.4% | 66.7% | 12.2% | 40.2% |
| costiA_stopmax30.0 | sviluppo_2018_2021 | 286 | 513.6 | 29.0% | 1.62 | 42.3% | 51.0% | 5.1% | 12.1% |
| costiA_stopmax30.0 | verifica_2022_2026 | 243 | 554.1 | 52.6% | 1.63 | 42.0% | 62.8% | 13.9% | 41.7% |
| costiA_stopmax20.0 | sviluppo_2018_2021 | 245 | 435.6 | 29.0% | 1.63 | 41.2% | 55.1% | 5.2% | 10.8% |
| costiA_stopmax20.0 | verifica_2022_2026 | 91 | 0.7 | 99.5% | 0.61 | 29.7% | 27.8% | 26.6% | 166.1% |
| costiA_stopmax15.0 | sviluppo_2018_2021 | 193 | 260.6 | 29.0% | 1.4 | 39.9% | 50.0% | 5.9% | 10.8% |
| costiA_stopmax15.0 | verifica_2022_2026 | 81 | 27.7 | 98.5% | 0.59 | 28.4% | 16.7% | 34.4% | 315.0% |
| costiA_stopmax10.0 | sviluppo_2018_2021 | 108 | 179.3 | 21.9% | 1.4 | 40.7% | 60.0% | 4.8% | 7.9% |
| costiA_stopmax10.0 | verifica_2022_2026 | 7 | 97.9 | 21.1% | 0.3 | 28.6% | 0.0% | 8.5% | 9.5% |
| costiB_stopmaxnessuno | sviluppo_2018_2021 | 297 | 489.1 | 34.5% | 1.51 | 42.1% | 51.0% | 6.0% | 35.3% |
| costiB_stopmaxnessuno | verifica_2022_2026 | 297 | 1166.8 | 61.6% | 2.01 | 43.1% | 64.6% | 14.0% | 45.1% |
| costiB_stopmax30.0 | sviluppo_2018_2021 | 286 | 464.0 | 34.5% | 1.51 | 41.3% | 51.0% | 5.6% | 13.9% |
| costiB_stopmax30.0 | verifica_2022_2026 | 243 | 509.0 | 64.6% | 1.54 | 41.6% | 60.5% | 16.3% | 50.7% |
| costiB_stopmax20.0 | sviluppo_2018_2021 | 245 | 393.2 | 34.5% | 1.52 | 40.4% | 55.1% | 5.7% | 10.9% |
| costiB_stopmax20.0 | verifica_2022_2026 | 89 | -3.3 | 102.7% | 0.6 | 29.2% | 27.8% | 40.0% | 423.2% |
| costiB_stopmax15.0 | sviluppo_2018_2021 | 193 | 226.8 | 36.5% | 1.28 | 38.9% | 50.0% | 6.6% | 12.1% |
| costiB_stopmax15.0 | verifica_2022_2026 | 65 | -1.1 | 103.9% | 0.37 | 27.7% | 11.1% | 40.5% | 371.0% |
| costiB_stopmax10.0 | sviluppo_2018_2021 | 108 | 160.0 | 25.2% | 1.26 | 39.8% | 56.0% | 5.2% | 8.0% |
| costiB_stopmax10.0 | verifica_2022_2026 | 7 | 96.5 | 22.2% | 0.27 | 28.6% | 0.0% | 8.6% | 9.7% |

## Conclusione
- Senza filtro: positiva in entrambi i periodi anche con costi B (116 -> 489-541 nel 2018-21, 116 -> 1.167-1.222 nel 2022-26).
- Prezzo: rischio medio per trade 12-14% del conto nel 2022-26 (fino al 40-45%), calo massimo 50-62%.
- Il filtro 'stop massimo in $' NON aiuta: con l'oro a 2.000-5.000 $ i range piccoli sono rari e peggiori (20 $ e 15 $: conto quasi azzerato nel 2022-26).
- La configurazione era già stata scelta in walk-forward (OCO-02, dal 2021 sempre la stessa): 2022-26 è fuori campione per la scelta, ma non per l'idea.
- Simulazione su barre M1 senza tick: lo slippage reale sugli ordini stop può essere maggiore. Preset: mql5/Presets/XauOcoBreakout_100EUR_FIXED001.set (prima in demo).
