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
# 1. MEMORY & SESSION STATE FOR PERSISTENT DATA
# ---------------------------------------------------------
if "df_followup" not in st.session_state:
    st.session_state.df_followup = pd.DataFrame(columns=[
        'TGL. TIKET', 'NO. RESI', 'AGEN', 'KODE LAYANAN', 
        'PETUGAS', 'STATUS RESI', 'SELESAI', 'DETAIL', 'FU SELANJUTNYA', 'CCH'
    ])

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
            
            df_raw.columns = df_raw.columns.astype(str).str.strip().str.upper()
            
            # Fungsi Pembaca Kolom Fleksibel
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
            df_mapped['DETAIL'] = find_col(['DETAIL', 'CATATAN', 'KET'], default_val="HOLD TANGGAL")
            df_mapped['FU SELANJUTNYA'] = find_col(['FU SELANJUTNYA', 'FU', 'TINDAK LANJUT'], default_val="SILAKAN DI FU ULANG")
            df_mapped['CCH'] = find_col(['CCH', 'STATUS CCH'], default_val="-")

            st.session_state.df_followup = df_mapped
            st.success("✅ Data berhasil diimpor & dipetakan!")
            
        except Exception as e:
            st.error(f"Gagal membaca file: {e}")

    st.markdown("---")
    # Tombol Tambah Baris Manual
    if st.button("➕ Tambah Baris Baru Secara Manual", use_container_width=True):
        new_row = pd.DataFrame([{
            'TGL. TIKET': pd.Timestamp.now().strftime('%d/%m/%Y %H:%M'),
            'NO. RESI': '',
            'AGEN': '',
            'KODE LAYANAN': 'PKH',
            'PETUGAS': 'CS1 MUC SWEET',
            'STATUS RESI': 'PERJALANAN',
            'SELESAI': 'BELUM',
            'DETAIL': 'HOLD TANGGAL',
            'FU SELANJUTNYA': 'SILAKAN DI FU ULANG',
            'CCH': '-'
        }])
        st.session_state.df_followup = pd.concat([st.session_state.df_followup, new_row], ignore_index=True)
        st.rerun()

    # Tombol Reset Data
    if not st.session_state.df_followup.empty:
        if st.button("🗑️ Reset / Kosongkan Semua Data", use_container_width=True):
            st.session_state.df_followup = pd.DataFrame(columns=[
                'TGL. TIKET', 'NO. RESI', 'AGEN', 'KODE LAYANAN', 
                'PETUGAS', 'STATUS RESI', 'SELESAI', 'DETAIL', 'FU SELANJUTNYA', 'CCH'
            ])
            st.rerun()

# ---------------------------------------------------------
# 3. TAMPILAN DASHBOARD METRIK
# ---------------------------------------------------------
df = st.session_state.df_followup

if not df.empty:
    total_tiket = len(df)
    total_retur = len(df[df['FU SELANJUTNYA'].astype(str).str.contains("RETUR", case=False, na=False)])
    total_cch = len(df[df['FU SELANJUTNYA'].astype(str).str.contains("CCH", case=False, na=False)])
    total_fu_ulang = len(df[df['FU SELANJUTNYA'].astype(str).str.contains("FU", case=False, na=False)])

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Tiket Resi", f"{total_tiket} Resi")
    m2.metric("Silakan FU Ulang", f"{total_fu_ulang} Resi")
    m3.metric("Status CCH", f"{total_cch} Resi")
    m4.metric("Proses Retur", f"{total_retur} Resi")

    st.markdown("<br>", unsafe_allow_html=True)

    # ---------------------------------------------------------
    # 4. FILTER & PENCARIAN DATA
    # ---------------------------------------------------------
    c_search, c_filter_status, c_filter_petugas = st.columns([2, 1, 1])
    
    with c_search:
        search_kw = st.text_input("🔍 Cari Resi / Nama Agen...", placeholder="Ketik No. Resi atau Nama Agen...")
    
    with c_filter_status:
        opt_status = ["SEMUA"] + list(df['STATUS RESI'].dropna().unique())
        selected_status = st.selectbox("Filter Status Resi", opt_status)
        
    with c_filter_petugas:
        opt_petugas = ["SEMUA"] + list(df['PETUGAS'].dropna().unique())
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

    # ---------------------------------------------------------
    # 5. TABEL INTERAKTIF (EDIT, HAPUS, TAMBAH)
    # ---------------------------------------------------------
    st.subheader("📋 Tabel Data Follow Up")
    st.caption("💡 *Fitur Tabel: Klik cell untuk **Edit**, tekan ikon **`+`** di bawah tabel untuk **Tambah**, atau pilih baris lalu tekan **`Delete`** untuk **Hapus**.*")

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
        num_rows="dynamic",  # IZINKAN TAMBAH & HAPUS BARIS DARI TABEL
        key="data_editor_fu"
    )

    # ---------------------------------------------------------
    # 6. SIMPAN HASIL & DOWNLOAD EXCEL
    # ---------------------------------------------------------
    st.markdown("<br>", unsafe_allow_html=True)
    c_btn1, c_btn2 = st.columns([1, 2])
    
    with c_btn1:
        if st.button("💾 Simpan Perubahan Tabel", use_container_width=True, type="primary"):
            st.session_state.df_followup = edited_df
            st.success("✅ Semua editan, penambahan, dan penghapusan berhasil disimpan!")
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
    st.info("💡 **Petunjuk**: Silakan unggah file ekspor tiket resi (`.xlsx` / `.csv`) dari **Sidebar di sebelah kiri** atau klik tombol **`➕ Tambah Baris Baru Secara Manual`** di sidebar untuk mulai mengisi data.")

# Sidebar & Footer
st.sidebar.markdown("---")
st.sidebar.markdown("🏢 **POSIX Helpdesk System**")
st.sidebar.markdown("💻 Developed by **Aldi**")

st.markdown("---")
st.caption("KurLog Operations Portal • Developed with ❤️ by **Aldi**")
