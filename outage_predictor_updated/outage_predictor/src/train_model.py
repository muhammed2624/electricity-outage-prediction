"""
Train a baseline outage-risk forecasting model.

IMPORTANT DESIGN DECISION: the model must predict a DisCo-month's risk
label using only information available BEFORE that month (lagged
values, rolling trend stats). It must NOT see that same month's raw
EnergyReceived/ATCC readings, because those were used to construct the
label itself -- feeding them back in would let the model trivially
re-learn the labeling rule instead of genuinely forecasting.

Split strategy: time-based, not random. We train on the earlier ~80%
of months and test on the most recent ~20%, per DisCo. This mirrors
how the model would actually be used (forecast the future from the
past) and avoids leaking future information into training.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    precision_score, recall_score, f1_score, accuracy_score,
    brier_score_loss, confusion_matrix
)
import joblib

PROC_DIR = Path(__file__).resolve().parent.parent / "data" / "processed"
MODEL_DIR = Path(__file__).resolve().parent.parent / "app" / "model"
MODEL_DIR.mkdir(parents=True, exist_ok=True)

TEST_FRACTION = 0.2  # most recent 20% of months per DisCo held out for testing

# Weather/holiday columns added by src/merge_weather_holidays.py, once
# src/fetch_weather_features.py and src/fetch_holiday_features.py have
# been run somewhere with real internet access (see those scripts).
# Training automatically picks these up if the enriched file exists;
# otherwise it falls back to the original DisCo-only feature set, so
# this script always runs even before that data has been pulled.
WEATHER_HOLIDAY_COLS = [
    "rainfall_mm_sum", "heavy_rain_days", "windspeed_max_kmh",
    "temp_max_c", "temp_min_c", "holiday_count",
]
ENRICHED_CSV = PROC_DIR / "master_discos_monthly_enriched.csv"


def load_master():
    if ENRICHED_CSV.exists():
        print(f"Using enriched training data (with weather/holiday features): {ENRICHED_CSV.name}")
        df = pd.read_csv(ENRICHED_CSV, parse_dates=["YearMonth"])
        use_weather = True
    else:
        print(
            "No master_discos_monthly_enriched.csv found -- training on DisCo-only "
            "features. Run fetch_weather_features.py + fetch_holiday_features.py + "
            "merge_weather_holidays.py (with real internet access) to add weather/"
            "holiday features."
        )
        df = pd.read_csv(PROC_DIR / "master_discos_monthly.csv", parse_dates=["YearMonth"])
        use_weather = False
    return df.sort_values(["DisCo", "YearMonth"]).reset_index(drop=True), use_weather


def build_features(df, use_weather):
    """Lagged-only features so the model genuinely forecasts, not reconstructs the label."""
    df = df.copy()

    for col in ["EnergyReceived_GWh", "ATCC_Losses_pct", "BillingEfficiency_pct"]:
        df[f"{col}_lag1"] = df.groupby("DisCo")[col].shift(1)
        df[f"{col}_lag2"] = df.groupby("DisCo")[col].shift(2)

    # trailing trend stats are already lagged by construction (shift(1) inside rolling)
    keep_cols = [
        "DisCo", "YearMonth", "Month", "Quarter",
        "EnergyReceived_GWh_lag1", "EnergyReceived_GWh_lag2",
        "ATCC_Losses_pct_lag1", "ATCC_Losses_pct_lag2",
        "BillingEfficiency_pct_lag1", "BillingEfficiency_pct_lag2",
        "ER_roll_mean", "ER_roll_std", "ATCC_roll_mean", "ATCC_roll_std",
        "outage_risk_label",
    ]
    if use_weather:
        # Weather/holidays describe conditions DURING the month itself, not
        # a lag -- that's fine here (unlike EnergyReceived/ATCC, they are
        # not used to construct the label, so no leakage risk).
        keep_cols[-1:-1] = WEATHER_HOLIDAY_COLS
    df = df[keep_cols].dropna()
    return df


def naive_baseline_predictions(df):
    """Naive baseline: predict this month's label = last month's actual label."""
    df = df.copy()
    df["naive_pred"] = df.groupby("DisCo")["outage_risk_label"].shift(1)
    return df["naive_pred"]


def time_based_split(df):
    train_idx, test_idx = [], []
    for disco, grp in df.groupby("DisCo"):
        grp = grp.sort_values("YearMonth")
        n_test = max(1, int(len(grp) * TEST_FRACTION))
        train_idx.extend(grp.index[:-n_test])
        test_idx.extend(grp.index[-n_test:])
    return df.loc[train_idx], df.loc[test_idx]


def main():
    master, use_weather = load_master()
    feat_df = build_features(master, use_weather)

    # attach naive baseline prediction (needs the label history, so compute before split)
    feat_df = feat_df.reset_index(drop=True)
    feat_df["naive_pred"] = naive_baseline_predictions(
        master.set_index(["DisCo", "YearMonth"]).loc[
            list(zip(feat_df["DisCo"], feat_df["YearMonth"]))
        ].reset_index()
    ).values

    feat_df = feat_df.dropna(subset=["naive_pred"])  # first labeled month per DisCo has no prior label

    train_df, test_df = time_based_split(feat_df)

    feature_cols = [
        "Month", "Quarter",
        "EnergyReceived_GWh_lag1", "EnergyReceived_GWh_lag2",
        "ATCC_Losses_pct_lag1", "ATCC_Losses_pct_lag2",
        "BillingEfficiency_pct_lag1", "BillingEfficiency_pct_lag2",
        "ER_roll_mean", "ER_roll_std", "ATCC_roll_mean", "ATCC_roll_std",
    ]
    if use_weather:
        feature_cols += WEATHER_HOLIDAY_COLS

    # one-hot encode DisCo
    train_X = pd.get_dummies(train_df[feature_cols + ["DisCo"]], columns=["DisCo"])
    test_X = pd.get_dummies(test_df[feature_cols + ["DisCo"]], columns=["DisCo"])
    test_X = test_X.reindex(columns=train_X.columns, fill_value=0)

    train_y = train_df["outage_risk_label"]
    test_y = test_df["outage_risk_label"]

    scaler = StandardScaler()
    train_X_scaled = scaler.fit_transform(train_X)
    test_X_scaled = scaler.transform(test_X)

    model = LogisticRegression(max_iter=1000, class_weight="balanced")
    model.fit(train_X_scaled, train_y)

    pred_proba = model.predict_proba(test_X_scaled)[:, 1]
    pred_label = model.predict(test_X_scaled)

    naive_pred = test_df["naive_pred"]

    print("="*60)
    print(f"Train months: {len(train_df)}  |  Test months: {len(test_df)}")
    print(f"Test set positive rate: {test_y.mean():.2%}")
    print("="*60)
    print("\nMODEL performance:")
    print(f"  Precision: {precision_score(test_y, pred_label):.3f}")
    print(f"  Recall:    {recall_score(test_y, pred_label):.3f}")
    print(f"  F1:        {f1_score(test_y, pred_label):.3f}")
    print(f"  Accuracy:  {accuracy_score(test_y, pred_label):.3f}")
    print(f"  Brier score (calibration, lower=better): {brier_score_loss(test_y, pred_proba):.3f}")

    print("\nNAIVE BASELINE (predict = last month's actual label) performance:")
    print(f"  Precision: {precision_score(test_y, naive_pred, zero_division=0):.3f}")
    print(f"  Recall:    {recall_score(test_y, naive_pred, zero_division=0):.3f}")
    print(f"  F1:        {f1_score(test_y, naive_pred, zero_division=0):.3f}")
    print(f"  Accuracy:  {accuracy_score(test_y, naive_pred):.3f}")

    print("\nConfusion matrix (model):")
    print(confusion_matrix(test_y, pred_label))

    # save model artifacts for the Streamlit app
    joblib.dump(model, MODEL_DIR / "logreg_model.joblib")
    joblib.dump(scaler, MODEL_DIR / "scaler.joblib")
    joblib.dump(list(train_X.columns), MODEL_DIR / "feature_columns.joblib")

    # save evaluation results for the evaluation panel in the app
    eval_results = {
        "model_precision": precision_score(test_y, pred_label),
        "model_recall": recall_score(test_y, pred_label),
        "model_f1": f1_score(test_y, pred_label),
        "model_accuracy": accuracy_score(test_y, pred_label),
        "model_brier": brier_score_loss(test_y, pred_proba),
        "naive_precision": precision_score(test_y, naive_pred, zero_division=0),
        "naive_recall": recall_score(test_y, naive_pred, zero_division=0),
        "naive_f1": f1_score(test_y, naive_pred, zero_division=0),
        "naive_accuracy": accuracy_score(test_y, naive_pred),
        "test_set_size": len(test_df),
        "test_positive_rate": test_y.mean(),
        "used_weather_holiday_features": use_weather,
    }
    joblib.dump(eval_results, MODEL_DIR / "eval_results.joblib")
    print(f"\nSaved model + evaluation results to {MODEL_DIR}")


if __name__ == "__main__":
    main()
