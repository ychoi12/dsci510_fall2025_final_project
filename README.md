This a dsci510 fall2025 final project

# Final Project — Which Topics Are Trending Across Online Learning Platforms?

# Clone
git clone <REPO_URL>
cd FinalProject

# Create & activate a virtual env
python -m venv .venv
# macOS/Linux:
source .venv/bin/activate
# Windows (PowerShell):
# .venv\Scripts\Activate.ps1

# Place raw data before running:
  data/Coursera.csv
  data/udemy_online_education_courses_dataset.csv

# Install dependencies
pip install -r requirements.txt

# Set up environment variables (no real keys in the repo)
cp .env.example .env
# (edit .env if you want to change GOOGLE_TRENDS_SLEEP, etc.)

# Run the end-to-end pipeline (from project root)
python -m src.main

# optional conda alterrnative:
conda create -n dsci510 python=3.9 -y
conda activate dsci510
pip install -r requirements.txt
cp .env.example .env
python -m src.main

# optional smoke test
python tests.py
