"""
Merge weather_features.csv and holiday_features.csv (produced by
fetch_weather_features.py and fetch_holiday_features.py) into
master_discos_monthly.csv, producing master_discos_monthly_enriched.csv.

Run this AFTER running both fetch scripts with real internet access.
Then point src/train_model.py at the enriched file (see the
USE_ENRICHED_FEATURES flag added to that script) to train with the new
weather/holiday columns included.

Run:
    python src/merge_weather_holidays.py
"""

from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
PROC_DIR = ROOT / "data" / "processed"

MASTER_CSV = PROC_DIR / "master_discos_monthly.csv"
WEATHER_CSV = PROC_DIR / "weather_features.csv"
HOLIDAY_CSV = PROC_DIR / "holiday_features.csv"
OUT_CSV = PROC_DIR / "master_discos_monthly_enriched.csv"


def main():
    if not WEATHER_CSV.exists() or not HOLIDAY_CSV.exists():
        sys.exit(
            "Missing weather_features.csv and/or holiday_features.csv.\n"
            "Run these first, somewhere with real internet access:\n"
            "  python src/fetch_weather_features.py\n"
            "  python src/fetch_holiday_features.py\n"
        )

    master = pd.read_csv(MASTER_CSV, parse_dates=["YearMonth"])
    weather = pd.read_csv(WEATHER_CSV, parse_dates=["YearMonth"])
    holidays = pd.read_csv(HOLIDAY_CSV, parse_dates=["YearMonth"])

    before_rows = len(master)
    enriched = master.merge(weather, on=["DisCo", "YearMonth"], how="left")
    enriched = enriched.merge(holidays, on=["DisCo", "YearMonth"], how="left")

    missing_weather = enriched["rainfall_mm_sum"].isna().sum()
    missing_holiday = enriched["holiday_count"].isna().sum()
    if missing_weather or missing_holiday:
        print(
            f"Warning: {missing_weather} rows missing weather data, "
            f"{missing_holiday} rows missing holiday data after merge. "
            "Check that fetch scripts covered the full date range."
        )

    assert len(enriched) == before_rows, "Merge changed row count -- check for duplicate keys."

    enriched.to_csv(OUT_CSV, index=False)
    print(f"Wrote {len(enriched)} rows to {OUT_CSV}")
    print(f"New columns: rainfall_mm_sum, rainfall_mm_max_day, heavy_rain_days, "
          f"windspeed_max_kmh, temp_max_c, temp_min_c, holiday_count")


if __name__ == "__main__":
    main()
