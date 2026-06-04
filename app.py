import streamlit as st
import pandas as pd
import pickle
import numpy as np
import pyodbc
import os
from languages import texts
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
import io

# ── 1. Veritabanı Altyapısı (MS SQL Server) ───────────────────────────────────────
SERVER_NAME = "localhost"  # Kendi SQL Server ismine göre değiştirebilirsin
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

# MS SQL Altyapısını tetikle
init_ms_sql()

# ── 2. Page Config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Insurance Cost Estimator",
    page_icon="🏥",
    layout="centered"
)

# ── 3. Custom CSS (Arayüz Tasarımın Aynen Korundu) ─────────────────────────────────
st.markdown("""
<style>
/* Sol taraftaki açılır kapanır sidebar'ı ve okunu tamamen görünmez yap */
[data-testid="stSidebar"], [data-testid="stSidebarCollapseButton"] {
    display: none !important;
}

/* ---- Global ---- */
[data-testid="stAppViewContainer"] {
    background-color: #f1f1f0 !important; /* İstediğin açık taş rengi buraya sabitlendi */
}
[data-testid="stHeader"] { background: transparent; }

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

# ── 4. Load Model ────────────────────────────────────────────────────────────────
try:
    model = pickle.load(open('model.pkl', 'rb'))
    scaler = pickle.load(open('scaler.pkl', 'rb'))
    model_loaded = True
except FileNotFoundError:
    st.error("⚠️ Model or Scaler files could not be found!")
    model_loaded = False

# ── 5. Top Bar & Language Selection (Hizalı ve Tekil Yapıldı) ─────────────────
top_col1, top_col2 = st.columns([4, 1])

with top_col2:
    lang = st.selectbox("🌐 Language", options=["English", "Türkçe"], label_visibility="collapsed")

t = texts[lang]

with top_col1:
    st.markdown("""
    <span style='background: #f1f5f9; color: #475569; padding: 4px 10px; border-radius: 20px; font-size: 12px; font-weight: 500;'>
      ⚡ Gradient Boosting Model (R²: 0.89)
    </span>
    """, unsafe_allow_html=True)

# ── 6. Page Header ───────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="page-header">
  <div class="page-title">{t["page_title"]}</div>
  <div class="page-sub">{t["page_sub"]}</div>
</div>
""", unsafe_allow_html=True)

# ── 7. Form – Personal Info ──────────────────────────────────────────────────────
st.markdown(f'<div class="section-card"><div class="section-title">{t["personal_info"]}</div>', unsafe_allow_html=True)
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
    
    region = st.selectbox(t["region"], options=["Northeast", "Northwest", "Southeast", "Southwest"])
st.markdown('</div>', unsafe_allow_html=True)

# ── 8. Form – Lifestyle ──────────────────────────────────────────────────────────
st.markdown(f'<div class="section-card"><div class="section-title">{t["lifestyle"]}</div>', unsafe_allow_html=True)
col3, col4 = st.columns(2)
with col3:
    children = st.slider(t["children"], min_value=0, max_value=5, value=0)
with col4:
    smoker = st.selectbox(t["smoke"], options=["No", "Yes"])
st.markdown('</div>', unsafe_allow_html=True)

# ── 9. Prediction Function ─────────────────────────────────────────────────────
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

