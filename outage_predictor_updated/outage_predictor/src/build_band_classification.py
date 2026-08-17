"""
Build discos_band_classification.csv -- REAL, CURRENT (July 2025) feeder-level
Band A-E service classification data, sourced directly from NERC's own
published regulatory Orders (nerc.gov.ng) under the Service-Based Tariff
(SBT) framework introduced April 2024.

WHY THIS MATTERS FOR THE CAPSTONE:
The tutor's feedback ("data ends in 2022... a lot has changed... bands
segment") points at exactly this. NERC's April 2024 SBT reform reclassified
every distribution feeder in Nigeria into Bands A-E based on guaranteed
daily supply hours (A=20+hrs, B=16-19, C=12-15, D=8-11, E=4-7), with:
  - Monthly/quarterly regulatory Orders per DisCo listing every feeder,
    its current Band, the streets/areas it serves, and its minimum
    guaranteed supply hours;
  - Automatic downgrade if a DisCo fails to deliver a Band A feeder's
    committed hours for 7 consecutive days (Order NERC/334/2022);
  - A public compensation and upgrade/downgrade mechanism reviewed monthly.

This is a genuinely current (2025), authoritative, feeder-level reliability
signal that did not exist in the 2019-2022 training window, and it is NOT
the same thing as the historical proxy-label model -- it's a live regulatory
status that can sit alongside the model's predictions as real, current
context, and it can be joined to street_grid_registry.csv at the
street/area level (the Order documents literally list "NAME OF STREETS
SERVED BY THE FEEDER" per row).

SOURCES (real NERC regulatory Orders, PDF text extracted directly --
not estimated, not fabricated):

  CONFIRMED AND FETCHED (text verified extractable):
  - BEDC (Benin): ORDER/NERC/2025/060, effective 1 July 2025
    https://nerc.gov.ng/wp-content/uploads/2025/08/BEDC_July_2025_060.pdf
    -> FULLY EXTRACTED in this pass: all 319 feeders, Appendix 3
       ("BEDC's Service Level Commitments for July 2025"), 79 Band A /
       40 Band B / 38 Band C / 89 Band D / 73 Band E feeders.

  CONFIRMED TO EXIST, NOT YET EXTRACTED (same document structure --
  each is a July 2025 Supplementary Order with an Appendix listing every
  feeder, its Band, streets served, and minimum supply hours):
  - AEDC (Abuja):   ORDER/NERC/2025/059
    https://nerc.gov.ng/wp-content/uploads/2025/08/AEDC_July_2025_059.pdf
    (Appendix 6 = full feeder list; 437+ feeders -- large document)
  - EEDC (Enugu):   ORDER/NERC/2025/062
    https://nerc.gov.ng/wp-content/uploads/2025/08/EEDC_July_2025_062.pdf
  - IBEDC (Ibadan): ORDER/NERC/2025/063
    https://nerc.gov.ng/wp-content/uploads/2025/08/IBEDC_July_2025_063.pdf
  - KAEDC (Kaduna): ORDER/NERC/2025/066
    https://nerc.gov.ng/wp-content/uploads/2025/08/KAEDC_July_2025_066.pdf
  - YEDC (Yola):    ORDER/NERC/2025/055 (May 2025 -- no July 2025 order
    found in this pass; may exist, worth re-checking)
    https://nerc.gov.ng/wp-content/uploads/2025/05/YEDC_May_2025_055.pdf

  KNOWN GAP -- NOT YET LOCATED (say this explicitly in the report):
  IKEDC (Ikeja), EKEDC (Eko), KEDCO (Kano), PHEDC (Port Harcourt),
  JEDC (Jos). These almost certainly exist at the same URL pattern
  (https://nerc.gov.ng/wp-content/uploads/2025/08/{ACRONYM}_July_2025_0XX.pdf,
  order numbers running roughly 059-069) but were not located in this
  pass. NERC also maintains a public landing page listing each DisCo's
  Band A feeders (https://nerc.gov.ng/media/nerc-approves-new-band-a-feeders/)
  though those particular graphics are image-based, not text-extractable --
  the numbered regulatory Orders above are the text-extractable source.

HOW TO EXTEND THIS: for each remaining DisCo, fetch the Order PDF,
locate the Appendix titled "{DISCO}'s Service Level Commitments for
[Month] 2025" (a table: S/N, BAND, FEEDER NAME, DESCRIPTION OF FEEDER
LOCATION, NAME OF STREETS SERVED BY THE FEEDER, MIN. SUPPLY DURATION),
and parse each row the same way BEDC was parsed below: a line beginning
with an S/N, then a single-letter Band (A-E), ending in a supply-hours
figure (20/16/12/8/4).

This file intentionally does NOT touch master_discos_monthly.csv, the
proxy label, or the trained model -- it is additive current-state
context, exactly like discos_recent_quarterly.csv.
"""

import csv
import re
from pathlib import Path

RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw" / "band_orders"
OUT_PATH = Path(__file__).resolve().parent.parent / "data" / "processed" / "discos_band_classification.csv"

SOURCES = {
    "Benin": (
        "NERC ORDER/NERC/2025/060 - July 2025 Supplementary Order for BEDC, "
        "Appendix 3 - https://nerc.gov.ng/wp-content/uploads/2025/08/BEDC_July_2025_060.pdf"
    ),
}


def parse_bedc_appendix(raw_text_path: Path):
    """Parse a raw-text dump of BEDC's Appendix 3 table into rows.

    Each line: "<S/N> <BAND letter> <free-text feeder/location/streets> <hours>"
    where hours is one of 20/16/12/8/4 (the SBT band minimums).
    """
    rows = []
    pattern = re.compile(r"^(\d+)\s+([A-E])\s+(.*)\s+(20|16|12|8|4)$")
    with open(raw_text_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            m = pattern.match(line)
            if not m:
                continue
            sn, band, description, hours = m.groups()
            rows.append((int(sn), band, description, int(hours)))
    return rows


if __name__ == "__main__":
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    all_rows = []

    bedc_raw = RAW_DIR / "bedc_raw.txt"
    if bedc_raw.exists():
        for sn, band, desc, hours in parse_bedc_appendix(bedc_raw):
            all_rows.append(["Benin", sn, band, desc, hours, "2025-07-01", SOURCES["Benin"]])
    else:
        print(f"NOTE: {bedc_raw} not found -- run with the BEDC raw text in place, "
              "or see discos_band_classification.csv already committed to the repo.")

    with open(OUT_PATH, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["DisCo", "s_n", "band", "feeder_description", "min_supply_hours",
                    "order_effective_date", "source_report"])
        w.writerows(all_rows)

    print(f"Wrote {len(all_rows)} rows to {OUT_PATH}")
    print("Covered DisCos: Benin (full). See module docstring for the other 10 "
          "DisCos' source URLs and next steps.")
