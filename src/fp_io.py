# safe, reusable helpers to read and write CSVs with clear errors and no crahses

# enable postponed evaluation of type hints (strings instead of real classes),
# improving import order and performance compatibility
from __future__ import annotations
import os
# let annotate that a function my return a value or 'None'
from typing import Optional
import pandas as pd

# define 'read_csv' that takes a file path string and returns a
# 'pd.DataFrame' or 'None' on failure
def read_csv(path: str) -> Optional[pd.DataFrame]:
    # start a 'try/except' to catch and handle any read errors without crashing the program
    try:
        # check if the path actually exists before attempting to read
        if not os.path.exists(path):
            # signal failure to the caller in a controlled way
            print("File not found:", path)
            return None
        # if the file exist, ask pandas to load it and return the DataFrame
        return pd.read_csv(path)
    # catch any unexpected error (permissions, malformed CSV, etc)
    except Exception as e:
        # log the file path the actual exception message for debugging
        print("Error reading CSV:", path, e)
        # fail gracefully instead of raising
        return None

# defines 'write_csv' that takes a DataFrame and a path; returns 'True' on success,
# 'False' on failure
def write_csv(df: pd.DataFrame, path: str) -> bool:
    # start error-handling block
    try:
        # ensure the output folder exist
        os.makedirs(os.path.dirname(path), exist_ok=True)
        # write DataFrame to disk as CSV, without the row index column
        df.to_csv(path, index=False)
        # confirms where the file was written-useful in logs and progress reports
        print("Saved:", path)
        # signals success to the caller
        return True
    # catch any write error (permission denied, invalid path)
    except Exception as e:
        # log the exact problem with context
        print("Error writing CSV:", path, e)
        # signals failure without throwing
        return False
