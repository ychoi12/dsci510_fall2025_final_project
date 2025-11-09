# src/fp_trends.py: fetches google weekly trends data, aggregate it to yearly averages,
# with simple retry/backoff to avoid 429 errors

# enable postponed evaluation of type hints
from __future__ import annotations

from typing import Optional
import time
import pandas as pd

# tries to import the pytrends client 'TrendReq'
try:
    from pytrends.request import TrendReq
except Exception as e:
    TrendReq = None

# declares the public API of this module
__all__ = ["fetch_trend_weekly", "fetch_trend_yearly"]

# private function to return a configured 'TrendReq' instance or raise if unavailable
def _ensure_pytrends():
    # if earlier import failed, raise a helpful 'ImportError' telling the user how to install
    if TrendReq is None:
        raise ImportError(
            "pytrends is not installed or failed to import. "
            "Install with: pip install pytrends"
        )
    # returns 'TrendReq' client with language set to US English and timezone offset 360 minutes
    return TrendReq(hl="en-US", tz=360)

# public function to fetch weekly google trends for one 'keyword'
def fetch_trend_weekly(
    keyword: str,
    timeframe: str = "today 5-y",
    geo: str = "",
    sleep: Optional[float] = None,
) -> pd.DataFrame:
    # create a 'TrendReq' client or raise if pytrends isn't installed
    pytrends = _ensure_pytrends()
    # loop over a sequence of increasing wait times to mitigate rate-limiting
    for delay in [0, 2, 4, 8, 16]:
        # if a delay is nonzero, sleep before retrying
        try:
            if delay:
                time.sleep(delay)
            # tell pytrends which keyword/timeframe/region to query
            pytrends.build_payload([keyword], timeframe=timeframe, geo=geo)
            # request weekly interest time series
            df = pytrends.interest_over_time()
            # if nothing came back, return an empty DataFrame with the expected columns
            if df is None or df.empty:
                return pd.DataFrame(columns=["date", "interest"])
            # drop the 'isPartial' flag column
            if "isPartial" in df.columns:
                df = df.drop(columns=["isPartial"])
            # move the date index into a regular column and rename the keyword column to a generic "interest"
            df = df.reset_index().rename(columns={keyword: "interest"})
            # keep only the 'date' and 'interest' columns and return the result
            df = df[["date", "interest"]]
            return df
        # on any error, skip to the next delay and retry
        except Exception:
            # try next delay
            continue
    # if all retries fail, return an empty DataFrame with the correct schema
    return pd.DataFrame(columns=["date", "interest"])

# public function to aggregate weekly data to yearly averages for a date range
def fetch_trend_yearly(
    keyword: str,
    start_year: int,
    end_year: int,
    sleep: Optional[float] = None,
) -> pd.DataFrame:
    # build a trends timeframe string for a closed date range from Jan 1 to Dec 31
    tf = f"{start_year}-01-01 {end_year}-12-31"
    # fetch weekly data over that range
    dfw = fetch_trend_weekly(keyword=keyword, timeframe=tf, sleep=sleep)
    # if no weekly data, return an empty yearly DataFrame with correct columns
    if dfw is None or dfw.empty:
        return pd.DataFrame(columns=["year", "interest"])
    # convert 'date' to datetime and extract the calendar year per row
    dfw["year"] = pd.to_datetime(dfw["date"]).dt.year
    # compute average interest per year
    out = dfw.groupby("year", as_index=False)["interest"].mean()
    # guarantee the 'year' column is integer type
    out["year"] = out["year"].astype(int)
    # return a tidy '['year', 'interest']' DataFrame
    return out
