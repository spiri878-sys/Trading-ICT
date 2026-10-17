# Mercati: verifica 2022-2026 (mai vista in addestramento)

Modello scelto sugli anni 2019-2021. Calibrazione dell'anno Y stimata solo sugli anni prima di Y. 'media' = frequenza dell'evento nello stesso campionato nei 3 anni prima. Stagioni = quota di stagioni con Brier migliore della media. Fascia 70% = quando dice >= 70%: previsto / uscito.

- **angoli**: modello LightGBM, dispersione casa 1.40 / ospite 1.38
- **gol**: modello LightGBM + mercato, dispersione casa 0.94 / ospite 0.96, rho -0.04
- **gol 1° tempo**: modello LightGBM, dispersione casa 0.98 / ospite 0.98, rho +0.01
- **gol 2° tempo**: modello LightGBM, dispersione casa 0.94 / ospite 0.96, rho +0.01
- **falli**: modello LightGBM, dispersione casa 1.04 / ospite 1.06
- **gialli**: modello LightGBM, dispersione casa 0.88 / ospite 0.86

Backtest soldi 1X2 + O/U 2.5 (regole fisse): massima: +6.1% su 681, Pinnacle: -9.6% su 41, Bet365: -10.0% su 71. Bookmaker dell'utente: Bet365.

