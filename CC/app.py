import streamlit as st

st.set_page_config(
    page_title="KurLog Operations Portal", 
    page_icon="⚡", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Main Banner
st.markdown("""
    <div style="
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        padding: 2rem;
        border-radius: 12px;
        color: white;
        margin-bottom: 1.5rem;
    ">
        <h1 style="color: white !important; margin: 0;">⚡ KurLog Operations Portal</h1>
        <p style="color: #94a3b8; margin-top: 0.5rem; font-size: 1.05rem;">
            Platform Integrasi & Otomasi Operasional Helpdesk / Call Center PPOB & Agen POS
        </p>
    </div>
""", unsafe_allow_html=True)

# Status Metrics
col1, col2, col3, col4 = st.columns(4)
col1.metric("Status Sistem", "🟢 Online", "v1.0 Stable")
col2.metric("Modul Aktif", "1 Modul", "Bagging Notifier")
col3.metric("Efisiensi Waktu", "~95%", "Otomatis")
col4.metric("Akses User", "Helpdesk", "Admin Level")

st.markdown("<br>", unsafe_allow_html=True)

# Fitur Cards
st.subheader("🛠️ Modul Operasional")

st.info("### 📦 Otomasi Bagging Notifier\n"
        "Menggabungkan multiple file Excel KurLog, memfilter status **'Belum Dibagging'** secara otomatis, "
        "dan menyusun draft template pesan WhatsApp per agen siap kirim.\n\n"
        "👈 **Buka menu 'Otomasi Bagging' di Sidebar untuk mulai.**")

# Sidebar & Footer
st.sidebar.markdown("---")
st.sidebar.markdown("🏢 **POSIX Helpdesk System**")
st.sidebar.markdown("💻 Developed by **Aldi**")

st.markdown("---")
st.caption("KurLog Operations Portal • Developed with 💻 by **Aldi**")
