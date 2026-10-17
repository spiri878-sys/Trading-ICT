# Mercati: verifica 2022-2026 (mai vista in addestramento)

Modello scelto sugli anni 2019-2021. Calibrazione dell'anno Y stimata solo sugli anni prima di Y. 'media' = frequenza dell'evento nello stesso campionato nei 3 anni prima. Stagioni = quota di stagioni con Brier migliore della media. Fascia 70% = quando dice >= 70%: previsto / uscito.

- **angoli**: modello LightGBM, dispersione casa 1.40 / ospite 1.38
- **gol**: modello LightGBM + mercato, dispersione casa 0.94 / ospite 0.96, rho -0.04
- **gol 1° tempo**: modello LightGBM, dispersione casa 0.98 / ospite 0.98, rho +0.01
- **gol 2° tempo**: modello LightGBM, dispersione casa 0.94 / ospite 0.96, rho +0.01
- **falli**: modello LightGBM, dispersione casa 1.04 / ospite 1.06
- **gialli**: modello LightGBM, dispersione casa 0.88 / ospite 0.86
- **cartellini**: modello LightGBM, dispersione casa 1.08 / ospite 1.08
- **tiri**: modello LightGBM, dispersione casa 1.50 / ospite 1.48
- **tiri in porta**: modello LightGBM, dispersione casa 1.14 / ospite 1.14

Backtest soldi 1X2 + O/U 2.5 (regole fisse): massima: +3.6% su 1191, Pinnacle: -2.5% su 107, Bet365: -0.9% su 161. Bookmaker dell'utente: Bet365.

