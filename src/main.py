# this script is end-to-end pipeline: load raw CSVs -> clean/normalize
# -> compute yearly topic shares -> make plots -> fetch/aggregate google trends
# -> run a simple regression -> save everything under 'results/'

from pathlib import Path
from typing import Optional
import json

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
plt.rcParams.update({"font.size": 22})

# import from the package `src`
from src.fp_io import read_csv, write_csv
from src.fp_topics import udemy_clean, coursera_clean, topic_share_by_year
from src.fp_trends import fetch_trend_yearly


# declares a function intended to safely yearly trends even if 'fetch_trend_yearly' isn't importable
def safe_fetch_trend_yearly(keyword: str, start_year: int, end_year: int, sleep: Optional[float] = None) -> pd.DataFrame:
    try:
        # attempts to import the "official" yearly function
        from src.fp_trends import fetch_trend_yearly
    # pulls weekly series
    except ImportError:
        # fall back: build yearly from weekly inside main.py
        from src.fp_trends import fetch_trend_weekly

        # local import for the fallback scope
        import pandas as pd

        # inner fallback that:
        # calls 'fetch_trend_weekly(...)' with a date range string
        # returns empty '['years', 'interest']' DataFrame if no data
        # converts 'date' to 'year' and groups by year to compute mean 'interest'
        def fetch_trend_yearly(keyword: str, start_year: int, end_year: int, sleep=None):
            dfw = fetch_trend_weekly(
                keyword=keyword,
                timeframe=f"{start_year}-01-01 {end_year}-12-31",
                sleep=sleep,
            )
            if dfw is None or dfw.empty:
                return pd.DataFrame(columns=["year", "interest"])
            dfw["year"] = pd.to_datetime(dfw["date"]).dt.year
            return dfw.groupby("year", as_index=False)["interest"].mean()

# project root = one level above '/src'
ROOT = Path(__file__).resolve().parents[1]
# local data folder (raw inputs)
DATA = ROOT / "data"

# root for all generated outputs
RESULTS = ROOT / "results"
# csv outputs live here
OUT = RESULTS / "outputs"
# figures live here
FIGS = RESULTS / "figs"

# udemy & coursera raw CSV path
UDEMY_RAW = DATA / "udemy_online_education_courses_dataset.csv"
COURSERA_RAW = DATA / "Coursera.csv"

# csv output paths for cleaned files and share tables
UDEMY_CLEAN_OUT = OUT / "udemy_clean.csv"
COURSERA_CLEAN_OUT = OUT / "coursera_clean.csv"
UDEMY_SHARE_OUT = OUT / "udemy_topic_shares.csv"
COURSERA_SHARE_OUT = OUT / "coursera_topic_shares.csv"

# google trends outputs
TRENDS_CSV_OUT = OUT / "trends_machine_learning_yearly.csv"
TRENDS_JSON_PREVIEW = OUT / "trends_machine_learning_preview.json"

# figure output path
FIG_UD_BUSINESS = FIGS / "udemy_Business_Finance_share.png"
FIG_UD_WEB      = FIGS / "udemy_Web_Development_share.png"
FIG_UD_GRAPHIC  = FIGS / "udemy_Graphic_Design_share.png"
FIG_UD_MUSIC    = FIGS / "udemy_Musical_Instruments_share.png"
FIG_COURSE_BARS = FIGS / "coursera_top_topics_bar.png"
FIG_COMBINED_TRENDS = FIGS / "platform_topic_share_comparison.png"
FIG_TRENDS_LINE     = FIGS / "trends_machine_learning_line.png"
FIG_U_HEATMAP       = FIGS / "udemy_topic_heatmap.png"
FIG_U_LEADLAG       = FIGS / "udemy_delta_share_vs_interest.png"

