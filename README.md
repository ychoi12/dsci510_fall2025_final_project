DSCI 510 Final Project – Fall 2025

Instructor: Dr. Alexey Tregubov

Project Title

Which Topics Are Trending Across Online Learning Platforms?

This project analyzes long-term topic trends on Udemy and compares them with Coursera’s 2025 course snapshot and global search interest from Google Trends (via Pytrends).
The pipeline loads raw Kaggle data, cleans and standardizes topics, computes yearly topic shares, pulls Google Trends data, and generates all figures and CSV outputs.

All results are saved automatically into the results/ directory.

1. Clone the Repository
git clone <REPO_URL>
cd FinalProject


2. Create & Activate a Virtual Environment
Option A — venv (Recommended)
python -m venv .venv

macOS / Linux:
source .venv/bin/activate

Windows (PowerShell):
.\.venv\Scripts\Activate.ps1

3. Add Required Raw Data (NOT included in GitHub)

Download from Kaggle and place into:

data/
   Coursera.csv
   udemy_online_education_courses_dataset.csv


4. Install Dependencies
pip install -r requirements.txt

5. Set Up Environment Variables

Copy the template:

cp .env.example .env


Edit .env if desired:

GOOGLE_TRENDS_SLEEP=1.0


6. Run the Full Pipeline

From the project root:

python -m src.main


This will:

Load Udemy & Coursera CSVs

Clean/normalize topics (fp_topics.py)

Fetch Google Trends using Pytrends (fp_trends.py)

Generate CSVs in:

results/outputs/


Generate all figures in:

results/figs/

7. Optional: Conda Environment
conda create -n dsci510 python=3.9 -y
conda activate dsci510
pip install -r requirements.txt
cp .env.example .env
python -m src.main

8. Optional: Smoke Test

Run a small test that checks directory structure and API availability:

python tests.py


This verifies:

data/ exists

CSVs can be read

results/ folders are created

Pytrends request succeeds or fails gracefully

9. Repository Structure
FinalProject/
│
├── src/
│   ├── main.py
│   ├── config.py
│   ├── fp_io.py
│   ├── fp_topics.py
│   └── fp_trends.py
│
├── data/                 # (ignored)
├── results/              # (ignored)
│   ├── outputs/
│   └── figs/
│
├── docs/
│   ├── Final Project Progress Report.pdf
│   └── Final Presentation.pptx
│
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md

10. Notes

No raw data or outputs are committed to GitHub, per project rules.

All results regenerate from scratch using python -m src.main.

All imports in your code are listed in requirements.txt.

No real secrets are stored—only .env.example is included.
