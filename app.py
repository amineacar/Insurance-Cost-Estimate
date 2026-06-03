import streamlit as st
import pandas as pd
import pickle
import numpy as np
from languages import texts

# ── Page Config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Insurance Cost Estimator",
    page_icon="🏥",
    layout="centered"
)

# ── Session State Initialization (Tahmin Geçmişi Hafızası) ────────────────────
if "prediction_history" not in st.session_state:
    st.session_state.prediction_history = pd.DataFrame(columns=[
        "Age", "Height (cm)", "Weight (kg)", "BMI", "Gender", "Children", "Smoker", "Region", "Estimated Cost ($)"
    ])

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* Sol taraftaki açılır kapanır sidebar'ı ve okunu tamamen görünmez yap */
[data-testid="stSidebar"], [data-testid="stSidebarCollapseButton"] {
    display: none !important;
}

<style>
/* ---- Global ---- */
[data-testid="stAppViewContainer"] {
    background-color: #f8faf9;
}
[data-testid="stHeader"] { background: transparent; }

/* ---- Sidebar ---- */
            

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


# ── Language Selection ────────────────────────────────────────────────────────
lang = st.sidebar.selectbox("🌐 Language / Dil", options=["English", "Türkçe"])



# Seçilen dile göre aktif metin setini atıyoruz
t = texts[lang]

# ── Top Bar (Language & Quick Info) ──────────────────────────────────────────
# Sayfanın en üstüne yan yana iki kolon açıyoruz
top_col1, top_col2 = st.columns([4, 1])

with top_col2:
    # Dil seçimi artık sol barda değil, sağ üst köşede kibar bir kutu olarak duracak
    lang = st.selectbox("🌐 Language", options=["English", "Türkçe"], label_visibility="collapsed")

# languages.py dosyasından aktif metinleri çekme kuralımız aynen kalıyor
from languages import texts
t = texts[lang]

with top_col1:
    # Sol üst köşeye el yapımı hissi veren küçük bir model künyesi koyuyoruz
    st.markdown("""
    <span style='background: #f1f5f9; color: #475569; padding: 4px 10px; border-radius: 20px; font-size: 12px; font-weight: 500;'>
      ⚡ Gradient Boosting Model (R²: 0.89)
    </span>
    """, unsafe_allow_html=True)

# ── Page Header ───────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="page-header">
  <div class="page-title">{t["page_title"]}</div>
  <div class="page-sub">{t["page_sub"]}</div>
