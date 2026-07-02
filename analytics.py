import streamlit as st
import pandas as pd
from database import get_ms_sql_connection

def render_analytics_panel(lang, t):
    """Fetches prediction history and renders the BI / Analytics panel based on roles."""
    try:
        conn = get_ms_sql_connection()
        query = """
            SELECT age AS Age, height AS [Height (cm)], weight AS [Weight (kg)],
                   bmi AS BMI, gender AS Gender, children AS Children,
                   smoker AS Smoker, region AS Region, estimated_cost AS [Estimated Cost ($)],
                   username
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
        st.markdown(f"### {hist_title}")

        if 'username' not in history_df.columns:
            history_df['username'] = 'unknown'

        # ── ADMIN KULLANICI GİRİŞ YAPTIYSA ─────────────────────────────────
        if st.session_state.role == "admin":
            st.caption("Welcome to Administrative Command Center" if lang == "English" else "Yönetici Kontrol Paneline Hoş Geldiniz")
            
            admin_view_mode = st.radio("View Mode" if lang == "English" else "Görünüm Modu", ["Show All Users", "Filter by Specific User"])
            
            if admin_view_mode == "Filter by Specific User":
                all_users = history_df['username'].unique().tolist()
                selected_user = st.selectbox("Select User to Inspect" if lang == "English" else "İncelemek için Kullanıcı Seçin", all_users)
                filtered_df = history_df[history_df['username'] == selected_user]
            else:
                filtered_df = history_df

            total_queries = len(filtered_df)
            avg_cost = filtered_df["Estimated Cost ($)"].mean() if total_queries > 0 else 0.0
            max_cost = filtered_df["Estimated Cost ($)"].max() if total_queries > 0 else 0.0

            m_col1, m_col2, m_col3 = st.columns(3)
            with m_col1:
                st.metric("Total Predictions" if lang == "English" else "Toplam Sorgulama", f"{total_queries}")
            with m_col2:
                st.metric("Average Estimate" if lang == "English" else "Ortalama Tahmin", f"${avg_cost:,.2f}")
            with m_col3:
                st.metric("Highest Estimate" if lang == "English" else "En Yüksek Tahmin", f"${max_cost:,.2f}")

            st.markdown("<br>", unsafe_allow_html=True)
            st.dataframe(filtered_df, use_container_width=True)

           # Butonlar 
            csv_data = filtered_df.to_csv(index=False).encode('utf-8')
            st.download_button(label="Download Logs as CSV" if lang == "English" else "Geçmişi CSV Olarak İndir", data=csv_data, file_name="admin_logs.csv", mime="text/csv")
            
            clear_lbl = "🗑️ Clear History" if lang == "English" else "🗑️ Geçmişi Temizle"
            if st.button(clear_lbl, type="secondary", use_container_width=False):
                try:
                    conn = get_ms_sql_connection()
                    cursor = conn.cursor()
                    cursor.execute("TRUNCATE TABLE predictions")
                    conn.commit()
                    conn.close()
                except Exception:
                    pass
                st.rerun()

            # ── İŞ ZEKASI VE MODEL İZLEME PANELİ (GRAPHICS) ─────────────────────────
            st.markdown("<br>", unsafe_allow_html=True)
            expander_title = "📊 Business Intelligence & Model Analytics Panel" if lang == "English" else "📊 İş Zekası ve Model Analiz Paneli"
            with st.expander(expander_title, expanded=False):
                st.markdown("### 📈 Real-Time Data Insights & Database Scalability" if lang == "English" else "### 📈 Gerçek Zamanlı Veri Analizi")
                st.caption("This panel visualizes production data from MS SQL Server...")
                st.markdown("---")

                if not filtered_df.empty:
                    age_col = "Age" if "Age" in filtered_df.columns else "age"
                    bmi_col = "BMI" if "BMI" in filtered_df.columns else "bmi"
                    cost_col = "Estimated Cost ($)" if "Estimated Cost ($)" in filtered_df.columns else "estimated_cost"

                    g_col1, g_col2 = st.columns(2)
                    with g_col1:
                        st.markdown("**👥 Age Distribution of Users**" if lang == "English" else "**👥 Kullanıcıların Yaş Dağılımı**")
                        if age_col in filtered_df.columns:
                            age_counts = filtered_df[age_col].value_counts().sort_index()
                            st.bar_chart(age_counts, use_container_width=True)
                    with g_col2:
                        st.markdown("**⚖️ BMI Distribution of Users**" if lang == "English" else "**⚖️ Kullanıcıların BMI Dağılımı**")
                        if bmi_col in filtered_df.columns:
                            bmi_data = filtered_df[bmi_col].reset_index(drop=True)
                            st.area_chart(bmi_data, use_container_width=True)

                    st.markdown("<br>", unsafe_allow_html=True)
                    st.markdown("**📈 Insurance Cost Trend Over Time**" if lang == "English" else "**📈 Zaman İçindeki Sigorta Maliyet Trendi**")
                    if cost_col in filtered_df.columns:
                        trend_data = filtered_df[cost_col].iloc[::-1].reset_index(drop=True)
                        st.line_chart(trend_data, use_container_width=True)
                else:
                    st.warning("No data available to visualize." if lang == "English" else "Görselleştirilecek veri bulunamadı.")

        # ── NORMAL KULLANICI GİRİŞ YAPTIYSA ────────────────────────────────
        else:
            st.caption("Below are the calculations made during this session" if lang == "English" else "Bu oturumda yaptığınız hesaplamalar")
            user_df = history_df[history_df['username'] == st.session_state.username]

            if user_df.empty:
                st.info("You haven't made any estimations yet. Your history will appear here." if lang == "English" else "Henüz bir tahmin geçmişiniz bulunmuyor.")
            else:
                total_queries = len(user_df)
                avg_cost = user_df["Estimated Cost ($)"].mean() if total_queries > 0 else 0.0
                max_cost = user_df["Estimated Cost ($)"].max() if total_queries > 0 else 0.0

                m_col1, m_col2, m_col3 = st.columns(3)
                with m_col1:
                    st.metric("Total Predictions" if lang == "English" else "Toplam Sorgulama", f"{total_queries}")
                with m_col2:
                    st.metric("Average Estimate" if lang == "English" else "Ortalama Tahmin", f"${avg_cost:,.2f}")
                with m_col3:
                    st.metric("Highest Estimate" if lang == "English" else "En Yüksek Tahmin", f"${max_cost:,.2f}")

                st.markdown("<br>", unsafe_allow_html=True)
                display_user_df = user_df.drop(columns=['username'])
                st.dataframe(display_user_df, use_container_width=True)

                csv_data = display_user_df.to_csv(index=False).encode('utf-8')
                st.download_button(label="Download My History as CSV" if lang == "English" else "Geçmişimi CSV Olarak İndir", data=csv_data, file_name="my_history.csv", mime="text/csv")