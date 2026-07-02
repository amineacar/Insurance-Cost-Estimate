from analytics import render_analytics_panel
from models import predict_insurance, generate_pdf_report, model
from auth_ui import render_auth_interface
from database import init_ms_sql, get_ms_sql_connection, register_user, login_user
from database import log_prediction
import streamlit as st
import pandas as pd
import pickle
import numpy as np
import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
import io
from languages import texts


response_time = 0.0 

# Session State Başlatma
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = None
if "role" not in st.session_state:
    st.session_state.role = None

# ── GİRİŞ / KAYIT EKRANI ARAYÜZÜ MODÜLÜ ───────────────────────────────
if not st.session_state.logged_in:
    render_auth_interface()
    st.stop()  # 🎯 BU SATIRI KESİNLİKLE EKLE! Giriş yapana kadar alt kodları durdurur.
   
       

# ── 2. Page Config ────────────────────────────────────────────────────────────────
if st.session_state.logged_in:

   st.set_page_config(
    page_title="Health Insurance Cost Estimator",
    page_icon="🩺",
    layout="wide"
)

# ── 3. Custom CSS (Premium Dark Theme & Custom Layouts) ───────────────────────────
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
    color:#14B8A6;
    letter-spacing:.12em;
    text-transform:uppercase;
    margin-bottom: 15px;
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
    padding:24px;
    width:100%;
    margin:20px 0;
    box-shadow: 0 10px 25px rgba(15,118,110,.18);
}

.result-label{
    color:#d1fae5;
    font-size:13px;
    text-transform:uppercase;
    letter-spacing:.15em;
    margin-bottom: 4px;
}

.result-amount{
    color:white;
    font-size:44px;
    font-weight:800;
    line-height: 1.1;
}

.result-monthly{
    color:#ecfdf5;
    font-size:18px;
    margin-top: 4px;
}

