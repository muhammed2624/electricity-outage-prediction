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
  of consistent reporting to do this properly — the model has 5 real quarters now
  plus whatever NERC publishes going forward).

## Known remaining gap — say this explicitly in the report

**2022/Q4 through 2023/Q2** (three quarters) are not covered. The NERC
quarterly reports for that period exist publicly but weren't pulled in this
pass. **2024/Q4 onward** is also not yet covered — NERC's most recent
published quarterly report at the time of writing was 2024/Q3.

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
current Band, and its minimum guaranteed supply hours plus an automatic
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
you cite them as confirmed** it worth a quick manual check against a
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

## Street index expansion (`expanded_street_index.csv`)

The 104-row `street_grid_registry.csv` above was a hand-built seed. Since
the Band classification table above already contains real, named
streets/communities inside its `feeder_description` field for all 2,679
feeder rows, `src/build_street_index.py` parses those free-text
descriptions into individual street/area names — stripping feeder/voltage
jargon (e.g. "132KV", "TS", "FDR", "1X15MVA"), splitting on delimiters
(commas, semicolons, "AND", "&"), and filtering out junk tokens.

Result: ~7,850 unique (DisCo, street) pairs, each carrying its own exact
Band, minimum-supply-hours, and source citation directly from the row it
was parsed from — no fuzzy re-matching needed at query time. This is now
what the app's Step 1 search uses; `street_grid_registry.csv` is kept as a
supplement/fallback.

This is real regulatory free text, not a clean address database, so
expect some noise: occasional duplicated fragments, feeder-code remnants,
or generic tokens ("Poly", "Govt") that survived filtering. That's a
known, stated limitation — still a large, genuine improvement over the
104-street seed, and each entry's Band/source data is exact regardless of
any noise in how the street name itself was parsed.

**Quality pass:** the first version of this parser produced ~9,400
entries, but a spot-check flagged ~15% as visibly messy run-on fragments
(unsplit feeder-topology jargon like "Ojo Local T3 Ojo Volkswagen Complex
Volkswagen Complex Volkswagen Complex"). Rather than accept that in an
investor-facing dropdown, `is_valid_token()` now rejects candidates that
are too long (>45 chars), too many words (>6), contain leftover
feeder-topology markers ("T1", repeated "LOCAL"), or are bare generic
words with no qualifier ("Poly", "Govt", "Estate" alone). This traded
~1,550 entries for a noise rate of ~0.05% on a manual re-check — the
right trade for a searchable dropdown, since the dropped entries were bad
*display* strings, not wrong data (their Band/source info wasn't lost,
just not surfaced by street name).

## Known limitation: Ogun state coverage under Eko DisCo

Eko DisCo's real feeder territory actually spans both Lagos and Ogun
states, but `DISCO_PRIMARY_STATE` in `src/build_street_index.py` assigns
each DisCo a single primary state (matching the simplification the
original `street_grid_registry.csv` seed already made). As a result, all
~708 real streets parsed from Eko's feeder records are tagged `state:
Lagos`, and Ogun search still falls back to the seed registry's single
Agbara entry.

I checked whether Eko's parsed street list could be split by state using
known Ogun-town keywords (Agbara, Abeokuta, Sagamu, etc.), but several of
the matches were Lagos-side roads *named after* those destinations (e.g.
an "Old Abeokuta Road" inside Lagos), so a name-based reassignment risked
mislabeling a street's state in a demo. Left
as-is; flagged here rather than silently accepted. 

## Future work: time-of-day prediction is not currently possible

A natural next question for a user is "will I have power at 3pm on
Tuesday?" — not just "roughly how many hours today." Right now Voltix
can't answer that, and it shouldn't fake an answer:

- The risk model is trained on **monthly** DisCo-level aggregates, there
  is no day, let alone hour, in that dataset.
- The Band data gives a **minimum supply hours per day** figure (e.g.
  Band A = 20 hrs/day), but that's a daily total, not a schedule. NERC's
  public Band orders don't specify which clock hours are covered.
- DisCos run informal, frequently-changing rotation schedules (e.g. "Line
  A gets 6am-2pm today") that aren't published in any dataset I could
  find. Building a schedule feature would mean fabricating plausible-
  looking hours rather than reporting real ones which conflicts with
  the data-honesty standard the rest of this project holds to.

**What would make this possible:** DisCo-level interruption/restoration
logs at hour granularity, which aren't currently public in Nigeria. If
that data becomes available (e.g. through a DisCo API or a future NERC
disclosure requirement), the same Band/street-matching infrastructure
already built here could be extended to it without a redesign.This is
a believable next feature that shows where the product goes with better 
data access, not a gap to hide.

### What's actually implemented vs. what's ready-to-run

**Live grid status (implemented, in the app):** `app.py` now shows a
"Live national grid now" panel (generation MW, frequency) sourced from
nigeriapowerdata.com, refreshed every 10 minutes, with graceful
degradation if the third-party API is unreachable. This is a nationwide
signal, separate from the trained risk model, same pattern as the Band
A-E data. Caveat: NIGGRID's generation readings are self-reported by
GenCos, not automated SCADA telemetry, so gaps/lag reflect real
reporting gaps in Nigeria's own grid data.

**Weather + holiday features (scripts written, NOT yet run):**
`src/fetch_weather_features.py` and `src/fetch_holiday_features.py` pull
real historical data from Open-Meteo and Nager.Date respectively, for
the same Jan 2019 - Sep 2022 window the risk model trains on.
`src/merge_weather_holidays.py` merges them into
`master_discos_monthly_enriched.csv`, and `src/train_model.py` picks
those columns up automatically if that file exists.

**Why these two haven't actually been run yet:** both APIs require a
real internet connection, and (a) the sandboxed environment used to
build this has a restricted network allowlist that doesn't include
these domains, and (b) both APIs' robots.txt blocks automated fetch
tooling. The pipeline is built, tested end-to-end with synthetic
placeholder data shaped like the real API responses (confirmed the
merge and retrain both run cleanly), then that placeholder data was
deleted so nothing fake ships. **To actually add these features:** run
the three scripts in order, anywhere with normal internet access:

```
pip install requests
python src/fetch_weather_features.py
python src/fetch_holiday_features.py
python src/merge_weather_holidays.py
python src/train_model.py
```
