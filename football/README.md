# Football: analisi delle partite a 360 gradi per le schedine

Progetto di ricerca con lo stesso metodo della ricerca sull'oro: dati storici, modelli causali (solo passato),
verifica onesta su stagioni mai viste, confronto con le quote del bookmaker.

## Dati (`data/raw/`, non versionati; hash in `data/manifest.json`)

- `Matches.csv`: 238.858 partite di 38 campionati, dal 2000/01 al 3/9/2026 (Football-Data.co.uk via
  github.com/xgabora/Club-Football-Match-Data). Risultato, primo tempo, tiri, tiri in porta, falli, angoli,
  cartellini, quote Bet365 e massime (1X2, O/U 2,5, handicap asiatico), Elo e forma pre-partita.
- `EloRatings.csv`: Elo dei club (ClubElo).
- Le colonne di cluster `C_*` sono stimate sull'intero archivio: **escluse** (informazione dal futuro).

## Fasi

| Fase | Contenuto | Stato |
|---|---|---|
| F0 | Audit dei dati, copertura per campionato | fatto |
| F1 | Motore gol: forze attacco/difesa dinamiche + matrice dei punteggi (Poisson / Dixon-Coles) -> tutti i mercati gol | fatto (base) |
| F2 | Modello AI che combina forze, tiri, angoli, Elo, forma, mercato (walk-forward per stagione) | fatto |
| F3 | Angoli e cartellini (Poisson / binomiale negativa) | fatto |
| F4 | Cacciatore di valore e backtest alle quote reali (1X2, O/U 2,5) | fatto |
| F5 | Costruttore di schedine (correlazioni, margine composto, puntata) | da fare |

## Scheda partita

```bash
python football/scripts/f5_train_final.py          # una volta: modelli finali in football/models/ (non versionati)
python football/scripts/scheda.py --squadre I1     # nomi delle squadre
python football/scripts/scheda.py "Inter" "Napoli" I1 2026-09-13 1=2.20 X=3.40 2=3.30 over25=1.90 under25=1.90
```

Esempio: `output/esempio_scheda_inter_napoli.md`.

## Risultati principali (verifica 2013-2026, mai vista in addestramento)

- Log-loss 1X2: Bet365 1,0032; AI calcio + quote 1,0047; AI solo calcio 1,0183; motore gol 1,0202.
- Over/Under 2,5: Bet365 0,6779; AI calcio + quote 0,6790.
- Angoli e gialli: il modello batte la frequenza storica del campionato (log-loss circa -3% e -8%).
- Scommesse simulate (regole scelte su 2013-2018, verifica 2019-2026): in perdita a quota Bet365; +2-3% di ROI
  alla quota MASSIMA fra circa 17 bookmaker. Una regola senza AI (probabilità Bet365, quota massima) fa +4-9% sull'1X2:
  il guadagno viene soprattutto dal confronto delle quote. Le schedine non possono usare quote di bookmaker diversi.
