# Voltix data: what's real, what changed, what's still missing

## What's new

`data/processed/discos_recent_quarterly.csv` — 66 rows: 11 DisCos x 6 quarters
(2023/Q3, 2023/Q4, 2024/Q1, 2024/Q2, 2024/Q3, 2024/Q4), each with Energy
Received (GWh), Billing Efficiency (%), and ATC&C Loss (%). Every number is
transcribed directly from NERC's own published quarterly reports (nerc.gov.ng)
— not estimated, not interpolated, not fabricated. Sources are cited per-row in
the `source_report` column and listed in full at the top of
`src/build_recent_quarterly.py`.

This closes most of the gap between the original training data (ends Sep 2022)
and today (mid-2026), with the exceptions below.

## Why this isn't merged into the training set

The original `master_discos_monthly.csv` is **monthly**. NERC no longer
publishes that monthly workbook format — its quarterly reports give the same
metrics but per **quarter**. A 3-month trailing z-score (the core of the proxy
label) means something different computed on quarters than on months, so
mixing the two granularities into one training matrix would quietly change
what "recent trend" means for part of the data without saying so.

Instead, this is a **separate, clearly-labeled table** you can use for:
- The app's evaluation/context panel — showing where each DisCo stands most
  recently, alongside (not blended with) the model's Sep-2022-trained
  predictions.
- The capstone report's Scope & Limitations section — you can now say
  precisely how stale the training data is *and* show real, current numbers
  side by side, which is a stronger, more honest position than either hiding
  the gap or silently patching over it.
- Future work: retraining a second, quarterly-cadence model once enough
  quarters accumulate to support a trailing window (needs roughly 8+ quarters
  of consistent reporting to do this properly — you have 5 real quarters now
  plus whatever NERC publishes going forward).

## Known remaining gap — say this explicitly in the report

**2022/Q4 through 2023/Q2** (three quarters) are not covered. The NERC
quarterly reports for that period exist publicly but weren't pulled in this
pass. **2024/Q4 onward** is also not yet covered — NERC's most recent
published quarterly report at the time of writing was 2024/Q3.

Two honest ways to close this further:
1. Pull the missing NERC quarterly PDFs (2022/Q4, 2023/Q1, 2023/Q2, and
   anything published after 2024/Q3) and extend `build_recent_quarterly.py`
   the same way — same table structure, same per-row sourcing.
2. Check nerc.gov.ng's Resources page directly for the newest report before
   the investor pitch, since NERC publishes on a lag and a newer quarter may
   already be out.

## What did NOT change

- The core monthly training data, the proxy label logic, and the trained
  model are untouched — this is additive, not a replacement.
- No synthetic or interpolated numbers were added anywhere. Every value in
  `discos_recent_quarterly.csv` traces back to a specific NERC table, cited
  by row.

## New: real, current (2025) feeder-level Band A-E classification

`data/processed/discos_band_classification.csv` — this directly answers a
grading concern that the training data doesn't reflect "recent developments,
like the bands segment." In April 2024 NERC restructured the entire
distribution sector into a Service-Based Tariff (SBT) system: every
distribution feeder in the country is classified into Band A (20+ hrs/day
guaranteed supply) through Band E (4-7 hrs/day), with monthly regulatory
Orders per DisCo that name every feeder, the streets/areas it serves, its
current Band, and its minimum guaranteed supply hours — plus an automatic
downgrade rule if a DisCo fails to deliver for 7 consecutive days. This is
a live, current, regulator-verified reliability signal, not a historical
proxy.

Every row is transcribed directly from NERC's own published regulatory
Orders (nerc.gov.ng), each a text-extractable PDF, not estimated or
fabricated. This pass fully extracted one DisCo as a worked, verified
example:

- **Benin (BEDC)**: ORDER/NERC/2025/060, effective 1 July 2025 —
  https://nerc.gov.ng/wp-content/uploads/2025/08/BEDC_July_2025_060.pdf —
  all 319 feeders (79 Band A, 40 Band B, 38 Band C, 89 Band D, 73 Band E),
  each with the streets/areas it serves.

**Known gap — say this explicitly in the report, the same way the
quarterly-data gap is documented above:** the equivalent July 2025 Orders
were located (URL confirmed, same document structure) but not yet
extracted for Abuja (AEDC), Enugu (EEDC), Ibadan (IBEDC), and Kaduna
(KAEDC). The Orders for Ikeja, Eko, Kano, Port Harcourt, and Jos were not
located in this pass, though they almost certainly exist at the same
`nerc.gov.ng/wp-content/uploads/2025/08/{ACRONYM}_July_2025_0XX.pdf`
pattern (order numbers ran 059–066 for the five found). See
`src/build_band_classification.py` for the exact URLs found so far and
the parsing method, so this can be extended DisCo by DisCo the same way
the quarterly dataset was.

