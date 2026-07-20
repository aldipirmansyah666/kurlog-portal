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
st.caption("Dashboard pemantauan tindak lanjut tiket resi bermasalah (Stuck, Kendala Pengiriman, CCH, & Retur).")
st.markdown("---")

# ---------------------------------------------------------
# 1. INIT SESSION STATE (DEFAULT TABEL KOSONG UNTUK INPUT MANUAL)
# ---------------------------------------------------------
def create_empty_df(num_rows=10):
    today_str = datetime.now().strftime('%d/%m/%Y')
    data = []
    for _ in range(num_rows):
        data.append({
            'TGL. TIKET': today_str,
            'NO. RESI': '',
            'AGEN': '',
            'KODE LAYANAN': 'PKH',
            'PETUGAS': 'CS1 MUC SWEET',
            'STATUS RESI': 'PERJALANAN',
            'SELESAI': 'BELUM',
            'TGL FU KEMBALI': today_str,
            'DETAIL': '-',
            'FU SELANJUTNYA': 'SILAKAN DI FU ULANG',
            'CCH': '-'
        })
    return pd.DataFrame(data)

if "df_followup" not in st.session_state or st.session_state.df_followup.empty:
    st.session_state.df_followup = create_empty_df(10)

# ---------------------------------------------------------
# 2. SIDEBAR - UPLOAD EXCEL / RESTORE DATA
# ---------------------------------------------------------
with st.sidebar:
    st.header("📂 Sumber Data")
    
    uploaded_file = st.file_uploader(
        "Unggah File Excel / Google Sheets (.xlsx / .csv)", 
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
                
                df_temp = pd.read_excel(xls, sheet_name=sheet_selected, header=None)
                header_idx = 0
                for idx, row in df_temp.iterrows():
                    row_str = " ".join([str(val).upper() for val in row.values if pd.notna(val)])
                    if 'RESI' in row_str or 'TIKET' in row_str:
                        header_idx = idx
                        break
                
                df_raw = pd.read_excel(xls, sheet_name=sheet_selected, header=header_idx)

            df_raw.columns = df_raw.columns.astype(str).str.strip().str.upper()

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
            
            today_str = datetime.now().strftime('%d/%m/%Y')
            df_mapped['TGL FU KEMBALI'] = find_col(['TGL FU', 'TANGGAL FU', 'FU KEMBALI'], default_val=today_str)
            df_mapped['DETAIL'] = find_col(['DETAIL', 'CATATAN', 'KET'], default_val="-")
            df_mapped['FU SELANJUTNYA'] = find_col(['FU SELANJUTNYA', 'FU', 'TINDAK LANJUT'], default_val="SILAKAN DI FU ULANG")
            df_mapped['CCH'] = find_col(['CCH', 'STATUS CCH'], default_val="-")

            # Hapus Baris Kosong
            df_mapped = df_mapped[df_mapped['NO. RESI'].str.strip() != "-"].reset_index(drop=True)

            if not df_mapped.empty:
                st.session_state.df_followup = df_mapped
                st.success(f"✅ Sheet **{sheet_selected}** ({len(df_mapped)} Resi) Berhasil Diimpor!")
            
        except Exception as e:
            st.error(f"Gagal membaca file: {e}")

    st.markdown("---")
    c_sb1, c_sb2 = st.columns(2)
    with c_sb1:
        if st.button("➕ 5 Baris", use_container_width=True):
            st.session_state.df_followup = pd.concat([st.session_state.df_followup, create_empty_df(5)], ignore_index=True)
            st.rerun()
    with c_sb2:
        if st.button("🗑️ Bersihkan", use_container_width=True):
            st.session_state.df_followup = create_empty_df(10)
            st.rerun()

# ---------------------------------------------------------
# 3. METRIK DASHBOARD
# ---------------------------------------------------------
df = st.session_state.df_followup
df_valid = df[df['NO. RESI'].astype(str).str.strip() != ""].copy()

total_tiket = len(df_valid)

mask_cch = (
    df_valid['CCH'].astype(str).str.contains("CCH", case=False, na=False) |
    df_valid['FU SELANJUTNYA'].astype(str).str.contains("CCH", case=False, na=False) |
    df_valid['DETAIL'].astype(str).str.contains("CCH", case=False, na=False)
)
total_cch = len(df_valid[mask_cch])

mask_retur = (
    df_valid['STATUS RESI'].astype(str).str.contains("RETUR", case=False, na=False) |
    df_valid['FU SELANJUTNYA'].astype(str).str.contains("RETUR", case=False, na=False)
)
total_retur = len(df_valid[mask_retur])

mask_done = (
    (df_valid['SELESAI'].astype(str).str.upper() == "SUDAH") |
    df_valid['FU SELANJUTNYA'].astype(str).str.contains("DONE", case=False, na=False) |
    df_valid['FU SELANJUTNYA'].astype(str).str.contains("SUKSES", case=False, na=False)
)
total_done = len(df_valid[mask_done])
total_fu_ulang = total_tiket - (total_cch + total_retur + total_done)
if total_fu_ulang < 0:
    total_fu_ulang = 0

m1, m2, m3, m4 = st.columns(4)
m1.metric("Total Tiket Resi", f"{total_tiket} Resi")
m2.metric("Silakan FU Ulang", f"{total_fu_ulang} Resi")
m3.metric("Status CCH", f"{total_cch} Resi")
m4.metric("Proses Retur", f"{total_retur} Resi")

st.markdown("<br>", unsafe_allow_html=True)

# ---------------------------------------------------------
# 4. FILTERING SYSTEM
# ---------------------------------------------------------
c_search, c_filter_status, c_filter_cch, c_filter_petugas = st.columns([2, 1, 1, 1])

with c_search:
    search_kw = st.text_input("🔍 Cari Resi / Nama Agen...", placeholder="Ketik No. Resi atau Nama Agen...")
with c_filter_status:
    opt_status = ["SEMUA"] + [x for x in df['STATUS RESI'].dropna().unique() if x != ""]
    selected_status = st.selectbox("Filter Status Resi", opt_status)
with c_filter_cch:
    selected_cch_filter = st.selectbox("Filter CCH", ["SEMUA", "Hanya CCH", "Bukan CCH"])
with c_filter_petugas:
    opt_petugas = ["SEMUA"] + [x for x in df['PETUGAS'].dropna().unique() if x != ""]
    selected_petugas = st.selectbox("Filter Petugas CC", opt_petugas)

df_filtered = df.copy()
if search_kw:
    df_filtered = df_filtered[
        df_filtered['NO. RESI'].astype(str).str.contains(search_kw, case=False, na=False) |
        df_filtered['AGEN'].astype(str).str.contains(search_kw, case=False, na=False)
    ]
if selected_status != "SEMUA":
    df_filtered = df_filtered[df_filtered['STATUS RESI'] == selected_status]
if selected_cch_filter == "Hanya CCH":
    df_filtered = df_filtered[mask_cch]
elif selected_cch_filter == "Bukan CCH":
    df_filtered = df_filtered[~mask_cch]
if selected_petugas != "SEMUA":
    df_filtered = df_filtered[df_filtered['PETUGAS'] == selected_petugas]

st.markdown("---")

# ---------------------------------------------------------
# 5. TABEL DATA INTERAKTIF & EDITABLE
# ---------------------------------------------------------
st.subheader("📋 Tabel Pemantauan & Penandaan FU Resi")
st.caption("⚡ *Anda bisa langsung mengisikan/copas data pada tabel di bawah. Klik tombol **`➕ 5 Baris`** di sidebar untuk menambah baris kosong.*")

edited_df = st.data_editor(
    df_filtered,
    column_config={
        "TGL. TIKET": st.column_config.TextColumn("Tgl. Tiket"),
        "NO. RESI": st.column_config.TextColumn("No. Resi"),
        "AGEN": st.column_config.TextColumn("Agen"),
        "KODE LAYANAN": st.column_config.TextColumn("Layanan"),
        "PETUGAS": st.column_config.SelectboxColumn(
            "Petugas CC",
            options=["ianCC", "CS3 MUC SWEET", "CS1 MUCSWEET", "CS2 MUC SWEET", "aldiCC", "NoviaCC", "AjengCC"],
            required=True
        ),
        "STATUS RESI": st.column_config.SelectboxColumn(
            "Status Resi",
            options=["PERJALANAN", "PENGANTARAN", "POTENSI KENDALA", "KENDALA", "PROSES RETUR", "SUKSES TERKIRIM"],
            required=True
        ),
        "SELESAI": st.column_config.SelectboxColumn(
            "Selesai",
            options=["BELUM", "SUDAH"],
            required=True
        ),
        "TGL FU KEMBALI": st.column_config.TextColumn("📅 Tgl FU Kembali"),
        "DETAIL": st.column_config.TextColumn("Detail Catatan"),
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
                "POTENSI CCH",
                "PROSES RETUR",
                "RETUR"
            ],
            required=True
        ),
        "CCH": st.column_config.SelectboxColumn(
            "Status CCH",
            options=["-", "SUDAH DI CCH", "POTENSI CCH", "CCH ULANG"],
            required=True
        )
    },
    use_container_width=True,
    hide_index=True,
    num_rows="dynamic",
    key="data_editor_fu_v4"
)

# Keep track of edited dataframe in session state
st.session_state.df_followup = edited_df

# ---------------------------------------------------------
# 6. EKSPOR EXCEL
# ---------------------------------------------------------
st.markdown("<br>", unsafe_allow_html=True)
buffer = io.BytesIO()
with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
    st.session_state.df_followup.to_excel(writer, index=False, sheet_name="DATA FOLLOW UP")

st.download_button(
    label="📥 Download Hasil Follow Up / Update Data (.xlsx)",
    data=buffer.getvalue(),
    file_name=f"DATA_FOLLOW_UP_RESI_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    use_container_width=True,
    type="primary"
)

# Sidebar & Footer
st.sidebar.markdown("---")
st.sidebar.markdown("🏢 **POSIX Helpdesk System**")
st.sidebar.markdown("💻 Developed by **Aldi**")

st.markdown("---")
st.caption("KurLog Operations Portal • Developed with ❤️ by **Aldi**")
