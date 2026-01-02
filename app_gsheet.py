import streamlit as st
import pandas as pd
from google.oauth2 import service_account
import gspread
from gspread_dataframe import set_with_dataframe
from datetime import datetime
from gspread.utils import rowcol_to_a1

# --- KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="Budget Planner",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS STYLING PROFESIONAL (NETRAL) ---
st.markdown("""
<style>
    /* Font Global */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        color: #333333;
    }

    /* Background Utama */
    .stApp {
        background-color: #F8F9FA;
    }

    /* Header Styling */
    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        color: #2C3E50;
        margin-bottom: 0.5rem;
    }
    
    .sub-title {
        font-size: 1rem;
        color: #6C757D;
        margin-bottom: 2rem;
        border-bottom: 1px solid #DEE2E6;
        padding-bottom: 1rem;
    }

    /* Metric Cards (Kotak Dashboard) */
    div[data-testid="metric-container"] {
        background-color: #FFFFFF;
        border: 1px solid #DEE2E6;
        padding: 20px;
        border-radius: 6px; /* Sudut sedikit melengkung */
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        text-align: left; /* Teks rata kiri biar formal */
    }

    div[data-testid="metric-container"] label {
        color: #6C757D; /* Warna label abu-abu */
        font-size: 0.9rem;
    }

    div[data-testid="metric-container"] div[data-testid="stMetricValue"] {
        color: #2C3E50; /* Angka warna gelap */
        font-size: 1.8rem;
    }

    /* Tombol (Buttons) */
    .stButton > button {
        background-color: #2C3E50; /* Warna Biru Tua Donker */
        color: white;
        border-radius: 4px;
        border: none;
        padding: 0.5rem 1rem;
        font-weight: 600;
        transition: background-color 0.2s;
    }
    
    .stButton > button:hover {
        background-color: #1A252F; /* Lebih gelap saat hover */
        color: white;
    }

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #FFFFFF;
        border-right: 1px solid #DEE2E6;
    }
    
    section[data-testid="stSidebar"] h2 {
        color: #2C3E50;
        font-size: 1.2rem;
    }

    /* Data Editor (Tabel) */
    div[data-testid="stDataEditor"] {
        border: 1px solid #DEE2E6;
        border-radius: 4px;
        background-color: white;
    }
</style>
""", unsafe_allow_html=True)

# --- KONFIGURASI GOOGLE SHEETS ---
SPREADSHEET_ID = "1TQAOaIcGsW9SiXySWXhpsABHkMsrPe1yf9x9a9FIZys"
WORKSHEET_NAME = "Sheet1"

@st.cache_resource
def init_gsheet_connection():
    try:
        credentials_dict = st.secrets["gcp_service_account"]
        credentials = service_account.Credentials.from_service_account_info(
            credentials_dict,
            scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        )
        gc = gspread.authorize(credentials)
        return gc
    except Exception as e:
        st.error(f"Error Koneksi Database: {str(e)}")
        return None

@st.cache_data(ttl=5)
def load_data_from_sheet():
    try:
        gc = init_gsheet_connection()
        if gc is None: return None
        
        spreadsheet = gc.open_by_key(SPREADSHEET_ID)
        worksheet = spreadsheet.worksheet(WORKSHEET_NAME)
        
        data = worksheet.get_all_values()
        
        expected_cols = ['Nama Barang', 'Qty', 'Harga Input', 'Total Akhir', 'Tipe', 'Status Pembayaran', 'Status Checkout']
        
        if len(data) <= 1:
            return pd.DataFrame(columns=expected_cols)
        
        df = pd.DataFrame(data[1:], columns=data[0])
        
        for col in expected_cols:
            if col not in df.columns:
                df[col] = "FALSE"
        
        df['Qty'] = pd.to_numeric(df['Qty'], errors='coerce').fillna(0).astype(int)
        df['Harga Input'] = pd.to_numeric(df['Harga Input'], errors='coerce').fillna(0).astype(int)
        df['Total Akhir'] = pd.to_numeric(df['Total Akhir'], errors='coerce').fillna(0).astype(int)
        
        df['Status Pembayaran'] = df['Status Pembayaran'].apply(lambda x: True if str(x).upper() == 'TRUE' else False)
        df['Status Checkout'] = df['Status Checkout'].apply(lambda x: True if str(x).upper() == 'TRUE' else False)
        
        return df[expected_cols]
    
    except Exception as e:
        st.error(f"Gagal memuat data: {str(e)}")
        return None

def append_to_sheet(nama, qty, harga, total, tipe, lunas, checkout):
    try:
        gc = init_gsheet_connection()
        if gc is None: return False
        
        spreadsheet = gc.open_by_key(SPREADSHEET_ID)
        worksheet = spreadsheet.worksheet(WORKSHEET_NAME)
        
        str_lunas = "TRUE" if lunas else "FALSE"
        str_checkout = "TRUE" if checkout else "FALSE"
        
        new_row = [nama, int(qty), int(harga), int(total), tipe, str_lunas, str_checkout]
        worksheet.append_row(new_row)
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"Gagal menyimpan data: {str(e)}")
        return False

