# Feature per segnale (Fase 4)

**105 feature**, tutte a soli rapporti/ATR (mai prezzi), direzionali moltiplicate per il lato (positivo = a favore), note alla chiusura dell'ultima barra prima del segnale. Codice: `python/raptor/prime/features.py`. Nel file `output/cache/features/default.parquet` hanno il prefisso `f_`.

**Mancante:** *notizia in arrivo* (citata nelle foto) richiede il calendario economico: Fase 6.

## A. Segnale

| Feature | Formula | TF | Fonte |
|---|---|---|---|
| `side` | lato del segnale (+1 buy, -1 sell) | - | nostra |
| `cell_PPK` | one-hot della cella che ha generato il segnale | - | SITO: ogni cella col suo modello |
| `cell_OTEOF` | one-hot della cella che ha generato il segnale | - | SITO: ogni cella col suo modello |
| `cell_PO3` | one-hot della cella che ha generato il segnale | - | SITO: ogni cella col suo modello |
| `cell_UNIOF` | one-hot della cella che ha generato il segnale | - | SITO: ogni cella col suo modello |
| `cell_LS` | one-hot della cella che ha generato il segnale | - | SITO: ogni cella col suo modello |
| `cell_BB` | one-hot della cella che ha generato il segnale | - | SITO: ogni cella col suo modello |
| `is_market` | 1 se ingresso a mercato (LS), 0 se limit | - | nostra |
| `entry_n` | numero d'ingresso nella stessa gamba (PPK in sequenza) | TF cella | SITO: ingressi in sequenza |
| `stop_struct_atr_tf` | distanza ingresso-stop strutturale / ATR14 del TF indicato | TF/M15/H1/H4/D1 | FOTO: stop in ATR M15/H1 |
| `stop_struct_atr_m15` | distanza ingresso-stop strutturale / ATR14 del TF indicato | TF/M15/H1/H4/D1 | FOTO: stop in ATR M15/H1 |
| `stop_struct_atr_h1` | distanza ingresso-stop strutturale / ATR14 del TF indicato | TF/M15/H1/H4/D1 | FOTO: stop in ATR M15/H1 |
| `stop_struct_atr_h4` | distanza ingresso-stop strutturale / ATR14 del TF indicato | TF/M15/H1/H4/D1 | FOTO: stop in ATR M15/H1 |
| `stop_struct_atr_d1` | distanza ingresso-stop strutturale / ATR14 del TF indicato | TF/M15/H1/H4/D1 | FOTO: stop in ATR M15/H1 |
| `stop_atr3_atr_h1` | stop 3xATR M15 / ATR H1 | M15/H1 | Fase 2 (trade 08/01) |
| `stop_struct_over_atr3` | stop strutturale / stop 3xATR M15 | M15 | nostra |
| `entry_dist_atr` | (chiusura - prezzo d'ingresso) x lato / ATR TF: profondità del ritracciamento richiesto | TF cella | nostra |
| `zone_width_atr` | ampiezza della zona d'ingresso (FVG/OTE/breaker) / ATR TF | TF cella | nostra |
| `leg_atr` | ampiezza della gamba di riferimento / ATR TF | TF cella | nostra |
| `entry_fib_in_leg` | posizione dell'ingresso nella gamba (0 = estremo, 1 = origine) | TF cella | SITO Premium: Fibonacci |

## B. Volatilità

| Feature | Formula | TF | Fonte |
|---|---|---|---|
| `vol_atr_rel` | ATR14 / media 100 barre dello stesso TF (regime di volatilità) | TF/M15/H1/H4/D1 | V5: volatilità |
| `vol_m15_atr_rel` | ATR14 / media 100 barre dello stesso TF (regime di volatilità) | TF/M15/H1/H4/D1 | V5: volatilità |
| `vol_h1_atr_rel` | ATR14 / media 100 barre dello stesso TF (regime di volatilità) | TF/M15/H1/H4/D1 | V5: volatilità |
| `vol_h4_atr_rel` | ATR14 / media 100 barre dello stesso TF (regime di volatilità) | TF/M15/H1/H4/D1 | V5: volatilità |
| `vol_d1_atr_rel` | ATR14 / media 100 barre dello stesso TF (regime di volatilità) | TF/M15/H1/H4/D1 | V5: volatilità |
| `atr_tf_over_h1` | rapporti fra ATR di timeframe diversi | multi-TF | V5: contesto multi-timeframe |
| `atr_m15_over_h1` | rapporti fra ATR di timeframe diversi | multi-TF | V5: contesto multi-timeframe |
| `atr_h1_over_d1` | rapporti fra ATR di timeframe diversi | multi-TF | V5: contesto multi-timeframe |
| `atr_h4_over_d1` | rapporti fra ATR di timeframe diversi | multi-TF | V5: contesto multi-timeframe |
| `rvol_30m_over_atr_h1` | volatilità realizzata M1 (radice somma rendimenti log^2) x prezzo / ATR H1 | M1 | nostra |
| `rvol_60m_over_atr_h1` | volatilità realizzata M1 (radice somma rendimenti log^2) x prezzo / ATR H1 | M1 | nostra |
| `rvol_240m_over_atr_h1` | volatilità realizzata M1 (radice somma rendimenti log^2) x prezzo / ATR H1 | M1 | nostra |
| `range_4h_atr_h1` | ampiezza massimo-minimo delle ultime 4h/24h / ATR H1 | TF cella | FOTO: range 4h/24h |
| `range_24h_atr_h1` | ampiezza massimo-minimo delle ultime 4h/24h / ATR H1 | TF cella | FOTO: range 4h/24h |
| `day_range_atr_d1` | range del giorno server finora / ATR D1 | TF cella | nostra |
| `bar_body_atr` | corpo della barra del segnale / ATR TF | TF cella | nostra |
| `bar_range_atr` | range della barra del segnale / ATR TF | TF cella | nostra |
| `disp_atr` | corpo massimo delle ultime 3 barre / ATR TF (displacement) | TF cella | V5/SITO: displacement |

## C. Struttura

| Feature | Formula | TF | Fonte |
|---|---|---|---|
| `brk_favor_4h` | rotture di struttura a favore nelle ultime 4h | TF cella | FOTO: rotture a favore |
| `brk_against_4h` | rotture di struttura contro nelle ultime 4h | TF cella | FOTO: rotture contro |
| `brk_now_al` | rottura sulla barra del segnale x lato | TF cella | nostra |
| `is_mss` | la rottura corrente è un cambio di struttura (MSS) | TF cella | PRES: MSS |
| `m15_trend_al` | direzione dell'ultima rottura HTF x lato | M15/H1/H4/D1 | V5: multi-timeframe |
| `dist_m15_ema` | distanze (con lato) da EMA50, swing, PDH/PDL, PWH/PWL, massimo/minimo asiatico in ATR | multi-TF | FOTO: distanza dalla media |
| `dist_m15_swing_fav` | distanze (con lato) da EMA50, swing, PDH/PDL, PWH/PWL, massimo/minimo asiatico in ATR | multi-TF | FOTO: distanza dalla media |
| `dist_m15_swing_adv` | distanze (con lato) da EMA50, swing, PDH/PDL, PWH/PWL, massimo/minimo asiatico in ATR | multi-TF | FOTO: distanza dalla media |
| `h1_trend_al` | direzione dell'ultima rottura HTF x lato | M15/H1/H4/D1 | V5: multi-timeframe |
| `dist_h1_ema` | distanze (con lato) da EMA50, swing, PDH/PDL, PWH/PWL, massimo/minimo asiatico in ATR | multi-TF | FOTO: distanza dalla media |
| `dist_h1_swing_fav` | distanze (con lato) da EMA50, swing, PDH/PDL, PWH/PWL, massimo/minimo asiatico in ATR | multi-TF | FOTO: distanza dalla media |
| `dist_h1_swing_adv` | distanze (con lato) da EMA50, swing, PDH/PDL, PWH/PWL, massimo/minimo asiatico in ATR | multi-TF | FOTO: distanza dalla media |
| `h4_trend_al` | direzione dell'ultima rottura HTF x lato | M15/H1/H4/D1 | V5: multi-timeframe |
| `dist_h4_ema` | distanze (con lato) da EMA50, swing, PDH/PDL, PWH/PWL, massimo/minimo asiatico in ATR | multi-TF | FOTO: distanza dalla media |
| `dist_h4_swing_fav` | distanze (con lato) da EMA50, swing, PDH/PDL, PWH/PWL, massimo/minimo asiatico in ATR | multi-TF | FOTO: distanza dalla media |
| `dist_h4_swing_adv` | distanze (con lato) da EMA50, swing, PDH/PDL, PWH/PWL, massimo/minimo asiatico in ATR | multi-TF | FOTO: distanza dalla media |
| `d1_trend_al` | direzione dell'ultima rottura HTF x lato | M15/H1/H4/D1 | V5: multi-timeframe |
| `dist_d1_ema` | distanze (con lato) da EMA50, swing, PDH/PDL, PWH/PWL, massimo/minimo asiatico in ATR | multi-TF | FOTO: distanza dalla media |
| `dist_d1_swing_fav` | distanze (con lato) da EMA50, swing, PDH/PDL, PWH/PWL, massimo/minimo asiatico in ATR | multi-TF | FOTO: distanza dalla media |
| `dist_d1_swing_adv` | distanze (con lato) da EMA50, swing, PDH/PDL, PWH/PWL, massimo/minimo asiatico in ATR | multi-TF | FOTO: distanza dalla media |
| `dist_tf_ema` | distanze (con lato) da EMA50, swing, PDH/PDL, PWH/PWL, massimo/minimo asiatico in ATR | multi-TF | FOTO: distanza dalla media |
| `pos_range_4h` | posizione del prezzo nel range 4h/24h/giorno/settimana (0 = sconto per il lato) | multi | FOTO: posizione nel range |
| `pos_range_24h` | posizione del prezzo nel range 4h/24h/giorno/settimana (0 = sconto per il lato) | multi | FOTO: posizione nel range |
| `pos_day` | posizione del prezzo nel range 4h/24h/giorno/settimana (0 = sconto per il lato) | multi | FOTO: posizione nel range |
| `pos_week` | posizione del prezzo nel range 4h/24h/giorno/settimana (0 = sconto per il lato) | multi | FOTO: posizione nel range |
| `dist_pdh_atr_h1` | distanze (con lato) da EMA50, swing, PDH/PDL, PWH/PWL, massimo/minimo asiatico in ATR | multi-TF | FOTO: distanza dalla media |
| `dist_pdl_atr_h1` | distanze (con lato) da EMA50, swing, PDH/PDL, PWH/PWL, massimo/minimo asiatico in ATR | multi-TF | FOTO: distanza dalla media |
| `dist_pwh_atr_d1` | distanze (con lato) da EMA50, swing, PDH/PDL, PWH/PWL, massimo/minimo asiatico in ATR | multi-TF | FOTO: distanza dalla media |
| `dist_pwl_atr_d1` | distanze (con lato) da EMA50, swing, PDH/PDL, PWH/PWL, massimo/minimo asiatico in ATR | multi-TF | FOTO: distanza dalla media |
| `dist_asia_hi_atr_h1` | distanze (con lato) da EMA50, swing, PDH/PDL, PWH/PWL, massimo/minimo asiatico in ATR | multi-TF | FOTO: distanza dalla media |
| `dist_asia_lo_atr_h1` | distanze (con lato) da EMA50, swing, PDH/PDL, PWH/PWL, massimo/minimo asiatico in ATR | multi-TF | FOTO: distanza dalla media |
| `asia_range_atr_h1` | ampiezza del range asiatico (03-07 server) / ATR H1 | TF cella | nostra (PO3) |
| `asia_known` | 1 se il range asiatico del giorno è già chiuso | TF cella | nostra |
| `fvg_count_24bars` | FVG formati nelle ultime 24 barre | TF cella | nostra |
| `sweep_count_48bars` | sweep di liquidità nelle ultime 48 barre | TF cella | SITO: liquidità |
| `sweep_lo_now` | sweep sulla barra del segnale | TF cella | nostra |
| `sweep_hi_now` | sweep sulla barra del segnale | TF cella | nostra |

## D. Momentum ed efficienza

| Feature | Formula | TF | Fonte |
|---|---|---|---|
| `push_15m_atr_h1` | variazione del prezzo (x lato) negli ultimi N minuti / ATR H1 | M1 | FOTO: spinta 60 min / 3 h |
| `push_60m_atr_h1` | variazione del prezzo (x lato) negli ultimi N minuti / ATR H1 | M1 | FOTO: spinta 60 min / 3 h |
| `push_180m_atr_h1` | variazione del prezzo (x lato) negli ultimi N minuti / ATR H1 | M1 | FOTO: spinta 60 min / 3 h |
| `push_1440m_atr_h1` | variazione del prezzo (x lato) negli ultimi N minuti / ATR H1 | M1 | FOTO: spinta 60 min / 3 h |
| `efficiency_4h` | |spostamento netto| / somma dei movimenti M1 (versione con segno x lato) | M1 | FOTO: efficienza 4h |
| `efficiency_4h_signed` | |spostamento netto| / somma dei movimenti M1 (versione con segno x lato) | M1 | FOTO: efficienza 4h |
| `efficiency_24h` | |spostamento netto| / somma dei movimenti M1 (versione con segno x lato) | M1 | FOTO: efficienza 4h |
| `efficiency_24h_signed` | |spostamento netto| / somma dei movimenti M1 (versione con segno x lato) | M1 | FOTO: efficienza 4h |
| `run_bars_al` | barre consecutive nella stessa direzione x lato | TF cella | nostra |

## E. Volumi

| Feature | Formula | TF | Fonte |
|---|---|---|---|
| `tv_rel_tf` | volume tick relativo (TF: / mediana 96 barre; M1: ultima ora / media oraria del giorno) | TF/M1 | V5: volumi |
| `tv_60m_over_1d_hourly` | volume tick relativo (TF: / mediana 96 barre; M1: ultima ora / media oraria del giorno) | TF/M1 | V5: volumi |

## F. Sessione e tempo

| Feature | Formula | TF | Fonte |
|---|---|---|---|
| `ny_sin` | ora di New York (sin/cos e ora intera) | - | FOTO: ora del giorno |
| `ny_cos` | ora di New York (sin/cos e ora intera) | - | FOTO: ora del giorno |
| `ny_hour` | ora di New York (sin/cos e ora intera) | - | FOTO: ora del giorno |
| `dow` | giorno della settimana | - | nostra |
| `kz_asia` | killzone Asia (NY 20-24), Londra (NY 02-05), New York (NY 07-10) | - | ICT |
| `kz_london` | killzone Asia (NY 20-24), Londra (NY 02-05), New York (NY 07-10) | - | ICT |
| `kz_ny` | killzone Asia (NY 20-24), Londra (NY 02-05), New York (NY 07-10) | - | ICT |
| `min_since_day_open` | minuti dall'apertura del giorno server (01:00) | - | nostra |
| `month_sin` | mese (sin/cos) | - | nostra |
| `month_cos` | mese (sin/cos) | - | nostra |

## G. Costi

| Feature | Formula | TF | Fonte |
|---|---|---|---|
| `spread_over_stop_struct` | spread dello scenario C1 / stop o / ATR | - | FOTO: spread rispetto alla volatilità |
| `spread_over_stop_atr3` | spread dello scenario C1 / stop o / ATR | - | FOTO: spread rispetto alla volatilità |
| `spread_over_atr_tf` | spread dello scenario C1 / stop o / ATR | - | FOTO: spread rispetto alla volatilità |

## H. Contesto delle celle

| Feature | Formula | TF | Fonte |
|---|---|---|---|
| `sig_all_1h` | segnali precedenti (tutte le celle / stessa cella / concordi / discordi) in 30 min, 1 h, 24 h | - | FOTO: probabilità delle celle (contesto) |
| `sig_all_24h` | segnali precedenti (tutte le celle / stessa cella / concordi / discordi) in 30 min, 1 h, 24 h | - | FOTO: probabilità delle celle (contesto) |
| `sig_same_cell_1h` | segnali precedenti (tutte le celle / stessa cella / concordi / discordi) in 30 min, 1 h, 24 h | - | FOTO: probabilità delle celle (contesto) |
| `sig_same_cell_24h` | segnali precedenti (tutte le celle / stessa cella / concordi / discordi) in 30 min, 1 h, 24 h | - | FOTO: probabilità delle celle (contesto) |
| `sig_agree_30m` | segnali precedenti (tutte le celle / stessa cella / concordi / discordi) in 30 min, 1 h, 24 h | - | FOTO: probabilità delle celle (contesto) |
| `sig_disagree_30m` | segnali precedenti (tutte le celle / stessa cella / concordi / discordi) in 30 min, 1 h, 24 h | - | FOTO: probabilità delle celle (contesto) |
