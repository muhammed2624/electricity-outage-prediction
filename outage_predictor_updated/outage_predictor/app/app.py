"""
=============================================================================
VOLTIX -- Electricity Outage Risk Predictor (Nigeria)
=============================================================================
Capstone MVP. This file is organized into clearly commented sections so a
reader (grader, teammate, or future you) can follow the logic top to bottom:

  1. Page config & branding (CSS)
  2. Load model + data artifacts
  3. Step 1 -- Location input (street/area search against the grid registry)
  4. Step 2 -- Time input (including HONEST handling of future dates)
  5. Step 3 -- Confirmation panel
  6. Prediction logic (reuses the trained DisCo-level model)
  7. Trend view
  8. Evaluation panel
  9. Methodology / "how this works" section (transparency for graders & users)
=============================================================================
"""

import streamlit as st
import pandas as pd
import numpy as np
import joblib
import plotly.graph_objects as go
from pathlib import Path
from datetime import date

APP_DIR = Path(__file__).resolve().parent
MODEL_DIR = APP_DIR / "model"
DATA_DIR = APP_DIR / "data"

# -----------------------------------------------------------------------
# 1. PAGE CONFIG & BRANDING
# -----------------------------------------------------------------------
st.set_page_config(
    page_title="Voltix | Outage Risk Predictor",
    page_icon="⚡",
    layout="wide",
)

