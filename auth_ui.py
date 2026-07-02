import streamlit as st
from database import register_user, login_user

def render_auth_interface():
    """Giriş ve Kayıt ekranını çizer, oturum kontrolü yapar."""
    st.set_page_config(page_title="Health Insurance Cost Estimator System", page_icon="📊", layout="centered")

    # CSS ile Giriş Ekranını Özelleştirme
    st.markdown("""
        <style>
        [data-testid="stSidebar"] {display: none !important;}
        [data-testid="stSidebarCollapseButton"] {display: none !important;}
        </style>
        """, unsafe_allow_html=True)

    # 🎯 BAŞLIK AYARI
    st.markdown("<h2 style='text-align: left; margin-bottom: 0px;'>📊 Health Insurance Cost Estimator System</h2>", unsafe_allow_html=True)
    st.markdown("---")

    st.info("💡 *Sign in to estimate your health insurance costs and access your saved reports.*")

    # Varsayılan dil ayarı
    lang = "English"

    tab1, tab2 = st.tabs(["🔑 Sign In", "📝 Register"])

    # ── SIGN IN  ───────────────────────────────────────────────
    with tab1:
        st.markdown("<br>", unsafe_allow_html=True)

        login_user_input = st.text_input("Email Address", placeholder="example@gmail.com", key="login_user")
        login_pass_input = st.text_input("Password", type="password", key="login_pass")

        st.checkbox("Remember Me", key="remember_me_checkbox")
        st.markdown("<br>", unsafe_allow_html=True)

        badge_col1, badge_col2, badge_col3 = st.columns(3)
        with badge_col1:
            st.caption("🔒 **Secure Login**")
        with badge_col2:
            st.caption("🛡️ **Encrypted Connection**")
        with badge_col3:
            st.caption("🤖 **ML-Powered Prediction**")

        st.markdown("<br>", unsafe_allow_html=True)
        login_triggered = st.button("Sign In", type="primary", use_container_width=True)

        if login_triggered:
            if login_user_input and login_pass_input:
                success, role = login_user(login_user_input, login_pass_input)
                if success:
                    st.session_state.logged_in = True
                    st.session_state.username = login_user_input
                    st.session_state.role = role
                    st.success("Access granted! Redirecting...")
                    st.rerun()
                else:
                    st.error("Invalid email address or password!")
            else:
                st.warning("Please fill in all fields.")

    # ── REGISTER ──────────────────────────────────────────────
    with tab2:
        st.markdown("<br>", unsafe_allow_html=True)
        
        reg_user_input = st.text_input("Email Address", placeholder="example@gmail.com", key="reg_user")
        reg_pass_input = st.text_input("New Password", type="password", key="reg_pass")
        reg_pass_confirm = st.text_input("Confirm Password", type="password", key="reg_confirm")

        st.markdown("<br>", unsafe_allow_html=True)

        if st.button("Register", type="secondary"):
            if reg_user_input and reg_pass_input and reg_pass_confirm:
                if reg_pass_input != reg_pass_confirm:
                    st.error("Passwords do not match!")
                elif len(reg_pass_input) < 4:
                    st.error("Password must be at least 4 characters long!")
                else:
                    status, message = register_user(reg_user_input, reg_pass_input)
                    if status:
                        st.success(message)
                    else:
                        st.error(message)
            else:
                st.warning("Please fill in all fields.")

    st.stop()  # Giriş yapılana kadar alt satırlara geçilmesini engeller