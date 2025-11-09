# src/config.py
from pathlib import Path
# bring helper that reads key value pairs from a .env filt into enfironment variables
from dotenv import load_dotenv
import os

# Actually loads key = value pairs from .env into environment variables for this Python process
load_dotenv()

# sets a reusable 'Path' to project root directory
PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Path object for the 'data/' folder under the project root.
# Raw inputs live here (local only)
DATA_DIR = PROJECT_ROOT / "data"
# Path for 'results/' Scripts write cleaned CSVs and artifacts here
RESULTS_DIR = PROJECT_ROOT / "results"
# Path for 'results/figs/ All generated charts go here
FIGS_DIR = RESULTS_DIR / "figs"

# controls the delay between google trends api requests preventing rate-limit errors
GOOGLE_TRENDS_SLEEP = float(os.getenv("GOOGLE_TRENDS_SLEEP", "1.0"))

# starts a loop over the three folder paths I defined
for d in (DATA_DIR, RESULTS_DIR, FIGS_DIR):
    # creates each directory if it doesn't exist
    d.mkdir(parents=True, exist_ok=True)
