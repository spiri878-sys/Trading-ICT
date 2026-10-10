"""FASE dati: audit qualità XAUUSD M1 e creazione cache parquet + manifest."""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from raptor import data as D

raw_path = D.RAW / "XAUUSD_M1.csv"
df = D.load_mt5_csv(raw_path)
rep = D.quality(df)
D.write_manifest(raw_path, rep, D.ROOT / "data" / "manifest" / "XAUUSD_M1.manifest.json")
print(json.dumps(rep.__dict__, indent=1))
clean, _ = D.clean(df)
D.PROCESSED.mkdir(parents=True, exist_ok=True)
clean.to_parquet(D.PROCESSED / "XAUUSD_M1.parquet")
