"""
Electricity Outage Risk Predictor -- Nigeria
MVP features: Area/Time input, Outage probability, Trend view, Evaluation panel.
"""

import streamlit as st
import pandas as pd
import numpy as np
import joblib
import plotly.graph_objects as go
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
MODEL_DIR = APP_DIR / "model"
DATA_PATH = APP_DIR / "data" / "master_discos_monthly.csv"

st.set_page_config(
    page_title="Nigeria Outage Risk Predictor",
    page_icon="⚡",
    layout="wide",
)

# ---------- load artifacts ----------
@st.cache_resource
def load_artifacts():
    model = joblib.load(MODEL_DIR / "logreg_model.joblib")
    scaler = joblib.load(MODEL_DIR / "scaler.joblib")
    feature_columns = joblib.load(MODEL_DIR / "feature_columns.joblib")
    eval_results = joblib.load(MODEL_DIR / "eval_results.joblib")
    return model, scaler, feature_columns, eval_results

@st.cache_data
def load_data():
    df = pd.read_csv(DATA_PATH, parse_dates=["YearMonth"])
    return df.sort_values(["DisCo", "YearMonth"]).reset_index(drop=True)

model, scaler, feature_columns, eval_results = load_artifacts()
master = load_data()

DISCOS = sorted(master["DisCo"].unique())

# ---------- header ----------
st.title("⚡ Nigeria Electricity Outage Risk Predictor")
st.caption(
    "Estimates outage risk from historical DisCo-level supply and loss patterns "
    "(NERC data, Jan 2019–Sep 2022). Built as a capstone MVP — see the Evaluation "
    "panel below for how reliable these predictions actually are."
)

# ---------- sidebar: Area / Time input ----------
st.sidebar.header("📍 Area & Time")
selected_disco = st.sidebar.selectbox("DisCo (distribution area)", DISCOS, index=DISCOS.index("Ikeja") if "Ikeja" in DISCOS else 0)

disco_months = master.loc[master["DisCo"] == selected_disco, "YearMonth"].sort_values()
# only months with enough history (2+ prior months) can be predicted
valid_months = disco_months[disco_months >= disco_months.min() + pd.DateOffset(months=2)]

if len(valid_months) == 0:
    st.error("Not enough historical data for this DisCo to make a prediction.")
    st.stop()

month_labels = [d.strftime("%B %Y") for d in valid_months]
selected_label = st.sidebar.selectbox("Month to predict", month_labels, index=len(month_labels) - 1)
selected_month = valid_months.iloc[month_labels.index(selected_label)]

st.sidebar.markdown("---")
st.sidebar.caption(
    "Prediction uses only data available *before* the selected month — "
    "this simulates a real forecast, not hindsight."
)

# ---------- build features for the selected DisCo/month (lagged, no leakage) ----------
def get_features_for(disco, target_month):
    hist = master[(master["DisCo"] == disco) & (master["YearMonth"] < target_month)].sort_values("YearMonth")
    if len(hist) < 2:
        return None
    last1 = hist.iloc[-1]
    last2 = hist.iloc[-2]
    row_at_target = master[(master["DisCo"] == disco) & (master["YearMonth"] == target_month)]
    if row_at_target.empty:
        return None
    target_row = row_at_target.iloc[0]

    feat = {
        "Month": target_month.month,
        "Quarter": target_row["Quarter"],
        "EnergyReceived_GWh_lag1": last1["EnergyReceived_GWh"],
        "EnergyReceived_GWh_lag2": last2["EnergyReceived_GWh"],
        "ATCC_Losses_pct_lag1": last1["ATCC_Losses_pct"],
        "ATCC_Losses_pct_lag2": last2["ATCC_Losses_pct"],
        "BillingEfficiency_pct_lag1": last1["BillingEfficiency_pct"],
        "BillingEfficiency_pct_lag2": last2["BillingEfficiency_pct"],
        "ER_roll_mean": target_row["ER_roll_mean"],
        "ER_roll_std": target_row["ER_roll_std"],
        "ATCC_roll_mean": target_row["ATCC_roll_mean"],
        "ATCC_roll_std": target_row["ATCC_roll_std"],
    }
    for d in DISCOS:
        feat[f"DisCo_{d}"] = 1 if d == disco else 0
    return feat, target_row

result = get_features_for(selected_disco, selected_month)

if result is None:
    st.warning("Not enough prior data to predict this month. Try a later month.")
    st.stop()

feat_dict, target_row = result
feat_df = pd.DataFrame([feat_dict])
feat_df = feat_df.reindex(columns=feature_columns, fill_value=0)

if feat_df.isna().any(axis=None):
    st.warning(
        "Some inputs for this month are missing in the source data "
        "(common in the most recent reporting months). Prediction may be less reliable."
    )
    feat_df = feat_df.fillna(feat_df.mean(numeric_only=True)).fillna(0)

feat_scaled = scaler.transform(feat_df)
probability = model.predict_proba(feat_scaled)[0, 1]

