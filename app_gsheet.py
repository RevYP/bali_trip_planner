import streamlit as st
import pandas as pd
from google.oauth2 import service_account
import gspread
from gspread_dataframe import set_with_dataframe
from datetime import datetime
from gspread.utils import rowcol_to_a1

# --- KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="Bali Trip Budget Planner",
    page_icon="🌴",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS STYLING ---
st.markdown("""
<style>
    .main-title {
        text-align: center;
        font-family: 'Helvetica Neue', sans-serif;
        color: #1E88E5;
        font-weight: 700;
        margin-bottom: 20px;
    }
    
    /* Metrics Cards */
    div[data-testid="metric-container"] {
        background-color: #FFFFFF;
        border: 1px solid #E0E0E0;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        text-align: center;
    }
    
    /* Highlight Status Columns in Editor */
    div[data-testid="stDataEditor"] table {
        font-size: 14px;
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
        st.error(f"❌ Error Koneksi: {str(e)}")
        return None

@st.cache_data(ttl=5) # Cache pendek biar cepat update
def load_data_from_sheet():
    try:
        gc = init_gsheet_connection()
        if gc is None: return None
        
        spreadsheet = gc.open_by_key(SPREADSHEET_ID)
        worksheet = spreadsheet.worksheet(WORKSHEET_NAME)
        
        data = worksheet.get_all_values()
        
        # DEFINISI KOLOM BARU (Sesuai Request)
        expected_cols = ['Nama Barang', 'Qty', 'Harga Input', 'Total Akhir', 'Tipe', 'Status Pembayaran', 'Status Checkout']
        
        if len(data) <= 1:
            return pd.DataFrame(columns=expected_cols)
        
        df = pd.DataFrame(data[1:], columns=data[0])
        
        # Handle jika kolom belum ada di sheet lama (Migration)
        for col in expected_cols:
            if col not in df.columns:
                df[col] = "FALSE"
        
        # Convert Tipe Data
        df['Qty'] = pd.to_numeric(df['Qty'], errors='coerce').fillna(0).astype(int)
        df['Harga Input'] = pd.to_numeric(df['Harga Input'], errors='coerce').fillna(0).astype(int)
        df['Total Akhir'] = pd.to_numeric(df['Total Akhir'], errors='coerce').fillna(0).astype(int)
        
        # Convert Status to Boolean (True/False) untuk Checkbox
        # Pastikan nama kolom di sini match dengan expected_cols
        df['Status Pembayaran'] = df['Status Pembayaran'].apply(lambda x: True if str(x).upper() == 'TRUE' else False)
        df['Status Checkout'] = df['Status Checkout'].apply(lambda x: True if str(x).upper() == 'TRUE' else False)
        
        return df[expected_cols]
    
    except Exception as e:
        st.error(f"❌ Gagal load data: {str(e)}")
        return None

def append_to_sheet(nama, qty, harga, total, tipe, lunas, checkout):
    try:
        gc = init_gsheet_connection()
        if gc is None: return False
        
        spreadsheet = gc.open_by_key(SPREADSHEET_ID)
        worksheet = spreadsheet.worksheet(WORKSHEET_NAME)
        
        # Convert boolean ke String buat GSheet
        str_lunas = "TRUE" if lunas else "FALSE"
        str_checkout = "TRUE" if checkout else "FALSE"
        
        new_row = [nama, int(qty), int(harga), int(total), tipe, str_lunas, str_checkout]
        worksheet.append_row(new_row)
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"❌ Gagal simpan: {str(e)}")
        return False

def update_sheet_data(df_edited):
    try:
        gc = init_gsheet_connection()
        if gc is None: return False
        
        spreadsheet = gc.open_by_key(SPREADSHEET_ID)
        worksheet = spreadsheet.worksheet(WORKSHEET_NAME)
        
        df_upload = df_edited.copy()
        # Kembalikan boolean ke string biar aman di sheet
        df_upload['Status Pembayaran'] = df_upload['Status Pembayaran'].apply(lambda x: "TRUE" if x else "FALSE")
        df_upload['Status Checkout'] = df_upload['Status Checkout'].apply(lambda x: "TRUE" if x else "FALSE")
        
        worksheet.clear()
        set_with_dataframe(worksheet, df_upload)
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"❌ Gagal update: {str(e)}")
        return False

# --- UI HEADER ---
st.markdown('<h1 class="main-title">🌴 Bali Trip Budget Planner</h1>', unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.header("📝 Tambah Item")
    
    with st.form("form_add", clear_on_submit=True):
        nama = st.text_input("Nama Item", placeholder="e.g. Sewa Motor")
        col_s1, col_s2 = st.columns(2)
        with col_s1: qty = st.number_input("Qty", min_value=1, value=1)
        with col_s2: harga = st.number_input("Harga (Rp)", min_value=0, step=10000)
        
        tipe = st.radio("Tipe Harga", ["Satuan (x Qty)", "Borongan (Total)"])
        
        st.markdown("---")
        st.markdown("**Status Awal:**")
        
        # Checkbox Input
        lunas = st.checkbox("Sudah Bayar?", value=False, help="Centang jika uang sudah ditransfer/keluar")
        checkout = st.checkbox("Sudah Checkout?", value=False, help="Centang jika barang sudah dipesan/booking")
        
        btn_add = st.form_submit_button("➕ Simpan Item", use_container_width=True)

    if btn_add:
        if not nama:
            st.warning("Nama wajib diisi!")
        else:
            total = (harga * qty) if tipe == "Satuan (x Qty)" else harga
            tipe_str = "Satuan" if tipe == "Satuan (x Qty)" else "Borongan"
            
            # Panggil fungsi append dengan parameter baru
            if append_to_sheet(nama, qty, harga, total, tipe_str, lunas, checkout):
                st.success(f"✅ {nama} tersimpan!")
                st.rerun()

# --- MAIN ---
df = load_data_from_sheet()

if df is not None:
    # 1. HITUNG DUIT
    if not df.empty:
        total_rencana = df['Total Akhir'].sum()
        
        # Hitung Uang Keluar (Status Pembayaran = TRUE)
        uang_keluar = df[df['Status Pembayaran'] == True]['Total Akhir'].sum()
        sisa_bayar = df[df['Status Pembayaran'] == False]['Total Akhir'].sum()
        
        # Hitung Barang Dipesan (Status Checkout = TRUE)
        item_checkout = df[df['Status Checkout'] == True]['Status Checkout'].count()
        
        # Persentase pembayaran
        persen = (uang_keluar/total_rencana*100) if total_rencana > 0 else 0
    else:
        total_rencana = 0; uang_keluar = 0; sisa_bayar = 0; persen = 0

    # 2. DASHBOARD
    k1, k2, k3 = st.columns(3)
    with k1:
        st.metric("💰 Total Rencana", f"Rp {total_rencana:,.0f}")
    with k2:
        st.metric("💸 Sudah Dibayar", f"Rp {uang_keluar:,.0f}", f"{persen:.1f}%")
    with k3:
        st.metric("⚠️ Belum Dibayar", f"Rp {sisa_bayar:,.0f}", delta_color="inverse")
        
    st.markdown("---")

    # 3. TABEL & TOMBOL SIMPAN
    col_h, col_r = st.columns([4,1])
    with col_h: st.subheader("📋 Rincian & Status")
    with col_r: 
        if st.button("🔄 Refresh"): st.cache_data.clear(); st.rerun()

    if not df.empty:
        edited_df = st.data_editor(
            df,
            column_config={
                "Status Pembayaran": st.column_config.CheckboxColumn(
                    "Sudah Bayar?",
                    help="Centang jika lunas",
                    default=False
                ),
                "Status Checkout": st.column_config.CheckboxColumn(
                    "Sudah Checkout?",
                    help="Centang jika sudah dipesan/booking",
                    default=False
                ),
                "Nama Barang": st.column_config.TextColumn("Nama Item", width="large"),
                "Total Akhir": st.column_config.NumberColumn("Total", format="Rp %d", disabled=True),
                "Harga Input": st.column_config.NumberColumn("Harga", format="Rp %d"),
                "Tipe": st.column_config.TextColumn("Tipe", disabled=True)
            },
            hide_index=True,
            use_container_width=True,
            num_rows="dynamic",
            key="editor_utama"
        )
        
        # Tombol Simpan di bawah tabel
        col_save_l, col_save_r = st.columns([3,1])
        with col_save_r:
            if st.button("💾 Simpan Perubahan", type="primary", use_container_width=True):
                # Hitung ulang total (jaga-jaga user edit harga di tabel)
                for idx, row in edited_df.iterrows():
                    if row['Tipe'] == 'Satuan':
                        edited_df.at[idx, 'Total Akhir'] = row['Harga Input'] * row['Qty']
                    else:
                        edited_df.at[idx, 'Total Akhir'] = row['Harga Input']
                
                if update_sheet_data(edited_df):
                    st.success("Tersimpan ke Google Sheets!")
                    st.rerun()

    else:
        st.info("Data masih kosong. Isi dulu di sebelah kiri ya!")