# filters to udemy + chosen 'topic', sorts by year, early-exists if empty
# builds a 12 * 7 figure with a line of 'share' over 'year'
# sets title/labels, saves to 'out_path', prints path
def plot_udemy_topic_trend(share_df: pd.DataFrame, topic: str, out_path: Path):
    sub = share_df[(share_df["platform"] == "Udemy") & (share_df["topic_norm"] == topic)].sort_values("year")
    if sub.empty:
        print(f"[skip] No Udemy rows for topic={topic}")
        return
    plt.figure(figsize=(12, 7))
    plt.plot(sub["year"], sub["share"], marker="o")
    plt.title(f"Udemy: Share over time — {topic}", fontsize=22, pad=12)
    plt.xlabel("Year"); plt.ylabel("Share of courses")
    plt.tight_layout(); plt.savefig(out_path, bbox_inches="tight"); print("Saved figure:", out_path)

# filters to coursera rows; if no rows, skip
# chooses 'year'
# keeps top 'k' topics by 'share' for that year
# horizontal bar chart, inverted y so largest at top
# title uses the resolved 'year'
# saves and prints
def plot_coursera_top_topics_bar(share_df: pd.DataFrame, out_path: Path, year: Optional[int] = None, top_k: int = 10):
    sub = share_df[share_df["platform"] == "Coursera"].copy()
    if sub.empty:
        print("[skip] No Coursera rows"); return
    if year is None:
        year = int(sub["year"].max())
    sub = sub[sub["year"] == year].sort_values("share", ascending=False).head(top_k)
    if sub.empty:
        print(f"[skip] No Coursera rows for year={year}"); return
    plt.figure(figsize=(18, 8))
    plt.barh(sub["topic_norm"], sub["share"]); plt.gca().invert_yaxis()
    plt.title(f"Coursera {year}: Top Topics by Course Share", fontsize=26, pad=10)
    plt.xlabel("Share of courses"); plt.tight_layout(); plt.savefig(out_path, bbox_inches="tight")
    print("Saved figure:", out_path)

# filters udemy rows; optional 'topics' subset
# pivots to 'topic_norm' x 'year' with mean share, fills NaNs with 0
# if pivot empty, skip
# simple 'imshow' heatmap with ticks/labels, colorbar, title
# saves and prints
def plot_udemy_topic_heatmap(share_df: pd.DataFrame, out_path: Path, topics: Optional[list] = None):
    sub = share_df[share_df["platform"] == "Udemy"].copy()
    if topics: sub = sub[sub["topic_norm"].isin(topics)]
    pivot = sub.pivot_table(index="topic_norm", columns="year", values="share", aggfunc="mean").fillna(0)
    if pivot.empty:
        print("[skip] Empty heatmap pivot"); return
    plt.figure(figsize=(14, 9)); plt.imshow(pivot.values, aspect="auto")
    plt.yticks(range(len(pivot.index)), pivot.index); plt.xticks(range(len(pivot.columns)), pivot.columns, rotation=45)
    plt.colorbar(label="Share (0–1)"); plt.title("Udemy Topic Share Heatmap", fontsize=22, pad=10)
    plt.tight_layout(); plt.savefig(out_path, bbox_inches="tight"); print("Saved figure:", out_path)

# splits udemy/coursera shares, finds overlapping 'topic_norm' labels
# if none overlap, prints a message and returns
# for each common topic: plot udemy as a line across years; coursera as dots
# title/legend, save, print
def plot_combined_topic_trends(u_share: pd.DataFrame, c_share: pd.DataFrame, out_path: Path):
    u = u_share[u_share["platform"] == "Udemy"]; c = c_share[c_share["platform"] == "Coursera"]
    common = sorted(set(u["topic_norm"]) & set(c["topic_norm"]))
    if not common:
        print("No overlapping topics to plot combined trends."); return
    plt.figure(figsize=(12, 7))
    for topic in common:
        t = u[u["topic_norm"] == topic].sort_values("year")
        if not t.empty: plt.plot(t["year"], t["share"], label=f"Udemy — {topic}", linewidth=2)
        tc = c[c["topic_norm"] == topic]
        if not tc.empty: plt.scatter(tc["year"], tc["share"], s=90, zorder=3)
    plt.xlabel("Year"); plt.ylabel("Share of courses")
    plt.title("Topic Trends: Udemy (lines) vs Coursera snapshot (dots)")
    plt.legend(ncol=2, fontsize=9); plt.tight_layout()
    plt.savefig(out_path, dpi=200, bbox_inches="tight"); print("Saved figure:", out_path)

