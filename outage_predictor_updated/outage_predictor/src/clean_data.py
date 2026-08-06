"""
Clean and join NERC datasets, then engineer a proxy 'outage risk' label.

Why a proxy label: NERC's public workbooks do not contain a raw outage
log (no per-event timestamp/duration at DisCo or feeder level). Instead
we derive a defensible risk label from two real signals that move
together with poor supply reliability:

  1. Energy Received (GWh) dropping sharply below a DisCo's own
     trailing trend  -> supply-side interruption signal
  2. ATC&C Losses (%) spiking above a DisCo's own trailing trend
     -> technical/commercial breakdown signal

A DisCo-month is flagged HIGH RISK (label = 1) if either signal
deviates more than `Z_THRESHOLD` standard deviations from that DisCo's
own trailing 3-month mean. This is a within-DisCo, self-relative
threshold (not a cross-DisCo comparison), so it's fair across DisCos
of very different sizes.
"""

import openpyxl
import pandas as pd
import numpy as np
from pathlib import Path

RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"
OUT_DIR = Path(__file__).resolve().parent.parent / "data" / "processed"
OUT_DIR.mkdir(parents=True, exist_ok=True)

FILE_KEY_OPS = RAW_DIR / "Key_Operational___Financial_Data_of_NESI_Jan_2019_Sep_2022_30122022.xlsx"

DISCOS = [
    "Abuja", "Benin", "Eko", "Enugu", "Ibadan", "Ikeja",
    "Jos", "Kaduna", "Kano", "Port Harcourt", "Yola",
]

Z_THRESHOLD = 1.5          # std-devs from trailing mean to flag as risk
ROLLING_WINDOW = 3          # months, for trailing mean/std


def _sheet_rows(fname, sheet):
    wb = openpyxl.load_workbook(fname, read_only=True, data_only=True)
    return list(wb[sheet].iter_rows(values_only=True))


def _extract_discos_wide(rows, header_row_idx, disco_row_start, disco_row_end):
    """Turn a wide DisCo x Month block into a long dataframe."""
    header = rows[header_row_idx]
    # first two cols are DisCo name + 'DisCo' tag; rest are month dates
    month_cols = []
    for i, val in enumerate(header):
        if isinstance(val, pd.Timestamp) or hasattr(val, "year"):
            month_cols.append(i)

    records = []
    for r in range(disco_row_start, disco_row_end + 1):
        row = rows[r]
        disco_name = row[0]
        if disco_name not in DISCOS:
            continue
        for c in month_cols:
            val = row[c] if c < len(row) else None
            if val is None:
                continue
            period = header[c]
            year_month = pd.Timestamp(period).to_period("M").to_timestamp()
            records.append({"DisCo": disco_name, "YearMonth": year_month, "Value": val})
    return pd.DataFrame.from_records(records)


def load_energy_received():
    rows = _sheet_rows(FILE_KEY_OPS, "DisCos-Energy Received")
    df = _extract_discos_wide(rows, header_row_idx=2, disco_row_start=3, disco_row_end=13)
    df = df.rename(columns={"Value": "EnergyReceived_GWh"})
    return df


def load_atcc_losses():
    rows = _sheet_rows(FILE_KEY_OPS, "DisCos-ATC&C Losses")
    df = _extract_discos_wide(rows, header_row_idx=2, disco_row_start=34, disco_row_end=44)
    df = df.rename(columns={"Value": "ATCC_Losses_pct"})
    # zero values in the tail months (data not yet reported) -> treat as missing
    df.loc[df["ATCC_Losses_pct"] == 0, "ATCC_Losses_pct"] = np.nan
    return df


def load_billing_efficiency():
    rows = _sheet_rows(FILE_KEY_OPS, "DisCos-ATC&C Losses")
    df = _extract_discos_wide(rows, header_row_idx=2, disco_row_start=4, disco_row_end=14)
    df = df.rename(columns={"Value": "BillingEfficiency_pct"})
    return df


def build_master():
    er = load_energy_received()
    atcc = load_atcc_losses()
    be = load_billing_efficiency()

    df = er.merge(atcc, on=["DisCo", "YearMonth"], how="outer")
    df = df.merge(be, on=["DisCo", "YearMonth"], how="outer")
    df = df.sort_values(["DisCo", "YearMonth"]).reset_index(drop=True)

    # calendar features
    df["Month"] = df["YearMonth"].dt.month
    df["Year"] = df["YearMonth"].dt.year
    df["Quarter"] = df["YearMonth"].dt.quarter

    # trailing mean/std per DisCo (computed on prior months only, no leakage)
    df["ER_roll_mean"] = (
        df.groupby("DisCo")["EnergyReceived_GWh"]
        .transform(lambda s: s.shift(1).rolling(ROLLING_WINDOW, min_periods=2).mean())
    )
    df["ER_roll_std"] = (
        df.groupby("DisCo")["EnergyReceived_GWh"]
        .transform(lambda s: s.shift(1).rolling(ROLLING_WINDOW, min_periods=2).std())
    )
    df["ATCC_roll_mean"] = (
        df.groupby("DisCo")["ATCC_Losses_pct"]
        .transform(lambda s: s.shift(1).rolling(ROLLING_WINDOW, min_periods=2).mean())
    )
    df["ATCC_roll_std"] = (
        df.groupby("DisCo")["ATCC_Losses_pct"]
        .transform(lambda s: s.shift(1).rolling(ROLLING_WINDOW, min_periods=2).std())
    )

    # z-scores relative to the DisCo's own recent trend
    df["ER_zscore"] = (df["EnergyReceived_GWh"] - df["ER_roll_mean"]) / df["ER_roll_std"]
    df["ATCC_zscore"] = (df["ATCC_Losses_pct"] - df["ATCC_roll_mean"]) / df["ATCC_roll_std"]

    # risk flags: energy received DROP (negative z) OR ATC&C losses SPIKE (positive z)
    er_risk = df["ER_zscore"] <= -Z_THRESHOLD
    atcc_risk = df["ATCC_zscore"] >= Z_THRESHOLD

    df["outage_risk_label"] = (er_risk | atcc_risk).astype(int)
    # rows with no rolling stats yet (first 2 months per DisCo) can't be labeled
    df.loc[df["ER_roll_std"].isna() & df["ATCC_roll_std"].isna(), "outage_risk_label"] = np.nan

    return df


if __name__ == "__main__":
    master = build_master()
    out_path = OUT_DIR / "master_discos_monthly.csv"
    master.to_csv(out_path, index=False)

    print(f"Saved: {out_path}")
    print(f"Rows: {len(master)}  |  DisCos: {master['DisCo'].nunique()}  |  "
          f"Months: {master['YearMonth'].min().date()} to {master['YearMonth'].max().date()}")
    print(f"Labeled rows: {master['outage_risk_label'].notna().sum()}  |  "
          f"Positive (high risk) rate: {master['outage_risk_label'].mean():.2%}")
    print("\nSample:")
    print(master[["DisCo", "YearMonth", "EnergyReceived_GWh", "ATCC_Losses_pct",
                   "ER_zscore", "ATCC_zscore", "outage_risk_label"]].dropna().head(10))
