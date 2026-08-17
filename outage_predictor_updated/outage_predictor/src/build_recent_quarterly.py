"""
Build discos_recent_quarterly.csv -- a REAL data extension covering
2023/Q3 through 2024/Q3, sourced directly from NERC's own published
quarterly reports (nerc.gov.ng). This closes most of the gap between
the original monthly dataset (ends Sep 2022) and today.

WHY QUARTERLY, NOT MERGED INTO THE MONTHLY MODEL:
NERC stopped publishing the monthly DisCo workbook format used for
master_discos_monthly.csv and now reports these same metrics (Energy
Received, Billing Efficiency, ATC&C Loss) per DisCo per QUARTER in its
narrative quarterly reports instead. Quarterly and monthly data have
different granularity -- the original model's trailing 3-MONTH rolling
z-score logic doesn't transfer cleanly onto quarterly points (a
3-quarter trailing window is a different, coarser signal). Rather than
force a fit that would silently change what "3 months of trend" means,
this is kept as a separate, clearly-labeled supplementary table. It's
genuinely useful for: (a) the app's evaluation/context panel showing
where each DisCo stands most recently, and (b) the capstone report's
Scope & Limitations section, honestly written up as future work
("retrain on quarterly cadence once enough quarters accumulate").

SOURCES (real NERC PDFs, fetched and transcribed directly from the
published tables -- not estimated, not fabricated):
  - 2023/Q3 vs 2023/Q4: NERC Fourth Quarter 2023 Report
    https://nerc.gov.ng/wp-content/uploads/2024/04/2023_Q4_Report_Final.pdf
    (Table 5: Energy Received & Billing Efficiency; Table 7: ATC&C Loss)
  - 2023/Q4 vs 2024/Q1: NERC First Quarter 2024 Report
    https://nerc.gov.ng/wp-content/uploads/2024/07/2024_Q1-Report_final.pdf
    (Table 5; Table 7)
  - 2024/Q2 vs 2024/Q3: NERC Third Quarter 2024 Report
    https://nerc.gov.ng/wp-content/uploads/2024/12/2024_Q3-Report.pdf
    (Table 5; Table 7)
  - 2024/Q3 vs 2024/Q4: NERC Fourth Quarter 2024 Report
    https://nerc.gov.ng/wp-content/uploads/2025/03/2024_Q4-Report.pdf
    (Table 5; Table 7)

KNOWN REMAINING GAP: 2022/Q4 through 2023/Q2 (three quarters) are not
covered by this extension -- the corresponding NERC quarterly reports
were not pulled for this pass. That gap should be named explicitly in
the capstone report's Limitations section rather than glossed over.
2025/Q1 onward is also not yet covered here, though NERC has continued
publishing (confirmed 2025/Q2 and 2025/Q3 reports exist at
nerc.gov.ng/wp-content/uploads/2025/10/2025_Q2-Report.pdf and
nerc.gov.ng/wp-content/uploads/2026/01/2025_Q3-Report.pdf) -- these
were not pulled in this pass but are a clear next step. NERC also now
publishes a MONTHLY "Commercial Performance Factsheet" (found at
nerc.gov.ng/resource-category/commercial-performance-factsheet/,
covering through March 2026) which would restore true monthly
granularity -- but these are image-based PDFs with no extractable
text, so pulling them requires OCR or manual transcription from the
published infographics, not a simple fetch.

DisCo name mapping note: NERC's quarterly reports abbreviate "Port
Harcourt" as "PH" and sometimes list Abuja/Benin/etc. by their AEDC/
BEDC-style acronyms in tables but by city name in prose. This script
uses the same DisCo name strings as master_discos_monthly.csv (city
names) so the two datasets join cleanly on DisCo.
"""

import csv
from pathlib import Path

OUT_PATH = Path(__file__).resolve().parent.parent / "data" / "processed" / "discos_recent_quarterly.csv"

# (DisCo, Year, Quarter, EnergyReceived_GWh, BillingEfficiency_pct, ATCC_Losses_pct, source_report)
Q4_2023_REPORT = "NERC 2023/Q4 Report (Table 5 & 7)"
Q1_2024_REPORT = "NERC 2024/Q1 Report (Table 5 & 7)"
Q3_2024_REPORT = "NERC 2024/Q3 Report (Table 5 & 7)"
Q4_2024_REPORT = "NERC 2024/Q4 Report (Table 5 & 7) - https://nerc.gov.ng/wp-content/uploads/2025/03/2024_Q4-Report.pdf"

