import streamlit as st
import pandas as pd
import pickle
import numpy as np

# ── Page Config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Insurance Cost Estimator",
    page_icon="🏥",
    layout="centered"
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* ---- Global ---- */
[data-testid="stAppViewContainer"] {
    background-color: #f8faf9;
}
[data-testid="stHeader"] { background: transparent; }

/* ---- Sidebar ---- */
[data-testid="stSidebar"] {
    background-color: #ffffff;
    border-right: 1px solid #e0ede8;
}

/* ---- Buttons ---- */
div.stButton > button {
    background-color: #1D9E75;
    color: white;
    border: none;
    border-radius: 10px;
    padding: 0.65rem 1.5rem;
    font-size: 16px;
    font-weight: 600;
    width: 100%;
    transition: background 0.2s ease;
}
div.stButton > button:hover {
    background-color: #0F6E56;
    color: white;
}

/* ---- Section card ---- */
.section-card {
    background: #ffffff;
    border: 1px solid #d4ece3;
    border-radius: 14px;
    padding: 1.4rem 1.6rem 1rem;
    margin-bottom: 1.2rem;
}
.section-title {
    font-size: 13px;
    font-weight: 600;
    color: #0F6E56;
    text-transform: uppercase;
    letter-spacing: 0.07em;
    margin-bottom: 1rem;
    display: flex;
    align-items: center;
    gap: 6px;
}