# if trends DataFrame is empty/None, skip
# line chart of yearly 'interest'
# title/labels, save, print
def plot_trend_line(trends_yearly: pd.DataFrame, out_path: Path, title: str = "Google Trends: 'machine learning' Interest Over Time"):
    if trends_yearly is None or trends_yearly.empty:
        print("[skip] No trends data"); return
    plt.figure(figsize=(14, 9)); plt.plot(trends_yearly["year"], trends_yearly["interest"], marker="o")
    plt.title(title, fontsize=26, pad=10); plt.xlabel("Year"); plt.ylabel("Interest")
    plt.tight_layout(); plt.savefig(out_path, bbox_inches="tight"); print("Saved figure:", out_path)

# import 'LinearRegression' and 'r2_score'
# filters udemy rows; if no data or no trends, skip
# sorts by topic/year; makes 'share_prev' and 'delta_share = share - share_prev'
# copies trends, renames 'interest' -> 'interest_lag' and shifts 'year' by +1 so interest(t-1) align with delta share(t)
# merges by 'year', drops rows missing lag/delta share. If too few rows (<10), skip
# fits 'delta_share ~ interest_lag'
# gets predictions, computes R2
# sorts x for a clean line; plots scatter + fitted line
# title/labels, save, print; returns 'float(r2)'
def run_udemy_lead_lag_regression(udemy_share: pd.DataFrame, trends_yearly: pd.DataFrame, out_path: Path) -> float:
    from sklearn.linear_model import LinearRegression
    from sklearn.metrics import r2_score
    u = udemy_share[udemy_share["platform"] == "Udemy"].copy()
    if u.empty or trends_yearly is None or trends_yearly.empty:
        print("[skip] Not enough data for regression"); return 0.0
    u = u.sort_values(["topic_norm", "year"]); u["share_prev"] = u.groupby("topic_norm")["share"].shift(1)
    u["delta_share"] = u["share"] - u["share_prev"]
    t = trends_yearly.rename(columns={"interest": "interest_lag"}).copy(); t["year"] = t["year"] + 1
    X = u.merge(t[["year", "interest_lag"]], on="year", how="left").dropna(subset=["delta_share", "interest_lag"])
    if len(X) < 10:
        print("[skip] Too few rows for regression"); return 0.0
    model = LinearRegression().fit(X[["interest_lag"]], X["delta_share"])
    preds = model.predict(X[["interest_lag"]]); r2 = r2_score(X["delta_share"], preds)
    order = np.argsort(X["interest_lag"].to_numpy())
    plt.figure(figsize=(12, 7))
    plt.scatter(X["interest_lag"], X["delta_share"], s=18)
    plt.plot(X["interest_lag"].to_numpy()[order], np.array(preds)[order])
    plt.title(f"Udemy: ΔShare vs Prior-year Interest (R²={r2:.3f})", fontsize=22, pad=10)
    plt.xlabel("Prior-year Google interest"); plt.ylabel("Δ Share")
    plt.tight_layout(); plt.savefig(out_path, bbox_inches="tight"); print("Saved figure:", out_path)
    return float(r2)