ROWS = [
    # DisCo, Year, Quarter, EnergyReceived_GWh, BillingEfficiency_pct, ATCC_Losses_pct, source

    # ---- 2023/Q3 (from 2023/Q4 report's prior-quarter column) ----
    ("Abuja", 2023, 3, 1060.00, 73.21, 40.42, Q4_2023_REPORT),
    ("Benin", 2023, 3, 602.39, 85.91, 42.02, Q4_2023_REPORT),
    ("Eko", 2023, 3, 938.00, 88.06, 25.72, Q4_2023_REPORT),
    ("Enugu", 2023, 3, 582.59, 75.99, 41.21, Q4_2023_REPORT),
    ("Ibadan", 2023, 3, 894.46, 76.21, 44.98, Q4_2023_REPORT),
    ("Ikeja", 2023, 3, 1158.73, 86.92, 14.71, Q4_2023_REPORT),
    ("Jos", 2023, 3, 371.81, 81.45, 60.88, Q4_2023_REPORT),
    ("Kaduna", 2023, 3, 416.00, 52.99, 66.09, Q4_2023_REPORT),
    ("Kano", 2023, 3, 415.51, 70.35, 52.48, Q4_2023_REPORT),
    ("Port Harcourt", 2023, 3, 527.89, 83.18, 42.06, Q4_2023_REPORT),
    ("Yola", 2023, 3, 217.06, 81.23, 60.88, Q4_2023_REPORT),

    # ---- 2023/Q4 ----
    ("Abuja", 2023, 4, 1248.00, 70.83, 43.02, Q4_2023_REPORT),
    ("Benin", 2023, 4, 664.61, 85.19, 44.52, Q4_2023_REPORT),
    ("Eko", 2023, 4, 1039.00, 89.89, 24.40, Q4_2023_REPORT),
    ("Enugu", 2023, 4, 681.61, 74.73, 43.08, Q4_2023_REPORT),
    ("Ibadan", 2023, 4, 988.35, 80.95, 44.56, Q4_2023_REPORT),
    ("Ikeja", 2023, 4, 1231.92, 86.84, 17.50, Q4_2023_REPORT),
    ("Jos", 2023, 4, 425.75, 79.35, 62.84, Q4_2023_REPORT),
    ("Kaduna", 2023, 4, 545.90, 44.37, 72.93, Q4_2023_REPORT),
    ("Kano", 2023, 4, 531.11, 68.14, 58.16, Q4_2023_REPORT),
    ("Port Harcourt", 2023, 4, 577.83, 81.99, 42.64, Q4_2023_REPORT),
    ("Yola", 2023, 4, 264.57, 95.67, 63.79, Q4_2023_REPORT),

    # ---- 2024/Q1 ----
    ("Abuja", 2024, 1, 1119.00, 75.60, 36.98, Q1_2024_REPORT),
    ("Benin", 2024, 1, 575.95, 84.87, 35.17, Q1_2024_REPORT),
    ("Eko", 2024, 1, 964.00, 89.75, 22.61, Q1_2024_REPORT),
    ("Enugu", 2024, 1, 551.55, 80.46, 35.61, Q1_2024_REPORT),
    ("Ibadan", 2024, 1, 837.59, 85.54, 42.02, Q1_2024_REPORT),
    ("Ikeja", 2024, 1, 1117.83, 81.26, 15.81, Q1_2024_REPORT),
    ("Jos", 2024, 1, 395.62, 76.04, 53.76, Q1_2024_REPORT),
    ("Kaduna", 2024, 1, 443.90, 56.66, 59.96, Q1_2024_REPORT),
    ("Kano", 2024, 1, 440.32, 74.93, 52.73, Q1_2024_REPORT),
    ("Port Harcourt", 2024, 1, 531.01, 85.01, 37.39, Q1_2024_REPORT),
    ("Yola", 2024, 1, 213.19, 86.03, 62.36, Q1_2024_REPORT),

    # ---- 2024/Q2 (from 2024/Q3 report's prior-quarter column) ----
    ("Abuja", 2024, 2, 1089.00, 76.68, 36.13, Q3_2024_REPORT),
    ("Benin", 2024, 2, 563.05, 83.35, 31.36, Q3_2024_REPORT),
    ("Eko", 2024, 2, 942.00, 89.70, 21.03, Q3_2024_REPORT),
    ("Enugu", 2024, 2, 492.00, 95.33, 29.12, Q3_2024_REPORT),
    ("Ibadan", 2024, 2, 816.11, 88.75, 37.66, Q3_2024_REPORT),
    ("Ikeja", 2024, 2, 1136.83, 82.47, 21.93, Q3_2024_REPORT),
    ("Jos", 2024, 2, 332.68, 72.76, 52.44, Q3_2024_REPORT),
    ("Kaduna", 2024, 2, 442.67, 63.07, 61.76, Q3_2024_REPORT),
    ("Kano", 2024, 2, 444.34, 74.63, 56.19, Q3_2024_REPORT),
    ("Port Harcourt", 2024, 2, 531.25, 83.58, 35.15, Q3_2024_REPORT),
    ("Yola", 2024, 2, 124.46, 93.34, 48.04, Q3_2024_REPORT),

    # ---- 2024/Q3 ----
    ("Abuja", 2024, 3, 1124.76, 81.00, 36.13, Q3_2024_REPORT),
    ("Benin", 2024, 3, 694.32, 84.27, 31.80, Q3_2024_REPORT),
    ("Eko", 2024, 3, 983.24, 89.30, 24.62, Q3_2024_REPORT),
    ("Enugu", 2024, 3, 636.21, 74.98, 42.89, Q3_2024_REPORT),
    ("Ibadan", 2024, 3, 958.37, 89.98, 30.86, Q3_2024_REPORT),
    ("Ikeja", 2024, 3, 1130.67, 84.24, 29.78, Q3_2024_REPORT),
    ("Jos", 2024, 3, 428.92, 62.66, 66.81, Q3_2024_REPORT),
    ("Kaduna", 2024, 3, 446.37, 64.01, 70.84, Q3_2024_REPORT),
    ("Kano", 2024, 3, 475.98, 87.38, 59.82, Q3_2024_REPORT),
    ("Port Harcourt", 2024, 3, 560.41, 83.74, 41.70, Q3_2024_REPORT),
    ("Yola", 2024, 3, 167.57, 85.73, 57.05, Q3_2024_REPORT),

    # ---- 2024/Q4 ----
    ("Abuja", 2024, 4, 1163.25, 78.92, 40.43, Q4_2024_REPORT),
    ("Benin", 2024, 4, 764.99, 86.89, 29.47, Q4_2024_REPORT),
    ("Eko", 2024, 4, 1004.07, 89.20, 19.72, Q4_2024_REPORT),
    ("Enugu", 2024, 4, 649.53, 73.13, 41.35, Q4_2024_REPORT),
    ("Ibadan", 2024, 4, 966.20, 89.99, 30.30, Q4_2024_REPORT),
    ("Ikeja", 2024, 4, 1190.55, 84.41, 30.25, Q4_2024_REPORT),
    ("Jos", 2024, 4, 301.24, 81.04, 59.74, Q4_2024_REPORT),
    ("Kaduna", 2024, 4, 330.41, 70.87, 60.65, Q4_2024_REPORT),
    ("Kano", 2024, 4, 329.16, 83.39, 52.55, Q4_2024_REPORT),
    ("Port Harcourt", 2024, 4, 582.82, 86.31, 34.58, Q4_2024_REPORT),
    ("Yola", 2024, 4, 138.37, 89.83, 43.19, Q4_2024_REPORT),
]

HEADER = ["DisCo", "Year", "Quarter", "EnergyReceived_GWh", "BillingEfficiency_pct", "ATCC_Losses_pct", "source_report"]

if __name__ == "__main__":
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(HEADER)
        writer.writerows(ROWS)
    print(f"Wrote {len(ROWS)} rows ({len(ROWS)//11} quarters x 11 DisCos) to {OUT_PATH}")
    print("Covers: 2023/Q3, 2023/Q4, 2024/Q1, 2024/Q2, 2024/Q3")
    print("Known gap: 2022/Q4-2023/Q2 and 2024/Q4 onward not yet pulled.")
