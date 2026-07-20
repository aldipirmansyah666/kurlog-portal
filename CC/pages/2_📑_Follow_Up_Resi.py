import streamlit as st
import pandas as pd
import io
import os
import json
from datetime import datetime

st.set_page_config(
    page_title="Data Follow Up Resi - KurLog", 
    page_icon="📑", 
    layout="wide"
)

st.title("📑 Monitoring & Follow Up Tiket Resi")
st.caption("Dashboard pemantauan tindak lanjut tiket resi bermasalah (Stuck, Kendala Pengiriman, CCH, & Retur).")
st.markdown("---")

# PATH PENYIMPANAN PERMANEN (LOKAL)
DATA_STORAGE_PATH = "CC/data_followup_saved.json"

# ---------------------------------------------------------
# 1. FUNGSIONALITAS LOAD & SAVE DATA PERMANEN
# ---------------------------------------------------------
def save_data_permanently(df):
    try:
        os.makedirs(os.path.dirname(DATA_STORAGE_PATH), exist_ok=True)
        # Hapus baris yang sepenuhnya kosong jika ada dari hasil copas
        df_clean = df.dropna(how="all").copy()
        df_clean.to_json(DATA_STORAGE_PATH, orient="records", date_format="iso")
        return True
    except Exception as e:
        st.error(f"Gagal menyimpan data ke penyimpanan permanen: {e}")
        return False

def load_permanent_data():
    if os.path.exists(DATA_STORAGE_PATH):
        try:
            df = pd.read_json(DATA_STORAGE_PATH, orient="records")
            return df
        except Exception:
            return pd.DataFrame()
    return pd.DataFrame()

# Initialize Session State
if "df_followup" not in st.session_state or st.session_state.df_followup.empty:
    st.session_state.df_followup = load_permanent_data()

# ---------------------------------------------------------
# 2. CALLBACK UNTUK AUTO-SAVE SAAT EDIT / COPAS
# ---------------------------------------------------------
def auto_save_callback():
    # Ambil perubahan terbaru dari widget data_editor
    if "data_editor_fu_v3" in st.session_state:
        editor_state = st.session_state["data_editor_fu_v3"]
        
        # Ambil dataframe saat ini
        current_df = st.session_state.df_followup.copy()
        
        # 1. Terapkan perubahan editan sel (Edited Rows)
        for row_idx_str, changes in editor_state.get("edited_rows", {}).items():
            row_idx = int(row_idx_str)
            if row_idx < len(current_df):
                for col_name, new_val in changes.items():
                    current_df.at[row_idx, col_name] = new_val
                    
        # 2. Terapkan penambahan baris / copas (Added Rows)
        added_rows = editor_state.get("added_rows", [])
        if added_rows:
            new_rows_df = pd.DataFrame(added_rows)
            current_df = pd.concat([current_df, new_rows_df], ignore_index=True)
            
        # 3. Terapkan penghapusan baris (Deleted Rows)
        deleted_indices = editor_state.get("deleted_rows", [])
        if deleted_indices:
            current_df = current_df.drop(index=deleted_indices).reset_index(drop=True)
            
        # Simpan hasil perubahan ke session state dan file json permanen
        st.session_state.df_followup = current_df
        save_data_permanently(current_df)

# ---------------------------------------------------------
# 3. SIDEBAR - UPLOAD & SUMBER DATA
# ---------------------------------------------------------
with st.sidebar:
    st.header("📂 Sumber Data")
    
    # Indikator Auto-Save
    if not st.session_state.df_followup.empty:
        st.success("🟢 **Auto-Save Aktif (Tersimpan Permanen)**")
    else:
        st.info("⚪ *Belum ada data tersimpan*")

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
                
                # Auto Detect Baris Header
                df_temp = pd.read_excel(xls, sheet_name=sheet_selected, header=None)
                header_idx = 0
                for idx, row in df_temp.iterrows():
                    row_str = " ".join([str(val).upper() for val in row.values if pd.notna(val)])
                    if 'RESI' in row_str or 'TIKET' in row_str:
                        header_idx = idx
                        break
                
                df_raw = pd.read_excel(xls, sheet_name=sheet_selected, header=header_idx)

            # Rapikan Kolom Header
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
            df_mapped['DETAIL'] = find_col(['DETAIL', 'CATATAN', 'KET'], default_val="HOLD HINGGA TGL ...")
            df_mapped['FU SELANJUTNYA'] = find_col(['FU SELANJUTNYA', 'FU', 'TINDAK LANJUT'], default_val="SILAKAN DI FU ULANG")
            df_mapped['CCH'] = find_col(['CCH', 'STATUS CCH'], default_val="-")

            # Hapus Baris Kosong
            df_mapped = df_mapped[df_mapped['NO. RESI'].str.strip() != "-"].reset_index(drop=True)

            # Simpan Otomatis ke Session State & File Permanen
            st.session_state.df_followup = df_mapped
            save_data_permanently(df_mapped)
            st.success(f"✅ Sheet **{sheet_selected}** ({len(df_mapped)} Resi) Berhasil Diimpor & Disimpan!")
            st.rerun()
            
        except Exception as e:
            st.error(f"Gagal membaca file: {e}")

    st.markdown("---")
    if not st.session_state.df_followup.empty:
        if st.button("🗑️ Reset & Hapus Data Permanen", use_container_width=True):
            st.session_state.df_followup = pd.DataFrame()
            if os.path.exists(DATA_STORAGE_PATH):
                os.remove(DATA_STORAGE_PATH)
            st.rerun()

