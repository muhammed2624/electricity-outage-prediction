"""
Fetch real Nigerian public holidays (Nager.Date API) for the risk model's
training years and compute a per-DisCo-month holiday-day-count feature.

Same sandbox caveat as fetch_weather_features.py: this needs a real
internet connection Claude's build sandbox doesn't have. Run it
yourself, then commit the resulting holiday_features.csv.

Data source: Nager.Date public holiday API
  https://date.nager.at/api/v3/PublicHolidays/{year}/NG
  Free, no API key required. Covers Nigeria. Note: Islamic holidays
  (Eid al-Fitr, Eid al-Kabir/Adha) are lunar-calendar-based and Nager.Date
  flags their dates as approximate ("fixed": false) since exact
  observance depends on moon sighting -- treat those dates as
  best-effort, not government-gazetted-exact.

Run:
    pip install requests
    python src/fetch_holiday_features.py

Output:
    data/processed/holiday_features.csv  (DisCo x YearMonth grain --
    holiday count is national, so it's the same across all DisCos for a
    given month, but kept at DisCo grain for a simple join onto
    master_discos_monthly.csv)
"""

from pathlib import Path

import pandas as pd

try:
    import requests
except ImportError:
    raise SystemExit(
        "This script needs the 'requests' package: pip install requests"
    )

ROOT = Path(__file__).resolve().parent.parent
OUT_CSV = ROOT / "data" / "processed" / "holiday_features.csv"
MASTER_CSV = ROOT / "data" / "processed" / "master_discos_monthly.csv"

API_URL = "https://date.nager.at/api/v3/PublicHolidays/{year}/NG"
YEARS = [2019, 2020, 2021, 2022]  # matches the risk model's training window


def fetch_year(year: int) -> list:
    resp = requests.get(API_URL.format(year=year), timeout=15)
    resp.raise_for_status()
    return resp.json()


def main():
    all_holidays = []
    for year in YEARS:
        print(f"Fetching {year} Nigerian public holidays...")
        try:
            holidays = fetch_year(year)
        except Exception as e:
            print(f"  FAILED for {year}: {e}")
            continue
        all_holidays.extend(holidays)

    if not all_holidays:
        raise SystemExit("No holiday data fetched -- check your internet connection.")

    hdf = pd.DataFrame(all_holidays)
    hdf["date"] = pd.to_datetime(hdf["date"])
    hdf["YearMonth"] = hdf["date"].dt.to_period("M").dt.to_timestamp()

    monthly_counts = hdf.groupby("YearMonth").size().rename("holiday_count").reset_index()

    # Broadcast the same national holiday count across every DisCo for
    # that month, so it joins cleanly onto master_discos_monthly.csv
    # (which is at DisCo x YearMonth grain).
    master = pd.read_csv(MASTER_CSV, parse_dates=["YearMonth"])
    discos = master["DisCo"].unique()
    rows = []
    for disco in discos:
        for _, r in monthly_counts.iterrows():
            rows.append({"DisCo": disco, "YearMonth": r["YearMonth"], "holiday_count": r["holiday_count"]})
    result = pd.DataFrame(rows)

    # Months with zero holidays won't appear in monthly_counts -- fill
    # those in as 0 rather than leaving gaps.
    all_months = master[["DisCo", "YearMonth"]].drop_duplicates()
    result = all_months.merge(result, on=["DisCo", "YearMonth"], how="left")
    result["holiday_count"] = result["holiday_count"].fillna(0).astype(int)

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(OUT_CSV, index=False)
    print(f"\nWrote {len(result)} DisCo-month holiday rows to {OUT_CSV}")
    print(
        "\nNext step: merge into master_discos_monthly.csv on "
        "(DisCo, YearMonth), then re-run src/train_model.py. "
        "See src/merge_weather_holidays.py."
    )


if __name__ == "__main__":
    main()
