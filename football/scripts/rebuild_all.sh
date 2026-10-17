#!/usr/bin/env bash
# Ricostruisce da zero dati, feature e modelli del progetto calcio (punto 11 del piano).
# Uso: bash football/scripts/rebuild_all.sh        (circa 1,5-2 ore; log in football/output/rebuild.log)
set -euo pipefail
cd "$(dirname "$0")/../.."
LOG=football/output/rebuild.log
: > "$LOG"
step() { echo "== $(date +%H:%M) $*" | tee -a "$LOG"; "$@" >> "$LOG" 2>&1; }

pip install -q scipy lightgbm scikit-learn pyflakes pytest >> "$LOG" 2>&1
mkdir -p football/data/raw football/data/cache football/models
# 1. archivio di base (fonte e hash in football/data/manifest.json)
for f in Matches EloRatings; do
  [ -f football/data/raw/$f.csv ] || curl -sSL -o football/data/raw/$f.csv \
    "https://raw.githubusercontent.com/xgabora/Club-Football-Match-Data-2000-2025/main/data/$f.csv"
done
step python football/scripts/f0_update.py            # football-data.co.uk: europei + 16 campionati extra
step python football/scripts/f0_check.py --fix       # doppioni, valori assurdi
step python football/scripts/f0_odds.py              # Pinnacle, media mercato, arbitro
# 2. feature (solo passato)
step python -c "import sys,pickle; sys.path.insert(0,'football'); from fb.data import matches, CACHE; from fb.feats import build_features; pickle.dump(build_features(matches()), open(CACHE/'m2_features.pkl','wb'))"
# 3. walk-forward 2019-2026 di tutte le statistiche
step python football/scripts/m3_walkforward.py
# 4. cancello di qualità e backtest dei soldi
step python football/scripts/m4_gate.py cor g ght g2h hh fou yel crd sh sot
step python football/scripts/m4_money.py
step python football/scripts/m4_report.py
# 5. modelli finali per l'uso giornaliero
step python football/scripts/m5_train_final.py
step python -m pytest -q football/tests
echo "== $(date +%H:%M) FINE" | tee -a "$LOG"
