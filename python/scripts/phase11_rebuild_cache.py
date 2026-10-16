"""FASE 11 — ricostruzione della cache quando il vecchio M1 MT5 (2018 -> 2026-10, con spread) non è disponibile.

Usa solo XAU_1m_data.csv (2004-06-11 -> 2026-01-30): stessa pulizia, stessi tick errati rimossi e stessi timeframe
della Fase 0. Lo spread resta -1 (sconosciuto): i costi usano gli scenari dichiarati C1 / C2. Il profilo di spread
per ora viene riscritto dai valori salvati in output/phase0_stats.json.

usage: python python/scripts/phase11_rebuild_cache.py
"""
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from phase0_data import CACHE, NEW_CSV, OUT, TF, TFS, cached, day_quality, remove_bad_ticks, weekly  # noqa: E402
from raptor.data import clean, load_semicolon_csv, resample  # noqa: E402


def main():
    CACHE.mkdir(parents=True, exist_ok=True)
    new = cached(CACHE / "src_new_m1.parquet", lambda: load_semicolon_csv(NEW_CSV))
    new_c, _ = clean(new)
    new_c, bad = remove_bad_ticks(new_c)
    print("bad ticks removed:", len(bad))
    day_quality(new_c).to_parquet(CACHE / "day_quality.parquet")
    new_c.to_parquet(CACHE / "XAUUSD_M1_master.parquet")
    TF.mkdir(parents=True, exist_ok=True)
    for name, rule in TFS.items():
        resample(new_c, rule).to_parquet(TF / f"XAUUSD_{name}.parquet")
    weekly(new_c).to_parquet(TF / "XAUUSD_W1.parquet")
    prof = pd.DataFrame(json.loads((OUT / "phase0_stats.json").read_text())["spread_profile_by_hour_usd"])
    prof.set_index("hour").to_csv(CACHE / "spread_profile_by_hour.csv")
    print("master", len(new_c), new_c.index[0], new_c.index[-1])


if __name__ == "__main__":
    main()