# ---------------------------------------------------------
# 4. METRIK & PENGENALAN CCH OTOMATIS
# ---------------------------------------------------------
df = st.session_state.df_followup

if not df.empty:
    total_tiket = len(df)
    
    # Deteksi CCH jika ada kata 'CCH' di kolom CCH, FU SELANJUTNYA, atau DETAIL
    mask_cch = (
        df['CCH'].astype(str).str.contains("CCH", case=False, na=False) |
        df['FU SELANJUTNYA'].astype(str).str.contains("CCH", case=False, na=False) |
        df['DETAIL'].astype(str).str.contains("CCH", case=False, na=False)
    )
    total_cch = len(df[mask_cch])

    # Deteksi Retur
    mask_retur = (
        df['STATUS RESI'].astype(str).str.contains("RETUR", case=False, na=False) |
        df['FU SELANJUTNYA'].astype(str).str.contains("RETUR", case=False, na=False)
    )
    total_retur = len(df[mask_retur])

    # Deteksi Selesai / Done FU
    mask_done = (
        (df['SELESAI'].astype(str).str.upper() == "SUDAH") |
        df['FU SELANJUTNYA'].astype(str).str.contains("DONE", case=False, na=False) |
        df['FU SELANJUTNYA'].astype(str).str.contains("SUKSES", case=False, na=False)
    )
    total_done = len(df[mask_done])
    total_fu_ulang = total_tiket - (total_cch + total_retur + total_done)
    if total_fu_ulang < 0:
        total_fu_ulang = 0

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Tiket Resi", f"{total_tiket} Resi")
    m2.metric("Silakan FU Ulang", f"{total_fu_ulang} Resi")
    m3.metric("Status CCH (Deteksi Otomatis)", f"{total_cch} Resi")
    m4.metric("Proses Retur", f"{total_retur} Resi")

    st.markdown("<br>", unsafe_allow_html=True)

    # ---------------------------------------------------------
    # 5. FILTERING SYSTEM
    # ---------------------------------------------------------
    c_search, c_filter_status, c_filter_cch, c_filter_petugas = st.columns([2, 1, 1, 1])
    
    with c_search:
        search_kw = st.text_input("🔍 Cari Resi / Nama Agen...", placeholder="Ketik No. Resi atau Nama Agen...")
    with c_filter_status:
        opt_status = ["SEMUA"] + list(df['STATUS RESI'].dropna().unique())
        selected_status = st.selectbox("Filter Status Resi", opt_status)
    with c_filter_cch:
        selected_cch_filter = st.selectbox("Filter CCH", ["SEMUA", "Hanya CCH", "Bukan CCH"])
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
    if selected_cch_filter == "Hanya CCH":
        df_filtered = df_filtered[mask_cch]
    elif selected_cch_filter == "Bukan CCH":
        df_filtered = df_filtered[~mask_cch]
    if selected_petugas != "SEMUA":
        df_filtered = df_filtered[df_filtered['PETUGAS'] == selected_petugas]

    st.markdown("---")

    # ---------------------------------------------------------
    # 6. TABEL DATA INTERAKTIF & AUTO-SAVE ON CHANGE (COPAS)
    # ---------------------------------------------------------
    st.subheader("📋 Tabel Pemantauan & Penandaan FU Resi")
    st.caption("⚡ *Sistem ini menggunakan **Auto-Save**. Hasil Copy-Paste (Ctrl+V) dan editan sel akan tersimpan otomatis secara permanen.*")

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
        key="data_editor_fu_v3",
        on_change=auto_save_callback  # MENTRIGGER AUTO SAVE SAAT TERJADI COPAS / EDIT
    )

    # ---------------------------------------------------------
    # 7. EKSPOR EXCEL
    # ---------------------------------------------------------
    st.markdown("<br>", unsafe_allow_html=True)
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        st.session_state.df_followup.to_excel(writer, index=False, sheet_name="DATA FOLLOW UP")
    
    st.download_button(
        label="📥 Download Hasil Follow Up Terbaru (.xlsx)",
        data=buffer.getvalue(),
        file_name=f"DATA_FOLLOW_UP_RESI_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )

else:
    st.info("💡 **Petunjuk**: Silakan unggah file Excel Google Sheets Anda melalui **Sidebar di sebelah kiri** atau salin-tempel (Ctrl+V) data langsung ke tabel.")

# Sidebar & Footer
st.sidebar.markdown("---")
st.sidebar.markdown("🏢 **POSIX Helpdesk System**")
st.sidebar.markdown("💻 Developed by **Aldi**")

st.markdown("---")
st.caption("KurLog Operations Portal • Developed with ❤️ by **Aldi**")
