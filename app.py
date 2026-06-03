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

# ── Session State Initialization (Tahmin Geçmişi Hafızası) ────────────────────
if "prediction_history" not in st.session_state:
    st.session_state.prediction_history = pd.DataFrame(columns=[
        "Age", "Height (cm)", "Weight (kg)", "BMI", "Gender", "Children", "Smoker", "Region", "Estimated Cost ($)"
    ])

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


# ── Language Selection ────────────────────────────────────────────────────────
lang = st.sidebar.selectbox("🌐 Language / Dil", options=["English", "Türkçe"])

# Dil sözlükleri (Dictionary)
texts = {
    "English": {
        "sidebar_title": "### 📊 Model Info",
        "page_title": "🏥 Insurance Cost Estimator",
        "page_sub": "Fill in the details below to get a personalized annual cost estimate.",
        "personal_info": "👤 Personal Information",
        "age": "Age",
        "gender": "Gender",
        "height": "Height (cm)",
        "weight": "Weight (kg)",
        "region": "Region",
        "lifestyle": "🌿 Lifestyle",
        "children": "Number of Children",
        "smoke": "Do You Smoke?",
        "predict_btn": "Predict my cost →",
        "err_validation": "⚠️ Age must be 18+ and BMI must be greater than 10.",
        "err_model": "Model files are missing — cannot predict.",
        "calc_spinner": "Calculating...",
        "res_annual": "Estimated Annual Cost",
        "res_month": "month",
        "sit_dataset": "**Where does your estimate sit in the dataset?**",
        "drivers_title": "💡 Key Cost Drivers"
    },
    "Türkçe": {
        "sidebar_title": "### 📊 Model Bilgisi",
        "page_title": "🏥 Sigorta Maliyeti Tahmin Sistemi",
        "page_sub": "Kişiselleştirilmiş yıllık maliyet tahminini almak için aşağıdaki detayları doldurun.",
        "personal_info": "👤 Kişisel Bilgiler",
        "age": "Yaş",
        "gender": "Cinsiyet",
        "height": "Boy (cm)",
        "weight": "Kilo (kg)",
        "region": "Bölge",
        "lifestyle": "🌿 Yaşam Tarzı",
        "children": "Çocuk Sayısı",
        "smoke": "Sigara Kullanıyor musunuz?",
        "predict_btn": "Maliyeti Tahmin Et →",
        "err_validation": "⚠️ Yaş 18+ ve BMI 10'dan büyük olmalıdır.",
        "err_model": "Model dosyaları eksik — tahmin yapılamıyor.",
        "calc_spinner": "Hesaplanıyor...",
        "res_annual": "Tahmini Yıllık Maliyet",
        "res_month": "ay",
        "sit_dataset": "**Tahmininiz veri setinde nerede yer alıyor?**",
        "drivers_title": "💡 Temel Maliyet Sürücüleri"
    }
}

# Seçilen dile göre aktif metin setini atıyoruz
t = texts[lang]

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(t["sidebar_title"])
    st.markdown("---")
    
    # Dile göre metrik etiketleri
    alg_lbl = "Algorithm" if lang == "English" else "Algoritma"
    feat_lbl = "Features" if lang == "English" else "Öznitelikler"
    imp_lbl = "Feature importance" if lang == "English" else "Öznitelik Önem Derecesi"
    
    st.metric(alg_lbl, "Gradient Boosting")
    st.metric("R² Score", "0.89")
    st.metric(feat_lbl, "8")
    st.markdown("---")
    st.markdown(f"**{imp_lbl}**")
    
    # İlerleme çubuklarının üzerindeki yazılar
    smk_side = "🚬 Smoking" if lang == "English" else "🚬 Sigara Kullanımı"
    age_side = "🎂 Age" if lang == "English" else "🎂 Yaş"
    bmi_side = "⚖️ BMI" if lang == "English" else "⚖️ BMI (Vücut Kitle)"
    chld_side = "👶 Children" if lang == "English" else "👶 Çocuk Sayısı"
    reg_side = "📍 Region" if lang == "English" else "📍 Bölge"
    
    st.progress(0.95, text=smk_side)
    st.progress(0.60, text=age_side)
    st.progress(0.40, text=bmi_side)
    st.progress(0.20, text=chld_side)
    st.progress(0.10, text=reg_side)
    st.markdown("---")
    
    caption_txt = "Insurance Cost Estimator · Week 4" if lang == "English" else "Sigorta Maliyet Tahmini · 4. Hafta"
    st.caption(caption_txt)
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


# ── Prediction History UI Section ─────────────────────────────────────────────
# Eğer hafızada en az 1 tane bile tahmin geçmişi varsa bu alanı gösteriyoruz
if not st.session_state.prediction_history.empty:
    st.markdown("---")
    
    # Dile göre başlık ve buton yazıları
    hist_title = "📋 Prediction History" if lang == "English" else "📋 Tahmin Geçmişi Records"
    hist_sub = "Below are the calculations made during this session:" if lang == "English" else "Bu oturumda yapılan hesaplamalar:"
    download_btn_lbl = "📥 Download History as CSV" if lang == "English" else "📥 Geçmişi CSV Olarak İndir"
    
    st.markdown(f"### {hist_title}")
    st.caption(hist_sub)
    
    # Geçmiş tablosunu şık bir Streamlit veri tablosu olarak gösteriyoruz
    st.dataframe(st.session_state.prediction_history, use_container_width=True)
    
    # Tabloyu CSV formatına dönüştürme fonksiyonu
    csv_data = st.session_state.prediction_history.to_csv(index=False).encode('utf-8')
    
    # Kullanıcının bilgisayarına indirmesini sağlayan buton
    st.download_button(
        label=download_btn_lbl,
        data=csv_data,
        file_name="insurance_predictions_history.csv",
        mime="text/csv"
    )