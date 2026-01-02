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
    page_icon="", # Icon Apple style
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS: SF PRO STYLE ---
st.markdown("""
<style>
    /* Import Font Inter (Mirip SF Pro) buat Backup Windows/Android */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    /* Terapkan Font Stack */
    html, body, [class*="css"], [data-testid="stAppViewContainer"] {
        font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text", "Inter", "Segoe UI", "Roboto", sans-serif !important;
        color: #1d1d1f; /* Warna Hitam Apple */
        background-color: #F5F5F7; /* Abu-abu muda khas iOS Settings */
    }

    /* Header */
    .main-title {
        font-size: 2.5rem;
        font-weight: 700;
        letter-spacing: -0.02em; /* Biar rapet kayak SF Pro */
        color: #1d1d1f;
        margin-bottom: 0.2rem;
    }
    
    /* Kartu Dashboard (Apple Style Card) */
    div[data-testid="metric-container"] {
        background-color: #FFFFFF;
        border: 1px solid #d2d2d7;
        padding: 20px;
        border-radius: 12px; /* Radius khas iOS */
        box-shadow: 0 4px 6px rgba(0,0,0,0.02);
    }
    
    /* Label di dalam Kartu */
    div[data-testid="metric-container"] label {
        font-weight: 500;
        color: #86868b; /* Abu-abu teks Apple */
        font-size: 0.9rem;
    }
    
    /* Angka di dalam Kartu */
    div[data-testid="metric-container"] div[data-testid="stMetricValue"] {
        font-weight: 600;
        font-size: 1.8rem;
        color: #1d1d1f;
    }

    /* Tombol (iOS Blue Button) */
    .stButton > button {
        background-color: #0071e3; /* Warna Biru Apple */
        color: white;
        border-radius: 8px;
        border: none;
        padding: 0.6rem 1.2rem;
        font-weight: 500;
        font-size: 0.95rem;
        transition: all 0.2s ease;
    }
    .stButton > button:hover {
        background-color: #0077ED;
        transform: scale(1.01);
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #FFFFFF;
        border-right: 1px solid #d2d2d7;
    }
    
    /* Tabel (Clean) */
    div[data-testid="stDataEditor"] {
        border-radius: 10px;
        border: 1px solid #d2d2d7;
        overflow: hidden;
    }
</style>
""", unsafe_allow_html=True)

# --- DATABASE CONNECTION ---
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
        return gspread.authorize(credentials)
    except Exception as e:
        st.error(f"Koneksi Gagal: {str(e)}")
        return None

@st.cache_data(ttl=5)
def load_data():
    try:
        gc = init_gsheet_connection()
        if not gc: return None
        
        ws = gc.open_by_key(SPREADSHEET_ID).worksheet(WORKSHEET_NAME)
        data = ws.get_all_values()
        
        cols = ['Nama Barang', 'Qty', 'Harga Input', 'Total Akhir', 'Tipe', 'Status Pembayaran', 'Status Checkout']
        
        if len(data) <= 1:
            return pd.DataFrame(columns=cols)
            
        df = pd.DataFrame(data[1:], columns=data[0])
        
        for c in cols:
            if c not in df.columns: df[c] = "FALSE"
            
        for c in ['Qty', 'Harga Input', 'Total Akhir']:
            df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0).astype(int)
            
        df['Status Pembayaran'] = df['Status Pembayaran'].apply(lambda x: str(x).upper() == 'TRUE')
        df['Status Checkout'] = df['Status Checkout'].apply(lambda x: str(x).upper() == 'TRUE')
        
        return df[cols]
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return None

def save_data(nama, qty, harga, total, tipe, lunas, checkout):
    try:
        gc = init_gsheet_connection()
        ws = gc.open_by_key(SPREADSHEET_ID).worksheet(WORKSHEET_NAME)
        ws.append_row([nama, int(qty), int(harga), int(total), tipe, "TRUE" if lunas else "FALSE", "TRUE" if checkout else "FALSE"])
        st.cache_data.clear()
        return True
    except Exception:
        return False

