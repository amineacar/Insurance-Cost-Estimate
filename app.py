import streamlit as st
import pandas as pd
import pickle
import numpy as np
import pyodbc
import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
import io
from languages import texts

# ── 1. Veritabanı Altyapısı (MS SQL Server) ───────────────────────────────────────
SERVER_NAME = "localhost"  
DB_NAME = "InsuranceDB"

def get_ms_sql_connection():
    """MS SQL Server'a Windows Authentication ile bağlanır."""
    conn_str = (
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER={SERVER_NAME};"
        f"DATABASE={DB_NAME};"
        f"Trusted_Connection=yes;"
    )
    return pyodbc.connect(conn_str)

def init_ms_sql():
    """Master veritabanına bağlanıp önce InsuranceDB'yi, sonra tabloları otomatik oluşturur."""
    try:
        master_str = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={SERVER_NAME};DATABASE=master;Trusted_Connection=yes;"
        conn = pyodbc.connect(master_str, autocommit=True)
        cursor = conn.cursor()
        cursor.execute(f"IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = '{DB_NAME}') CREATE DATABASE {DB_NAME}")
        conn.close()
        
        conn = get_ms_sql_connection()
        cursor = conn.cursor()
        cursor.execute("""
            IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[predictions]') AND type in (N'U'))
            BEGIN
                CREATE TABLE [dbo].[predictions] (
                    [id] INT IDENTITY(1,1) PRIMARY KEY,
                    [age] INT,
                    [height] INT,
                    [weight] INT,
                    [bmi] FLOAT,
                    [gender] VARCHAR(10),
                    [children] INT,
                    [smoker] VARCHAR(5),
                    [region] VARCHAR(20),
                    [estimated_cost] FLOAT,
                    [timestamp] DATETIME DEFAULT GETDATE()
                )
            END
        """)
        conn.commit()
        conn.close()
    except Exception as e:
        st.error(f"MS SQL Connection Error: {e}. Lütfen SERVER_NAME alanını kontrol edin.")


init_ms_sql()

# ── 2. Page Config ────────────────────────────────────────────────────────────────
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

# ── 4. Load Model ────────────────────────────────────────────────────────────────
try:
    model = pickle.load(open('model.pkl', 'rb'))
    scaler = pickle.load(open('scaler.pkl', 'rb'))
    model_loaded = True
except FileNotFoundError:
    st.error("⚠️ Model or Scaler files could not be found!")
    model_loaded = False

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

# ── 9. Core Utility Functions (Prediction & English-Only PDF) ────────────────────
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