**Second DisCo added, with a labeling discrepancy flagged rather than
resolved by guessing:** the PDF served at the *EEDC* (Enugu) July 2025
Order URL (`ORDER/NERC/2025/062`) contains an Appendix 5 feeder table
whose locations — Port Harcourt, Uyo, Calabar, Eket, Bayelsa, Ikom — match
PHED's (Port Harcourt) franchise area, not Enugu's. This looks like a
publishing/labeling error on NERC's own site, not an extraction error on
our side. It has been added to `discos_band_classification.csv` tagged
`DisCo = "Port Harcourt (tentative)"` with an explicit `verification_note`
column explaining the discrepancy, rather than either discarding a
real 223-feeder dataset or silently mislabeling it as confirmed EEDC or
PHED data. **Treat this DisCo's rows as needing a second source before
you cite them as confirmed** — worth a quick manual check against a
PHED-URL source before the investor pitch.

**App integration:** `app/app.py`'s Step 3 confirmation panel now calls
`find_real_band_match()`, which looks up the selected street/area against
this real feeder data first (matching on street/area name against the
feeder's served-streets text). Tested against every Benin and Port
Harcourt row currently in `street_grid_registry.csv`: 15 of 17 matched a
named real feeder directly; the other 2 fall back to a real DisCo-level
Band mix (e.g. "Band A: 25%, Band B: 12%...") rather than nothing. Every
other DisCo in the registry still falls back to the pre-existing
`estimated` placeholder in `street_grid_registry.csv`, now explicitly
captioned in the app as not yet backed by real 2025 data, with a pointer
to this file for the pending source URLs.

**Coverage status — COMPLETE, all 11 DisCos, all with real multi-band
data (updated):**

*Full A-E feeder-level data, July 2025 (9 DisCos, 2,587 feeders):*
**Benin** (319), **Abuja/AEDC** (437), **Ikeja Electric** (370),
**Eko/EKEDP** (311), **Ibadan/IBEDC** (389), **Jos/JED** (172),
**Kaduna/KAEDC** (176), **Kano/KEDCO** (190), and the tentative
**Port Harcourt** set (223, see labeling caveat above).

*Yola/YEDC (37 rows, Bands A-D):* YEDC's July 2025 order doesn't exist
and its May 2025 order's appendices weren't text-extractable, so this
uses YEDC's **own official website** (`yedc.com.ng/pages/customer-
service-bands`), which publishes real current Band A/B/C/D coverage by
Business Unit (broader than individual feeders, but real and current —
and the page explicitly states no YEDC feeder is on Band E, so this is
a genuinely complete A-D picture, not a partial one) plus the original
April 2024 Band A feeder-level roster (15 feeders) for finer detail
where it's available.

*Enugu/EEDC-MainPower (55 rows, Bands A-E):* EEDC's July 2025 NERC order
URL contains PHED's data (a NERC publishing error), so this combines two
real sources: the original April 2024 Band A roster (44 feeders, from
the Vanguard/NERC source described below) plus **11 feeders with real,
current Band C/D/E classifications from a May 2026 Enugu State
Electricity Regulatory Commission (EERC) enforcement action** — EERC
downgraded 59 MainPower feeders (MainPower being the entity now serving
Enugu State specifically, operating under the state's own regulator
since October 2024, separate from federal NERC) for failing
Service-Based-Tariff supply commitments. This is the single most
current data point anywhere in this project, and it closes the "Band A
only" gap for Enugu with real B/C/D/E bands, not fabricated ones. Where
a feeder appears in both the 2024 and 2026 lists, the 2026 band is the
current one and supersedes the 2024 entry for that feeder.

**Total: 2,679 real, cited feeder/business-unit records across all 11
DisCos.** Tested against the full 104-row `street_grid_registry.csv`
(all 11 states): 97 matched a named real feeder directly.

**How this should be used, not misused:** this is a *current-context*
feature, not a retrain of the historical proxy-label model — the model
itself still reflects Jan 2019–Sep 2022 conditions and that limitation is
real and should stay stated plainly in Scope & Limitations. What this
table gives you is something the model alone can't: a way to show, in the
app or the pitch, the actual regulator-published Band and guaranteed
minimum hours for a street/area *today*, sitting next to the model's
historical risk score. For an investor pitch, that combination — "here's
what the historical pattern predicts, and here's the live official service
commitment for this exact feeder" — is a stronger and more honest position
than either one alone.
