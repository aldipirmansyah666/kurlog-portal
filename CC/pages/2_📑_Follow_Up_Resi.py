import streamlit as st
import pandas as pd
import io

st.set_page_config(
    page_title="Data Follow Up Resi - KurLog", 
    page_icon="📑", 
    layout="wide"
)

st.title("📑 Monitoring & Follow Up Tiket Resi")
st.caption("Dashboard pemantauan tindak lanjut tiket resi bermasalah (Stuck, Kendala Pengiriman, & Retur).")
st.markdown("---")

# ---------------------------------------------------------
# 1. BACA / SIMPAN DATA DI SESSION STATE
# ---------------------------------------------------------
if "df_followup" not in st.session_state:
    st.session_state.df_followup = pd.DataFrame()

# ---------------------------------------------------------
# 2. FITUR UPLOAD FILE EKSPOR KURLOG TICKET
# ---------------------------------------------------------
with st.sidebar:
    st.header("📂 Sumber Data")
    uploaded_file = st.file_uploader(
        "Unggah Ekspor Tiket Resi (.xlsx / .csv)", 
        type=["xlsx", "csv"]
    )
    
    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith(".csv"):
                df_raw = pd.read_csv(uploaded_file)
            else:
                df_raw = pd.read_excel(uploaded_file)
            
            # Rapikan nama kolom
            df_raw.columns = df_raw.columns.str.strip()
            
            # Memastikan kolom standar tersedia
            kolom_wajib = ['TGL. TIKET', 'NO. RESI', 'AGEN', 'KODE LAYANAN', 'PETUGAS', 'STATUS RESI', 'SELESAI']
            for col in kolom_wajib:
                if col not in df_raw.columns:
                    df_raw[col] = "-"
            
            # Tambahkan kolom FU jika belum ada
            if 'DETAIL' not in df_raw.columns:
                df_raw['DETAIL'] = "HOLD TANGGAL"
            if 'FU SELANJUTNYA' not in df_raw.columns:
                df_raw['FU SELANJUTNYA'] = "SILAKAN DI FU ULANG"
            if 'CCH' not in df_raw.columns:
                df_raw['CCH'] = "-"

            st.session_state.df_followup = df_raw[
                ['TGL. TIKET', 'NO. RESI', 'AGEN', 'KODE LAYANAN', 'PETUGAS', 'STATUS RESI', 'SELESAI', 'DETAIL', 'FU SELANJUTNYA', 'CCH']
            ].copy()
            
            st.success("✅ Data berhasil diimpor!")
        except Exception as e:
            st.error(f"Gagal membaca file: {e}")

# ---------------------------------------------------------
# 3. TAMPILAN DASHBOARD METRIK
# ---------------------------------------------------------
df = st.session_state.df_followup