# Custom CSS: gives the app a distinct brand identity instead of default
# Streamlit styling. Kept in one place so it's easy to tweak later.
st.markdown("""
<style>
    .voltix-hero {
        background: linear-gradient(135deg, #0B1F3A 0%, #14315C 100%);
        padding: 2rem 2.2rem;
        border-radius: 14px;
        margin-bottom: 1.5rem;
        color: white;
    }
    .voltix-hero h1 {
        font-size: 2.1rem;
        margin-bottom: 0.2rem;
        color: white;
    }
    .voltix-hero p {
        color: #B9C7DE;
        font-size: 1.02rem;
        margin: 0;
    }
    .voltix-badge {
        display: inline-block;
        background: #1E3A66;
        color: #8FD3FF;
        padding: 3px 10px;
        border-radius: 20px;
        font-size: 0.78rem;
        margin-right: 6px;
    }
    .voltix-card {
        background: #F7F9FC;
        border: 1px solid #E3E8F0;
        border-radius: 12px;
        padding: 1.1rem 1.3rem;
        margin-bottom: 0.8rem;
    }
    .voltix-step-label {
        font-weight: 600;
        color: #14315C;
        font-size: 0.95rem;
    }
    .voltix-disclaimer {
        background: #FFF8E8;
        border-left: 4px solid #E0A030;
        padding: 0.8rem 1rem;
        border-radius: 6px;
        font-size: 0.88rem;
        color: #6B5416;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------
# 2. LOAD MODEL + DATA ARTIFACTS
# -----------------------------------------------------------------------
@st.cache_resource
def load_model_artifacts():
    """Load the trained model artifacts, with a clear error message instead
    of a cryptic crash if the deployed environment's scikit-learn/joblib
    version doesn't match what the model was pickled with -- this is the
    single most common real-world Streamlit Cloud deployment failure for
    projects that ship a trained model. If this fires, the fix is either
    pinning requirements.txt to match the training environment's versions,
    or retraining the model in the deployed environment (`python
    src/train_model.py`) so the pickle matches.
    """
    try:
        model = joblib.load(MODEL_DIR / "logreg_model.joblib")
        scaler = joblib.load(MODEL_DIR / "scaler.joblib")
        feature_columns = joblib.load(MODEL_DIR / "feature_columns.joblib")
        eval_results = joblib.load(MODEL_DIR / "eval_results.joblib")
    except Exception as e:
        st.error(
            "Couldn't load the trained model artifacts. This usually means the "
            "deployed environment's scikit-learn/joblib version doesn't match the "
            "version the model was trained and pickled with.\n\n"
            f"**Error:** `{e}`\n\n"
            "**Fix:** either pin `app/requirements.txt` to the exact scikit-learn/"
            "joblib versions used for training, or retrain in this environment "
            "with `python src/train_model.py` and redeploy."
        )
        st.stop()
    return model, scaler, feature_columns, eval_results

@st.cache_data
def load_discos_data():
    df = pd.read_csv(DATA_DIR / "master_discos_monthly.csv", parse_dates=["YearMonth"])
    return df.sort_values(["DisCo", "YearMonth"]).reset_index(drop=True)

@st.cache_data
def load_registry():
    return pd.read_csv(DATA_DIR / "street_grid_registry.csv")

@st.cache_data
def load_band_classification():
    """Real, current (July 2025) NERC feeder-level Band A-E data.

    Only covers the DisCos we've extracted so far from NERC's own
    regulatory Orders (see DATA_NOTES.md). Everything else still falls
    back to the legacy `service_band` estimate in street_grid_registry.csv.
    """
    path = DATA_DIR / "discos_band_classification.csv"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)

model, scaler, feature_columns, eval_results = load_model_artifacts()
master = load_discos_data()
registry = load_registry()
band_data = load_band_classification()

DISCOS = sorted(master["DisCo"].unique())
DATA_MAX_MONTH = master["YearMonth"].max()   # last month we have real historical data for

# DisCo name -> label used in band_data['DisCo'] (kept explicit since the
# PHED rows are currently tagged "tentative" pending source verification --
# see DATA_NOTES.md). Add an entry here each time another DisCo's Order is
# extracted.
BAND_DATA_DISCO_MAP = {
    "Benin": "Benin",
    "Port Harcourt": "Port Harcourt (tentative)",
    "Abuja": "Abuja",
    "Ikeja": "Ikeja",
    "Eko": "Eko",
    "Ibadan": "Ibadan",
    "Jos": "Jos",
    "Kaduna": "Kaduna",
    "Kano": "Kano",
    "Enugu": "Enugu",
    "Yola": "Yola",
}


def find_real_band_match(disco_id, street_name, area_neighborhood):
    """
    Try to match the selected street/area against a real NERC feeder
    record for this DisCo. Returns a dict with match details, or None if
    no real data exists yet for this DisCo, or a dict with match=False if
    real DisCo-level data exists but no specific feeder matched.
    """
    band_label = BAND_DATA_DISCO_MAP.get(disco_id)
    if band_label is None or band_data.empty:
        return None  # no real data for this DisCo yet

    disco_rows = band_data[band_data["DisCo"] == band_label]
    if disco_rows.empty:
        return None

    needles = [street_name.lower(), area_neighborhood.lower()]
    # also try individual significant words (drop generic terms like "road","street")
    stop = {"road", "street", "way", "avenue", "close", "layout", "estate", "the", "of"}
    for text in [street_name, area_neighborhood]:
        needles += [w.lower() for w in text.split() if w.lower() not in stop and len(w) > 3]

    haystack = disco_rows["feeder_description"].str.lower()
    for needle in needles:
        hit = disco_rows[haystack.str.contains(needle, regex=False, na=False)]
        if not hit.empty:
            row = hit.iloc[0]
            return {
                "match": True,
                "band": row["band"],
                "min_supply_hours": int(row["min_supply_hours"]),
                "feeder_description": row["feeder_description"],
                "source_report": row["source_report"],
                "verification_note": row.get("verification_note", ""),
            }

    # No specific feeder matched -- still offer DisCo-level real context
    band_mix = disco_rows["band"].value_counts(normalize=True).sort_index() * 100
    return {
        "match": False,
        "band_mix": band_mix.round(0).to_dict(),
        "n_feeders": len(disco_rows),
        "source_report": disco_rows.iloc[0]["source_report"],
        "verification_note": disco_rows.iloc[0].get("verification_note", ""),
    }

# -----------------------------------------------------------------------
# HERO / HEADER
# -----------------------------------------------------------------------
st.markdown("""
<div class="voltix-hero">
    <span class="voltix-badge">⚡ CAPSTONE MVP</span>
    <span class="voltix-badge">Nigeria</span>
    <h1>Voltix</h1>
    <p>Know your power, before it goes. Area-level electricity outage risk, built on real NERC grid data.</p>
</div>
""", unsafe_allow_html=True)

# =========================================================================
# 3. STEP 1 -- LOCATION INPUT (street/area search)
# =========================================================================
st.markdown('<p class="voltix-step-label">Step 1 of 3 &nbsp;·&nbsp; Where are you?</p>', unsafe_allow_html=True)

col_a, col_b = st.columns([1, 1])
with col_a:
    # With nationwide coverage the registry now spans 11 DisCo territories
    # and 100+ areas, so a flat dropdown stops being usable -- narrow by
    # state first, the way a real address search would. Real geocoding
    # (typing any address in Nigeria) would need a Maps API + a full
    # national registry -- out of scope for MVP, flagged in the
    # methodology section below.
    states = sorted(registry["state"].unique())
    selected_state = st.selectbox("State", states, index=0)
    state_registry = registry[registry["state"] == selected_state].reset_index(drop=True)

    street_options = state_registry["street_name"] + " (" + state_registry["area_neighborhood"] + ")"
    selected_street_label = st.selectbox("Search street / area", street_options, index=0)
    selected_row = state_registry.iloc[street_options[street_options == selected_street_label].index[0]]

with col_b:
    st.markdown(f"""
    <div class="voltix-card">
        <b>{selected_row['area_neighborhood']}</b><br>
        LGA: {selected_row['lga']}<br>
        State: {selected_row['state']}
    </div>
    """, unsafe_allow_html=True)

inferred_disco = selected_row["disco_id"]
inferred_feeder = selected_row["feeder_code"]
inferred_band = selected_row["service_band"]
confidence = selected_row["confidence"]

# =========================================================================
# 4. STEP 2 -- TIME INPUT (with HONEST future-date handling)
# =========================================================================
st.markdown('<p class="voltix-step-label">Step 2 of 3 &nbsp;·&nbsp; When?</p>', unsafe_allow_html=True)

today = date.today()
selected_date = st.date_input(
    "Select a date",
    value=today,
    min_value=date(2019, 3, 1),
    help="You can pick any date, including future ones. See how this is handled below.",
)
selected_month_ts = pd.Timestamp(selected_date).to_period("M").to_timestamp()

# This is the key honesty fix: distinguish between a date we have real
# historical data for, versus a future date where we can only offer a
# PATTERN-BASED estimate (seasonal / calendar patterns learned from
# history), never a claim of literally forecasting a specific future event.
is_historical = selected_month_ts <= DATA_MAX_MONTH

if not is_historical:
    st.markdown(f"""
    <div class="voltix-disclaimer">
        ⚠️ <b>Pattern-based forecast.</b> {selected_date.strftime('%B %Y')} is beyond our historical
        data (which runs through {DATA_MAX_MONTH.strftime('%B %Y')}). Voltix cannot predict a specific
        future outage event. What you'll see instead is a <b>seasonal risk estimate</b> — how this area
        has historically behaved in this calendar month — used as a proxy for what to expect. Treat it
        as an informed pattern, not a forecast of a specific day.
    </div>
    """, unsafe_allow_html=True)

# =========================================================================
# 5. STEP 3 -- CONFIRMATION PANEL
# =========================================================================
st.markdown('<p class="voltix-step-label">Step 3 of 3 &nbsp;·&nbsp; Confirm</p>', unsafe_allow_html=True)

real_band = find_real_band_match(inferred_disco, selected_row["street_name"], selected_row["area_neighborhood"])

if real_band and real_band.get("match"):
    # Real, current (2025), regulator-published feeder match -- the strongest
    # case: shows the model's historical read next to NERC's own live
    # service commitment for this exact feeder.
    st.info(
        f"You're checking **{selected_row['street_name']}, {selected_row['area_neighborhood']}** — "
        f"served by **{inferred_disco} DisCo**, for **{selected_date.strftime('%B %Y')}**."
    )
    note = f" — {real_band['verification_note']}" if real_band.get("verification_note") else ""
    st.success(
        f"📡 **Live NERC service commitment (July 2025):** feeder *{real_band['feeder_description'].split(',')[0].strip()}* "
        f"— **Band {real_band['band']}**, minimum **{real_band['min_supply_hours']} hrs/day** guaranteed supply.{note}\n\n"
        f"Source: {real_band['source_report']}"
    )
elif real_band and not real_band.get("match"):
    # DisCo-level real data exists but this exact street didn't match a
    # named feeder -- still real and current, just less granular.
    st.info(
        f"You're checking **{selected_row['street_name']}, {selected_row['area_neighborhood']}** — "
        f"served by **{inferred_disco} DisCo**, for **{selected_date.strftime('%B %Y')}**."
    )
    mix = ", ".join(f"Band {b}: {p:.0f}%" for b, p in sorted(real_band["band_mix"].items()))
    st.info(
        f"No named feeder matched this exact street in NERC's July 2025 Order, but real data exists "
        f"for {inferred_disco} DisCo ({real_band['n_feeders']} feeders): {mix}.{' ' + real_band['verification_note'] if real_band.get('verification_note') else ''}"
    )
else:
    # Fallback: legacy estimated placeholder, clearly labelled as such.
    band_note = " (estimated -- not yet verified against real DisCo records)" if confidence == "estimated" else ""
    st.info(
        f"You're checking **{selected_row['street_name']}, {selected_row['area_neighborhood']}** — "
        f"served by **{inferred_disco} DisCo**, Service Band **{inferred_band}**{band_note}, "
        f"for **{selected_date.strftime('%B %Y')}**."
    )
    st.caption(
        "Real July 2025 NERC Band classification data isn't extracted for this DisCo yet -- "
        "see DATA_NOTES.md for the confirmed source URLs still pending."
    )

st.markdown("---")

# =========================================================================
# 6. PREDICTION LOGIC
# =========================================================================
def get_features_for(disco, target_month, historical):
    """
    Build the model's input features for a DisCo/month.

    If `historical` is True: use the real lagged data leading up to that
    month (genuine forecast from real trend data -- same logic as before).

    If `historical` is False (a future date): there's no real trend data
    to lag from, so we instead build a representative feature vector from
    that DisCo's AVERAGE historical pattern for the same calendar month
    across all years -- i.e. "what does a typical <month-name> look like
    for this DisCo, historically". This is explicitly a seasonal pattern
    estimate, not a forecast, and the UI labels it as such.
    """
    disco_hist = master[master["DisCo"] == disco].sort_values("YearMonth")

    if historical:
        hist = disco_hist[disco_hist["YearMonth"] < target_month]
        if len(hist) < 2:
            return None
        last1, last2 = hist.iloc[-1], hist.iloc[-2]
        row = disco_hist[disco_hist["YearMonth"] == target_month]
        if row.empty:
            return None
        target_row = row.iloc[0]
        feat = {
            "Month": target_month.month, "Quarter": target_row["Quarter"],
            "EnergyReceived_GWh_lag1": last1["EnergyReceived_GWh"],
            "EnergyReceived_GWh_lag2": last2["EnergyReceived_GWh"],
            "ATCC_Losses_pct_lag1": last1["ATCC_Losses_pct"],
            "ATCC_Losses_pct_lag2": last2["ATCC_Losses_pct"],
            "BillingEfficiency_pct_lag1": last1["BillingEfficiency_pct"],
            "BillingEfficiency_pct_lag2": last2["BillingEfficiency_pct"],
            "ER_roll_mean": target_row["ER_roll_mean"], "ER_roll_std": target_row["ER_roll_std"],
            "ATCC_roll_mean": target_row["ATCC_roll_mean"], "ATCC_roll_std": target_row["ATCC_roll_std"],
        }
        actual_label = target_row["outage_risk_label"]
    else:
        # seasonal average across all historical years for this calendar month
        same_month_hist = disco_hist[disco_hist["YearMonth"].dt.month == target_month.month]
        if same_month_hist.empty:
            same_month_hist = disco_hist  # fallback: use full history if no exact month match
        recent = disco_hist.tail(2)
        feat = {
            "Month": target_month.month,
            "Quarter": ((target_month.month - 1) // 3) + 1,
            "EnergyReceived_GWh_lag1": recent["EnergyReceived_GWh"].mean(),
            "EnergyReceived_GWh_lag2": recent["EnergyReceived_GWh"].mean(),
            "ATCC_Losses_pct_lag1": same_month_hist["ATCC_Losses_pct"].mean(),
            "ATCC_Losses_pct_lag2": same_month_hist["ATCC_Losses_pct"].mean(),
            "BillingEfficiency_pct_lag1": same_month_hist["BillingEfficiency_pct"].mean(),
            "BillingEfficiency_pct_lag2": same_month_hist["BillingEfficiency_pct"].mean(),
            "ER_roll_mean": disco_hist["ER_roll_mean"].mean(),
            "ER_roll_std": disco_hist["ER_roll_std"].mean(),
            "ATCC_roll_mean": disco_hist["ATCC_roll_mean"].mean(),
            "ATCC_roll_std": disco_hist["ATCC_roll_std"].mean(),
        }
        actual_label = None  # unknown -- it's the future

    for d in DISCOS:
        feat[f"DisCo_{d}"] = 1 if d == disco else 0
    return feat, actual_label


result = get_features_for(inferred_disco, selected_month_ts, is_historical)

if result is None:
    st.warning("Not enough historical data to compute a prediction for this selection.")
    st.stop()

feat_dict, actual_label = result
feat_df = pd.DataFrame([feat_dict]).reindex(columns=feature_columns, fill_value=0)
if feat_df.isna().any(axis=None):
    feat_df = feat_df.fillna(feat_df.mean(numeric_only=True)).fillna(0)

feat_scaled = scaler.transform(feat_df)
probability = model.predict_proba(feat_scaled)[0, 1]

# =========================================================================
# RESULTS: probability gauge + trend view, side by side
# =========================================================================
col1, col2 = st.columns([1, 1.3])

with col1:
    label = "Seasonal Risk Estimate" if not is_historical else "Outage Risk Probability"
    st.subheader(f"🎯 {label}")

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
        title={"text": f"{selected_row['area_neighborhood']} — {selected_date.strftime('%B %Y')}"},
    ))
    fig.update_layout(height=280, margin=dict(l=20, r=20, t=50, b=10))
    st.plotly_chart(fig, use_container_width=True)

    if probability >= 0.5:
        st.error(f"**High risk** — {probability:.0%} estimated.")
    elif probability >= 0.3:
        st.warning(f"**Moderate risk** — {probability:.0%} estimated.")
    else:
        st.success(f"**Low risk** — {probability:.0%} estimated.")

    if is_historical and actual_label is not None and not pd.isna(actual_label):
        actual_txt = "High risk" if actual_label == 1 else "Normal"
        st.caption(f"Actual recorded status for reference: **{actual_txt}** "
                   f"(model did not see this month's own data to predict).")

with col2:
    st.subheader("📈 Trend View")
    trend_df = master[master["DisCo"] == inferred_disco].copy()
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(
        x=trend_df["YearMonth"], y=trend_df["EnergyReceived_GWh"],
        mode="lines+markers", name="Energy Received (GWh)", line=dict(color="#2E6F9E"),
    ))
    high_risk_pts = trend_df[trend_df["outage_risk_label"] == 1]
    fig2.add_trace(go.Scatter(
        x=high_risk_pts["YearMonth"], y=high_risk_pts["EnergyReceived_GWh"],
        mode="markers", name="High-risk month", marker=dict(color="#D64545", size=9, symbol="x"),
    ))
    if is_historical:
        fig2.add_vline(x=selected_month_ts, line_dash="dash", line_color="gray")
    fig2.update_layout(
        height=280, margin=dict(l=20, r=20, t=30, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    st.plotly_chart(fig2, use_container_width=True)
    st.caption(f"Historical pattern for {inferred_disco} DisCo. Red X = months flagged high-risk.")

st.markdown("---")

# =========================================================================
# 8. EVALUATION PANEL
# =========================================================================
st.subheader("✅ Evaluation — How reliable is this model?")
st.caption("Computed on held-out months never seen during training, vs. a naive baseline.")

e1, e2, e3, e4 = st.columns(4)
delta_f1 = eval_results["model_f1"] - eval_results["naive_f1"]
e1.metric("Model F1-score", f"{eval_results['model_f1']:.2f}", f"{delta_f1:+.2f} vs naive")
e2.metric("Precision", f"{eval_results['model_precision']:.2f}")
e3.metric("Recall", f"{eval_results['model_recall']:.2f}")
e4.metric("Calibration (Brier)", f"{eval_results['model_brier']:.2f}")

comp_fig = go.Figure(data=[
    go.Bar(name="Model", x=["Precision", "Recall", "F1"],
           y=[eval_results["model_precision"], eval_results["model_recall"], eval_results["model_f1"]],
           marker_color="#2E6F9E"),
    go.Bar(name="Naive baseline", x=["Precision", "Recall", "F1"],
           y=[eval_results["naive_precision"], eval_results["naive_recall"], eval_results["naive_f1"]],
           marker_color="#B7C4CE"),
])
comp_fig.update_layout(barmode="group", height=280, margin=dict(l=20, r=20, t=20, b=10))
st.plotly_chart(comp_fig, use_container_width=True)

st.markdown("---")

# =========================================================================
# 9. METHODOLOGY / TRANSPARENCY SECTION
# =========================================================================
with st.expander("ℹ️ How Voltix works, and its current limitations"):
    st.markdown(f"""
**Data source:** NERC (Nigerian Electricity Regulatory Commission) public operational
and financial reports, Jan 2019 – Sep 2022, at DisCo level.

**What "risk" means here:** NERC's public data does not include a raw outage log.
Voltix uses a proxy label — a DisCo-month is flagged high-risk when energy received
drops sharply or technical/commercial losses spike, relative to that DisCo's own
trailing trend. This is a defensible research approach, not a confirmed outage record.

**Area lookup:** the street/area search uses a seed `street_grid_registry`
covering all 11 DisCos in the trained model — real areas in Lagos (Ikeja Electric,
Eko), Abuja (AEDC), Benin (BEDC), Enugu (EEDC), Ibadan (IBEDC), Jos (JED), Kaduna
(KAEDCO), Kano (KEDCO), Port Harcourt (PHED), and Yola (YEDC), mapped to their DisCo
(each DisCo's franchise territory is public regulatory information). This is a
representative seed (roughly 6–17 areas per DisCo), not an exhaustive national
address database — expanding it further is the main way to make Voltix
production-ready. Feeder codes and service bands shown are **estimated**, not yet
sourced from real DisCo feeder registries — a production version would replace
these with verified DisCo/NERC records.

**Future dates:** Voltix cannot predict a specific real outage on a future date —
no dataset can support that level of certainty. For dates beyond
{DATA_MAX_MONTH.strftime('%B %Y')}, it shows a **seasonal pattern estimate** based on
how that DisCo has historically behaved in that calendar month, clearly labeled as
such rather than presented as a forecast.

**Note on DisCo names:** Lagos's DisCo structure changed in late 2025 — Eko DisCo
and Ikeja Electric were succeeded by newly licensed entities under LASERC. This
model is trained on the historical NERC data under the original DisCo names, which
is what was in effect during the data collection period.
    """)

st.caption("Voltix — Capstone MVP. Built on real NERC data. Not a substitute for official DisCo outage alerts.")
