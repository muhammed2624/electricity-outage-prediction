"""
Fetch real historical weather data (rainfall, wind, temperature) for each
DisCo's primary state capital, covering the same window as the risk
model's training data (Jan 2019 - Sep 2022), and merge it into
master_discos_monthly.csv as new model features.

WHY THIS IS A SEPARATE, MANUALLY-RUN SCRIPT
---------------------------------------------
This needs a real internet connection to reach Open-Meteo's API
(archive-api.open-meteo.com). It CANNOT be run from Claude's sandboxed
build environment -- that sandbox's network is restricted to a small
allowlist (pypi, npm, github, etc.) and does not include this domain.
Run this yourself, locally or in CI, wherever you have normal internet
access, then commit the resulting weather_features.csv.

Data source: Open-Meteo Historical Weather API
  https://open-meteo.com/en/docs/historical-weather-api
  Free, no API key required. CC BY 4.0 licence -- attribution required
  if this data is used publicly (e.g. in the app's methodology panel).
  Non-commercial use up to 10,000 calls/day is free; this script makes
  11 calls (one per DisCo), well within that.

Run:
    pip install requests
    python src/fetch_weather_features.py

Output:
    data/processed/weather_features.csv  (DisCo x YearMonth grain, ready
    to left-join onto master_discos_monthly.csv on those two columns)
"""

import time
from pathlib import Path

import pandas as pd

try:
    import requests
except ImportError:
    raise SystemExit(
        "This script needs the 'requests' package: pip install requests"
    )

ROOT = Path(__file__).resolve().parent.parent
OUT_CSV = ROOT / "data" / "processed" / "weather_features.csv"

ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"

# Same training window as the risk model.
START_DATE = "2019-01-01"
END_DATE = "2022-09-30"

# One representative city per DisCo (its primary state capital / largest
# service city) -- the risk model is DisCo-level, not street-level, so a
# single representative coordinate per DisCo is the right grain here.
# Matches DISCO_PRIMARY_STATE in src/build_street_index.py.
DISCO_COORDS = {
    "Abuja":         (9.0765, 7.3986),    # Abuja (FCT)
    "Benin":         (6.3350, 5.6037),    # Benin City, Edo
    "Eko":           (6.4550, 3.3841),    # Lagos Island (Eko territory)
    "Enugu":         (6.4413, 7.4989),    # Enugu
    "Ibadan":        (7.3775, 3.9470),    # Ibadan, Oyo
    "Ikeja":         (6.6018, 3.3515),    # Ikeja, Lagos
    "Jos":           (9.8965, 8.8583),    # Jos, Plateau
    "Kaduna":        (10.5222, 7.4383),   # Kaduna
    "Kano":          (12.0022, 8.5920),   # Kano
    "Port Harcourt": (4.8156, 7.0498),    # Port Harcourt, Rivers
    "Yola":          (9.2035, 12.4954),   # Yola, Adamawa
}

DAILY_VARS = "precipitation_sum,windspeed_10m_max,temperature_2m_max,temperature_2m_min"


def fetch_disco_weather(disco: str, lat: float, lon: float) -> pd.DataFrame:
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": START_DATE,
        "end_date": END_DATE,
        "daily": DAILY_VARS,
        "timezone": "Africa/Lagos",
    }
    resp = requests.get(ARCHIVE_URL, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()["daily"]
    df = pd.DataFrame(data)
    df["time"] = pd.to_datetime(df["time"])
    df["DisCo"] = disco
    return df


def to_monthly(daily_df: pd.DataFrame) -> pd.DataFrame:
    daily_df = daily_df.copy()
    daily_df["YearMonth"] = daily_df["time"].dt.to_period("M").dt.to_timestamp()
    monthly = daily_df.groupby(["DisCo", "YearMonth"]).agg(
        rainfall_mm_sum=("precipitation_sum", "sum"),
        rainfall_mm_max_day=("precipitation_sum", "max"),
        heavy_rain_days=("precipitation_sum", lambda s: (s > 10).sum()),  # NAMP finding: >10mm triggers local outages
        windspeed_max_kmh=("windspeed_10m_max", "max"),
        temp_max_c=("temperature_2m_max", "max"),
        temp_min_c=("temperature_2m_min", "min"),
    ).reset_index()
    return monthly


def main():
    all_monthly = []
    for disco, (lat, lon) in DISCO_COORDS.items():
        print(f"Fetching weather for {disco} ({lat}, {lon})...")
        try:
            daily = fetch_disco_weather(disco, lat, lon)
        except Exception as e:
            print(f"  FAILED for {disco}: {e}")
            continue
        all_monthly.append(to_monthly(daily))
        time.sleep(1)  # be polite to the free API

    if not all_monthly:
        raise SystemExit("No weather data fetched -- check your internet connection.")

    result = pd.concat(all_monthly, ignore_index=True)
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(OUT_CSV, index=False)
    print(f"\nWrote {len(result)} DisCo-month weather rows to {OUT_CSV}")
    print(
        "\nNext step: merge this into master_discos_monthly.csv on "
        "(DisCo, YearMonth), then re-run src/train_model.py with the new "
        "columns added to feature_cols. See src/merge_weather_holidays.py."
    )


if __name__ == "__main__":
    main()
