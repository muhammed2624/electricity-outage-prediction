# Voltix — Electricity Outage Risk Predictor for Nigeria

A machine learning app that predicts electricity outage risk across all 11
Nigerian DisCo (electricity distribution company) territories, built on real
NERC operational and financial data. Built as a 3MTT capstone project.

## What it does

Voltix takes a location (state, then street/area) and a date, and returns a
predicted outage risk probability for that DisCo, backed by a trained
logistic regression model. The app also shows a historical trend chart and
the model's real evaluation metrics, so the prediction comes with context
instead of a bare number.

## Why this exists

Nigeria's power grid has well-documented reliability problems, but there is
no public per-feeder or per-area outage log to train a model on directly.
Voltix works around that by deriving a proxy risk label from two real,
regulator-published signals (energy received and technical/commercial
losses), and is upfront everywhere in the app and docs about what's real
data, what's a modeled proxy, and what's still an estimate.

## Project structure

- `data/raw/` — the two original NERC source workbooks.
- `data/raw_recent/` — placeholder for any newer raw source files.
- `data/processed/master_discos_monthly.csv` — cleaned, joined, labeled
  monthly dataset, Jan 2019 to Sep 2022, all 11 DisCos.
- `data/processed/discos_recent_quarterly.csv` — real NERC data extending
  coverage from 2023/Q3 through 2024/Q4 (quarterly, not monthly — see
  `DATA_NOTES.md` for why).
- `src/clean_data.py` — builds the monthly master dataset and the proxy
  outage-risk label from the raw NERC workbooks.
- `src/train_model.py` — trains the logistic regression model on lagged
  features, evaluates it against a naive baseline, saves the model artifacts.
- `src/build_registry.py` — builds `street_grid_registry.csv`, the original
  104-street hand-built seed street/area to DisCo lookup covering all 11
  DisCo territories.
- `src/build_street_index.py` — builds `expanded_street_index.csv`, a much
  larger (~7,850-street) real street/area index parsed directly from the
  `feeder_description` field of `discos_band_classification.csv`. This is
  what Step 1's search actually uses now; the seed registry is kept as a
  supplement/fallback.
- `src/build_recent_quarterly.py` — builds the real 2023-2024 quarterly
  data extension, sourced from NERC's published quarterly reports.
- `src/fetch_weather_features.py` / `src/fetch_holiday_features.py` /
  `src/merge_weather_holidays.py` — ready-to-run pipeline that pulls real
  historical weather (Open-Meteo) and public holiday (Nager.Date) data
  and merges it into the training set as new model features. **Not yet
  run** — needs a real internet connection these scripts document; see
  the "Real public data does exist" section of `DATA_NOTES.md`.
  `train_model.py` picks these features up automatically once run.
- `app/app.py` — the Streamlit app.
- `app/model/` — the four saved model artifacts (see below).
- `app/data/` — copies of the CSVs the app reads at runtime.
- `app/requirements.txt` — Python dependencies for deployment.
- `app/Dockerfile` — Hugging Face Spaces deployment config (not used by
  Streamlit Community Cloud, which reads `requirements.txt` directly).
- `DATA_NOTES.md` — what's real, what's a proxy, and what's still a gap in
  the data, written for the report's Limitations section.
- `notebooks/voltix_pipeline_walkthrough.ipynb` — runs the real pipeline
  end to end (clean data, train model, evaluate, build registry, build
  quarterly extension) by calling the actual `src/` functions/scripts, with
  real executed output saved in the notebook — nothing hardcoded.

## How the model works, briefly

There's no real outage log, so "outage risk" is a proxy label: a DisCo-month
is flagged high risk when either Energy Received drops sharply or ATC&C
Losses spike sharply, relative to that same DisCo's own trailing 3-month
trend (z-score threshold of 1.5). This keeps the comparison fair across
DisCos of very different sizes.

The model itself only sees lagged features (last month's and two months
ago's values, plus rolling trend stats) — never the same-month raw values
that built the label, so it can't just cheat by re-deriving the labeling
rule. It's trained on a time-based split (earliest ~80% of months for
training, most recent ~20% for testing), not a random split, since that's
how the model would actually be used.

## Evaluation results

On the held-out test set (88 samples, ~39% actually high-risk):

- Model: precision 0.66, recall 0.56, F1 0.60, accuracy 0.72
- Naive baseline (predict "same as last month"): precision 0.48, recall
  0.56, F1 0.51, accuracy 0.59

The model beats the naive baseline on every metric except recall, where
they're tied — meaning the model is meaningfully better at not crying wolf
(higher precision) while catching just as many real risk months.

## Data honesty, in one paragraph

Street/area search now covers ~7,950 streets across all 11 DisCo
territories: ~7,850 parsed directly from real NERC/DisCo feeder records
(`expanded_street_index.csv`, via `src/build_street_index.py`), plus the
original 104-street hand-built seed kept as a supplement. Real entries carry
their exact, source-cited Band and minimum-supply-hours data; seed entries
are estimated and clearly labeled as such. The risk model's training data
runs Jan 2019-Sep 2022; `discos_recent_quarterly.csv` adds real NERC data
through 2024/Q4 for context, though it isn't merged into the trained model
because of a monthly-vs-quarterly granularity mismatch. The live Band A-E
data (all 11 DisCos, July 2025 and later where available) is separate from
and more current than the risk model's training window. Full detail in
`DATA_NOTES.md`.

## Running it locally

From the `app/` folder:

    pip install -r requirements.txt
    streamlit run app.py

## Deployment

Target: **Streamlit Community Cloud**, connected via GitHub.

1. Push this repo to GitHub (any visibility Streamlit Cloud can read).
2. On [share.streamlit.io](https://share.streamlit.io), "New app" → pick
   the repo/branch → **Main file path: `outage_predictor/app/app.py`**
   (adjust the `outage_predictor/` prefix if your repo root sits one
   level differently than this zip's structure — the file itself must
   still be at `<repo root>/.../app/app.py`).
3. Streamlit Cloud auto-detects `app/requirements.txt` and
   `app/runtime.txt` (Python 3.11 pinned) from the same folder as the
   main file — nothing else to configure.
4. Deploy. First build takes a few minutes.

**`app/Dockerfile` and the Hugging-Face-style front matter in
`app/README.md` are for Hugging Face Spaces, not Streamlit Cloud —
Streamlit Cloud ignores both and reads `requirements.txt` directly.**
Harmless to leave in place if you might also deploy to HF Spaces later;
delete them if you want a cleaner repo for Streamlit Cloud only.

**If the deployed app errors on load with a model-loading message**
(the app now catches this explicitly instead of crashing silently): it
means the deployed scikit-learn/joblib version doesn't match what the
model was trained with. Either tighten the pins in
`app/requirements.txt` to match your training environment exactly, or
retrain in a fresh environment matching those pins
(`python src/train_model.py`) and redeploy.

## Rebuilding the data or model

If you get new NERC source data, or want to extend the registry or the
quarterly extension further:

    python src/clean_data.py            # rebuilds master_discos_monthly.csv
    python src/train_model.py           # retrains the model, saves artifacts
    python src/build_registry.py        # rebuilds street_grid_registry.csv
    python src/build_recent_quarterly.py  # rebuilds the quarterly extension

Each script prints a sanity check when it finishes (e.g. confirming every
DisCo in the registry matches the trained model's DisCo list).
