# Fase 16 — scalping M1 sull'oro con i costi del broker dell'utente

Costi dichiarati dall'utente: spread fisso 9 punti (0,09 $) e commissione 0,04 $ per 0,01 lotti.
Scenario A = 0,09 + 0,04 + 0,02 slippage = 0,15 $ a trade; B prudente = 0,27 $ (commissione per lato, slippage 0,10).
Dati: XAU_1m_data.csv (2010 -> 30/01/2026), sviluppo 2010-15, verifica 2016-01/2026. Un trade alla volta, stop e target
sempre presenti, nessuna griglia o martingala. Script: `python/scripts/phase16_m1_user_costs.py` (e `--larghi`).

## Risultato
- Griglia base (9 famiglie x 12 uscite, stop 1-2 ATR M1 ≈ 0,9-1,5 $): **0 su 108** positive in entrambi i periodi.
- Prova aggiuntiva stop larghi (4-8 ATR M1 ≈ 3,5-4 $, solo famiglie contro-movimento): **0 su 60** (A e B).
- Le famiglie contro-movimento (IMP_R, BB_R, BRK_R) hanno un vantaggio LORDO di +0,08/+0,11 R con stop di circa 1 $,
  cioè 0,08-0,11 $ a trade: meno del costo minimo (0,15 $). Con stop più larghi il vantaggio lordo scende verso 0
  (+0,01/+0,03 R): è rumore di brevissimo periodo, non un vantaggio sfruttabile.
- Conclusione: anche con costi bassi (0,15 $) nessun bot M1 sull'oro risulta profittevole su questi dati.
