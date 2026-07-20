import streamlit as st
import pandas as pd
import urllib.parse
import json
import os
import re

st.set_page_config(
    page_title="Otomasi Bagging - KurLog", 
    page_icon="📦", 
    layout="wide"
)

st.title("📦 Otomasi Pengingat Bagging Resi")
st.caption("Unggah file Excel KurLog untuk memproses data dan menghasilkan template pesan pengingat WhatsApp.")
st.markdown("---")

# --- MEMBACA DATABASE KONTAK AGEN DARI JSON ---
DB_PATH = "CC/database_agen.json"

def get_kontak_database():
    if os.path.exists(DB_PATH):
        try:
            with open(DB_PATH, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

KONTAK_AGEN = get_kontak_database()

def format_no_wa(no_hp):
    """Mengubah format 08xx menjadi 628xx untuk link WhatsApp"""
    if not no_hp or pd.isna(no_hp):
        return ""
    clean_num = re.sub(r'\D', '', str(no_hp))
    if clean_num.startswith("0"):
        clean_num = "62" + clean_num[1:]
    return clean_num

# --- SECTION UPLOAD FILE ---
uploaded_files = st.file_uploader(
    "Unggah File KurLog (.xlsx) — Bisa pilih beberapa file sekaligus", 
    type=["xlsx"], 
    accept_multiple_files=True
)

if uploaded_files:
    dataframes = []
    for file in uploaded_files:
        try:
            df = pd.read_excel(file, header=1) 
            dataframes.append(df)
        except Exception as e:
            st.error(f"Gagal membaca file **{file.name}**: {e}")
            
    if dataframes:
        combined_df = pd.concat(dataframes, ignore_index=True)
        combined_df.columns = combined_df.columns.str.strip()
        
        # Filter Status 'Belum dibagging'
        filtered_df = combined_df[combined_df['Status Bagging'].astype(str).str.lower() == 'belum dibagging']
        
        # Dashboard Metrik
        st.markdown("<br>", unsafe_allow_html=True)
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Resi Diunggah", f"{len(combined_df):,} Paket")
        m2.metric("Belum Dibagging", f"{len(filtered_df):,} Paket")
        m3.metric("Jumlah Agen Terdampak", f"{filtered_df['Agen'].nunique()} Agen")
        
        st.markdown("---")
        st.subheader("📋 Draft Pesan Pengingat per Agen")
        
        agen_list = filtered_df['Agen'].unique()
        
        for agen in agen_list:
            agen_data = filtered_df[filtered_df['Agen'] == agen]
            sample_date = pd.to_datetime(agen_data['Tanggal'].iloc[0]).strftime('%d/%m/%Y')
            resi_list_str = "\n".join(agen_data['No Resi'].astype(str).tolist())
            
            # Match nama agen dengan database (case-insensitive)
            raw_phone = KONTAK_AGEN.get(str(agen).strip().upper(), "")
            formatted_phone = format_no_wa(raw_phone)
            
            pesan_template = f"""Selamat pagi pak, mohon maaf mengganggu waktunya pak, kami sampaikan ada paket di agen bapak {agen} pada Tanggal {sample_date} yang belum dibagging ya pak?
Mohon dibantu untuk segera dibagging.

Berikut informasi resinya :
{resi_list_str}"""
            
            encoded_message = urllib.parse.quote(pesan_template)
            
            if formatted_phone:
                wa_url = f"https://web.whatsapp.com/send?phone={formatted_phone}&text={encoded_message}"
                status_wa = f"🟢 **No. WA:** `{raw_phone}`"
            else:
                wa_url = f"https://web.whatsapp.com/send?text={encoded_message}"
                status_wa = "⚠️ *Nomor belum terdaftar di menu 'Kontak Agen'*"
            
            with st.expander(f"🏢 **{agen}** — ({len(agen_data)} Paket Belum Dibagging)", expanded=True):
                col_txt, col_btn = st.columns([3, 1])
                
                with col_txt:
                    st.caption(f"{status_wa} | 👇 *Klik icon salin di pojok kanan atas:*")
                    st.code(pesan_template, language=None)
                
                with col_btn:
                    st.markdown("<br>", unsafe_allow_html=True)
                    st.markdown(f"""
                        <a href="{wa_url}" target="_blank" style="text-decoration: none;">
                            <div style="
                                background-color: #25D366;
                                color: white !important;
                                padding: 0.7rem 1rem;
                                border-radius: 8px;
                                text-align: center;
                                font-weight: 600;
                                margin-bottom: 10px;
                                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                            ">
                                💬 Kirim ke WA Agen
                            </div>
                        </a>
                    """, unsafe_allow_html=True)
                    st.info(f"**Total Resi:** {len(agen_data)}")
                
                # Table Data
                st.dataframe(
                    agen_data[['Tanggal', 'No Resi', 'Kode Layanan', 'Status Bagging']], 
                    use_container_width=True
                )

else:
    st.info("💡 **Petunjuk**: Silakan *drag & drop* atau klik tombol di atas untuk mengunggah file Excel KurLog Anda.")

st.markdown("---")
st.caption("KurLog Operations Portal • Developed with 💻 by **Aldi**")