/* Driver cards */
.drivers-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 12px;
    margin-top: 0.8rem;
}
.driver-card {
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 14px;
    padding: 16px 12px;
    text-align: center;
}
.driver-icon { font-size: 24px; margin-bottom: 4px; }
.driver-name { font-size: 13px; color: #94a3b8; margin-bottom: 6px; }
.driver-high  { font-size: 12px; font-weight: 600; color: #ef4444; background: rgba(239, 68, 68, 0.15); padding: 4px 10px; border-radius: 20px; display: inline-block; }
.driver-med   { font-size: 12px; font-weight: 600; color: #f59e0b; background: rgba(245, 158, 11, 0.15); padding: 4px 10px; border-radius: 20px; display: inline-block; }
.driver-low   { font-size: 12px; font-weight: 600; color: #10b981; background: rgba(16, 185, 129, 0.15); padding: 4px 10px; border-radius: 20px; display: inline-block; }

.stNumberInput, .stSelectbox, .stSlider{
    border-radius:14px;
}
            
label, p, span, h5 {
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
            
            /* ---- İndirme Butonlarının Yazı Rengini Düzeltme ---- */
div[data-testid="stDownloadButton"] button p,
div[data-testid="stDownloadButton"] button span,
div[data-testid="stDownloadButton"] button p span {
    color: #1e293b !important; /* Yazı rengini görünür koyu füme yapar */
}

/* İndirme butonunun üzerine fareyle gelindiğinde yazı rengi beyaz olsun (Hover Etkisi) */
div[data-testid="stDownloadButton"] button:hover p,
div[data-testid="stDownloadButton"] button:hover span {
    color: #ffffff !important;
}
            
      
div[data-testid="stDataFrameToolbar"] button svg,
[class*="StyledDataFrameToolbar"] button svg,
.stDataFrameToolbar button svg,
div[class*="StyledDataFrameToolbar"] svg {
    fill: #000000 !important; /* İkon rengini tamamen siyah yapar */
    color: #000000 !important; /* Bazı tarayıcılar için alternatif renk zorlaması */
}

/* Fareyle ikonun üzerine gelindiğinde zümrüt yeşili parlasın (Şık dursun) */
div[data-testid="stDataFrameToolbar"] button:hover svg,
[class*="StyledDataFrameToolbar"] button:hover svg {
    fill: #0F766E !important;
    color: #0F766E !important;
}
            
</style>
""", unsafe_allow_html=True)



# ── 5. Top Bar & Language Selection ──────────────────────────────────────────────
top_col1, top_col2 = st.columns([4, 1])

with top_col2:
    lang = st.selectbox("🌐 Language", options=["English", "Türkçe"], label_visibility="collapsed")


t = texts[lang]

with top_col1:
    st.markdown("""
    <span style='background: rgba(255,255,255,0.1); color: #f1f5f9; padding: 6px 14px; border-radius: 20px; font-size: 12px; font-weight: 500; border: 1px solid rgba(255,255,255,0.05);'>
      ⚡ Gradient Boosting Model (R²: 0.89)
    </span>
    """, unsafe_allow_html=True)

# ── 6. Page Header  ────────────────────
st.markdown(f"""
<div style="text-align:center; margin-top:30px; margin-bottom: 40px;">
    <div class="hero-title">
        <span>🩺 {t['page_title'].split(' ')[0]}</span> <span class="hero-highlight">{" ".join(t['page_title'].split(' ')[1:])}</span>
    </div>
    <div class="hero-subtitle">
        {t['page_sub']}
    </div>
</div>
""", unsafe_allow_html=True)


# ── Form – Personal Info ──────────────────────────────────────────────────────
st.markdown('<div class="section-card"><div class="section-title">👤 Personal Information</div>', unsafe_allow_html=True)
col1, col2 = st.columns(2)
with col1:
    age = st.number_input(t["age"], min_value=18, max_value=100, value=25, step=1)
    sex = st.selectbox(t["gender"], options=["Male", "Female"])
with col2:
    height = st.number_input(t["height"], min_value=100, max_value=250, value=175, step=1)
    weight = st.number_input(t["weight"], min_value=30, max_value=250, value=70, step=1)
    
    height_m = height / 100.0
    calculated_bmi = weight / (height_m ** 2)
    bmi = float(np.clip(calculated_bmi, 10.0, 50.0))
    
    bmi_label = "Calculated BMI" if lang == "English" else "Hesaplanan BMI"
    st.info(f"🔢 {bmi_label}: **{bmi:.1f}**")
st.markdown('</div>', unsafe_allow_html=True)

# ── 8. Form – Lifestyle ──────────────────────────────────────────────────────────
st.markdown(f'<div class="section-card"><div class="section-title">{t["lifestyle"]}</div>', unsafe_allow_html=True)
col3, col4 = st.columns(2)
with col3:
    children = st.slider(t["children"], min_value=0, max_value=5, value=0)
with col4:
    smoker = st.selectbox(t["smoke"], options=["No", "Yes"])
    region = st.selectbox(t["region"], options=["Northeast", "Northwest", "Southeast", "Southwest"])
st.markdown('</div>', unsafe_allow_html=True)



# ── 10. Predict Button & Core Execution Pipeline ─────────────────────────────────
if st.button(t["predict_btn"]):
    if age < 18 or bmi < 10.0:
        st.error("⚠️ Age must be 18+ and BMI must be greater than 10.")
    elif model is None:
        st.error("Model files are missing — cannot predict.")
    else:
            with st.spinner("Calculating..."):

                import time
                start_time = time.time()

                result  = predict_insurance(age, sex, bmi, children, smoker, region)
                monthly = result / 12

            # SQL bağlantı ve insert kısımlarının yerine gelen temiz çağrı:
            db_status = log_prediction(age, height, weight, bmi, sex, children, smoker, region, result, st.session_state.username)
            if not db_status:
                st.warning("⚠️ Prediction could not be logged to the database.")

                
                end_time = time.time()
                response_time = end_time - start_time

                print(f"⏱️ Performance Test - Total Response Time: {response_time:.4f} seconds")

                # ── Result Card ──
                st.markdown(f"""
                <div class="result-card">
                    <div class="result-label">Estimated Annual Cost</div>
                    <div class="result-amount">${result:,.2f}</div>
                    <div class="result-monthly">≈ ${monthly:,.2f} / month</div>
                    
                </div>
                """, unsafe_allow_html=True)

            
            pdf_data = generate_pdf_report(age, sex, bmi, children, smoker, region, result)
            pdf_btn_lbl = "📥 Download Official Insurance PDF Report (English Only)" if lang == "English" else "📥 Resmi Sigorta PDF Raporunu İndir (Yalnızca İngilizce)"
            st.download_button(label=pdf_btn_lbl, data=pdf_data, file_name=f"Insurance_Quote_{age}_{sex}.pdf", mime="application/pdf")

            
            st.markdown("---")
            sim_title = "🔮 What-If Financial Optimization" if lang == "English" else "🔮 'Ya Değilse' Finansal Optimizasyon Simülasyonu"
            st.markdown(f"##### {sim_title}")

# 1. (orijinal bmi ve smoker girdilerini doğrudan kullanıyoruz)
            is_smoker = (smoker == "Yes")
            is_high_bmi = (bmi > 24.9)

# 2. Simülasyon değerleri (İdeal sağlıklı senaryo hedefi)
            sim_smoker = "No"
            sim_bmi = 22.0 if is_high_bmi else bmi

# 3. Model tahmini ve tasarruf hesabı 
            sim_result = predict_insurance(age, sex, sim_bmi, children, sim_smoker, region)
            yearly_savings = result - sim_result

# 4. Senaryolar
            if yearly_savings > 10:
    #  Hem Sigara var Hem Yüksek BMI
                if is_smoker and is_high_bmi:
                    sav_msg_en = f"💡 **Financial Optimization:** If you live tobacco-free and reach a healthy target weight (BMI 22.0), your annual premium drops significantly. *You would save* **${yearly_savings:,.2f}** per year!"
                    sav_msg_tr = f"💡 **Finansal Optimizasyon:** Sigarasız bir yaşam sürüp ideal kilonuza (BMI 22.0) ulaştığınız takdirde, yıllık sigorta priminiz ciddi oranda düşer. *Yıllık tasarrufunuz:* **{yearly_savings:,.2f} TL** olur!"
    
    # Sadece Sigara var (Kilosu zaten ideal)
                elif is_smoker:
                    sav_msg_en = f"💡 **Financial Optimization:** If you live tobacco-free, your estimated premium drops to a healthier bracket. *You would save* **${yearly_savings:,.2f}** per year!"
                    sav_msg_tr = f"💡 **Finansal Optimizasyon:** Sigarasız bir yaşama geçiş yaptığınız takdirde, tahmini sigorta priminiz düşecektir. *Yıllık tasarrufunuz:* **{yearly_savings:,.2f} TL** olur!"
    
    # Sadece Yüksek BMI var (Sigara içmiyor)
                else:
                    sav_msg_en = f"💡 **Financial Optimization:** If you reach a healthy target weight (BMI 22.0) by reducing metabolic risks, your estimated premium drops. *You would save* **${yearly_savings:,.2f}** per year!"
                    sav_msg_tr = f"💡 **Finansal Optimizasyon:** Metabolik riskleri azaltarak ideal kilonuza (BMI 22.0) ulaştığınız takdirde, tahmini priminiz düşecektir. *Yıllık tasarrufunuz:* **{yearly_savings:,.2f} TL** olur!"

                st.success(sav_msg_en if lang == "English" else sav_msg_tr)

            else:
    #  PERFECT PROFILE 
                perfect_en = "✨ **Perfect Profile:** You already have the most optimal financial and health metrics!"
                perfect_tr = "✨ **Mükemmel Profil:** Zaten en optimum finansal ve sağlık değerlerine sahipsiniz!"
                st.info(perfect_en if lang == "English" else perfect_tr)                         
                    
            # ── Progress Bar ──
            DATASET_MIN, DATASET_MAX = 1_121, 63_770
            progress_val = float(np.clip((result - DATASET_MIN) / (DATASET_MAX - DATASET_MIN), 0, 1))
            st.markdown("**Where does your estimate sit in the dataset?**")
            st.progress(progress_val, text=f"${DATASET_MIN:,} (min) ──── your estimate: ${result:,.0f} ──── ${DATASET_MAX:,} (max)")

            # ── Key Cost Drivers Paneli ──
            st.markdown(f'<div class="section-card"><div class="section-title">{t["drivers_title"]}</div>', unsafe_allow_html=True)
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

            # ── Kişiselleştirilmiş İpuçları ──
            if bmi > 30.0:
                st.markdown(f"##### {t['tips_title']}")
                st.info(t["bmi_tip"].format(bmi_val=bmi))
            st.markdown('</div>', unsafe_allow_html=True)

# ── 11. MS SQL Veri Çekme Motoru & Tablo/Grafik Paneli ──────────────────────────
render_analytics_panel(lang, t)
  
        
  
      # ── SAYFA SONU GÜVENLİ ÇIKIŞ  ──────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)

# Dil seçeneğine göre buton metnini belirle
logout_text = "🔓 Log Out" if lang == "English" else "🔓 Çıkış Yap"

l_col1, l_col2, l_col3 = st.columns([1, 1, 1])
with l_col2:
    if st.button(logout_text, use_container_width=True, type="secondary"):
        st.session_state.logged_in = False
        st.session_state.username = None
        st.session_state.role = None
        st.rerun()


st.markdown("<br><br><br>", unsafe_allow_html=True) 
st.markdown("---") 

footer_text = (
    "© 2026 Health Insurance Cost Estimator | Privacy Policy | Terms of Service | Contact"
    if lang == "English" else
    "© 2026 Sağlık Sigortası Maliyet Tahmincisi | Gizlilik Politikası | Kullanım Şartları | İletişim"
)
st.markdown(f"<p style='text-align: center; color: gray; font-size: 0.8rem;'>{footer_text}</p>", unsafe_allow_html=True)