if not df.empty:
    # Metrik Ringkasan
    total_tiket = len(df)
    total_retur = len(df[df['FU SELANJUTNYA'].astype(str).str.contains("RETUR", case=False, na=False)])
    total_cch = len(df[df['FU SELANJUTNYA'].astype(str).str.contains("CCH", case=False, na=False)])
    total_fu_ulang = len(df[df['FU SELANJUTNYA'].astype(str).str.contains("FU", case=False, na=False)])

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Tiket Resi", f"{total_tiket} Resi")
    m2.metric("Silakan FU Ulang", f"{total_fu_ulang} Resi", delta_color="normal")
    m3.metric("Status CCH", f"{total_cch} Resi", delta_color="off")
    m4.metric("Proses Retur", f"{total_retur} Resi", delta_color="inverse")

    st.markdown("<br>", unsafe_allow_html=True)

    # ---------------------------------------------------------
    # 4. FILTER & PENCARIAN DATA
    # ---------------------------------------------------------
    c_search, c_filter_status, c_filter_petugas = st.columns([2, 1, 1])
    
    with c_search:
        search_kw = st.text_input("🔍 Cari Resi / Nama Agen...", placeholder="Ketik No. Resi atau Nama Agen...")
    
    with c_filter_status:
        opt_status = ["SEMUA"] + list(df['STATUS RESI'].unique())
        selected_status = st.selectbox("Filter Status Resi", opt_status)
        
    with c_filter_petugas:
        opt_petugas = ["SEMUA"] + list(df['PETUGAS'].unique())
        selected_petugas = st.selectbox("Filter Petugas CC", opt_petugas)

    # Filtering Logic
    df_filtered = df.copy()
    if search_kw:
        df_filtered = df_filtered[
            df_filtered['NO. RESI'].astype(str).str.contains(search_kw, case=False, na=False) |
            df_filtered['AGEN'].astype(str).str.contains(search_kw, case=False, na=False)
        ]
    if selected_status != "SEMUA":
        df_filtered = df_filtered[df_filtered['STATUS RESI'] == selected_status]
    if selected_petugas != "SEMUA":
        df_filtered = df_filtered[df_filtered['PETUGAS'] == selected_petugas]

    st.markdown("---")

    # Legend Penanda Warna
    st.markdown("""
        **Keterangan Warna Status FU:**
        - 🟢 **Hijau**: Silakan di-FU ulang / Done FU / Sukses Terkirim
        - 🟠 **Oranye**: CCH Ulang / Sudah CCH
        - 🔴 **Merah**: Retur / Proses Retur
    """)

    # ---------------------------------------------------------
    # 5. TABEL INTERAKTIF (EDITABLE TABLE WITH COLORING)
    # ---------------------------------------------------------
    # Fungsi Pemberian Warna Baris/Cell
    def highlight_fu(val):
        val_str = str(val).upper()
        if "RETUR" in val_str:
            return 'background-color: #ff4d4d; color: white; font-weight: bold;'
        elif "CCH" in val_str:
            return 'background-color: #ff9900; color: white; font-weight: bold;'
        elif "FU" in val_str or "DONE" in val_str or "SUKSES" in val_str:
            return 'background-color: #28a745; color: white; font-weight: bold;'
        return ''

    # Gunakan st.data_editor agar tim CC bisa langsung mengedit status/catatan di tabel
    edited_df = st.data_editor(
        df_filtered,
        column_config={
            "TGL. TIKET": st.column_config.TextColumn("Tgl. Tiket", disabled=True),
            "NO. RESI": st.column_config.TextColumn("No. Resi", disabled=True),
            "AGEN": st.column_config.TextColumn("Agen", disabled=True),
            "KODE LAYANAN": st.column_config.TextColumn("Layanan", disabled=True),
            "PETUGAS": st.column_config.SelectboxColumn(
                "Petugas CC",
                options=["ianCC", "CS3 MUC SWEET", "CS1 MUCSWEET", "aldiCC", "NoviaCC", "AjengCC"],
                required=True
            ),
            "STATUS RESI": st.column_config.SelectboxColumn(
                "Status Resi",
                options=["PERJALANAN", "PENGANTARAN", "POTENSI KENDALA", "PROSES RETUR"],
                required=True
            ),
            "SELESAI": st.column_config.SelectboxColumn(
                "Selesai",
                options=["BELUM", "SUDAH"],
                required=True
            ),
            "DETAIL": st.column_config.TextColumn("Detail Catatan"),
            "FU SELANJUTNYA": st.column_config.SelectboxColumn(
                "FU Selanjutnya",
                options=[
                    "SILAKAN DI FU ULANG",
                    "DONE FU",
                    "DONE FU 13",
                    "HOLD HINGGA TGL",
                    "SUDAH DI CCH",
                    "CCH ULANG",
                    "PROSES RETUR",
                    "RETUR"
                ],
                required=True
            ),
            "CCH": st.column_config.TextColumn("Status CCH")
        },
        use_container_width=True,
        hide_index=True,
        num_rows="dynamic"
    )

    # ---------------------------------------------------------
    # 6. EKSPOR HASIL FOLLOW UP KE EXCEL
    # ---------------------------------------------------------
    st.markdown("<br>", unsafe_allow_html=True)
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        edited_df.to_excel(writer, index=False, sheet_name="DATA FOLLOW UP")
    
    st.download_button(
        label="📥 Download Hasil Follow Up (.xlsx)",
        data=buffer.getvalue(),
        file_name="DATA_FOLLOW_UP_RESI_UPDATED.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

else:
    # Tampilan saat belum ada file yang diunggah
    st.info("💡 **Petunjuk**: Silakan unggah file ekspor tiket resi (`.xlsx` / `.csv`) dari web KurLog melalui **Sidebar di sebelah kiri** untuk menampilkan dashboard Follow Up.")

# Sidebar & Footer
st.sidebar.markdown("---")
st.sidebar.markdown("🏢 **POSIX Helpdesk System**")
st.sidebar.markdown("💻 Developed by **Aldi**")

st.markdown("---")
st.caption("KurLog Operations Portal • Developed with ❤️ by **Aldi**")
