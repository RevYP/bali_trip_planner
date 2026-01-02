import streamlit as st
import pandas as pd
from google.oauth2 import service_account
import gspread
from gspread_dataframe import set_with_dataframe
from datetime import datetime
from gspread.utils import rowcol_to_a1

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="Bali Trip Planner",
    page_icon="🌴",
    layout="wide", # Ini biar tabelnya lebar ke samping (tidak kepotong)
    initial_sidebar_state="expanded"
)

# --- 2. CSS "ANTI-GAIB" & TEMA DARK MODERN ---
st.markdown("""
<style>
    /* --- PAKSA HURUF PUTIH & BACKGROUND GELAP (PERBAIKAN UTAMA) --- */
    html, body, [class*="css"], [data-testid="stAppViewContainer"] {
        font-family: 'Open Sans', sans-serif !important;
        background-color: #313338 !important; /* Abu Gelap Discord */
        color: #FFFFFF !important; /* Paksa Huruf Putih Terang */
    }

    /* Paksa Sidebar Gelap */
    section[data-testid="stSidebar"] {
        background-color: #2b2d31 !important; 
    }

    /* Paksa Input Box (Kotak Ketik) jadi Gelap & Tulisannya Putih */
    input[type="text"], input[type="number"] {
        background-color: #1E1F22 !important;
        color: #FFFFFF !important;
        border: 1px solid #1E1F22 !important;
    }
    
    /* Perbaikan Tampilan Dropdown/Radio */
    div[role="radiogroup"] label {
        color: #FFFFFF !important;
    }

    /* --- GAYA TABEL (Supaya Rapi & Jelas) --- */
    div[data-testid="stDataEditor"] {
        background-color: #2b2d31 !important; /* Background Tabel */
        border: 1px solid #1e1f22;
        border-radius: 8px;
    }
    
    /* Warna Header Tabel */
    div[data-testid="stDataEditor"] div[role="columnheader"] {
        background-color: #1E1F22 !important;
        color: #FFFFFF !important;
        font-weight: 700;
    }

    /* --- KARTU ANGKA (DASHBOARD) --- */
    div[data-testid="metric-container"] {
        background-color: #2b2d31; 
        border-left: 5px solid #5865F2; /* Garis Biru Keren */
        padding: 15px;
        border-radius: 6px; 
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    
    /* Judul Kecil di atas Angka */
    div[data-testid="metric-container"] label {
        color: #B5BAC1 !important; /* Abu terang */
        font-weight: 700;
    }
    
    /* Angka Besar */
    div[data-testid="metric-container"] div[data-testid="stMetricValue"] {
        color: #FFFFFF !important;
    }

    /* --- JUDUL HALAMAN --- */
    .main-title {
        font-weight: 800; 
        font-size: 2.5rem;
        color: #FFFFFF !important;
        margin-bottom: 0px;
    }
    
    .sub-title {
        font-size: 1rem;
        color: #949BA4 !important;
        margin-bottom: 30px;
    }

    /* --- TOMBOL (BUTTONS) --- */
    .stButton > button {
        background-color: #5865F2; /* Biru Discord */
        color: white !important;
        border-radius: 5px;
        border: none;
        font-weight: 600;
        transition: 0.2s;
    }
    .stButton > button:hover {
        background-color: #4752C4;
    }
    
    /* Tombol Delete (Merah) */
    button[kind="secondary"] {
        background-color: transparent !important;
        border: 1px solid #DA373C !important;
        color: #DA373C !important;
    }
    button[kind="secondary"]:hover {
        background-color: #DA373C !important;
        color: white !important;
    }

</style>
""", unsafe_allow_html=True)

# --- 3. KONEKSI DATABASE (LOGIC SAMA) ---
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
        st.error(f"Koneksi Error: {str(e)}")
        return None

@st.cache_data(ttl=5)
def load_data():
    try:
        gc = init_gsheet_connection()
        if not gc: return None
        ws = gc.open_by_key(SPREADSHEET_ID).worksheet(WORKSHEET_NAME)
        data = ws.get_all_values()
        
        cols = ['Item', 'Qty', 'Price', 'Total', 'Type', 'Paid', 'Booked']
        
        if len(data) <= 1:
            return pd.DataFrame(columns=cols)
            
        df = pd.DataFrame(data[1:], columns=data[0])
        
        for c in cols:
            if c not in df.columns: df[c] = "FALSE"
            
        for c in ['Qty', 'Price', 'Total']:
            df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0).astype(int)
            
        df['Paid'] = df['Paid'].apply(lambda x: str(x).upper() == 'TRUE')
        df['Booked'] = df['Booked'].apply(lambda x: str(x).upper() == 'TRUE')
        
        return df[cols]
    except Exception as e:
        st.error(f"Gagal memuat data: {str(e)}")
        return None

def save_data(item, qty, price, total, type_, paid, booked):
    try:
        gc = init_gsheet_connection()
        ws = gc.open_by_key(SPREADSHEET_ID).worksheet(WORKSHEET_NAME)
        ws.append_row([item, int(qty), int(price), int(total), type_, "TRUE" if paid else "FALSE", "TRUE" if booked else "FALSE"])
        st.cache_data.clear()
        return True
    except Exception: return False

