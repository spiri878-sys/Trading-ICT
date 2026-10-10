"""Session/time helpers.

Evidence (data audit, see docs/data_quality.md): the feed's daily break is 23:55->01:01 server
and the week opens at 01:00 server, i.e. the server clock follows "New York close + 7h"
(GMT+2 winter / GMT+3 summer). Therefore New-York local time = server time - 7h, all year,
except the ~2-3 weeks per year when US and EU DST are misaligned (error of 1h, documented).
"""
import numpy as np
import pandas as pd

NY_OFFSET_H = 7


def ny_hour_minute(index: pd.DatetimeIndex) -> tuple[np.ndarray, np.ndarray]:
    t = index - pd.Timedelta(hours=NY_OFFSET_H)
    return t.hour.values, t.minute.values


def ny_minutes_of_day(index: pd.DatetimeIndex) -> np.ndarray:
    h, m = ny_hour_minute(index)
    return h * 60 + m


def trading_day(index: pd.DatetimeIndex) -> np.ndarray:
    """Server calendar day == NY 17:00-to-17:00 trading day (because server = NY+7)."""
    return index.normalize().values
