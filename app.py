import streamlit as st
import pandas as pd
import pickle
import numpy as np



def get_ms_sql_connection():
    import pyodbc
  
    conn_str = 'DRIVER={ODBC Driver 17 for SQL Server};SERVER=your_server;DATABASE=your_db;UID=your_user;PWD=your_password'
    return pyodbc.connect(conn_str)

# ── Page Config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Health Insurance Cost Estimator",
    page_icon="🩺",
    layout="wide"
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* Sidebar gizle */
[data-testid="stSidebar"],
[data-testid="stSidebarCollapseButton"]{
    display:none !important;
}

/* Genel arkaplan */
[data-testid="stAppViewContainer"]{
    background: #000000 !important;
}

[data-testid="stHeader"]{
    background:transparent;
}

.block-container{
    max-width:1200px;
    padding-top:2rem;
}

/* Header */
.page-header{
    text-align:center;
    margin-bottom:2.5rem;
}

.page-title{
    font-size:56px;
    font-weight:900;
    letter-spacing:-1px;
    background: linear-gradient(90deg, #0F766E, #14B8A6);
    -webkit-background-clip:text;
    -webkit-text-fill-color:transparent;
}

.page-sub{
    font-size:18px;
    color:#64748b;
}

/* Kartlar */
.section-card{
    background: rgba(255,255,255,0.06);
    backdrop-filter: blur(18px);
    border-radius:24px;
    padding:28px;
    margin-bottom:24px;
    border: 1px solid rgba(255,255,255,0.12);
    box-shadow: 0 10px 35px rgba(0,0,0,.35);
    transition:.3s;
}

.section-card:hover{
    transform:translateY(-3px);
}

.section-title{
    font-size:14px;
    font-weight:700;
    color:#0F766E;
    letter-spacing:.12em;
    text-transform:uppercase;
}

/* Butonlar */
div.stButton > button{
    width:100%;
    border:none;
    border-radius:16px;
    padding:15px;
    font-size:18px;
    font-weight:700;
    color:white;
    background: linear-gradient(135deg, #10B981, #059669);
    box-shadow: 0 10px 25px rgba(16,185,129,.25);
    transition:.3s;
}

div.stButton > button:hover{
    transform:translateY(-2px);
    box-shadow: 0 15px 35px rgba(16,185,129,.35);
}

/* Sonuç kartı */
.result-card{
    background: linear-gradient(135deg, #0F766E, #14B8A6);
    border-radius:20px;
    padding:20px 24px;
    width:100%;
    margin:20px 0;
    box-shadow: 0 10px 25px rgba(15,118,110,.18);
}

.result-label{
    color:#d1fae5;
    font-size:13px;
    text-transform:uppercase;
    letter-spacing:.15em;
}

.result-amount{
    color:white;
    font-size:44px;
    font-weight:800;
}

.result-monthly{
    color:#ecfdf5;
    font-size:18px;
}

.stNumberInput, .stSelectbox{
    border-radius:14px;
}
            
            label, p, span {
    color: #f1f5f9 !important;
}

.hero-title{
    font-size:52px;
    font-weight:900;
    color:white;
    line-height:1.1;
    letter-spacing:-1px;
    text-align:center;
}

.hero-highlight{
    background: linear-gradient(135deg, #10B981, #14B8A6, #06B6D4);
    -webkit-background-clip:text;
    -webkit-text-fill-color:transparent;
}

.hero-subtitle{
    margin-top:14px;
    font-size:18px;
    color:#cbd5e1;
    max-width:750px;
    margin-left:auto;
    margin-right:auto;
    line-height:1.6;
    text-align:center;
}
            
            [data-baseweb="input"] input {
    color: #6B7280 !important;
    font-weight: 600;
}

[data-baseweb="select"] span {
    color: #6B7280 !important;
    font-weight: 600;
}
</style>
""", unsafe_allow_html=True)

# ── 4. Load Model ────────────────────────────────────────────────────────────────
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

# ── Değişken Tanımlamaları (Hataları Önleyen Kısım) ───────────────────────────
# Pylance hatalarını çözmek için kolonları ve dil sözlüğünü tanımlıyoruz:
top_col1, top_col2 = st.columns([3, 1])

texts = {
    "English": {
        "height": "Height (cm)",
        "weight": "Weight (kg)",
        "children": "Number of Children",
        "smoke": "Do you smoke?",
        "region": "Region"
    },
    "Türkçe": {
        "height": "Boy (cm)",
        "weight": "Kilo (kg)",
        "children": "Çocuk Sayısı",
        "smoke": "Sigara kullanıyor musunuz?",
        "region": "Bölge"
    }
}

with top_col2:
    lang = st.selectbox("🌐 Language", options=["English", "Türkçe"], label_visibility="collapsed")

t = texts[lang]

with top_col1:
    st.markdown("""
    <span style='background:#374151;
    color:#FFFFFF;
    padding:6px 12px;
    border-radius:20px;
    font-size:12px;
    font-weight:700;'>
    ⚡ Gradient Boosting Model (R²: 0.89)
    </span>
    """, unsafe_allow_html=True)

# ── 6. Page Header ───────────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center; margin-top:30px;">
    <div class="hero-title">
        🩺 Health Insurance <span class="hero-highlight">Cost Estimator</span>
    </div>
    <div class="hero-subtitle">
        Predict insurance premiums instantly using machine learning and risk analytics.
    </div>
</div>
""", unsafe_allow_html=True)


# ── Form – Personal Info ──────────────────────────────────────────────────────
st.markdown('<div class="section-card"><div class="section-title">👤 Personal Information</div>', unsafe_allow_html=True)
col1, col2 = st.columns(2)
with col1:
    age = st.number_input("Age", min_value=18, max_value=100, value=25)
    sex = st.selectbox("Gender", options=["Male", "Female"])
with col2:
    height = st.number_input(t["height"], min_value=100, max_value=250, value=175, step=1)
    weight = st.number_input(t["weight"], min_value=30, max_value=250, value=70, step=1)
    
    height_m = height / 100.0
    calculated_bmi = weight / (height_m ** 2)
    bmi = float(np.clip(calculated_bmi, 10.0, 50.0))
    
    bmi_label = "Calculated BMI" if lang == "English" else "Hesaplanan BMI"
    st.info(f"🔢 {bmi_label}: **{bmi:.1f}**")
    
st.markdown('</div>', unsafe_allow_html=True)

# ── Form – Lifestyle ──────────────────────────────────────────────────────────
st.markdown('<div class="section-card"><div class="section-title">🌿 Lifestyle</div>', unsafe_allow_html=True)
col3, col4 = st.columns(2)
with col3:
    children = st.slider(
        t["children"],
        min_value=0,
        max_value=5,
        value=0
    )

with col4:
    smoker = st.selectbox(
        t["smoke"],
        options=["No", "Yes"]
    )

    region = st.selectbox(
        t["region"],
        options=["Northeast", "Northwest", "Southeast", "Southwest"]
    )
st.markdown('</div>', unsafe_allow_html=True)

# ── Prediction Function ───────────────────────────────────────────────────────
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
            DATASET_MIN = 1_121
            DATASET_MAX = 63_770
            progress_val = float(np.clip((result - DATASET_MIN) / (DATASET_MAX - DATASET_MIN), 0, 1))

            st.markdown(f"""
            <div class="result-card">
            <div class="result-label">Estimated Annual Cost</div>
            <div class="result-amount">${result:,.2f}</div>
            <div class="result-monthly">≈ ${monthly:,.2f} / month</div>
            </div>
            """, unsafe_allow_html=True)

            # ── Progress bar ──────────────────────────────────────────────────
            st.markdown("**Where does your estimate sit in the dataset?**")
            st.progress(progress_val,
                        text=f"${DATASET_MIN:,} (min) ──── your estimate: ${result:,.0f} ──── ${DATASET_MAX:,} (max)")

            # Personalized tips
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

# ── 11. MS SQL Veri Çekme Motoru & Tablo/Grafik Paneli ──────────────────────────
try:
    conn = get_ms_sql_connection()
    query = """
        SELECT age AS Age, height AS [Height (cm)], weight AS [Weight (kg)], 
               bmi AS BMI, gender AS Gender, children AS Children, 
               smoker AS Smoker, region AS Region, estimated_cost AS [Estimated Cost ($)] 
        FROM predictions 
        ORDER BY id DESC
    """
    history_df = pd.read_sql_query(query, conn)
    conn.close()
except Exception:
    history_df = pd.DataFrame()

if not history_df.empty:
    st.markdown("---")
    
    hist_title = "📊 Estimation History" if lang == "English" else "📊 Tahmin Geçmişi"
    hist_sub = "Below are the calculations made during this session:" if lang == "English" else "Bu oturumda yapılan hesaplamalar:"
    download_btn_lbl = "📥 Download History as CSV" if lang == "English" else "📥 Geçmişi CSV Olarak İndir"
    clear_btn_lbl = "🗑️ Clear History" if lang == "English" else "🗑️ Geçmişi Temizle"
    
    st.markdown(f"### {hist_title}")
    st.caption(hist_sub)

    # Canlı Metrik Kartları
    total_queries = len(history_df)
    avg_cost = history_df["Estimated Cost ($)"].mean() if total_queries > 0 else 0.0
    max_cost = history_df["Estimated Cost ($)"].max() if total_queries > 0 else 0.0

    m_col1, m_col2, m_col3 = st.columns(3)
    with m_col1:
        lbl_q = "Total Predictions" if lang == "English" else "Toplam Sorgulama"
        st.metric(lbl_q, f"{total_queries}")
    with m_col2:
        lbl_a = "Average Estimate" if lang == "English" else "Ortalama Tahmin"
        st.metric(lbl_a, f"${avg_cost:,.2f}")
    with m_col3:
        lbl_m = "Highest Estimate" if lang == "English" else "En Yüksek Tahmin"
        st.metric(lbl_m, f"${max_cost:,.2f}")

    st.markdown("<br>", unsafe_allow_html=True)
    st.dataframe(history_df, use_container_width=True)
    
    b_col1, b_col2 = st.columns([1, 1])
    with b_col1:
        csv_data = history_df.to_csv(index=False).encode('utf-8')
        st.download_button(label=download_btn_lbl, data=csv_data, file_name="insurance_predictions_history.csv", mime="text/csv")
        
    with b_col2:
        if st.button(clear_btn_lbl):
            try:
                conn = get_ms_sql_connection()
                cursor = conn.cursor()
                cursor.execute("TRUNCATE TABLE predictions")
                conn.commit()
                conn.close()
            except Exception:
                pass
            st.rerun()