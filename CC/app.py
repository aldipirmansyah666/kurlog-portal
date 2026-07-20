import streamlit as st

# 1. Konfigurasi Halaman
st.set_page_config(
    page_title="KurLog Operations Portal", 
    page_icon="⚡", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Custom CSS untuk Styling & Footer Watermark
st.markdown("""
    <style>
    /* Main Background */
    .stApp {
        background-color: #f8fafc !important;
    }
    
    /* Header Container Styling */
    .main-header {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        padding: 2.5rem;
        border-radius: 16px;
        color: white;
        margin-bottom: 2rem;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
    }
    .main-header h1 {
        color: #ffffff !important;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    .main-header p {
        color: #94a3b8;
        font-size: 1.1rem;
    }

    /* Metric Card Customization */
    div[data-testid="stMetric"] {
        background-color: #ffffff !important;
        border: 1px solid #e2e8f0 !important;
        padding: 1.25rem;
        border-radius: 12px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }

    /* Custom Card Containers */
    .feature-card {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        height: 100%;
        transition: transform 0.2s ease;
    }
    .feature-card:hover {
        border-color: #3b82f6;
    }

    /* Watermark / Footer Style */
    .dev-footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: #ffffff;
        color: #64748b;
        text-align: center;
        padding: 8px;
        font-size: 0.85rem;
        border-top: 1px solid #e2e8f0;
        z-index: 100;
    }
    .dev-badge {
        background-color: #e0e7ff;
        color: #3730a3;
        padding: 2px 8px;
        border-radius: 6px;
        font-weight: 600;
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# 3. Main Header / Banner
st.markdown("""
    <div class="main-header">
        <h1>⚡ KurLog Operations Portal</h1>
        <p>Platform Integrasi & Otomasi Operasional Helpdesk / Call Center PPOB & Agen POS</p>
    </div>
""", unsafe_allow_html=True)

# 4. Ringkasan Status Sistem (Metrics)
col1, col2, col3, col4 = st.columns(4)
col1.metric("Status Sistem", "🟢 Online", "v1.0 Stable")
col2.metric("Modul Aktif", "1 Modul", "Bagging Notifier")
col3.metric("Efisiensi Waktu", "~95%", "Otomatis")
col4.metric("Akses User", "Helpdesk", "Admin Level")

st.markdown("<br>", unsafe_allow_html=True)

# 5. Fitur Cards Grid
st.subheader("🛠️ Modul Operasional")

col_left, col_right = st.columns(2)

with col_left:
    st.markdown("""
        <div class="feature-card">
            <h3 style="color: #1e293b; margin-bottom: 0.5rem;">📦 Otomasi Bagging Notifier</h3>
            <p style="color: #64748b; font-size: 0.95rem;">
                Menggabungkan multiple file Excel KurLog, memfilter status <b>'Belum Dibagging'</b> secara otomatis, 
                dan menyusun draft template pesan WhatsApp per agen siap kirim.
            </p>
            <hr style="border: 0.5px solid #f1f5f9;">
            <span style="color: #2563eb; font-weight: 600; font-size: 0.85rem;">👈 Buka menu 'Otomasi Bagging' di Sidebar</span>
        </div>
    """, unsafe_allow_html=True)

with col_right:
    st.markdown("""
        <div class="feature-card">
            <h3 style="color: #1e293b; margin-bottom: 0.5rem;">📇 Database Kontak & WA Direct</h3>
            <p style="color: #64748b; font-size: 0.95rem;">
                Modul mendatang untuk menyimpan kontak agen & integrasi WhatsApp Direct Link untuk pengiriman pesan satu-klik.
            </p>
            <hr style="border: 0.5px solid #f1f5f9;">
            <span style="color: #94a3b8; font-weight: 600; font-size: 0.85rem;">🔒 Dalam Tahap Perancangan</span>
        </div>
    """, unsafe_allow_html=True)

# Floating Footer Watermark
st.markdown("""
    <div class="dev-footer">
        KurLog Operations Portal • Developed with 💻 by <b>Aldi</b>
    </div>
""", unsafe_allow_html=True)