def update_data(df_edited):
    try:
        gc = init_gsheet_connection()
        ws = gc.open_by_key(SPREADSHEET_ID).worksheet(WORKSHEET_NAME)
        
        df_up = df_edited.copy()
        if 'Delete' in df_up.columns: df_up = df_up.drop(columns=['Delete'])
        
        df_up['Paid'] = df_up['Paid'].apply(lambda x: "TRUE" if x else "FALSE")
        df_up['Booked'] = df_up['Booked'].apply(lambda x: "TRUE" if x else "FALSE")
        
        ws.clear()
        set_with_dataframe(ws, df_up)
        st.cache_data.clear()
        return True
    except Exception: return False

# --- 4. TAMPILAN UTAMA (UI) ---
st.markdown('<div class="main-title">Bali Trip Planner</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Kelola budget perjalananmu dengan efisien</div>', unsafe_allow_html=True)

# --- SIDEBAR: INPUT ---
with st.sidebar:
    st.markdown("### 📝 Tambah Item Baru")
    with st.form("add_form", clear_on_submit=True):
        item = st.text_input("Nama Item", placeholder="Contoh: Tiket Pesawat")
        
        c1, c2 = st.columns(2)
        with c1: qty = st.number_input("Qty", 1, value=1)
        with c2: price = st.number_input("Harga (IDR)", 0, step=50000)
        
        type_ = st.radio("Tipe Hitungan", ["Per Unit", "Borongan/Total"])
        
        st.markdown("---")
        c3, c4 = st.columns(2)
        with c3: paid = st.checkbox("Sudah Bayar")
        with c4: booked = st.checkbox("Sudah Booking")
        
        st.markdown("")
        if st.form_submit_button("Simpan Item", use_container_width=True):
            if item:
                tot = (price * qty) if type_ == "Per Unit" else price
                typ = "Unit" if type_ == "Per Unit" else "Lump Sum"
                if save_data(item, qty, price, tot, typ, paid, booked):
                    st.success("Berhasil disimpan!")
                    st.rerun()
            else:
                st.warning("Nama item wajib diisi.")

# --- DASHBOARD (ANGKA) ---
df = load_data()
if df is not None:
    if not df.empty:
        total = df['Total'].sum()
        paid_amt = df[df['Paid']]['Total'].sum()
        remain = total - paid_amt
        pct = (paid_amt/total*100) if total > 0 else 0
    else:
        total = paid_amt = remain = pct = 0

    m1, m2, m3 = st.columns(3)
    with m1: st.metric("Total Rencana", f"Rp {total:,.0f}", f"{len(df)} Item")
    with m2: st.metric("Sudah Dibayar", f"Rp {paid_amt:,.0f}", f"{pct:.1f}%")
    with m3: st.metric("Sisa Tagihan", f"Rp {remain:,.0f}", f"- Rp {paid_amt:,.0f}", delta_color="inverse")

    st.markdown("---")
    
    # --- TABEL DATA ---
    c_head, c_btn = st.columns([4,1])
    with c_head: st.markdown("#### Rincian Budget")
    with c_btn: 
        if st.button("🔄 Refresh Data"): st.cache_data.clear(); st.rerun()

    if not df.empty:
        df_display = df.copy()
        df_display.insert(0, "Delete", False)

        edited_df = st.data_editor(
            df_display,
            column_config={
                "Delete": st.column_config.CheckboxColumn("🗑️", width="small", help="Centang untuk hapus"),
                "Item": st.column_config.TextColumn("Nama Item", width="large"), # Large biar panjang
                "Qty": st.column_config.NumberColumn("Qty", width="small"),
                "Price": st.column_config.NumberColumn("Harga", format="Rp %d"),
                "Total": st.column_config.NumberColumn("Total", format="Rp %d", disabled=True),
                "Type": st.column_config.TextColumn("Tipe", width="small", disabled=True),
                "Paid": st.column_config.CheckboxColumn("Lunas?", width="small"),
                "Booked": st.column_config.CheckboxColumn("Book?", width="small")
            },
            hide_index=True,
            use_container_width=True, # INI KUNCINYA BIAR FULL LEBAR
            num_rows="dynamic",
            height=500 # Tinggi tabel biar kelihatan banyak
        )

        col_del, col_space, col_save = st.columns([1.5, 2, 1.5])
        
        # TOMBOL DELETE
        with col_del:
            to_del = edited_df[edited_df['Delete'] == True]
            if not to_del.empty:
                if st.button(f"🗑️ Hapus {len(to_del)} Item", type="secondary", use_container_width=True):
                    update_data(edited_df[edited_df['Delete'] == False])
                    st.rerun()
            else:
                st.button("🗑️ Hapus Terpilih", disabled=True, use_container_width=True)
        
        # TOMBOL SAVE
        with col_save:
            if st.button("💾 Simpan Perubahan", type="primary", use_container_width=True):
                 for idx, row in edited_df.iterrows():
                    val = row['Price'] * row['Qty'] if row['Type'] == 'Unit' else row['Price']
                    edited_df.at[idx, 'Total'] = val
                 update_data(edited_df)
                 st.success("Data terupdate!")
                 st.rerun()
    else:
        st.info("Belum ada data. Silakan input di sebelah kiri.")
