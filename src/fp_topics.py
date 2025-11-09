# src/fp_topics.py

# enable postponed evaluation of type hints
from __future__ import annotations
# 're' is for regular expressions used in string cleanup
import re
from typing import Dict, Iterable, Optional
import pandas as pd

# compiles a regex that matches any run of characters that are not letters or digits
_ALNUM_UNDERSCORE = re.compile(r"[^A-Za-z0-9]+")

# define a private helper to convert messy labels into a canonical slug
def _slug_topic(s: str) -> str:
    # if input is not a non-empty string, return a safe fallback
    if not isinstance(s, str) or not s.strip():
        return "Other"
    # remove leading/trailing spaces
    s = s.strip()
    # replace all non-alphanumeric runs with underscores
    s = _ALNUM_UNDERSCORE.sub("_", s)
    # collapse multiple underscores to a single '_', then strip leading/trailing underscores
    s = re.sub(r"_+", "_", s).strip("_")
    # Title-case by splitting on underscore
    parts = [p.capitalize() for p in s.split("_") if p]
    # rejoin with '_'; if nothing left, return fallback
    return "_".join(parts) if parts else "Other"

# dictionary to remap coursera subjects into the standardized buckets to increase overlap with udemy
COURSE_SUBJECT_MAP: Dict[str, str] = {
    # concrete key -> value mapping; comments explain intent and I can adjust
    "Business": "Business_Finance",
    "Information Technology": "Web_Development",
    "Computer Science": "Web_Development",
    "Data Science": "Data_Science",
    "Health": "Health_Fitness",
    "Arts And Humanities": "Graphic_Design",
    "Personal Development": "Personal_Development",
    "Physical Science And Engineering": "Other",
    "Social Sciences": "Other",
    "Language Learning": "Other",
    "Math And Logic": "Data_Tools",
}

# public function to standardize udemy data to '['year', 'topic_norm']'
def udemy_clean(df: pd.DataFrame) -> pd.DataFrame:
    # work on a copy to avoid mutating the caller's DataFrame
    out = df.copy()

    # parse 'published_timestamp' into datetimes; invalid values become 'NaT'
    # uses '.get' to avid KeyError, defaulting to 'NaT'.
    # Set 'utc=True' for consistent timezone handling
    out["published_timestamp"] = pd.to_datetime(out.get("published_timestamp", pd.NaT), errors="coerce", utc=True)
    # extract the publication year as an integer series (may be 'NaN' for 'NaT' rows)
    out["year"] = out["published_timestamp"].dt.year

    # get the 'subject' column (or fallback "Other") and slugify each value
    out["topic_norm"] = out.get("subject", "Other").map(_slug_topic)

    # drop rows where year is missing
    out = out.dropna(subset=["year"])
    # convert year to integer type
    out["year"] = out["year"].astype(int)
    # filter to a reasonable range to avoid outliers/bad parses
    out = out[(out["year"] >= 2007) & (out["year"] <= 2030)]

    # return only the fields later functions expect, with a clean index
    return out[["year", "topic_norm"]].reset_index(drop=True)

# public function to standardize Coursera snapshot data to '['year', 'topic_norm']'
def coursera_clean(df: pd.DataFrame, snapshot_year: Optional[int] = None) -> pd.DataFrame:
    # work on a copy
    out = df.copy()

    # if a 'Year' column exists, coerce to numeric and compute a representative year (median)
    # if not, use 'snapshot_year' argument or default to 2025
    if "Year" in out.columns:
        # coerce and use the most common or latest
        out["Year"] = pd.to_numeric(out["Year"], errors="coerce")
        year_val = int(out["Year"].dropna().astype(int).median()) if out["Year"].notna().any() else (snapshot_year or 2025)
    else:
        year_val = snapshot_year or 2025

    # obtain the subject field, with a fallback to 'Category' if needed
    # Map Coursera subject to canonical topic bucket, then slug.
    raw_subject = out.get("Subject")
    if raw_subject is None:
        # some Coursera files use 'Category' instead of 'Subject'
        raw_subject = out.get("Category", "Other")

    # fill missing subjects with "Other", coerce to strings, trim spaces, then map through 'COURSE_SUBJECT_MAP'
    mapped = raw_subject.fillna("Other").astype(str).str.strip().map(lambda s: COURSE_SUBJECT_MAP.get(s, s))
    # slugify the mapped values for consistency
    out["topic_norm"] = mapped.map(_slug_topic)

    # assign the chosen snapshot year to every row
    out["year"] = year_val

    # return standardized columns
    return out[["year", "topic_norm"]].reset_index(drop=True)

# public function to compute within-year proportions of each topic and label them with the given platform name
def topic_share_by_year(df: pd.DataFrame, platform: str) -> pd.DataFrame:
    # gaurd clause: empty input -> empty output with correct columns
    if df is None or df.empty:
        return pd.DataFrame(columns=["year", "topic_norm", "share", "platform"])

    # work on a copy
    tmp = df.copy()
    # coerce year to numeric (nullable Int64), drop missing, then cast to plain 'int'
    tmp["year"] = pd.to_numeric(tmp["year"], errors="coerce").astype("Int64")
    tmp = tmp.dropna(subset=["year"])
    tmp["year"] = tmp["year"].astype(int)

    # count rows per '(year, topic_norm)' pair; name the count column 'n'
    grp = (
        tmp.groupby(["year", "topic_norm"], as_index=False)
          .size()
          .rename(columns={"size": "n"})
    )
    # Guard: nothing to aggregate
    if grp.empty:
        return pd.DataFrame(columns=["year", "topic_norm", "share", "platform"])

    # compute total courses per year to use as the denominator
    grp["total"] = grp.groupby("year")["n"].transform("sum")
    # share = topic count divided by year total
    grp["share"] = grp["n"] / grp["total"]
    # attach the platform label
    grp["platform"] = platform

    # return standardized columns with a fresh index
    return grp[["year", "topic_norm", "share", "platform"]].reset_index(drop=True)
