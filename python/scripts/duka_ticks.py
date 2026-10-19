"""Scarica i tick XAUUSD di Dukascopy (gratis, pubblici) per un mese e li salva in parquet.
File orari .bi5 (LZMA), record da 20 byte big-endian: ms dall'inizio dell'ora, ask, bid (x1000), volumi.
Ore in UTC. Va piano (pausa tra le richieste) e riprova sui 429.
usage: python python/scripts/duka_ticks.py 2026 1 [out_dir]
"""
import lzma
import struct
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]


def hour(dt):
    url = (f"https://datafeed.dukascopy.com/datafeed/XAUUSD/{dt.year}/{dt.month - 1:02d}/{dt.day:02d}/"
           f"{dt.hour:02d}h_ticks.bi5")
    for att in range(8):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            data = urllib.request.urlopen(req, timeout=60).read()
            break
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            time.sleep(10 * (att + 1))
        except OSError:
            time.sleep(10 * (att + 1))
    else:
        raise RuntimeError(f"non scaricato: {url}")
    if not data:
        return None
    raw = lzma.decompress(data)
    n = len(raw) // 20
    rec = np.frombuffer(raw[: n * 20], dtype=">u4").reshape(n, 5)
    ms = rec[:, 0].astype(np.int64)
    ask = rec[:, 1] / 1000.0
    bid = rec[:, 2] / 1000.0
    t = np.datetime64(dt.replace(tzinfo=None), "ms") + ms.astype("timedelta64[ms]")
    return pd.DataFrame({"time": t, "bid": bid, "ask": ask})


def main(y, m, out):
    start = datetime(y, m, 1, tzinfo=timezone.utc)
    end = datetime(y + (m == 12), m % 12 + 1, 1, tzinfo=timezone.utc)
    end = min(end, datetime.now(timezone.utc) - timedelta(hours=2))
    parts = []
    dt = start
    while dt < end:
        if dt.weekday() != 5:                                  # sabato: mercato chiuso
            df = hour(dt)
            if df is not None and len(df):
                parts.append(df)
            time.sleep(0.4)
        dt += timedelta(hours=1)
    ticks = pd.concat(parts, ignore_index=True)
    out.mkdir(parents=True, exist_ok=True)
    fn = out / f"XAUUSD_ticks_{y}_{m:02d}.parquet"
    ticks.to_parquet(fn)
    print(fn, len(ticks), ticks.time.min(), ticks.time.max())


if __name__ == "__main__":
    out = Path(sys.argv[3]) if len(sys.argv) > 3 else ROOT / "output" / "cache" / "ticks"
    main(int(sys.argv[1]), int(sys.argv[2]), out)
