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
| F2 | Modello AI che combina forze, tiri, angoli, Elo, forma, mercato | in corso |
| F3 | Angoli e cartellini | da fare |
| F4 | Cacciatore di valore e backtest alle quote reali (1X2, O/U 2,5, handicap) | da fare |
| F5 | Costruttore di schedine (correlazioni, margine composto, puntata) | da fare |
