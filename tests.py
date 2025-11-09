# tests.py
from pathlib import Path
import pandas as pd

from src.config import DATA_DIR, RESULTS_DIR
from src.fp_trends import fetch_trend_yearly

def test_dirs_exist():
    assert DATA_DIR.exists()
    assert RESULTS_DIR.exists()

def test_pytrends_fetch():
    df = fetch_trend_yearly("machine learning", 2010, 2012)
    assert isinstance(df, pd.DataFrame)
    assert {"year", "interest"}.issubset(df.columns)
    assert len(df) > 0

if __name__ == "__main__":
    failed = False
    try:
        test_dirs_exist(); print("✓ test_dirs_exist")
        test_pytrends_fetch(); print("✓ test_pytrends_fetch")
    except AssertionError as e:
        failed = True
        print("✗ test failed:", e)
    exit(1 if failed else 0)