def update_sheet_data(df_edited):
    try:
        gc = init_gsheet_connection()
        if gc is None: return False
        
        spreadsheet = gc.open_by_key(SPREADSHEET_ID)
        worksheet = spreadsheet.worksheet(WORKSHEET_NAME)
        
        df_upload = df_edited.copy()
        df_upload['Status Pembayaran'] = df_upload['Status Pembayaran'].apply(lambda x: "TRUE" if x else "FALSE")
        df_upload['Status Checkout'] = df_upload['Status Checkout'].apply(lambda x: "TRUE" if x else "FALSE")
        
        worksheet.clear()
        set_with_dataframe(worksheet, df_upload)
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"Gagal memperbarui data: {str(e)}")
        return False

# --- HEADER ---
st.markdown('<div class="main-title">Bali Trip Budget Planner</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Sistem Manajemen Anggaran Perjalanan</div>', unsafe_allow_html=True)

# --- SIDEBAR: INPUT ---
with st.sidebar:
    st.markdown("### Input Data Baru")
    
    with st.form("form_add", clear_on_submit=True):
        nama = st.text_input("Nama Item", placeholder="Contoh: Tiket Pesawat")
        col_s1, col_s2 = st.columns(2)
        with col_s1: qty = st.number_input("Jumlah (Qty)", min_value=1, value=1)
        with col_s2: harga = st.number_input("Harga Satuan (Rp)", min_value=0, step=10000)
        
        tipe = st.radio("Metode Perhitungan", ["Satuan (x Qty)", "Borongan (Total)"])
        
        st.markdown("---")
        st.caption("Status Awal")
        
        lunas = st.checkbox("Sudah Bayar", value=False)
        checkout = st.checkbox("Sudah Checkout", value=False)
        
        st.markdown("")
        btn_add = st.form_submit_button("Simpan Data", use_container_width=True)

    if btn_add:
        if not nama:
            st.warning("Nama item tidak boleh kosong.")
        else:
            total = (harga * qty) if tipe == "Satuan (x Qty)" else harga
            tipe_str = "Satuan" if tipe == "Satuan (x Qty)" else "Borongan"
            
            if append_to_sheet(nama, qty, harga, total, tipe_str, lunas, checkout):
                st.success(f"Data '{nama}' berhasil disimpan.")
                st.rerun()

# --- MAIN CONTENT ---
df = load_data_from_sheet()

if df is not None:
    # 1. PERHITUNGAN
    if not df.empty:
        total_rencana = df['Total Akhir'].sum()
        uang_keluar = df[df['Status Pembayaran'] == True]['Total Akhir'].sum()
        sisa_bayar = df[df['Status Pembayaran'] == False]['Total Akhir'].sum()
        persen = (uang_keluar/total_rencana*100) if total_rencana > 0 else 0
    else:
        total_rencana = 0; uang_keluar = 0; sisa_bayar = 0; persen = 0

    # 2. DASHBOARD METRICS
    k1, k2, k3 = st.columns(3)
    with k1:
        st.metric("Total Rencana Anggaran", f"Rp {total_rencana:,.0f}")
    with k2:
        st.metric("Total Terbayar", f"Rp {uang_keluar:,.0f}")
    with k3:
        st.metric("Sisa Pembayaran", f"Rp {sisa_bayar:,.0f}")
        
    st.markdown("---")

    # 3. TABEL DATA
    col_h, col_r = st.columns([4,1])
    with col_h: st.markdown("#### Rincian Anggaran")
    with col_r: 
        if st.button("Muat Ulang Data"): st.cache_data.clear(); st.rerun()

    if not df.empty:
        edited_df = st.data_editor(
            df,
            column_config={
                "Status Pembayaran": st.column_config.CheckboxColumn(
                    "Lunas",
                    default=False
                ),
                "Status Checkout": st.column_config.CheckboxColumn(
                    "Checkout",
                    default=False
                ),
                "Nama Barang": st.column_config.TextColumn("Nama Item", width="large"),
                "Total Akhir": st.column_config.NumberColumn("Total", format="Rp %d", disabled=True),
                "Harga Input": st.column_config.NumberColumn("Harga Input", format="Rp %d"),
                "Tipe": st.column_config.TextColumn("Tipe", disabled=True)
            },
            hide_index=True,
            use_container_width=True,
            num_rows="dynamic",
            key="editor_utama"
        )
        
        col_save_l, col_save_r = st.columns([3,1])
        with col_save_r:
            if st.button("Simpan Perubahan Tabel", type="primary", use_container_width=True):
                for idx, row in edited_df.iterrows():
                    if row['Tipe'] == 'Satuan':
                        edited_df.at[idx, 'Total Akhir'] = row['Harga Input'] * row['Qty']
                    else:
                        edited_df.at[idx, 'Total Akhir'] = row['Harga Input']
                
                if update_sheet_data(edited_df):
                    st.success("Perubahan berhasil disimpan ke database.")
                    st.rerun()

    else:
        st.info("Belum ada data tersedia. Silakan input data baru melalui panel di sebelah kiri.")
