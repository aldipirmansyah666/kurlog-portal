import streamlit as st
import pandas as pd
import io
from datetime import datetime

st.set_page_config(
    page_title="Data Follow Up Resi - KurLog", 
    page_icon="📑", 
    layout="wide"
)

st.title("📑 Monitoring & Follow Up Tiket Resi")
st.caption("Dashboard pemantauan tindak lanjut tiket resi bermasalah (Stuck, Kendala Pengiriman, & Retur).")
st.markdown("---")

# ---------------------------------------------------------
# 1. MEMORY & SESSION STATE
# ---------------------------------------------------------
if "df_followup" not in st.session_state:
    st.session_state.df_followup = pd.DataFrame()

# ---------------------------------------------------------
# 2. FITUR UPLOAD FILE & DETEKSI HEADER / SHEET OTOMATIS
# ---------------------------------------------------------
with st.sidebar:
    st.header("📂 Sumber Data")
    uploaded_file = st.file_uploader(
        "Unggah File Excel Google Sheets (.xlsx / .csv)", 
        type=["xlsx", "csv"]
    )
    
    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith(".csv"):
                df_raw = pd.read_csv(uploaded_file)
                sheet_selected = "CSV Data"
            else:
                xls = pd.ExcelFile(uploaded_file)
                sheet_names = xls.sheet_names
                sheet_selected = st.selectbox("📌 Pilih Tab / Sheet Tanggal", sheet_names, index=len(sheet_names)-1)
                
                # Deteksi otomatis baris header yang mengandung kata 'RESI' / 'TIKET'
                df_temp = pd.read_excel(xls, sheet_name=sheet_selected, header=None)
                header_idx = 0
                for idx, row in df_temp.iterrows():
                    row_str = " ".join([str(val).upper() for val in row.values if pd.notna(val)])
                    if 'RESI' in row_str or 'TIKET' in row_str:
                        header_idx = idx
                        break
                
                df_raw = pd.read_excel(xls, sheet_name=sheet_selected, header=header_idx)

            # Clean header column names
            df_raw.columns = df_raw.columns.astype(str).str.strip().str.upper()

            # Smart Column Matcher
            def find_col(possible_names, default_val="-"):
                for name in possible_names:
                    for col in df_raw.columns:
                        if name in col:
                            return df_raw[col].fillna(default_val).astype(str)
                return pd.Series([default_val] * len(df_raw))

            df_mapped = pd.DataFrame()
            df_mapped['TGL. TIKET'] = find_col(['TGL', 'TANGGAL', 'TIKET'])
            df_mapped['NO. RESI'] = find_col(['RESI', 'NO. RESI', 'NO RESI', 'AWB'])
            df_mapped['AGEN'] = find_col(['AGEN', 'POS', 'MITRA'])
            df_mapped['KODE LAYANAN'] = find_col(['LAYANAN', 'KODE', 'SERVICE'])
            df_mapped['PETUGAS'] = find_col(['PETUGAS', 'CS', 'ADMIN', 'USER'], default_val="CS1 MUC SWEET")
            df_mapped['STATUS RESI'] = find_col(['STATUS RESI', 'STATUS_RESI', 'STATUS'], default_val="PERJALANAN")
            df_mapped['SELESAI'] = find_col(['SELESAI', 'FINISH'], default_val="BELUM")
            
            # PENANDA TANGGAL FU KEMBALI DI
            # Mencegah TGL FU KEMBALI berubah otomatis dengan membaca tanggal tersimpan
            today_str = datetime.now().strftime('%d/%m/%Y')
            df_mapped['TGL FU KEMBALI'] = find_col(['TGL FU', 'TANGGAL FU', 'FU KEMBALI'], default_val=today_str)
            df_mapped['DETAIL'] = find_col(['DETAIL', 'CATATAN', 'KET'], default_val="HOLD HINGGA TGL ...")
            df_mapped['FU SELANJUTNYA'] = find_col(['FU SELANJUTNYA', 'FU', 'TINDAK LANJUT'], default_val="SILAKAN DI FU ULANG")
            df_mapped['CCH'] = find_col(['CCH', 'STATUS CCH'], default_val="-")

            # Hapus baris kosong yang tidak punya nomor resi
            df_mapped = df_mapped[df_mapped['NO. RESI'].str.strip() != "-"]

            st.session_state.df_followup = df_mapped.reset_index(drop=True)
            st.success(f"✅ Berhasil memuat sheet: **{sheet_selected}** ({len(df_mapped)} resi)")
            
        except Exception as e:
            st.error(f"Gagal membaca file: {e}")

    st.markdown("---")
    if not st.session_state.df_followup.empty:
        if st.button("🗑️ Reset / Kosongkan Data Sesi", use_container_width=True):
            st.session_state.df_followup = pd.DataFrame()
            st.rerun()

# ---------------------------------------------------------
# 3. METRIK & FILTER DATA
# ---------------------------------------------------------
df = st.session_state.df_followup