| mercato | log-loss vs media | calibrazione (errore) | stagioni | fascia 70% | soldi | esito |
|---|---|---|---|---|---|---|
| angoli: 1X2 A | 0.6117 vs 0.6580 (+7.0%) | 0.014 | 100% | 77% / 76% (1001) | non provato | AMMESSO |
| angoli: 1X2 D | 0.3167 vs 0.3182 (+0.5%) | 0.003 | 100% | - | non provato | AMMESSO |
| angoli: 1X2 H | 0.6431 vs 0.6914 (+7.0%) | 0.012 | 100% | 78% / 78% (3682) | non provato | AMMESSO |
| angoli: handicap asiatico A | 0.5868 vs 0.6323 (+7.2%) | 0.012 | 100% | 78% / 76% (23455) | non provato | AMMESSO |
| angoli: handicap asiatico H | 0.5868 vs 0.6323 (+7.2%) | 0.012 | 100% | 81% / 82% (53701) | non provato | AMMESSO |
| angoli: doppia chance DA | 0.6431 vs 0.6914 (+7.0%) | 0.012 | 100% | 78% / 76% (2315) | non provato | NON AMMESSO |
| angoli: doppia chance HA | 0.3167 vs 0.3182 (+0.5%) | 0.003 | 100% | 91% / 90% (29638) | non provato | AMMESSO |
| angoli: doppia chance HD | 0.6117 vs 0.6580 (+7.0%) | 0.014 | 100% | 78% / 79% (9281) | non provato | AMMESSO |
| angoli: pari/dispari even | 0.6932 vs 0.6934 (+0.0%) | 0.004 | 80% | - | non provato | AMMESSO |
| angoli: pari/dispari odd | 0.6932 vs 0.6934 (+0.0%) | 0.007 | 80% | - | non provato | AMMESSO |
| angoli: Over/Under ospite over | 0.5076 vs 0.5343 (+5.0%) | 0.005 | 100% | 84% / 83% (61883) | non provato | AMMESSO |
| angoli: Over/Under ospite under | 0.5076 vs 0.5343 (+5.0%) | 0.005 | 100% | 83% / 84% (74124) | non provato | AMMESSO |
| angoli: Over/Under casa over | 0.5340 vs 0.5638 (+5.3%) | 0.011 | 100% | 82% / 83% (48841) | non provato | AMMESSO |
| angoli: Over/Under casa under | 0.5340 vs 0.5638 (+5.3%) | 0.011 | 100% | 83% / 82% (77015) | non provato | AMMESSO |
| angoli: Over/Under totale over | 0.5625 vs 0.5682 (+1.0%) | 0.007 | 100% | 79% / 80% (56519) | non provato | AMMESSO |
| angoli: Over/Under totale under | 0.5625 vs 0.5682 (+1.0%) | 0.007 | 100% | 82% / 81% (75299) | non provato | AMMESSO |
| angoli: multi (fasce) | 0.4656 vs 0.4682 (+0.5%) | 0.002 | 100% | - | non provato | AMMESSO |
| falli: 1X2 A | 0.6558 vs 0.6927 (+5.3%) | 0.010 | 100% | 75% / 77% (1282) | non provato | AMMESSO |
| falli: 1X2 D | 0.2821 vs 0.2828 (+0.3%) | 0.001 | 80% | - | non provato | AMMESSO |
| falli: 1X2 H | 0.6467 vs 0.6829 (+5.3%) | 0.010 | 100% | 75% / 74% (551) | non provato | AMMESSO |
| falli: handicap asiatico A | 0.6199 vs 0.6555 (+5.4%) | 0.011 | 100% | 78% / 79% (32342) | non provato | AMMESSO |
| falli: handicap asiatico H | 0.6199 vs 0.6555 (+5.4%) | 0.011 | 100% | 77% / 76% (23666) | non provato | AMMESSO |
| falli: doppia chance DA | 0.6467 vs 0.6829 (+5.3%) | 0.010 | 100% | 76% / 76% (4568) | non provato | AMMESSO |
| falli: doppia chance HA | 0.2821 vs 0.2828 (+0.3%) | 0.001 | 80% | 92% / 92% (29639) | non provato | AMMESSO |
| falli: doppia chance HD | 0.6558 vs 0.6927 (+5.3%) | 0.010 | 100% | 75% / 74% (3062) | non provato | AMMESSO |
| falli: draw no bet A | 0.6558 vs 0.6927 (+5.3%) | 0.010 | 100% | 75% / 77% (1282) | non provato | AMMESSO |
| falli: draw no bet H | 0.6467 vs 0.6829 (+5.3%) | 0.010 | 100% | 75% / 74% (551) | non provato | AMMESSO |
| falli: handicap europeo A | 0.6266 vs 0.6623 (+5.4%) | 0.011 | 100% | 77% / 78% (14004) | non provato | AMMESSO |
| falli: handicap europeo D | 0.2660 vs 0.2675 (+0.6%) | 0.001 | 100% | - | non provato | AMMESSO |
| falli: handicap europeo H | 0.6168 vs 0.6524 (+5.4%) | 0.011 | 100% | 76% / 76% (9933) | non provato | AMMESSO |
| falli: pari/dispari even | 0.6932 vs 0.6937 (+0.1%) | 0.001 | 100% | - | non provato | NON AMMESSO |
| falli: pari/dispari odd | 0.6932 vs 0.6937 (+0.1%) | 0.001 | 100% | - | non provato | NON AMMESSO |
| falli: Over/Under ospite over | 0.5434 vs 0.5838 (+6.9%) | 0.017 | 100% | 82% / 83% (60673) | non provato | NON AMMESSO |
| falli: Over/Under ospite under | 0.5434 vs 0.5838 (+6.9%) | 0.017 | 100% | 83% / 82% (70745) | non provato | NON AMMESSO |
| falli: Over/Under casa over | 0.5330 vs 0.5757 (+7.4%) | 0.004 | 100% | 81% / 82% (57400) | non provato | AMMESSO |
| falli: Over/Under casa under | 0.5330 vs 0.5757 (+7.4%) | 0.004 | 100% | 84% / 84% (78839) | non provato | AMMESSO |
| falli: Over/Under totale over | 0.5087 vs 0.5551 (+8.3%) | 0.014 | 100% | 84% / 85% (118436) | non provato | AMMESSO |
| falli: Over/Under totale under | 0.5087 vs 0.5551 (+8.3%) | 0.014 | 100% | 84% / 83% (117736) | non provato | AMMESSO |
| gol 2° tempo: 1X2 A | 0.5664 vs 0.5933 (+4.5%) | 0.003 | 100% | - | non provato | AMMESSO |
| gol 2° tempo: 1X2 D | 0.6437 vs 0.6469 (+0.5%) | 0.003 | 100% | - | non provato | AMMESSO |
| gol 2° tempo: 1X2 H | 0.6285 vs 0.6595 (+4.7%) | 0.006 | 100% | 73% / 67% (290) | non provato | NON AMMESSO |
| gol 2° tempo: Gol/NoGol no | 0.5721 vs 0.5746 (+0.4%) | 0.004 | 100% | 75% / 75% (27387) | non provato | AMMESSO |
| gol 2° tempo: Gol/NoGol yes | 0.5721 vs 0.5746 (+0.4%) | 0.004 | 100% | - | non provato | AMMESSO |
| gol 2° tempo: doppia chance DA | 0.6285 vs 0.6595 (+4.7%) | 0.006 | 100% | 77% / 77% (8868) | non provato | AMMESSO |
| gol 2° tempo: doppia chance HA | 0.6437 vs 0.6469 (+0.5%) | 0.003 | 100% | 72% / 72% (4926) | non provato | AMMESSO |
| gol 2° tempo: doppia chance HD | 0.5664 vs 0.5933 (+4.5%) | 0.003 | 100% | 78% / 78% (21367) | non provato | AMMESSO |
| gol 2° tempo: numero esatto | 0.5266 vs 0.5288 (+0.4%) | 0.002 | 100% | - | non provato | AMMESSO |
| gol 2° tempo: pari/dispari even | 0.6920 vs 0.6924 (+0.1%) | 0.002 | 100% | - | non provato | NON AMMESSO |
| gol 2° tempo: pari/dispari odd | 0.6920 vs 0.6924 (+0.1%) | 0.002 | 100% | - | non provato | NON AMMESSO |
| gol 2° tempo: Over/Under ospite over | 0.4059 vs 0.4203 (+3.4%) | 0.003 | 100% | 74% / 74% (927) | non provato | AMMESSO |
| gol 2° tempo: Over/Under ospite under | 0.4059 vs 0.4203 (+3.4%) | 0.003 | 100% | 91% / 91% (62280) | non provato | AMMESSO |
| gol 2° tempo: Over/Under casa over | 0.4490 vs 0.4663 (+3.7%) | 0.004 | 100% | 74% / 75% (3531) | non provato | AMMESSO |
| gol 2° tempo: Over/Under casa under | 0.4490 vs 0.4663 (+3.7%) | 0.004 | 100% | 89% / 89% (58611) | non provato | AMMESSO |
| gol 2° tempo: Over/Under totale over | 0.4749 vs 0.4798 (+1.0%) | 0.004 | 100% | 78% / 79% (31251) | non provato | AMMESSO |
| gol 2° tempo: Over/Under totale under | 0.4749 vs 0.4798 (+1.0%) | 0.004 | 100% | 88% / 88% (62281) | non provato | AMMESSO |
| gol 1° tempo: 1X2 A | 0.5434 vs 0.5663 (+4.0%) | 0.004 | 100% | - | non provato | AMMESSO |
| gol 1° tempo: 1X2 D | 0.6711 vs 0.6753 (+0.6%) | 0.002 | 100% | - | non provato | AMMESSO |
| gol 1° tempo: 1X2 H | 0.6120 vs 0.6399 (+4.4%) | 0.004 | 100% | - | non provato | AMMESSO |
| gol 1° tempo: Gol/NoGol no | 0.4909 vs 0.4931 (+0.5%) | 0.002 | 100% | 81% / 81% (31441) | non provato | AMMESSO |
| gol 1° tempo: Gol/NoGol yes | 0.4909 vs 0.4931 (+0.5%) | 0.002 | 100% | - | non provato | AMMESSO |
| gol 1° tempo: doppia chance DA | 0.6120 vs 0.6399 (+4.4%) | 0.004 | 100% | 76% / 76% (13175) | non provato | AMMESSO |
| gol 1° tempo: doppia chance HA | 0.6711 vs 0.6753 (+0.6%) | 0.002 | 100% | 72% / 74% (762) | non provato | AMMESSO |
| gol 1° tempo: doppia chance HD | 0.5434 vs 0.5663 (+4.0%) | 0.004 | 100% | 80% / 80% (21751) | non provato | AMMESSO |
| gol 1° tempo: numero esatto | 0.5931 vs 0.5955 (+0.4%) | 0.000 | 100% | - | non provato | AMMESSO |
| gol 1° tempo: pari/dispari even | 0.6893 vs 0.6903 (+0.1%) | 0.001 | 100% | - | non provato | NON AMMESSO |
| gol 1° tempo: pari/dispari odd | 0.6893 vs 0.6903 (+0.1%) | 0.001 | 100% | - | non provato | NON AMMESSO |
| gol 1° tempo: Over/Under ospite over | 0.3576 vs 0.3685 (+2.9%) | 0.002 | 100% | 73% / 69% (300) | non provato | AMMESSO |
| gol 1° tempo: Over/Under ospite under | 0.3576 vs 0.3685 (+2.9%) | 0.002 | 100% | 93% / 93% (64385) | non provato | AMMESSO |
| gol 1° tempo: Over/Under casa over | 0.3991 vs 0.4159 (+4.0%) | 0.002 | 100% | 73% / 77% (845) | non provato | AMMESSO |
| gol 1° tempo: Over/Under casa under | 0.3991 vs 0.4159 (+4.0%) | 0.002 | 100% | 92% / 92% (62266) | non provato | AMMESSO |
| gol 1° tempo: Over/Under totale over | 0.5326 vs 0.5387 (+1.1%) | 0.002 | 100% | 75% / 75% (15262) | non provato | AMMESSO |
| gol 1° tempo: Over/Under totale under | 0.5326 vs 0.5387 (+1.1%) | 0.002 | 100% | 85% / 85% (37473) | non provato | AMMESSO |
| gol: 1X2 A | 0.5592 vs 0.6105 (+8.4%) | 0.005 | 100% | 76% / 75% (908) | in perdita al tuo bookmaker | NON AMMESSO |
| gol: 1X2 D | 0.5688 vs 0.5748 (+1.1%) | 0.002 | 100% | - | in perdita al tuo bookmaker | NON AMMESSO |
| gol: 1X2 H | 0.6279 vs 0.6856 (+8.4%) | 0.004 | 100% | 77% / 79% (3343) | in perdita al tuo bookmaker | NON AMMESSO |
| gol: handicap asiatico A | 0.5041 vs 0.5507 (+8.5%) | 0.003 | 100% | 82% / 83% (50061) | non provato | AMMESSO |
| gol: handicap asiatico H | 0.5041 vs 0.5507 (+8.5%) | 0.003 | 100% | 85% / 85% (81424) | non provato | AMMESSO |
| gol: Gol/NoGol no | 0.6838 vs 0.6887 (+0.7%) | 0.005 | 100% | - | non provato | AMMESSO |
| gol: Gol/NoGol yes | 0.6838 vs 0.6887 (+0.7%) | 0.005 | 100% | 71% / 65% (40) | non provato | AMMESSO |
| gol: porta inviolata ospite no | 0.5105 vs 0.5369 (+4.9%) | 0.004 | 100% | 81% / 81% (38722) | non provato | AMMESSO |
| gol: porta inviolata ospite yes | 0.5105 vs 0.5369 (+4.9%) | 0.004 | 100% | - | non provato | AMMESSO |
| gol: porta inviolata casa no | 0.5931 vs 0.6157 (+3.7%) | 0.004 | 100% | 77% / 78% (22641) | non provato | AMMESSO |
| gol: porta inviolata casa yes | 0.5931 vs 0.6157 (+3.7%) | 0.004 | 100% | - | non provato | AMMESSO |
| gol: risultato esatto | 0.2015 vs 0.2059 (+2.2%) | 0.000 | 100% | - | non provato | AMMESSO |
| gol: doppia chance DA | 0.6279 vs 0.6856 (+8.4%) | 0.004 | 100% | 77% / 78% (10430) | non provato | AMMESSO |
| gol: doppia chance HA | 0.5688 vs 0.5748 (+1.1%) | 0.002 | 100% | 75% / 75% (42746) | non provato | AMMESSO |
| gol: doppia chance HD | 0.5592 vs 0.6105 (+8.4%) | 0.005 | 100% | 80% / 80% (29197) | non provato | AMMESSO |
| gol: numero esatto | 0.4145 vs 0.4172 (+0.6%) | 0.001 | 100% | - | non provato | AMMESSO |
| gol: ospite vince a zero yes | 0.4070 vs 0.4340 (+6.2%) | 0.003 | 100% | - | non provato | AMMESSO |
| gol: casa vince a zero yes | 0.5184 vs 0.5461 (+5.1%) | 0.004 | 100% | - | non provato | AMMESSO |
| gol: pari/dispari ospite even | 0.6863 vs 0.6885 (+0.3%) | 0.002 | 100% | 71% / 72% (43) | non provato | AMMESSO |
| gol: pari/dispari ospite odd | 0.6863 vs 0.6885 (+0.3%) | 0.002 | 100% | - | non provato | AMMESSO |
| gol: pari/dispari casa even | 0.6906 vs 0.6928 (+0.3%) | 0.005 | 100% | - | non provato | AMMESSO |
| gol: pari/dispari casa odd | 0.6906 vs 0.6928 (+0.3%) | 0.005 | 100% | - | non provato | AMMESSO |
| gol: pari/dispari even | 0.6932 vs 0.6936 (+0.1%) | 0.002 | 80% | - | non provato | NON AMMESSO |
| gol: pari/dispari odd | 0.6932 vs 0.6936 (+0.1%) | 0.002 | 80% | - | non provato | NON AMMESSO |
| gol: Over/Under ospite over | 0.5171 vs 0.5427 (+4.7%) | 0.003 | 100% | 77% / 78% (22840) | non provato | AMMESSO |
| gol: Over/Under ospite under | 0.5171 vs 0.5427 (+4.7%) | 0.003 | 100% | 85% / 85% (71520) | non provato | AMMESSO |
| gol: Over/Under casa over | 0.5370 vs 0.5705 (+5.9%) | 0.005 | 100% | 81% / 81% (41061) | non provato | AMMESSO |
| gol: Over/Under casa under | 0.5370 vs 0.5705 (+5.9%) | 0.005 | 100% | 83% / 83% (52730) | non provato | AMMESSO |
| gol: Over/Under totale over | 0.4455 vs 0.4546 (+2.0%) | 0.003 | 100% | 86% / 86% (90973) | in perdita al tuo bookmaker | NON AMMESSO |
| gol: Over/Under totale under | 0.4455 vs 0.4546 (+2.0%) | 0.003 | 100% | 87% / 87% (131569) | in perdita al tuo bookmaker | NON AMMESSO |
| gol: multi (fasce) | 0.6346 vs 0.6387 (+0.6%) | 0.002 | 100% | 77% / 77% (78158) | non provato | AMMESSO |
| gol: 1X2 + Gol/NoGol A | 0.3999 vs 0.4223 (+5.3%) | 0.003 | 100% | - | non provato | AMMESSO |
| gol: 1X2 + Gol/NoGol D | 0.3682 vs 0.3719 (+1.0%) | 0.001 | 100% | - | non provato | AMMESSO |
| gol: 1X2 + Gol/NoGol H | 0.5024 vs 0.5246 (+4.2%) | 0.002 | 100% | - | non provato | AMMESSO |
| gol: 1X2 + Over/Under over | 0.4077 vs 0.4319 (+5.6%) | 0.002 | 100% | 74% / 76% (217) | non provato | AMMESSO |
| gol: 1X2 + Over/Under under | 0.4277 vs 0.4386 (+2.5%) | 0.002 | 100% | - | non provato | AMMESSO |
| gol: segna l'ospite no | 0.5931 vs 0.6157 (+3.7%) | 0.004 | 100% | - | non provato | AMMESSO |
| gol: segna l'ospite yes | 0.5931 vs 0.6157 (+3.7%) | 0.004 | 100% | 77% / 78% (22641) | non provato | AMMESSO |
| gol: segna la casa no | 0.5105 vs 0.5369 (+4.9%) | 0.004 | 100% | - | non provato | AMMESSO |
| gol: segna la casa yes | 0.5105 vs 0.5369 (+4.9%) | 0.004 | 100% | 81% / 81% (38722) | non provato | AMMESSO |
| gol: Over/Under + Gol/NoGol over | 0.4926 vs 0.5004 (+1.6%) | 0.003 | 100% | - | non provato | AMMESSO |
| gol: Over/Under + Gol/NoGol under | 0.5056 vs 0.5113 (+1.1%) | 0.003 | 100% | - | non provato | AMMESSO |
| gol (due tempi): gol in entrambi i tempi no | 0.6744 vs 0.6823 (+1.2%) | 0.006 | 100% | - | non provato | AMMESSO |
| gol (due tempi): gol in entrambi i tempi yes | 0.6744 vs 0.6823 (+1.2%) | 0.006 | 100% | 72% / 74% (985) | non provato | AMMESSO |
| gol (due tempi): Gol in entrambi i tempi no | 0.2083 vs 0.2103 (+0.9%) | 0.003 | 80% | 95% / 95% (31475) | non provato | AMMESSO |
| gol (due tempi): Gol in entrambi i tempi yes | 0.2083 vs 0.2103 (+0.9%) | 0.003 | 80% | - | non provato | AMMESSO |
| gol (due tempi): tempo con più gol | 0.6234 vs 0.6239 (+0.1%) | 0.002 | 100% | - | non provato | NON AMMESSO |
| gol (due tempi): parziale/finale | 0.3088 vs 0.3199 (+3.5%) | 0.001 | 100% | - | non provato | AMMESSO |
| gol (due tempi): squadra segna in entrambi i tempi A | 0.4876 vs 0.5096 (+4.3%) | 0.004 | 100% | - | non provato | AMMESSO |
| gol (due tempi): squadra segna in entrambi i tempi H | 0.5627 vs 0.5911 (+4.8%) | 0.005 | 100% | - | non provato | AMMESSO |
| gol (due tempi): vince entrambi i tempi A | 0.2452 vs 0.2662 (+7.9%) | 0.002 | 100% | - | non provato | AMMESSO |
| gol (due tempi): vince entrambi i tempi H | 0.3549 vs 0.3836 (+7.5%) | 0.003 | 100% | - | non provato | AMMESSO |
| gol (due tempi): vince almeno un tempo A | 0.6474 vs 0.6896 (+6.1%) | 0.004 | 100% | 79% / 78% (1799) | non provato | AMMESSO |
| gol (due tempi): vince almeno un tempo H | 0.6328 vs 0.6809 (+7.1%) | 0.008 | 100% | 78% / 78% (6899) | non provato | AMMESSO |
| gialli: 1X2 A | 0.6745 vs 0.6870 (+1.8%) | 0.020 | 100% | - | non provato | NON AMMESSO |
| gialli: 1X2 D | 0.5425 vs 0.5439 (+0.2%) | 0.005 | 100% | - | non provato | AMMESSO |
| gialli: 1X2 H | 0.6184 vs 0.6313 (+2.0%) | 0.016 | 100% | - | non provato | NON AMMESSO |
| gialli: handicap asiatico A | 0.4609 vs 0.4707 (+2.1%) | 0.012 | 100% | 87% / 88% (71053) | non provato | AMMESSO |
| gialli: handicap asiatico H | 0.4609 vs 0.4707 (+2.1%) | 0.012 | 100% | 85% / 84% (61942) | non provato | AMMESSO |
| gialli: doppia chance DA | 0.6184 vs 0.6313 (+2.0%) | 0.016 | 100% | 75% / 77% (8363) | non provato | NON AMMESSO |
| gialli: doppia chance HA | 0.5425 vs 0.5439 (+0.2%) | 0.005 | 100% | 76% / 77% (31019) | non provato | AMMESSO |
| gialli: doppia chance HD | 0.6745 vs 0.6870 (+1.8%) | 0.020 | 100% | 73% / 72% (2199) | non provato | NON AMMESSO |
| gialli: draw no bet A | 0.6745 vs 0.6870 (+1.8%) | 0.020 | 100% | - | non provato | NON AMMESSO |
| gialli: draw no bet H | 0.6184 vs 0.6313 (+2.0%) | 0.016 | 100% | - | non provato | NON AMMESSO |
| gialli: handicap europeo A | 0.4707 vs 0.4807 (+2.1%) | 0.012 | 100% | 82% / 83% (39127) | non provato | AMMESSO |
| gialli: handicap europeo D | 0.4193 vs 0.4223 (+0.7%) | 0.001 | 100% | - | non provato | AMMESSO |
| gialli: handicap europeo H | 0.4585 vs 0.4682 (+2.1%) | 0.013 | 100% | 79% / 77% (31228) | non provato | AMMESSO |
| gialli: pari/dispari even | 0.6932 vs 0.6937 (+0.1%) | 0.003 | 80% | - | non provato | NON AMMESSO |
| gialli: pari/dispari odd | 0.6932 vs 0.6937 (+0.1%) | 0.003 | 80% | - | non provato | NON AMMESSO |
| gialli: Over/Under ospite over | 0.5058 vs 0.5202 (+2.8%) | 0.009 | 100% | 86% / 87% (39812) | non provato | AMMESSO |
| gialli: Over/Under ospite under | 0.5058 vs 0.5202 (+2.8%) | 0.009 | 100% | 83% / 82% (39330) | non provato | AMMESSO |
| gialli: Over/Under casa over | 0.4984 vs 0.5132 (+2.9%) | 0.009 | 100% | 85% / 84% (35706) | non provato | AMMESSO |
| gialli: Over/Under casa under | 0.4984 vs 0.5132 (+2.9%) | 0.009 | 100% | 84% / 84% (48128) | non provato | AMMESSO |
| gialli: Over/Under totale over | 0.5012 vs 0.5180 (+3.2%) | 0.002 | 100% | 85% / 84% (61051) | non provato | AMMESSO |
| gialli: Over/Under totale under | 0.5012 vs 0.5180 (+3.2%) | 0.002 | 100% | 84% / 84% (61613) | non provato | AMMESSO |