def main():
    # ensure results folders exist
    OUT.mkdir(parents=True, exist_ok=True)
    FIGS.mkdir(parents=True, exist_ok=True)

    # load raw CSVs with safe reader
    u_raw = read_csv(UDEMY_RAW); c_raw = read_csv(COURSERA_RAW)

    # clean/normalize both datasets
    u_clean = udemy_clean(u_raw); c_clean = coursera_clean(c_raw)
    write_csv(u_clean, UDEMY_CLEAN_OUT); print("Saved:", UDEMY_CLEAN_OUT)
    write_csv(c_clean, COURSERA_CLEAN_OUT); print("Saved:", COURSERA_CLEAN_OUT)

    # compute yearly topic shares per platform and save
    u_share = topic_share_by_year(u_clean, platform="Udemy")
    c_share = topic_share_by_year(c_clean, platform="Coursera")
    write_csv(u_share, UDEMY_SHARE_OUT); print("Saved:", UDEMY_SHARE_OUT)
    write_csv(c_share, COURSERA_SHARE_OUT); print("Saved:", COURSERA_SHARE_OUT)

    # make figures
    plot_udemy_topic_trend(u_share, "Business_Finance", FIG_UD_BUSINESS)
    plot_udemy_topic_trend(u_share, "Web_Development", FIG_UD_WEB)
    plot_udemy_topic_trend(u_share, "Graphic_Design", FIG_UD_GRAPHIC)
    plot_udemy_topic_trend(u_share, "Musical_Instruments", FIG_UD_MUSIC)
    plot_coursera_top_topics_bar(c_share, FIG_COURSE_BARS)
    plot_udemy_topic_heatmap(u_share, FIG_U_HEATMAP)
    plot_combined_topic_trends(u_share, c_share, FIG_COMBINED_TRENDS)

    if not u_share.empty:
        y0, y1 = int(u_share["year"].min()) - 1, int(u_share["year"].max())
    else:
        y0, y1 = 2010, 2017

    trends = fetch_trend_yearly(keyword="machine learning", start_year=y0, end_year=y1, sleep=None)

    # Normalize to a DataFrame (never None) so downstream code is safe
    if trends is None or not isinstance(trends, pd.DataFrame) or trends.empty:
        print("[Trends] No data returned (None or empty). Skipping Trends outputs.")
        trends = pd.DataFrame(columns=["year", "interest"])
        wrote_trends = False
    else:
        wrote_trends = True

    # Write CSV/json only if we actually have rows
    if wrote_trends and len(trends) > 0:
        write_csv(trends, TRENDS_CSV_OUT)
        try:
            TRENDS_JSON_PREVIEW.write_text(
                json.dumps(trends.head(5).to_dict("records"), indent=2),
                encoding="utf-8"
            )
            print("Saved:", TRENDS_JSON_PREVIEW)
        except Exception as e:
            print("[Trends] Could not write preview JSON:", e)
        # Line plot
        try:
            plt.figure(figsize=(10, 6))
            plt.plot(trends["year"], trends["interest"], marker="o")
            plt.title("Google Trends: 'machine learning' Interest Over Time")
            plt.xlabel("Year");
            plt.ylabel("Interest")
            plt.tight_layout()
            plt.savefig(FIG_TRENDS_LINE, bbox_inches="tight")
            print("Saved figure:", FIG_TRENDS_LINE)
        except Exception as e:
            print("[Trends] Could not plot trends line:", e)
    else:
        # still create an empty CSV so your pipeline leaves a trace if desired
        try:
            write_csv(trends, TRENDS_CSV_OUT)
        except Exception:
            pass  # OK to skip

    # Regression: delta share ~ prior-year interest (only if we have trends)
    try:
        if wrote_trends and len(trends) > 0:
            r2 = run_udemy_lead_lag_regression(u_share, trends, FIG_U_LEADLAG)
            print(
                f"[Udemy] LinearRegression R²={r2:.4f}: {(r2 * 100):.1f}% of Δshare variance explained by prior-year interest.")
        else:
            print("[Udemy] Regression skipped: no trends data.")
    except Exception as e:
        print("[Udemy] Regression failed:", e)


if __name__ == "__main__":
    main()