if not df.empty:
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Tiket Resi", f"{len(df)} Resi")
    m2.metric("Silakan FU Ulang", f"{len(df[df['FU SELANJUTNYA'].str.contains('FU', case=False, na=False)])} Resi")
    m3.metric("Status CCH", f"{len(df[df['FU SELANJUTNYA'].str.contains('CCH', case=False, na=False)])} Resi")
    m4.metric("Proses Retur", f"{len(df[df['FU SELANJUTNYA'].str.contains('RETUR', case=False, na=False)])} Resi")

    st.markdown("<br>", unsafe_allow_html=True)

    c_search, c_filter_status, c_filter_petugas = st.columns([2, 1, 1])
    with c_search:
        search_kw = st.text_input("🔍 Cari Resi / Nama Agen...", placeholder="Ketik No. Resi atau Nama Agen...")
    with c_filter_status:
        opt_status = ["SEMUA"] + list(df['STATUS RESI'].dropna().unique())
        selected_status = st.selectbox("Filter Status Resi", opt_status)
    with c_filter_petugas:
        opt_petugas = ["SEMUA"] + list(df['PETUGAS'].dropna().unique())
        selected_petugas = st.selectbox("Filter Petugas CC", opt_petugas)

    df_filtered = df.copy()
    if search_kw:
        df_filtered = df_filtered[
            df_filtered['NO. RESI'].str.contains(search_kw, case=False, na=False) |
            df_filtered['AGEN'].str.contains(search_kw, case=False, na=False)
        ]
    if selected_status != "SEMUA":
        df_filtered = df_filtered[df_filtered['STATUS RESI'] == selected_status]
    if selected_petugas != "SEMUA":
        df_filtered = df_filtered[df_filtered['PETUGAS'] == selected_petugas]

    st.markdown("---")

    # ---------------------------------------------------------
    # 4. TABEL DATA FOLLOW UP INTERAKTIF
    # ---------------------------------------------------------
    st.subheader("📋 Tabel Pemantauan & Penandaan FU Resi")
    st.info("""
        📌 **Panduan Penandaan Status:**
        * **Sukses Terkirim**: Ubah `SELESAI` -> **SUDAH**, `FU SELANJUTNYA` -> **DONE FU / SUKSES TERKIRIM**.
        * **Hold Tanggal**: Ubah `FU SELANJUTNYA` -> **HOLD HINGGA TGL**, isi `DETAIL` -> **HOLD HINGGA TGL 25/07**.
        * **Retur**: Ubah `STATUS RESI` -> **PROSES RETUR**, `FU SELANJUTNYA` -> **RETUR**.
        * **TGL FU KEMBALI**: Nilai tanggal diam & tidak akan berubah otomatis setelah tersimpan.
    """)

    edited_df = st.data_editor(
        df_filtered,
        column_config={
            "TGL. TIKET": st.column_config.TextColumn("Tgl. Tiket"),
            "NO. RESI": st.column_config.TextColumn("No. Resi"),
            "AGEN": st.column_config.TextColumn("Agen"),
            "KODE LAYANAN": st.column_config.TextColumn("Layanan"),
            "PETUGAS": st.column_config.SelectboxColumn(
                "Petugas CC",
                options=["ianCC", "CS3 MUC SWEET", "CS1 MUCSWEET", "aldiCC", "NoviaCC", "AjengCC"],
                required=True
            ),
            "STATUS RESI": st.column_config.SelectboxColumn(
                "Status Resi",
                options=["PERJALANAN", "PENGANTARAN", "POTENSI KENDALA", "PROSES RETUR", "SUKSES TERKIRIM"],
                required=True
            ),
            "SELESAI": st.column_config.SelectboxColumn(
                "Selesai",
                options=["BELUM", "SUDAH"],
                required=True
            ),
            "TGL FU KEMBALI": st.column_config.TextColumn("📅 Tgl FU Kembali (Tetap)"),
            "DETAIL": st.column_config.TextColumn("Detail Catatan (misal: HOLD TGL 25/07)"),
            "FU SELANJUTNYA": st.column_config.SelectboxColumn(
                "FU Selanjutnya",
                options=[
                    "SILAKAN DI FU ULANG",
                    "DONE FU",
                    "DONE FU 13",
                    "SUKSES TERKIRIM",
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
        num_rows="dynamic",
        key="data_editor_fu"
    )

    # ---------------------------------------------------------
    # 5. SIMPAN HASIL & DOWNLOAD
    # ---------------------------------------------------------
    st.markdown("<br>", unsafe_allow_html=True)
    c_btn1, c_btn2 = st.columns([1, 2])
    
    with c_btn1:
        if st.button("💾 Simpan Perubahan Tabel", use_container_width=True, type="primary"):
            st.session_state.df_followup = edited_df
            st.success("✅ Semua perubahan status & tanggal berhasil dikunci!")
            st.rerun()

    with c_btn2:
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            st.session_state.df_followup.to_excel(writer, index=False, sheet_name="DATA FOLLOW UP")
        
        st.download_button(
            label="📥 Download Hasil Follow Up Terbaru (.xlsx)",
            data=buffer.getvalue(),
            file_name="DATA_FOLLOW_UP_RESI_UPDATED.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

else:
    st.info("💡 **Petunjuk**: Silakan unggah file Excel Google Sheets Anda dari **Sidebar di sebelah kiri**, lalu pilih Tab/Sheet tanggal yang ingin diproses.")

# Sidebar & Footer
st.sidebar.markdown("---")
st.sidebar.markdown("🏢 **POSIX Helpdesk System**")
st.sidebar.markdown("💻 Developed by **Aldi**")

st.markdown("---")
st.caption("KurLog Operations Portal • Developed with ❤️ by **Aldi**")