def generate_pdf_report(age, sex, bmi, children, smoker, region, result, lang):
    """Generates a clean, professional, English-only PDF report for the insurance quote."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    story = []
    
    styles = getSampleStyleSheet()
    
    # Premium Corporate Colors & Typography Styles
    primary_color = colors.HexColor("#085041")
    secondary_color = colors.HexColor("#1D9E75")
    
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=primary_color,
        spaceAfter=6
    )
    
    sub_style = ParagraphStyle(
        'DocSub',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor("#475569"),
        spaceAfter=20
    )
    
    section_heading = ParagraphStyle(
        'SecHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=primary_color,
        spaceBefore=12,
        spaceAfter=8
    )

    # Clean English Headers
    title_text = "HEALTH INSURANCE QUOTE REPORT"
    sub_text = "Generated by AI-Powered InsurTech Estimation System"
    
    story.append(Paragraph(title_text, title_style))
    story.append(Paragraph(sub_text, sub_style))
    story.append(Spacer(1, 10))
    
    # Section 1: Customer Info Table (English Only)
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
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 10),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
    ]))
    story.append(t1)
    story.append(Spacer(1, 20))
    
    # Section 2: Financial Estimation Table (English Only)
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
        ('FONTNAME', (0,0), (1,0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
        ('TOPPADDING', (0,0), (-1,-1), 10),
        ('BACKGROUND', (0,1), (-1,-1), colors.HexColor("#f0faf6")),
        ('GRID', (0,0), (-1,-1), 0.5, secondary_color),
        ('FONTSIZE', (0,1), (-1,-1), 11),
    ]))
    story.append(t2)
    story.append(Spacer(1, 25))
    
    # English Only Disclaimer Footer
    footer_text = ("* Legal Notice: This document provides an artificial intelligence estimation based on historical health data grids (R2: 0.89). "
                   "It serves as a technical preview and does not constitute a final binding underwriting contract.")
                   
    story.append(Paragraph(footer_text, ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, textColor=colors.HexColor("#64748b"))))
    
    doc.build(story)
    buffer.seek(0)
    return buffer

# ── 10. Predict Button & Core Pipeline ─────────────────────────────────────────
if st.button("Predict my cost →"):
    if age < 18 or bmi < 10.0:
        st.error("⚠️ Age must be 18+ and BMI must be greater than 10.")
    elif not model_loaded:
        st.error("Model files are missing — cannot predict.")
    else:
        with st.spinner("Calculating..."):
            result  = predict_insurance(age, sex, bmi, children, smoker, region)
            monthly = result / 12

            # 💾 MS SQL Server'a Kalıcı Kayıt Düzenlemesi (SQLite Temizlendi)
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


            # ── 📥 PDF Rapor İndirme Mekanizması ──────────────────────────────
            pdf_data = generate_pdf_report(age, sex, bmi, children, smoker, region, result, lang)
            pdf_btn_lbl = "📥 Download Official Insurance PDF Report" if lang == "English" else "📥 Resmi Sigorta PDF Raporunu İndir"
            
            st.download_button(
                label=pdf_btn_lbl,
                data=pdf_data,
                file_name=f"Insurance_Quote_{age}_{sex}.pdf",
                mime="application/pdf"
            )


            # ── 🔮 "What-If" Finansal Simülatör (Değişken Hataları Giderildi) ─────
            if smoker == "Yes" or bmi > 24.9:
                st.markdown("---")
                sim_title = "🔮 What-If Financial Optimization" if lang == "English" else "🔮 'Ya Değilse' Finansal Optimizasyon Simülasyonu"
                st.markdown(f"##### {sim_title}")
                
                sim_smoker = "No"
                sim_bmi = 22.0 if bmi > 24.9 else bmi
                
                sim_result = predict_insurance(age, sex, sim_bmi, children, sim_smoker, region)
                yearly_savings = result - sim_result
                
                if yearly_savings > 100:
                    sav_msg_en = f"💡 **Financial Optimization:** If you quit smoking and achieve an ideal BMI (22.0), your estimated annual premium drops to **${sim_result:,.2f}**. You would save **${yearly_savings:,.2f}** per year!"
                    sav_msg_tr = f"💡 **Finansal Optimizasyon:** Sigarayı bırakıp ideal kilonunuza (BMI 22.0) ulaştığınız takdirde, tahmini yıllık priminiz **${sim_result:,.2f}** seviyesine düşer. Yılda tam **${yearly_savings:,.2f}** tasarruf edebilirsiniz!"
                    st.success(sav_msg_en if lang == "English" else sav_msg_tr)

            # ── Progress bar ──────────────────────────────────────────────────
            st.markdown("**Where does your estimate sit in the dataset?**")
            st.progress(progress_val, text=f"${DATASET_MIN:,} (min) ──── your estimate: ${result:,.0f} ──── ${DATASET_MAX:,} (max)")

            # ── Key Cost Drivers ──────────────────────────────────────────────
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
            </div>
            """, unsafe_allow_html=True)

            # ── Personalized Tips ─────────────────────────────────────────────
            tips = []
            if smoker == "Yes":
                tips.append("🚬 Smoking is the single largest cost driver — it can multiply your premium by 3–4×.")
            
            if bmi > 30.0:
                st.markdown(f"##### {t['tips_title']}")
                tip_msg = t["bmi_tip"].format(bmi_val=bmi)
                st.info(tip_msg)
                
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
    
    hist_title = "📋 Prediction History" if lang == "English" else "📋 Tahmin Geçmişi"
    hist_sub = "Below are the calculations made during this session:" if lang == "English" else "Bu oturumda yapılan hesaplamalar:"
    download_btn_lbl = "📥 Download History as CSV" if lang == "English" else "📥 Geçmişi CSV Olarak İndir"
    clear_btn_lbl = "🗑️ Clear History" if lang == "English" else "🗑️ Geçmişi Temizle"
    
    st.markdown(f"### {hist_title}")
    st.caption(hist_sub)

    # Canlı Metrik Kartları (Korumalı Hesaplama)
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