</div>
""", unsafe_allow_html=True)
# ── Form – Personal Info ──────────────────────────────────────────────────────
# ── Form – Personal Info ──────────────────────────────────────────────────────
st.markdown(f'<div class="section-card"><div class="section-title">{t["personal_info"]}</div>', unsafe_allow_html=True)
col1, col2 = st.columns(2)
with col1:
    # İlki etiket (label) kısmıdır. Oraya t["age"] ve t["gender"] verdik
    age = st.number_input(t["age"], min_value=18, max_value=100, value=25, step=1)
    sex = st.selectbox(t["gender"], options=["Male", "Female"])
with col2:
    height = st.number_input(t["height"], min_value=100, max_value=250, value=175, step=1)
    weight = st.number_input(t["weight"], min_value=30, max_value=250, value=70, step=1)
    
    height_m = height / 100.0
    calculated_bmi = weight / (height_m ** 2)
    bmi = float(np.clip(calculated_bmi, 10.0, 50.0))
    
    # Bilgi kutusunun içindeki yazıyı da dile göre değiştiriyoruz
    bmi_label = "Calculated BMI" if lang == "English" else "Hesaplanan BMI"
    st.info(f"🔢 {bmi_label}: **{bmi:.1f}**")
    
    region = st.selectbox(t["region"], options=["Northeast", "Northwest", "Southeast", "Southwest"])
st.markdown('</div>', unsafe_allow_html=True)
# ── Form – Lifestyle ──────────────────────────────────────────────────────────
# ── Form – Lifestyle ──────────────────────────────────────────────────────────
st.markdown(f'<div class="section-card"><div class="section-title">{t["lifestyle"]}</div>', unsafe_allow_html=True)
col3, col4 = st.columns(2)
with col3:
    children = st.slider(t["children"], min_value=0, max_value=5, value=0)
with col4:
    smoker = st.selectbox(t["smoke"], options=["No", "Yes"])
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
    # Geliştirme 3: Hatalı veya mantıksız veri girişine karşı backend doğrulama kontrolü
    if age < 18 or bmi < 10.0:
        st.error("⚠️ Age must be 18+ and BMI must be greater than 10.")
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
              <div class="divider"></div>
              <span class="model-pill">📈 Gradient Boosting · R² 0.89</span>
            </div>
            """, unsafe_allow_html=True)

            # Yeni tahmin verilerini bir sözlük olarak hazırlıyoruz
            new_record = {
                "Age": age,
                "Height (cm)": height,
                "Weight (kg)": weight,
                "BMI": round(bmi, 2),
                "Gender": sex,
                "Children": children,
                "Smoker": smoker,
                "Region": region,
                "Estimated Cost ($)": round(float(result), 2)
            }
            
            # Yeni kaydı mevcut geçmiş tablosuna ekliyoruz
            st.session_state.prediction_history = pd.concat([
                st.session_state.prediction_history, 
                pd.DataFrame([new_record])
            ], ignore_index=True)

            # ── Progress bar: where does this person's cost sit? ──────────────
            st.markdown("**Where does your estimate sit in the dataset?**")
            st.progress(progress_val,
                        text=f"${DATASET_MIN:,} (min) ──── your estimate: ${result:,.0f} ──── ${DATASET_MAX:,} (max)")

            # ── Key Cost Drivers ──────────────────────────────────────────────
            # ── Key Cost Drivers ──────────────────────────────────────────────
            st.markdown(f'<div class="section-card"><div class="section-title">{t["drivers_title"]}</div>', unsafe_allow_html=True)
            
            # Dile göre kart içindeki etiketleri dinamik yapıyoruz
            smk_lbl = "Smoking" if lang == "English" else "Sigara"
            age_lbl = "Age" if lang == "English" else "Yaş"
            imp_high = "High impact" if lang == "English" else "Yüksek etki"
            imp_med = "Medium impact" if lang == "English" else "Orta etki"
            imp_low = "Low–medium" if lang == "English" else "Düşük-Orta"

            st.markdown(f"""
            <div class="drivers-grid">
              <div class="driver-card">
                <div class="driver-icon">🚬</div>
                <div class="driver-name">{smk_lbl}</div>
                <div class="driver-high">{imp_high}</div>
              </div>
              <div class="driver-card">
                <div class="driver-icon">🎂</div>
                <div class="driver-name">{age_lbl}</div>
                <div class="driver-med">{imp_med}</div>
              </div>
              <div class="driver-card">
                <div class="driver-icon">⚖️</div>
                <div class="driver-name">BMI</div>
                <div class="driver-low">{imp_low}</div>
              </div>
            </div>
            """, unsafe_allow_html=True)

            # Personalized tip
            tips = []
            if smoker == "Yes":
                tips.append("🚬 Smoking is the single largest cost driver — it can multiply your premium by 3–4×.")
            # ── Personalized Tips Section ────────────────────────────────────────────────
            if bmi > 30.0:
                st.markdown(f"##### {t['tips_title']}")
                # .format(bmi_val=bmi) kullanarak BMI değerini dile göre metnin içine gömüyoruz
                tip_msg = t["bmi_tip"].format(bmi_val=bmi)
                
                st.info(tip_msg)
            if age > 50:
                tips.append("🎂 Premiums increase significantly after age 50 — consider locking in a plan early.")
            if tips:
                st.markdown("---")
                st.markdown("**Personalized tips for you:**")
                for tip in tips:
                    st.info(tip)

            st.markdown('</div>', unsafe_allow_html=True)


# ── Prediction History UI Section ─────────────────────────────────────────────
if not st.session_state.prediction_history.empty:
    st.markdown("---")
    
    # Dile göre başlık ve metrik isimleri
    hist_title = "📋 Prediction History" if lang == "English" else "📋 Tahmin Geçmişi"
    hist_sub = "Below are the calculations made during this session:" if lang == "English" else "Bu oturumda yapılan hesaplamalar:"
    download_btn_lbl = "📥 Download History as CSV" if lang == "English" else "📥 Geçmişi CSV Olarak İndir"
    clear_btn_lbl = "🗑️ Clear History" if lang == "English" else "🗑️ Geçmişi Temizle"
    
    st.markdown(f"### {hist_title}")
    st.caption(hist_sub)

    # 📊 CANLI METRİK KARTLARI (Oturum İstatistikleri)
    history_df = st.session_state.prediction_history
    total_queries = len(history_df)
    avg_cost = history_df["Estimated Cost ($)"].mean()
    max_cost = history_df["Estimated Cost ($)"].max()

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
    
    # Geçmiş tablosunu gösterme
    st.dataframe(history_df, use_container_width=True)
    
    # BUTONLAR İÇİN YAN YANA KOLONLAR (İndir & Temizle)
    b_col1, b_col2 = st.columns([1, 1])
    
    with b_col1:
        csv_data = history_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label=download_btn_lbl,
            data=csv_data,
            file_name="insurance_predictions_history.csv",
            mime="text/csv"
        )
        
    with b_col2:
        # Tek tıkla geçmişi sıfırlayan reset mekanizması
        if st.button(clear_btn_lbl):
            st.session_state.prediction_history = pd.DataFrame(columns=[
                "Age", "Height (cm)", "Weight (kg)", "BMI", "Gender", "Children", "Smoker", "Region", "Estimated Cost ($)"
            ])
            st.rerun()  # Sayfayı anında yenileyip arayüzü günceller