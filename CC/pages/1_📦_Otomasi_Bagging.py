import streamlit as st
import pandas as pd
import urllib.parse

st.set_page_config(
    page_title="Otomasi Bagging - KurLog", 
    page_icon="📦", 
    layout="wide"
)

# Custom Styling
st.markdown("""
    <style>
    .stApp { background-color: #f8fafc !important; }
    
    .stApp, .stApp p, .stApp h1, .stApp h2, .stApp h3, .stApp span, .stApp label {
        color: #0f172a !important;
    }

    .stCaption { color: #475569 !important; }

    div[data-testid="stMetric"] {
        background-color: #ffffff !important;
        border: 1px solid #cbd5e1 !important;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    div[data-testid="stMetric"] * { color: #0f172a !important; }

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

st.title("📦 Otomasi Pengingat Bagging Resi")
st.caption("Unggah file Excel KurLog untuk memproses data dan menghasilkan template pesan pengingat WhatsApp.")
st.markdown("---")

# Section Upload
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
            
            pesan_template = f"""Selamat pagi pak, mohon maaf mengganggu waktunya pak, kami sampaikan ada paket di agen bapak {agen} pada Tanggal {sample_date} yang belum dibagging ya pak?
Mohon dibantu untuk segera dibagging.

Berikut informasi resinya :
{resi_list_str}"""
            
            # Encoded pesan untuk URL WhatsApp Web Direct
            encoded_message = urllib.parse.quote(pesan_template)
            wa_url = f"https://web.whatsapp.com/send?text={encoded_message}"
            
            with st.expander(f"🏢 **{agen}** — ({len(agen_data)} Paket Belum Dibagging)", expanded=True):
                col_txt, col_btn = st.columns([3, 1])
                
                with col_txt:
                    st.caption("👇 *Klik icon salin di pojok kanan atas kotak di bawah untuk menyalin teks:*")
                    st.code(pesan_template, language=None)
                
                with col_btn:
                    st.markdown("<br>", unsafe_allow_html=True)
                    st.markdown(f"""
                        <a href="{wa_url}" target="_blank" style="text-decoration: none;">
                            <div style="
                                background-color: #25D366;
                                color: white !important;
                                padding: 0.6rem 1rem;
                                border-radius: 8px;
                                text-align: center;
                                font-weight: 600;
                                margin-bottom: 10px;
                                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                            ">
                                💬 Buka di WA Web
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


# Floating Footer Watermark
st.markdown("""
    <div class="dev-footer">
        KurLog Operations Portal • Developed with by <b>Aldi</b>
    </div>
""", unsafe_allow_html=True)