def update_data(df_edited):
    try:
        gc = init_gsheet_connection()
        ws = gc.open_by_key(SPREADSHEET_ID).worksheet(WORKSHEET_NAME)
        
        df_up = df_edited.copy()
        df_up['Status Pembayaran'] = df_up['Status Pembayaran'].apply(lambda x: "TRUE" if x else "FALSE")
        df_up['Status Checkout'] = df_up['Status Checkout'].apply(lambda x: "TRUE" if x else "FALSE")
        
        ws.clear()
        set_with_dataframe(ws, df_up)
        st.cache_data.clear()
        return True
    except Exception:
        return False

# --- UI START ---
st.markdown('<div class="main-title">Bali Trip Planner</div>', unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("### 📝 Input Baru")
    with st.form("add_form", clear_on_submit=True):
        nama = st.text_input("Nama Item", placeholder="Contoh: Tiket Pesawat")
        c1, c2 = st.columns(2)
        with c1: qty = st.number_input("Qty", 1, value=1)
        with c2: harga = st.number_input("Harga", 0, step=50000)
        tipe = st.radio("Tipe", ["Satuan (x Qty)", "Borongan (Total)"])
        
        st.markdown("---")
        st.caption("Status Awal")
        lunas = st.checkbox("✅ Sudah Bayar")
        checkout = st.checkbox("🛒 Sudah Checkout")
        
        if st.form_submit_button("Simpan", use_container_width=True):
            if nama:
                tot = (harga * qty) if tipe == "Satuan (x Qty)" else harga
                typ = "Satuan" if tipe == "Satuan (x Qty)" else "Borongan"
                if save_data(nama, qty, harga, tot, typ, lunas, checkout):
                    st.toast("Berhasil disimpan!", icon="✅")
                    st.rerun()
            else:
                st.toast("Nama item wajib diisi.", icon="⚠️")

# --- DASHBOARD ---
df = load_data()
if df is not None:
    if not df.empty:
        total = df['Total Akhir'].sum()
        paid = df[df['Status Pembayaran']]['Total Akhir'].sum()
        remain = total - paid
        pct = (paid/total*100) if total > 0 else 0
    else:
        total = paid = remain = pct = 0

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Rencana", f"Rp {total:,.0f}", delta=f"{len(df)} Items")
    with col2:
        st.metric("Sudah Dibayar", f"Rp {paid:,.0f}", delta=f"{pct:.1f}% Lunas")
    with col3:
        st.metric("Sisa Tagihan", f"Rp {remain:,.0f}", delta=f"- Rp {paid:,.0f}", delta_color="inverse")

    st.markdown("---")
    
    # --- TABLE ---
    c_head, c_btn = st.columns([4,1])
    with c_head: st.markdown("#### Rincian Budget")
    with c_btn: 
        if st.button("🔄 Refresh"): st.cache_data.clear(); st.rerun()

    if not df.empty:
        edited_df = st.data_editor(
            df,
            column_config={
                "Status Pembayaran": st.column_config.CheckboxColumn("Lunas", default=False),
                "Status Checkout": st.column_config.CheckboxColumn("Checkout", default=False),
                "Nama Barang": st.column_config.TextColumn("Item", width="large"),
                "Total Akhir": st.column_config.NumberColumn("Total", format="Rp %d", disabled=True),
                "Harga Input": st.column_config.NumberColumn("Harga", format="Rp %d"),
                "Tipe": st.column_config.TextColumn("Tipe", disabled=True)
            },
            hide_index=True,
            use_container_width=True,
            num_rows="dynamic"
        )

        col_l, col_r = st.columns([3,1])
        with col_r:
            if st.button("💾 Simpan Perubahan", type="primary", use_container_width=True):
                for idx, row in edited_df.iterrows():
                    val = row['Harga Input'] * row['Qty'] if row['Tipe'] == 'Satuan' else row['Harga Input']
                    edited_df.at[idx, 'Total Akhir'] = val
                
                if update_data(edited_df):
                    st.toast("Data berhasil diperbarui!", icon="💾")
                    st.rerun()
    else:
        st.info("Belum ada data.")