/* ---- Result card ---- */
.result-card {
    background: linear-gradient(135deg, #e1f5ee 0%, #f0faf6 100%);
    border: 1px solid #5DCAA5;
    border-radius: 14px;
    padding: 1.6rem;
    margin: 1.2rem 0;
}
.result-label {
    font-size: 12px;
    font-weight: 600;
    color: #0F6E56;
    text-transform: uppercase;
    letter-spacing: 0.07em;
    margin-bottom: 6px;
}
.result-amount {
    font-size: 38px;
    font-weight: 700;
    color: #085041;
    line-height: 1.1;
}
.result-monthly {
    font-size: 15px;
    color: #1D9E75;
    margin-top: 4px;
    margin-bottom: 1rem;
}
.divider {
    height: 1px;
    background: #b2ddd0;
    margin: 1rem 0;
}
.model-pill {
    display: inline-block;
    background: #ffffff;
    border: 1px solid #b2ddd0;
    border-radius: 20px;
    padding: 4px 12px;
    font-size: 12px;
    color: #0F6E56;
}

/* ---- Driver cards ---- */
.drivers-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 10px;
    margin-top: 0.8rem;
}
.driver-card {
    background: #f8faf9;
    border: 1px solid #d4ece3;
    border-radius: 10px;
    padding: 12px 10px;
    text-align: center;
}
.driver-icon { font-size: 20px; margin-bottom: 4px; }
.driver-name { font-size: 12px; color: #6b7c74; margin-bottom: 4px; }
.driver-high  { font-size: 12px; font-weight: 600; color: #D85A30; }
.driver-med   { font-size: 12px; font-weight: 600; color: #BA7517; }
.driver-low   { font-size: 12px; font-weight: 600; color: #1D9E75; }

/* ---- Page header ---- */
.page-header {
    margin-bottom: 1.8rem;
}
.page-title {
    font-size: 28px;
    font-weight: 700;
    color: #085041;
    margin-bottom: 4px;
}
.page-sub {
    font-size: 15px;
    color: #6b7c74;
}
</style>
""", unsafe_allow_html=True)

# ── Load Model ────────────────────────────────────────────────────────────────
try:
    model = pickle.load(open('model.pkl', 'rb'))
    scaler = pickle.load(open('scaler.pkl', 'rb'))
    model_loaded = True
except FileNotFoundError:
    st.error("⚠️ Model or Scaler files could not be found!")
    model_loaded = False

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 📊 Model Info")
    st.markdown("---")
    st.metric("Algorithm", "Gradient Boosting")
    st.metric("R² Score", "0.89")
    st.metric("Features", "8")
    st.markdown("---")
    st.markdown("**Feature importance**")
    st.progress(0.95, text="🚬 Smoking")
    st.progress(0.60, text="🎂 Age")
    st.progress(0.40, text="⚖️ BMI")
    st.progress(0.20, text="👶 Children")
    st.progress(0.10, text="📍 Region")
    st.markdown("---")
    st.caption("Insurance Cost Estimator · Week 4")

# ── Page Header ───────────────────────────────────────────────────────────────
st.markdown("""
<div class="page-header">
  <div class="page-title">🏥 Insurance Cost Estimator</div>
  <div class="page-sub">Fill in the details below to get a personalized annual cost estimate.</div>
</div>
""", unsafe_allow_html=True)

# ── Form – Personal Info ──────────────────────────────────────────────────────
st.markdown('<div class="section-card"><div class="section-title">👤 Personal Information</div>', unsafe_allow_html=True)
col1, col2 = st.columns(2)
with col1:
    age = st.number_input("Age", min_value=18, max_value=100, value=25)
    sex = st.selectbox("Gender", options=["Male", "Female"])
with col2:
    bmi = st.number_input("BMI (Body Mass Index)", min_value=10.0, max_value=50.0, value=25.0, step=0.1)
    region = st.selectbox("Region", options=["Northeast", "Northwest", "Southeast", "Southwest"])
st.markdown('</div>', unsafe_allow_html=True)

# ── Form – Lifestyle ──────────────────────────────────────────────────────────
st.markdown('<div class="section-card"><div class="section-title">🌿 Lifestyle</div>', unsafe_allow_html=True)
col3, col4 = st.columns(2)
with col3:
    children = st.slider("Number of Children", min_value=0, max_value=5, value=0)
with col4:
    smoker = st.selectbox("Do You Smoke?", options=["No", "Yes"])
st.markdown('</div>', unsafe_allow_html=True)

# ── Prediction Function (unchanged logic) ─────────────────────────────────────
def predict_insurance(age, sex, bmi, children, smoker, region):
    numerical_inputs = np.array([[age, bmi]])
    scaled_numerical = scaler.transform(numerical_inputs)
    age_scaled = scaled_numerical[0][0]
    bmi_scaled = scaled_numerical[0][1]

    sex_val    = 1 if sex == "Female" else 0
    smoker_val = 1 if smoker == "Yes" else 0
    r_nw = 1 if region == "Northwest"  else 0
    r_se = 1 if region == "Southeast"  else 0
    r_sw = 1 if region == "Southwest"  else 0

    final_features = np.array([[age_scaled, sex_val, bmi_scaled, children, smoker_val, r_nw, r_se, r_sw]])
    return model.predict(final_features)[0]

# ── Predict Button ─────────────────────────────────────────────────────────────
if st.button("Predict my cost →"):
    if age <= 0 or bmi <= 0:
        st.error("Age and BMI must be greater than 0.")
    elif not model_loaded:
        st.error("Model files are missing — cannot predict.")
    else:
        with st.spinner("Calculating..."):
            result  = predict_insurance(age, sex, bmi, children, smoker, region)
            monthly = result / 12

            # ── Result Card ───────────────────────────────────────────────────
            # Cost range for the dataset (approximate min/max for progress bar)
            DATASET_MIN = 1_121
            DATASET_MAX = 63_770
            progress_val = float(np.clip((result - DATASET_MIN) / (DATASET_MAX - DATASET_MIN), 0, 1))

            st.markdown(f"""
            <div class="result-card">
              <div class="result-label">Estimated Annual Cost</div>
              <div class="result-amount">${result:,.2f}</div>
              <div class="result-monthly">≈ ${monthly:,.2f} / month</div>
              <div class="divider"></div>
              <span class="model-pill">📈 Gradient Boosting · R² 0.89</span>
            </div>
            """, unsafe_allow_html=True)

            # ── Progress bar: where does this person's cost sit? ──────────────
            st.markdown("**Where does your estimate sit in the dataset?**")
            st.progress(progress_val,
                        text=f"${DATASET_MIN:,} (min) ──── your estimate: ${result:,.0f} ──── ${DATASET_MAX:,} (max)")

            # ── Key Cost Drivers ──────────────────────────────────────────────
            st.markdown('<div class="section-card"><div class="section-title">💡 Key Cost Drivers</div>', unsafe_allow_html=True)
            st.markdown("""
            <div class="drivers-grid">
              <div class="driver-card">
                <div class="driver-icon">🚬</div>
                <div class="driver-name">Smoking</div>
                <div class="driver-high">High impact</div>
              </div>
              <div class="driver-card">
                <div class="driver-icon">🎂</div>
                <div class="driver-name">Age</div>
                <div class="driver-med">Medium impact</div>
              </div>
              <div class="driver-card">
                <div class="driver-icon">⚖️</div>
                <div class="driver-name">BMI</div>
                <div class="driver-low">Low–medium</div>
              </div>
            </div>
            """, unsafe_allow_html=True)

            # Personalized tip
            tips = []
            if smoker == "Yes":
                tips.append("🚬 Smoking is the single largest cost driver — it can multiply your premium by 3–4×.")
            if bmi > 30:
                tips.append(f"⚖️ Your BMI ({bmi:.1f}) is above 30. Reducing it can noticeably lower your premium.")
            if age > 50:
                tips.append("🎂 Premiums increase significantly after age 50 — consider locking in a plan early.")
            if tips:
                st.markdown("---")
                st.markdown("**Personalized tips for you:**")
                for tip in tips:
                    st.info(tip)

            st.markdown('</div>', unsafe_allow_html=True)