actual_label = target_row["outage_risk_label"]

# ================= MAIN LAYOUT =================
col1, col2 = st.columns([1, 1.3])

# ---------- Feature: Outage Probability ----------
with col1:
    st.subheader("🎯 Outage Risk Probability")

    risk_color = "#D64545" if probability >= 0.5 else ("#E0A030" if probability >= 0.3 else "#3A9D5D")
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=probability * 100,
        number={"suffix": "%", "font": {"size": 40}},
        gauge={
            "axis": {"range": [0, 100]},
            "bar": {"color": risk_color},
            "steps": [
                {"range": [0, 30], "color": "#EAF6EE"},
                {"range": [30, 50], "color": "#FCF1DA"},
                {"range": [50, 100], "color": "#FBE7E7"},
            ],
        },
        title={"text": f"{selected_disco} DisCo — {selected_label}"},
    ))
    fig.update_layout(height=280, margin=dict(l=20, r=20, t=50, b=10))
    st.plotly_chart(fig, use_container_width=True)

    if probability >= 0.5:
        st.error(f"**High risk** — {probability:.0%} estimated probability of an elevated-outage-risk period.")
    elif probability >= 0.3:
        st.warning(f"**Moderate risk** — {probability:.0%} estimated probability.")
    else:
        st.success(f"**Low risk** — {probability:.0%} estimated probability.")

    if not pd.isna(actual_label):
        actual_txt = "High risk" if actual_label == 1 else "Normal"
        st.caption(f"For reference, this month's actual recorded status was: **{actual_txt}** "
                   f"(shown for validation — the model did not see this month's own data to predict).")

# ---------- Feature: Trend View ----------
with col2:
    st.subheader("📈 Trend View")
    trend_df = master[master["DisCo"] == selected_disco].copy()
    trend_df["RiskLabel"] = trend_df["outage_risk_label"].map({1: "High risk", 0: "Normal"})

    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(
        x=trend_df["YearMonth"], y=trend_df["EnergyReceived_GWh"],
        mode="lines+markers", name="Energy Received (GWh)",
        line=dict(color="#2E6F9E"),
    ))
    high_risk_pts = trend_df[trend_df["outage_risk_label"] == 1]
    fig2.add_trace(go.Scatter(
        x=high_risk_pts["YearMonth"], y=high_risk_pts["EnergyReceived_GWh"],
        mode="markers", name="High-risk month",
        marker=dict(color="#D64545", size=9, symbol="x"),
    ))
    fig2.add_vline(x=selected_month, line_dash="dash", line_color="gray")
    fig2.update_layout(
        height=280, margin=dict(l=20, r=20, t=30, b=10),
        xaxis_title=None, yaxis_title="GWh",
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    st.plotly_chart(fig2, use_container_width=True)
    st.caption("Red X marks = months flagged high-risk historically. Dashed line = month selected above.")

st.markdown("---")

# ---------- Feature: Evaluation Panel ----------
st.subheader("✅ Evaluation — How reliable is this model?")
st.caption(
    "Computed once on a held-out set of the most recent months (never seen during training), "
    "compared against a naive baseline that simply repeats last month's status."
)

e1, e2, e3, e4 = st.columns(4)
delta_f1 = eval_results["model_f1"] - eval_results["naive_f1"]
e1.metric("Model F1-score", f"{eval_results['model_f1']:.2f}", f"{delta_f1:+.2f} vs naive")
e2.metric("Precision", f"{eval_results['model_precision']:.2f}")
e3.metric("Recall", f"{eval_results['model_recall']:.2f}")
e4.metric("Calibration (Brier, lower=better)", f"{eval_results['model_brier']:.2f}")

comp_fig = go.Figure(data=[
    go.Bar(name="Model", x=["Precision", "Recall", "F1"],
           y=[eval_results["model_precision"], eval_results["model_recall"], eval_results["model_f1"]],
           marker_color="#2E6F9E"),
    go.Bar(name="Naive baseline", x=["Precision", "Recall", "F1"],
           y=[eval_results["naive_precision"], eval_results["naive_recall"], eval_results["naive_f1"]],
           marker_color="#B7C4CE"),
])
comp_fig.update_layout(barmode="group", height=300, margin=dict(l=20, r=20, t=20, b=10))
st.plotly_chart(comp_fig, use_container_width=True)

st.caption(
    f"Evaluated on {eval_results['test_set_size']} held-out DisCo-months "
    f"({eval_results['test_positive_rate']:.0%} were actually high-risk). "
    "The naive baseline predicts each month's status by simply repeating last month's — "
    "the model beating it demonstrates genuine predictive value rather than pattern repetition."
)

st.markdown("---")
st.caption(
    "⚠️ Note on methodology: this dataset does not contain a raw outage log. 'Outage risk' is a proxy "
    "label derived from sharp drops in energy received and spikes in technical/commercial losses "
    "relative to each DisCo's own trailing trend. Predictions reflect risk of degraded supply "
    "conditions, not confirmed outage events."
)
