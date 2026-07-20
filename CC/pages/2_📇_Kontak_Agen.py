import streamlit as st
import pandas as pd
import json
import os
import re

st.set_page_config(
    page_title="Manajemen Kontak Agen - KurLog", 
    page_icon="📇", 
    layout="wide"
)

st.title("📇 Database & Manajemen Kontak Agen")
st.caption("Kelola nomor WhatsApp mitra agen POS untuk otomatisasi pengiriman pesan pengingat bagging.")
st.markdown("---")

DB_PATH = "CC/database_agen.json"

# --- FUNGSIONALITAS BACA & SIMPAN DATABASE ---
def load_database():
    if os.path.exists(DB_PATH):
        try:
            with open(DB_PATH, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_database(data):
    # Buat direktori jika belum ada
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with open(DB_PATH, "w") as f:
        json.dump(data, f, indent=2)

# Load data awal ke Session State
if "db_kontak" not in st.session_state:
    st.session_state.db_kontak = load_database()

# --- LAYOUT DUA KOLOM ---
col_form, col_table = st.columns([1, 2])

# 1. FORM INPUT & EDIT KONTAK
with col_form:
    st.subheader("➕ Tambah / Edit Kontak")
    
    with st.form("form_kontak", clear_on_submit=True):
        nama_agen = st.text_input(
            "Nama Agen (Presisi Sesuai Excel KurLog)", 
            placeholder="Contoh: AGEN POS MERDEKA"
        ).strip().upper()
        
        no_wa = st.text_input(
            "Nomor WhatsApp Agen", 
            placeholder="Contoh: 081234567890"
        )
        
        btn_simpan = st.form_submit_button("💾 Simpan Kontak Permanen", use_container_width=True)
        
        if btn_simpan:
            if nama_agen and no_wa:
                clean_wa = re.sub(r'\D', '', no_wa)
                
                # Simpan ke session state dan file JSON
                st.session_state.db_kontak[nama_agen] = clean_wa
                save_database(st.session_state.db_kontak)
                
                st.success(f"✅ Kontak **{nama_agen}** ({clean_wa}) berhasil disimpan!")
                st.rerun()
            else:
                st.error("⚠️ Mohon isi Nama Agen dan Nomor WhatsApp secara lengkap!")

    st.info("💡 **Petunjuk Helpdesk**: Penulisan Nama Agen dibuat otomatis huruf KAPITAL untuk menghindari ketidakcocokan data dengan Excel.")

# 2. TABEL MASTER KONTAK AGEN
with col_table:
    st.subheader("📋 Master Database Agen")
    
    dict_kontak = st.session_state.db_kontak
    
    if dict_kontak:
        # Transformasi ke DataFrame
        df_display = pd.DataFrame(list(dict_kontak.items()), columns=["Nama Agen", "No WhatsApp"])
        
        # Search Bar
        search_query = st.text_input("🔍 Cari Nama Agen...", placeholder="Ketik nama agen...")
        if search_query:
            df_display = df_display[df_display['Nama Agen'].str.contains(search_query, case=False, na=False)]
            
        m1, m2 = st.columns(2)
        m1.metric("Total Agen Terdaftar", f"{len(dict_kontak)} Agen")
        
        # Format Link Tes Chat WA
        df_display['Tes Link WA'] = df_display['No WhatsApp'].apply(
            lambda x: f"https://wa.me/{'62' + x[1:] if str(x).startswith('0') else x}"
        )
        
        st.dataframe(
            df_display[['Nama Agen', 'No WhatsApp', 'Tes Link WA']],
            column_config={
                "Tes Link WA": st.column_config.LinkColumn(
                    "Uji Chat WA",
                    display_text="💬 Kirim Tes"
                )
            },
            use_container_width=True,
            hide_index=True
        )
        
        # Tombol Backup Database JSON
        json_str = json.dumps(dict_kontak, indent=2)
        st.download_button(
            label="📥 Download Backup Database (.json)",
            data=json_str,
            file_name="database_agen_backup.json",
            mime="application/json"
        )
    else:
        st.warning("Belum ada data kontak agen yang terdaftar.")

st.markdown("---")
st.caption("KurLog Operations Portal • Developed with 💻 by **Aldi**")