| mercato | log-loss vs media | calibrazione (errore) | stagioni | fascia 70% | soldi | esito |
|---|---|---|---|---|---|---|
| angoli: 1X2 A | 0.6114 vs 0.6580 (+7.1%) | 0.007 | 100% | 78% / 79% (301) | non provato | AMMESSO |
| angoli: 1X2 D | 0.3166 vs 0.3182 (+0.5%) | 0.002 | 100% | - | non provato | AMMESSO |
| angoli: 1X2 H | 0.6428 vs 0.6914 (+7.0%) | 0.007 | 100% | 78% / 77% (1967) | non provato | AMMESSO |
| angoli: handicap asiatico A | 0.5866 vs 0.6323 (+7.2%) | 0.005 | 100% | 78% / 77% (9170) | non provato | AMMESSO |
| angoli: handicap asiatico H | 0.5866 vs 0.6323 (+7.2%) | 0.005 | 100% | 80% / 81% (15579) | non provato | AMMESSO |
| angoli: doppia chance DA | 0.6428 vs 0.6914 (+7.0%) | 0.007 | 100% | 78% / 78% (742) | non provato | AMMESSO |
| angoli: doppia chance HA | 0.3166 vs 0.3182 (+0.5%) | 0.002 | 100% | - | non provato | AMMESSO |
| angoli: doppia chance HD | 0.6114 vs 0.6580 (+7.1%) | 0.007 | 100% | 78% / 78% (4121) | non provato | AMMESSO |
| angoli: draw no bet A | 0.6114 vs 0.6580 (+7.1%) | 0.007 | 100% | 78% / 79% (301) | non provato | AMMESSO |
| angoli: draw no bet H | 0.6428 vs 0.6914 (+7.0%) | 0.007 | 100% | 78% / 77% (1967) | non provato | AMMESSO |
| angoli: handicap europeo A | 0.5770 vs 0.6218 (+7.2%) | 0.004 | 100% | 77% / 77% (3477) | non provato | AMMESSO |
| angoli: handicap europeo D | 0.2914 vs 0.2937 (+0.8%) | 0.001 | 100% | - | non provato | AMMESSO |
| angoli: handicap europeo H | 0.6006 vs 0.6475 (+7.2%) | 0.005 | 100% | 79% / 79% (10087) | non provato | AMMESSO |
| angoli: pari/dispari ospite even | 0.6932 vs 0.6935 (+0.0%) | 0.005 | 80% | - | non provato | NON AMMESSO |
| angoli: pari/dispari ospite odd | 0.6932 vs 0.6935 (+0.0%) | 0.005 | 80% | - | non provato | NON AMMESSO |
| angoli: pari/dispari casa even | 0.6933 vs 0.6935 (+0.0%) | 0.008 | 80% | - | non provato | NON AMMESSO |
| angoli: pari/dispari casa odd | 0.6933 vs 0.6935 (+0.0%) | 0.008 | 80% | - | non provato | NON AMMESSO |
| angoli: pari/dispari even | 0.6933 vs 0.6934 (+0.0%) | 0.005 | 80% | - | non provato | NON AMMESSO |
| angoli: pari/dispari odd | 0.6933 vs 0.6934 (+0.0%) | 0.003 | 80% | - | non provato | NON AMMESSO |
| angoli: Over/Under ospite over | 0.5075 vs 0.5343 (+5.0%) | 0.001 | 100% | 84% / 84% (11788) | non provato | AMMESSO |
| angoli: Over/Under ospite under | 0.5075 vs 0.5343 (+5.0%) | 0.001 | 100% | 84% / 84% (12060) | non provato | AMMESSO |
| angoli: Over/Under casa over | 0.5338 vs 0.5638 (+5.3%) | 0.005 | 100% | 82% / 82% (8733) | non provato | AMMESSO |
| angoli: Over/Under casa under | 0.5338 vs 0.5638 (+5.3%) | 0.005 | 100% | 83% / 82% (15708) | non provato | AMMESSO |
| angoli: Over/Under totale over | 0.5624 vs 0.5682 (+1.0%) | 0.004 | 100% | 80% / 80% (13078) | non provato | AMMESSO |
| angoli: Over/Under totale under | 0.5624 vs 0.5682 (+1.0%) | 0.004 | 100% | 81% / 81% (15326) | non provato | AMMESSO |
| angoli: multi (fasce) | 0.4657 vs 0.4682 (+0.5%) | 0.001 | 100% | - | non provato | AMMESSO |
| cartellini: 1X2 A | 0.6747 vs 0.6894 (+2.1%) | 0.009 | 100% | - | non provato | AMMESSO |
| cartellini: 1X2 D | 0.5216 vs 0.5232 (+0.3%) | 0.002 | 100% | - | non provato | AMMESSO |
| cartellini: 1X2 H | 0.6219 vs 0.6362 (+2.2%) | 0.008 | 100% | - | non provato | AMMESSO |
| cartellini: handicap asiatico A | 0.4879 vs 0.4991 (+2.3%) | 0.006 | 100% | 86% / 86% (7033) | non provato | AMMESSO |
| cartellini: handicap asiatico H | 0.4879 vs 0.4991 (+2.3%) | 0.006 | 100% | 83% / 82% (10353) | non provato | AMMESSO |
| cartellini: doppia chance DA | 0.6219 vs 0.6362 (+2.2%) | 0.008 | 100% | 75% / 76% (4610) | non provato | AMMESSO |
| cartellini: doppia chance HA | 0.5216 vs 0.5232 (+0.3%) | 0.002 | 100% | 78% / 78% (1172) | non provato | AMMESSO |
| cartellini: doppia chance HD | 0.6747 vs 0.6894 (+2.1%) | 0.009 | 100% | 73% / 72% (1327) | non provato | AMMESSO |
| cartellini: draw no bet A | 0.6747 vs 0.6894 (+2.1%) | 0.009 | 100% | - | non provato | AMMESSO |
| cartellini: draw no bet H | 0.6219 vs 0.6362 (+2.2%) | 0.008 | 100% | - | non provato | AMMESSO |
| cartellini: handicap europeo A | 0.4988 vs 0.5100 (+2.2%) | 0.006 | 100% | 81% / 82% (6714) | non provato | AMMESSO |
| cartellini: handicap europeo D | 0.4080 vs 0.4107 (+0.7%) | 0.001 | 100% | - | non provato | AMMESSO |
| cartellini: handicap europeo H | 0.4843 vs 0.4955 (+2.3%) | 0.006 | 100% | 77% / 76% (10727) | non provato | AMMESSO |
| cartellini: pari/dispari ospite even | 0.6930 vs 0.6936 (+0.1%) | 0.005 | 100% | - | non provato | NON AMMESSO |
| cartellini: pari/dispari ospite odd | 0.6930 vs 0.6936 (+0.1%) | 0.004 | 100% | - | non provato | NON AMMESSO |
| cartellini: pari/dispari casa even | 0.6926 vs 0.6936 (+0.1%) | 0.006 | 80% | - | non provato | NON AMMESSO |
| cartellini: pari/dispari casa odd | 0.6926 vs 0.6936 (+0.1%) | 0.006 | 80% | - | non provato | NON AMMESSO |
| cartellini: pari/dispari even | 0.6931 vs 0.6937 (+0.1%) | 0.003 | 80% | - | non provato | NON AMMESSO |
| cartellini: pari/dispari odd | 0.6931 vs 0.6937 (+0.1%) | 0.001 | 80% | - | non provato | NON AMMESSO |
| cartellini: Over/Under ospite over | 0.4776 vs 0.4911 (+2.7%) | 0.003 | 100% | 86% / 86% (6015) | non provato | AMMESSO |
| cartellini: Over/Under ospite under | 0.4776 vs 0.4911 (+2.7%) | 0.003 | 100% | 85% / 85% (6603) | non provato | AMMESSO |
| cartellini: Over/Under casa over | 0.4623 vs 0.4768 (+3.0%) | 0.005 | 100% | 85% / 85% (3815) | non provato | AMMESSO |
| cartellini: Over/Under casa under | 0.4623 vs 0.4768 (+3.0%) | 0.005 | 100% | 86% / 87% (10698) | non provato | AMMESSO |
| cartellini: Over/Under totale over | 0.4908 vs 0.5071 (+3.2%) | 0.003 | 100% | 85% / 85% (8631) | non provato | AMMESSO |
| cartellini: Over/Under totale under | 0.4908 vs 0.5071 (+3.2%) | 0.003 | 100% | 84% / 85% (13001) | non provato | AMMESSO |
| falli: 1X2 A | 0.6558 vs 0.6927 (+5.3%) | 0.010 | 100% | 75% / 77% (700) | non provato | AMMESSO |
| falli: 1X2 D | 0.2821 vs 0.2828 (+0.3%) | 0.001 | 80% | - | non provato | AMMESSO |
| falli: 1X2 H | 0.6467 vs 0.6829 (+5.3%) | 0.010 | 100% | 75% / 74% (355) | non provato | AMMESSO |
| falli: handicap asiatico A | 0.6199 vs 0.6555 (+5.4%) | 0.011 | 100% | 78% / 79% (11961) | non provato | AMMESSO |
| falli: handicap asiatico H | 0.6199 vs 0.6555 (+5.4%) | 0.011 | 100% | 77% / 76% (8634) | non provato | AMMESSO |
| falli: doppia chance DA | 0.6467 vs 0.6829 (+5.3%) | 0.010 | 100% | 76% / 76% (2764) | non provato | AMMESSO |
| falli: doppia chance HA | 0.2821 vs 0.2828 (+0.3%) | 0.001 | 80% | - | non provato | AMMESSO |
| falli: doppia chance HD | 0.6558 vs 0.6927 (+5.3%) | 0.010 | 100% | 75% / 74% (2092) | non provato | AMMESSO |
| falli: draw no bet A | 0.6558 vs 0.6927 (+5.3%) | 0.010 | 100% | 75% / 77% (700) | non provato | AMMESSO |
| falli: draw no bet H | 0.6467 vs 0.6829 (+5.3%) | 0.010 | 100% | 75% / 74% (355) | non provato | AMMESSO |
| falli: handicap europeo A | 0.6266 vs 0.6623 (+5.4%) | 0.011 | 100% | 77% / 78% (6693) | non provato | AMMESSO |
| falli: handicap europeo D | 0.2660 vs 0.2675 (+0.6%) | 0.001 | 100% | - | non provato | AMMESSO |
| falli: handicap europeo H | 0.6168 vs 0.6524 (+5.4%) | 0.011 | 100% | 76% / 76% (4667) | non provato | AMMESSO |
| falli: pari/dispari ospite even | 0.6932 vs 0.6938 (+0.1%) | 0.001 | 100% | - | non provato | NON AMMESSO |
| falli: pari/dispari ospite odd | 0.6932 vs 0.6938 (+0.1%) | 0.001 | 100% | - | non provato | NON AMMESSO |
| falli: pari/dispari casa even | 0.6932 vs 0.6937 (+0.1%) | 0.007 | 60% | - | non provato | NON AMMESSO |
| falli: pari/dispari casa odd | 0.6932 vs 0.6937 (+0.1%) | 0.006 | 80% | - | non provato | NON AMMESSO |
| falli: pari/dispari even | 0.6932 vs 0.6937 (+0.1%) | 0.001 | 100% | - | non provato | NON AMMESSO |
| falli: pari/dispari odd | 0.6932 vs 0.6937 (+0.1%) | 0.001 | 100% | - | non provato | NON AMMESSO |
| falli: Over/Under ospite over | 0.5434 vs 0.5838 (+6.9%) | 0.017 | 100% | 82% / 83% (13816) | non provato | NON AMMESSO |
| falli: Over/Under ospite under | 0.5434 vs 0.5838 (+6.9%) | 0.017 | 100% | 83% / 82% (11970) | non provato | NON AMMESSO |
| falli: Over/Under casa over | 0.5330 vs 0.5757 (+7.4%) | 0.004 | 100% | 81% / 82% (13882) | non provato | AMMESSO |
| falli: Over/Under casa under | 0.5330 vs 0.5757 (+7.4%) | 0.004 | 100% | 84% / 84% (14107) | non provato | AMMESSO |
| falli: Over/Under totale over | 0.5087 vs 0.5551 (+8.3%) | 0.014 | 100% | 84% / 85% (20160) | non provato | AMMESSO |
| falli: Over/Under totale under | 0.5087 vs 0.5551 (+8.3%) | 0.014 | 100% | 84% / 83% (18806) | non provato | AMMESSO |
| gol 2° tempo: 1X2 A | 0.5666 vs 0.5933 (+4.5%) | 0.002 | 100% | - | non provato | AMMESSO |
| gol 2° tempo: 1X2 D | 0.6438 vs 0.6469 (+0.5%) | 0.004 | 100% | - | non provato | AMMESSO |
| gol 2° tempo: 1X2 H | 0.6286 vs 0.6595 (+4.7%) | 0.003 | 100% | 73% / 69% (217) | non provato | AMMESSO |
| gol 2° tempo: Gol/NoGol no | 0.5722 vs 0.5746 (+0.4%) | 0.005 | 100% | 75% / 75% (12430) | non provato | AMMESSO |
| gol 2° tempo: Gol/NoGol yes | 0.5722 vs 0.5746 (+0.4%) | 0.005 | 100% | - | non provato | AMMESSO |
| gol 2° tempo: doppia chance DA | 0.6286 vs 0.6595 (+4.7%) | 0.003 | 100% | 77% / 77% (3686) | non provato | AMMESSO |
| gol 2° tempo: doppia chance HA | 0.6438 vs 0.6469 (+0.5%) | 0.004 | 100% | 73% / 72% (3764) | non provato | AMMESSO |
| gol 2° tempo: doppia chance HD | 0.5666 vs 0.5933 (+4.5%) | 0.002 | 100% | 78% / 78% (8085) | non provato | AMMESSO |
| gol 2° tempo: draw no bet A | 0.5666 vs 0.5933 (+4.5%) | 0.002 | 100% | - | non provato | AMMESSO |
| gol 2° tempo: draw no bet H | 0.6286 vs 0.6595 (+4.7%) | 0.003 | 100% | 73% / 69% (217) | non provato | AMMESSO |
| gol 2° tempo: numero esatto | 0.5266 vs 0.5288 (+0.4%) | 0.002 | 100% | - | non provato | AMMESSO |
| gol 2° tempo: pari/dispari even | 0.6920 vs 0.6924 (+0.1%) | 0.002 | 80% | - | non provato | NON AMMESSO |
| gol 2° tempo: pari/dispari odd | 0.6920 vs 0.6924 (+0.1%) | 0.002 | 80% | - | non provato | NON AMMESSO |
| gol 2° tempo: Over/Under ospite over | 0.4059 vs 0.4203 (+3.4%) | 0.003 | 100% | 74% / 73% (566) | non provato | AMMESSO |
| gol 2° tempo: Over/Under ospite under | 0.4059 vs 0.4203 (+3.4%) | 0.003 | 100% | 91% / 91% (2433) | non provato | AMMESSO |
| gol 2° tempo: Over/Under casa over | 0.4491 vs 0.4663 (+3.7%) | 0.003 | 100% | 75% / 75% (2161) | non provato | AMMESSO |
| gol 2° tempo: Over/Under casa under | 0.4491 vs 0.4663 (+3.7%) | 0.003 | 100% | 89% / 89% (2968) | non provato | AMMESSO |
| gol 2° tempo: Over/Under totale over | 0.4749 vs 0.4798 (+1.0%) | 0.003 | 100% | 79% / 79% (6828) | non provato | AMMESSO |
| gol 2° tempo: Over/Under totale under | 0.4749 vs 0.4798 (+1.0%) | 0.003 | 100% | 88% / 88% (3738) | non provato | AMMESSO |
| gol 1° tempo: 1X2 A | 0.5436 vs 0.5663 (+4.0%) | 0.005 | 100% | - | non provato | AMMESSO |
| gol 1° tempo: 1X2 D | 0.6712 vs 0.6753 (+0.6%) | 0.002 | 100% | - | non provato | AMMESSO |
| gol 1° tempo: 1X2 H | 0.6121 vs 0.6399 (+4.3%) | 0.005 | 100% | 71% / 86% (36) | non provato | AMMESSO |
| gol 1° tempo: Gol/NoGol no | 0.4909 vs 0.4931 (+0.4%) | 0.002 | 100% | 81% / 81% (1959) | non provato | AMMESSO |
| gol 1° tempo: Gol/NoGol yes | 0.4909 vs 0.4931 (+0.4%) | 0.002 | 100% | - | non provato | AMMESSO |
| gol 1° tempo: doppia chance DA | 0.6121 vs 0.6399 (+4.3%) | 0.005 | 100% | 77% / 76% (6414) | non provato | AMMESSO |
| gol 1° tempo: doppia chance HA | 0.6712 vs 0.6753 (+0.6%) | 0.002 | 100% | 73% / 73% (828) | non provato | AMMESSO |
| gol 1° tempo: doppia chance HD | 0.5436 vs 0.5663 (+4.0%) | 0.005 | 100% | 80% / 80% (4684) | non provato | AMMESSO |
| gol 1° tempo: draw no bet A | 0.5436 vs 0.5663 (+4.0%) | 0.005 | 100% | - | non provato | AMMESSO |
| gol 1° tempo: draw no bet H | 0.6121 vs 0.6399 (+4.3%) | 0.005 | 100% | 71% / 86% (36) | non provato | AMMESSO |
| gol 1° tempo: numero esatto | 0.5932 vs 0.5955 (+0.4%) | 0.001 | 100% | - | non provato | AMMESSO |
| gol 1° tempo: pari/dispari even | 0.6894 vs 0.6903 (+0.1%) | 0.001 | 100% | - | non provato | NON AMMESSO |
| gol 1° tempo: pari/dispari odd | 0.6894 vs 0.6903 (+0.1%) | 0.001 | 100% | - | non provato | NON AMMESSO |
| gol 1° tempo: Over/Under ospite over | 0.3577 vs 0.3685 (+2.9%) | 0.001 | 100% | 73% / 68% (212) | non provato | AMMESSO |
| gol 1° tempo: Over/Under ospite under | 0.3577 vs 0.3685 (+2.9%) | 0.001 | 100% | 93% / 93% (1760) | non provato | AMMESSO |
| gol 1° tempo: Over/Under casa over | 0.3991 vs 0.4159 (+4.0%) | 0.001 | 100% | 74% / 75% (714) | non provato | AMMESSO |
| gol 1° tempo: Over/Under casa under | 0.3991 vs 0.4159 (+4.0%) | 0.001 | 100% | 92% / 92% (2205) | non provato | AMMESSO |
| gol 1° tempo: Over/Under totale over | 0.5327 vs 0.5387 (+1.1%) | 0.001 | 100% | 75% / 75% (9266) | non provato | AMMESSO |
| gol 1° tempo: Over/Under totale under | 0.5327 vs 0.5387 (+1.1%) | 0.001 | 100% | 85% / 85% (5885) | non provato | AMMESSO |
| gol: 1X2 A | 0.5592 vs 0.6105 (+8.4%) | 0.003 | 100% | 77% / 76% (338) | in perdita al tuo bookmaker | NON AMMESSO |
| gol: 1X2 D | 0.5689 vs 0.5748 (+1.0%) | 0.004 | 100% | - | in perdita al tuo bookmaker | NON AMMESSO |
| gol: 1X2 H | 0.6279 vs 0.6856 (+8.4%) | 0.003 | 100% | 78% / 79% (1075) | in perdita al tuo bookmaker | NON AMMESSO |
| gol: handicap asiatico A | 0.5041 vs 0.5507 (+8.5%) | 0.002 | 100% | 82% / 83% (7785) | non provato | AMMESSO |
| gol: handicap asiatico H | 0.5041 vs 0.5507 (+8.5%) | 0.002 | 100% | 85% / 85% (11345) | non provato | AMMESSO |
| gol: Gol/NoGol no | 0.6839 vs 0.6887 (+0.7%) | 0.005 | 100% | - | non provato | AMMESSO |
| gol: Gol/NoGol yes | 0.6839 vs 0.6887 (+0.7%) | 0.005 | 100% | 71% / 66% (53) | non provato | AMMESSO |
| gol: porta inviolata ospite no | 0.5105 vs 0.5369 (+4.9%) | 0.003 | 100% | 81% / 81% (8037) | non provato | AMMESSO |
| gol: porta inviolata ospite yes | 0.5105 vs 0.5369 (+4.9%) | 0.003 | 100% | - | non provato | AMMESSO |
| gol: porta inviolata casa no | 0.5931 vs 0.6157 (+3.7%) | 0.003 | 100% | 78% / 78% (10615) | non provato | AMMESSO |
| gol: porta inviolata casa yes | 0.5931 vs 0.6157 (+3.7%) | 0.003 | 100% | - | non provato | AMMESSO |
| gol: risultato esatto | 0.2015 vs 0.2059 (+2.2%) | 0.000 | 100% | - | non provato | AMMESSO |
| gol: doppia chance DA | 0.6279 vs 0.6856 (+8.4%) | 0.003 | 100% | 78% / 79% (2946) | non provato | AMMESSO |
| gol: doppia chance HA | 0.5689 vs 0.5748 (+1.0%) | 0.004 | 100% | 75% / 75% (25558) | non provato | AMMESSO |
| gol: doppia chance HD | 0.5592 vs 0.6105 (+8.4%) | 0.003 | 100% | 80% / 80% (5613) | non provato | AMMESSO |
| gol: draw no bet A | 0.5592 vs 0.6105 (+8.4%) | 0.003 | 100% | 77% / 76% (338) | non provato | AMMESSO |
| gol: draw no bet H | 0.6279 vs 0.6856 (+8.4%) | 0.003 | 100% | 78% / 79% (1075) | non provato | AMMESSO |
| gol: handicap europeo A | 0.4858 vs 0.5307 (+8.5%) | 0.003 | 100% | 83% / 83% (6908) | non provato | AMMESSO |
| gol: handicap europeo D | 0.4407 vs 0.4512 (+2.3%) | 0.002 | 100% | - | non provato | AMMESSO |
| gol: handicap europeo H | 0.4390 vs 0.4815 (+8.8%) | 0.001 | 100% | 80% / 80% (6484) | non provato | AMMESSO |
| gol: numero esatto | 0.4145 vs 0.4172 (+0.6%) | 0.001 | 100% | - | non provato | AMMESSO |
| gol: ospite vince a zero yes | 0.4070 vs 0.4340 (+6.2%) | 0.002 | 100% | - | non provato | AMMESSO |
| gol: casa vince a zero yes | 0.5185 vs 0.5461 (+5.1%) | 0.003 | 100% | - | non provato | AMMESSO |
| gol: pari/dispari ospite even | 0.6863 vs 0.6885 (+0.3%) | 0.002 | 100% | 71% / 73% (60) | non provato | AMMESSO |
| gol: pari/dispari ospite odd | 0.6863 vs 0.6885 (+0.3%) | 0.002 | 100% | - | non provato | AMMESSO |
| gol: pari/dispari casa even | 0.6907 vs 0.6928 (+0.3%) | 0.005 | 100% | - | non provato | AMMESSO |
| gol: pari/dispari casa odd | 0.6907 vs 0.6928 (+0.3%) | 0.005 | 100% | - | non provato | AMMESSO |
| gol: pari/dispari even | 0.6932 vs 0.6936 (+0.1%) | 0.003 | 80% | - | non provato | NON AMMESSO |
| gol: pari/dispari odd | 0.6932 vs 0.6936 (+0.1%) | 0.003 | 80% | - | non provato | NON AMMESSO |
| gol: Over/Under ospite over | 0.5171 vs 0.5427 (+4.7%) | 0.003 | 100% | 77% / 78% (11369) | non provato | AMMESSO |
| gol: Over/Under ospite under | 0.5171 vs 0.5427 (+4.7%) | 0.003 | 100% | 85% / 84% (13411) | non provato | AMMESSO |
| gol: Over/Under casa over | 0.5369 vs 0.5705 (+5.9%) | 0.004 | 100% | 81% / 81% (8730) | non provato | AMMESSO |
| gol: Over/Under casa under | 0.5369 vs 0.5705 (+5.9%) | 0.004 | 100% | 83% / 83% (9470) | non provato | AMMESSO |
| gol: Over/Under totale over | 0.4455 vs 0.4546 (+2.0%) | 0.002 | 100% | 86% / 86% (13789) | in perdita al tuo bookmaker | NON AMMESSO |
| gol: Over/Under totale under | 0.4455 vs 0.4546 (+2.0%) | 0.002 | 100% | 87% / 87% (15514) | in perdita al tuo bookmaker | NON AMMESSO |
| gol: multi (fasce) | 0.6347 vs 0.6387 (+0.6%) | 0.001 | 100% | 77% / 76% (34272) | non provato | AMMESSO |
| gol: 1X2 + Gol/NoGol A | 0.3999 vs 0.4223 (+5.3%) | 0.002 | 100% | - | non provato | AMMESSO |
| gol: 1X2 + Gol/NoGol D | 0.3683 vs 0.3719 (+1.0%) | 0.001 | 100% | - | non provato | AMMESSO |
| gol: 1X2 + Gol/NoGol H | 0.5025 vs 0.5246 (+4.2%) | 0.001 | 100% | - | non provato | AMMESSO |
| gol: 1X2 + Over/Under over | 0.4077 vs 0.4319 (+5.6%) | 0.002 | 100% | 74% / 74% (159) | non provato | AMMESSO |
| gol: 1X2 + Over/Under under | 0.4277 vs 0.4386 (+2.5%) | 0.001 | 100% | - | non provato | AMMESSO |
| gol: segna l'ospite no | 0.5931 vs 0.6157 (+3.7%) | 0.003 | 100% | - | non provato | AMMESSO |
| gol: segna l'ospite yes | 0.5931 vs 0.6157 (+3.7%) | 0.003 | 100% | 78% / 78% (10615) | non provato | AMMESSO |
| gol: segna la casa no | 0.5105 vs 0.5369 (+4.9%) | 0.003 | 100% | - | non provato | AMMESSO |
| gol: segna la casa yes | 0.5105 vs 0.5369 (+4.9%) | 0.003 | 100% | 81% / 81% (8037) | non provato | AMMESSO |
| gol: Over/Under + Gol/NoGol over | 0.4927 vs 0.5004 (+1.5%) | 0.002 | 100% | - | non provato | AMMESSO |
| gol: Over/Under + Gol/NoGol under | 0.5056 vs 0.5113 (+1.1%) | 0.002 | 100% | - | non provato | AMMESSO |
| gol (due tempi): gol in entrambi i tempi no | 0.6744 vs 0.6823 (+1.2%) | 0.003 | 100% | - | non provato | AMMESSO |
| gol (due tempi): gol in entrambi i tempi yes | 0.6744 vs 0.6823 (+1.2%) | 0.003 | 100% | 72% / 73% (1230) | non provato | AMMESSO |
| gol (due tempi): Gol in entrambi i tempi no | 0.2084 vs 0.2103 (+0.9%) | 0.002 | 80% | - | non provato | AMMESSO |
| gol (due tempi): Gol in entrambi i tempi yes | 0.2084 vs 0.2103 (+0.9%) | 0.002 | 80% | - | non provato | AMMESSO |
| gol (due tempi): tempo con più gol | 0.6233 vs 0.6239 (+0.1%) | 0.002 | 100% | - | non provato | NON AMMESSO |
| gol (due tempi): parziale/finale | 0.3089 vs 0.3199 (+3.5%) | 0.001 | 100% | - | non provato | AMMESSO |
| gol (due tempi): squadra segna in entrambi i tempi A | 0.4877 vs 0.5096 (+4.3%) | 0.004 | 100% | - | non provato | AMMESSO |
| gol (due tempi): squadra segna in entrambi i tempi H | 0.5627 vs 0.5911 (+4.8%) | 0.003 | 100% | - | non provato | AMMESSO |
| gol (due tempi): vince entrambi i tempi A | 0.2454 vs 0.2662 (+7.8%) | 0.003 | 100% | - | non provato | AMMESSO |
| gol (due tempi): vince entrambi i tempi H | 0.3549 vs 0.3836 (+7.5%) | 0.003 | 100% | - | non provato | AMMESSO |
| gol (due tempi): vince almeno un tempo A | 0.6475 vs 0.6896 (+6.1%) | 0.004 | 100% | 79% / 78% (577) | non provato | AMMESSO |
| gol (due tempi): vince almeno un tempo H | 0.6329 vs 0.6809 (+7.1%) | 0.004 | 100% | 78% / 78% (3304) | non provato | AMMESSO |
| tiri: 1X2 A | 0.5665 vs 0.6529 (+13.2%) | 0.011 | 100% | 81% / 78% (647) | non provato | AMMESSO |
| tiri: 1X2 D | 0.1988 vs 0.2014 (+1.3%) | 0.001 | 100% | - | non provato | AMMESSO |
| tiri: 1X2 H | 0.5881 vs 0.6769 (+13.1%) | 0.012 | 100% | 81% / 81% (2875) | non provato | AMMESSO |
| tiri: handicap asiatico A | 0.5646 vs 0.6520 (+13.4%) | 0.010 | 100% | 81% / 79% (4564) | non provato | AMMESSO |
| tiri: handicap asiatico H | 0.5646 vs 0.6520 (+13.4%) | 0.010 | 100% | 83% / 83% (13436) | non provato | AMMESSO |
| tiri: doppia chance DA | 0.5881 vs 0.6769 (+13.1%) | 0.012 | 100% | 81% / 79% (832) | non provato | AMMESSO |
| tiri: doppia chance HA | 0.1988 vs 0.2014 (+1.3%) | 0.001 | 100% | - | non provato | AMMESSO |
| tiri: doppia chance HD | 0.5665 vs 0.6529 (+13.2%) | 0.011 | 100% | 82% / 82% (2416) | non provato | AMMESSO |
| tiri: draw no bet A | 0.5665 vs 0.6529 (+13.2%) | 0.011 | 100% | 81% / 78% (647) | non provato | AMMESSO |
| tiri: draw no bet H | 0.5881 vs 0.6769 (+13.1%) | 0.012 | 100% | 81% / 81% (2875) | non provato | AMMESSO |
| tiri: handicap europeo A | 0.5552 vs 0.6416 (+13.5%) | 0.009 | 100% | 82% / 79% (1978) | non provato | NON AMMESSO |
| tiri: handicap europeo D | 0.1944 vs 0.1971 (+1.4%) | 0.001 | 100% | - | non provato | AMMESSO |
| tiri: handicap europeo H | 0.5755 vs 0.6641 (+13.3%) | 0.011 | 100% | 82% / 82% (8820) | non provato | AMMESSO |
| tiri: pari/dispari ospite even | 0.6933 vs 0.6938 (+0.1%) | 0.001 | 100% | - | non provato | NON AMMESSO |
| tiri: pari/dispari ospite odd | 0.6933 vs 0.6938 (+0.1%) | 0.001 | 100% | - | non provato | NON AMMESSO |
| tiri: pari/dispari casa even | 0.6933 vs 0.6935 (+0.0%) | 0.007 | 60% | - | non provato | NON AMMESSO |
| tiri: pari/dispari casa odd | 0.6933 vs 0.6935 (+0.0%) | 0.007 | 60% | - | non provato | NON AMMESSO |
| tiri: pari/dispari even | 0.6932 vs 0.6937 (+0.1%) | 0.004 | 100% | - | non provato | NON AMMESSO |
| tiri: pari/dispari odd | 0.6932 vs 0.6937 (+0.1%) | 0.004 | 100% | - | non provato | NON AMMESSO |
| tiri: Over/Under ospite over | 0.5003 vs 0.5574 (+10.2%) | 0.007 | 100% | 86% / 85% (18809) | non provato | AMMESSO |
| tiri: Over/Under ospite under | 0.5003 vs 0.5574 (+10.2%) | 0.007 | 100% | 84% / 84% (16008) | non provato | AMMESSO |
| tiri: Over/Under casa over | 0.4984 vs 0.5625 (+11.4%) | 0.008 | 100% | 85% / 86% (13906) | non provato | AMMESSO |
| tiri: Over/Under casa under | 0.4984 vs 0.5625 (+11.4%) | 0.008 | 100% | 85% / 84% (15302) | non provato | AMMESSO |
| tiri: Over/Under totale over | 0.5091 vs 0.5384 (+5.4%) | 0.003 | 100% | 82% / 82% (18516) | non provato | AMMESSO |
| tiri: Over/Under totale under | 0.5091 vs 0.5384 (+5.4%) | 0.003 | 100% | 85% / 85% (23734) | non provato | AMMESSO |
| tiri in porta: 1X2 A | 0.5753 vs 0.6463 (+11.0%) | 0.008 | 100% | 78% / 78% (513) | non provato | AMMESSO |
| tiri in porta: 1X2 D | 0.3504 vs 0.3540 (+1.0%) | 0.003 | 100% | - | non provato | AMMESSO |
| tiri in porta: 1X2 H | 0.6150 vs 0.6909 (+11.0%) | 0.011 | 100% | 80% / 80% (2107) | non provato | AMMESSO |
| tiri in porta: handicap asiatico A | 0.5387 vs 0.6060 (+11.1%) | 0.007 | 100% | 81% / 80% (8406) | non provato | AMMESSO |
| tiri in porta: handicap asiatico H | 0.5387 vs 0.6060 (+11.1%) | 0.007 | 100% | 84% / 84% (13365) | non provato | AMMESSO |
| tiri in porta: doppia chance DA | 0.6150 vs 0.6909 (+11.0%) | 0.011 | 100% | 80% / 80% (1035) | non provato | AMMESSO |
| tiri in porta: doppia chance HA | 0.3504 vs 0.3540 (+1.0%) | 0.003 | 100% | - | non provato | AMMESSO |
| tiri in porta: doppia chance HD | 0.5753 vs 0.6463 (+11.0%) | 0.008 | 100% | 81% / 81% (3318) | non provato | AMMESSO |
| tiri in porta: draw no bet A | 0.5753 vs 0.6463 (+11.0%) | 0.008 | 100% | 78% / 78% (513) | non provato | AMMESSO |
| tiri in porta: draw no bet H | 0.6150 vs 0.6909 (+11.0%) | 0.011 | 100% | 80% / 80% (2107) | non provato | AMMESSO |
| tiri in porta: handicap europeo A | 0.5267 vs 0.5936 (+11.3%) | 0.008 | 100% | 79% / 79% (4842) | non provato | AMMESSO |
| tiri in porta: handicap europeo D | 0.3274 vs 0.3332 (+1.7%) | 0.000 | 100% | - | non provato | AMMESSO |
| tiri in porta: handicap europeo H | 0.5563 vs 0.6247 (+11.0%) | 0.008 | 100% | 82% / 82% (9778) | non provato | AMMESSO |
| tiri in porta: pari/dispari ospite even | 0.6933 vs 0.6934 (+0.0%) | 0.008 | 40% | - | non provato | NON AMMESSO |
| tiri in porta: pari/dispari ospite odd | 0.6933 vs 0.6934 (+0.0%) | 0.008 | 40% | - | non provato | NON AMMESSO |
| tiri in porta: pari/dispari casa even | 0.6933 vs 0.6934 (+0.0%) | 0.008 | 60% | - | non provato | NON AMMESSO |
| tiri in porta: pari/dispari casa odd | 0.6933 vs 0.6934 (+0.0%) | 0.008 | 60% | - | non provato | NON AMMESSO |
| tiri in porta: pari/dispari even | 0.6933 vs 0.6937 (+0.1%) | 0.005 | 100% | - | non provato | NON AMMESSO |
| tiri in porta: pari/dispari odd | 0.6933 vs 0.6937 (+0.1%) | 0.005 | 80% | - | non provato | NON AMMESSO |
| tiri in porta: Over/Under ospite over | 0.5009 vs 0.5393 (+7.1%) | 0.002 | 100% | 84% / 84% (7788) | non provato | AMMESSO |
| tiri in porta: Over/Under ospite under | 0.5009 vs 0.5393 (+7.1%) | 0.002 | 100% | 84% / 84% (12379) | non provato | AMMESSO |
| tiri in porta: Over/Under casa over | 0.5130 vs 0.5588 (+8.2%) | 0.008 | 100% | 82% / 83% (8526) | non provato | AMMESSO |
| tiri in porta: Over/Under casa under | 0.5130 vs 0.5588 (+8.2%) | 0.008 | 100% | 85% / 84% (7962) | non provato | AMMESSO |
| tiri in porta: Over/Under totale over | 0.5299 vs 0.5478 (+3.3%) | 0.006 | 100% | 81% / 81% (15349) | non provato | AMMESSO |
| tiri in porta: Over/Under totale under | 0.5299 vs 0.5478 (+3.3%) | 0.006 | 100% | 84% / 83% (14082) | non provato | AMMESSO |
| gialli: 1X2 A | 0.6739 vs 0.6870 (+1.9%) | 0.010 | 100% | - | non provato | AMMESSO |
| gialli: 1X2 D | 0.5426 vs 0.5439 (+0.2%) | 0.002 | 100% | - | non provato | AMMESSO |
| gialli: 1X2 H | 0.6181 vs 0.6313 (+2.1%) | 0.007 | 100% | - | non provato | AMMESSO |
| gialli: handicap asiatico A | 0.4606 vs 0.4707 (+2.2%) | 0.005 | 100% | 87% / 88% (6170) | non provato | AMMESSO |
| gialli: handicap asiatico H | 0.4606 vs 0.4707 (+2.2%) | 0.005 | 100% | 84% / 84% (8751) | non provato | AMMESSO |
| gialli: doppia chance DA | 0.6181 vs 0.6313 (+2.1%) | 0.007 | 100% | 75% / 75% (5078) | non provato | AMMESSO |
| gialli: doppia chance HA | 0.5426 vs 0.5439 (+0.2%) | 0.002 | 100% | 77% / 77% (5809) | non provato | AMMESSO |
| gialli: doppia chance HD | 0.6739 vs 0.6870 (+1.9%) | 0.010 | 100% | 73% / 73% (1483) | non provato | AMMESSO |
| gialli: draw no bet A | 0.6739 vs 0.6870 (+1.9%) | 0.010 | 100% | - | non provato | AMMESSO |
| gialli: draw no bet H | 0.6181 vs 0.6313 (+2.1%) | 0.007 | 100% | - | non provato | AMMESSO |
| gialli: handicap europeo A | 0.4703 vs 0.4807 (+2.2%) | 0.005 | 100% | 82% / 83% (6682) | non provato | AMMESSO |
| gialli: handicap europeo D | 0.4193 vs 0.4223 (+0.7%) | 0.001 | 100% | - | non provato | AMMESSO |
| gialli: handicap europeo H | 0.4581 vs 0.4682 (+2.2%) | 0.006 | 100% | 78% / 78% (9014) | non provato | AMMESSO |
| gialli: pari/dispari ospite even | 0.6930 vs 0.6936 (+0.1%) | 0.003 | 100% | - | non provato | NON AMMESSO |
| gialli: pari/dispari ospite odd | 0.6930 vs 0.6936 (+0.1%) | 0.003 | 100% | - | non provato | NON AMMESSO |
| gialli: pari/dispari casa even | 0.6926 vs 0.6936 (+0.1%) | 0.006 | 80% | - | non provato | NON AMMESSO |
| gialli: pari/dispari casa odd | 0.6926 vs 0.6936 (+0.1%) | 0.006 | 80% | - | non provato | NON AMMESSO |
| gialli: pari/dispari even | 0.6931 vs 0.6937 (+0.1%) | 0.004 | 80% | - | non provato | NON AMMESSO |
| gialli: pari/dispari odd | 0.6932 vs 0.6937 (+0.1%) | 0.004 | 80% | - | non provato | NON AMMESSO |
| gialli: Over/Under ospite over | 0.5056 vs 0.5202 (+2.8%) | 0.003 | 100% | 86% / 87% (4150) | non provato | AMMESSO |
| gialli: Over/Under ospite under | 0.5056 vs 0.5202 (+2.8%) | 0.003 | 100% | 83% / 82% (6831) | non provato | AMMESSO |
| gialli: Over/Under casa over | 0.4983 vs 0.5132 (+2.9%) | 0.005 | 100% | 85% / 85% (2976) | non provato | AMMESSO |
| gialli: Over/Under casa under | 0.4983 vs 0.5132 (+2.9%) | 0.005 | 100% | 84% / 84% (7976) | non provato | AMMESSO |
| gialli: Over/Under totale over | 0.5012 vs 0.5180 (+3.2%) | 0.002 | 100% | 85% / 84% (8690) | non provato | AMMESSO |
| gialli: Over/Under totale under | 0.5012 vs 0.5180 (+3.2%) | 0.002 | 100% | 84% / 84% (8561) | non provato | AMMESSO |