def generate_pdf_report(age, sex, bmi, children, smoker, region, result):
    """Generates a clean, professional, English-only PDF report."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    story = []
    styles = getSampleStyleSheet()
    
    primary_color = colors.HexColor("#085041")
    secondary_color = colors.HexColor("#1D9E75")
    
    title_style = ParagraphStyle('DocTitle', parent=styles['Heading1'], fontSize=24, textColor=primary_color, spaceAfter=6)
    sub_style = ParagraphStyle('DocSub', parent=styles['Normal'], fontSize=10, textColor=colors.HexColor("#475569"), spaceAfter=20)
    section_heading = ParagraphStyle('SecHeading', parent=styles['Heading2'], fontSize=14, textColor=primary_color, spaceBefore=12, spaceAfter=8)

    story.append(Paragraph("HEALTH INSURANCE QUOTE REPORT", title_style))
    story.append(Paragraph("Generated by AI-Powered InsurTech Estimation System", sub_style))
    story.append(Spacer(1, 10))
    
    story.append(Paragraph("1. Customer Demographics & Lifestyle", section_heading))
    data_labels = [
        ["Age", str(age), "Gender", str(sex)],
        ["BMI", f"{bmi:.1f}", "Children", str(children)],
        ["Smoker Status", str(smoker), "Region", str(region)]
    ]
    t1 = Table(data_labels, colWidths=[130, 130, 130, 130])
    t1.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (0,-1), colors.HexColor("#f1f5f9")),
        ('BACKGROUND', (2,0), (2,-1), colors.HexColor("#f1f5f9")),
        ('TEXTCOLOR', (0,0), (-1,-1), colors.HexColor("#1e293b")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
        ('PADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(t1)
    story.append(Spacer(1, 20))
    
    story.append(Paragraph("2. AI Financial Risk & Premium Estimation", section_heading))
    financial_data = [
        ["Calculation Metric", "Value ($)"],
        ["Estimated Annual Premium", f"${result:,.2f}"],
        ["Estimated Monthly Premium", f"${(result/12):,.2f}"]
    ]
    t2 = Table(financial_data, colWidths=[300, 220])
    t2.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (1,0), primary_color),
        ('TEXTCOLOR', (0,0), (1,0), colors.white),
        ('BACKGROUND', (0,1), (-1,-1), colors.HexColor("#f0faf6")),
        ('GRID', (0,0), (-1,-1), 0.5, secondary_color),
        ('PADDING', (0,0), (-1,-1), 10),
    ]))
    story.append(t2)
    story.append(Spacer(1, 25))
    
    footer_text = ("* Legal Notice: This document provides an artificial intelligence estimation based on historical health data grids (R2: 0.89). "
                   "It serves as a technical preview and does not constitute a final binding contract.")
    story.append(Paragraph(footer_text, ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, textColor=colors.HexColor("#64748b"))))
    
    doc.build(story)
    buffer.seek(0)
    return buffer

# ── 10. Predict Button & Core Execution Pipeline ─────────────────────────────────
if st.button(t["predict_btn"]):
    if age < 18 or bmi < 10.0:
        st.error("⚠️ Age must be 18+ and BMI must be greater than 10.")
    elif not model_loaded:
        st.error("Model files are missing — cannot predict.")
    else:
        with st.spinner("Calculating..."):
            result  = predict_insurance(age, sex, bmi, children, smoker, region)
            monthly = result / 12

            
            try:
                conn = get_ms_sql_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO predictions (age, height, weight, bmi, gender, children, smoker, region, estimated_cost)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (age, height, weight, round(bmi, 2), sex, children, smoker, region, round(result, 2)))
                conn.commit()
                conn.close()
            except Exception as e:
                st.warning(f"Database write error: {e}")

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
            
            
            current_smoker = smoker if 'smoker' in locals() else "No"
            current_bmi = bmi if 'bmi' in locals() else 22.0
            
            
            sim_smoker = "No"
            sim_bmi = 22.0 if current_bmi > 24.9 else current_bmi
            
            
            sim_result = predict_insurance(age, sex, sim_bmi, children, sim_smoker, region)
            yearly_savings = result - sim_result
            
            if yearly_savings > 10: 
                sav_msg_en = f"💡 **Financial Optimization:** If you live tobacco-free and maintain a healthy weight (BMI 22.0), your estimated premium drops to **${sim_result:,.2f}**. You would save **${yearly_savings:,.2f}** per year!"
                sav_msg_tr = f"💡 **Finansal Optimizasyon:** Sigarasız bir yaşam sürüp ideal kilonuza (BMI 22.0) ulaştığınız takdirde, tahmini priminiz **${sim_result:,.2f}** seviyesine düşer. Yılda tam **${yearly_savings:,.2f}** tasarruf edebilirsiniz!"
                st.success(sav_msg_en if lang == "English" else sav_msg_tr)
            else:
                
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

    # Canlı Analitik Metrik Kartları
    total_queries = len(history_df)
    avg_cost = history_df["Estimated Cost ($)"].mean() if total_queries > 0 else 0.0
    max_cost = history_df["Estimated Cost ($)"].max() if total_queries > 0 else 0.0

    m_col1, m_col2, m_col3 = st.columns(3)
    with m_col1:
        st.metric("Total Predictions" if lang == "English" else "Toplam Sorgulama", f"{total_queries}")
    with m_col2:
        st.metric("Average Estimate" if lang == "English" else "Ortalama Tahmin", f"${avg_cost:,.2f}")
    with m_col3:
        st.metric("Highest Estimate" if lang == "English" else "En Yüksek Tahmin", f"${max_cost:,.2f}")

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