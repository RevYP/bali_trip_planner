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
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. CSS "ANTI-GAIB" KHUSUS (Teks Putih, Kecuali Tombol) ---
st.markdown("""
<style>
    /* 1. GLOBAL: Paksa Background Gelap & Tulisan Putih */
    html, body, [class*="css"], [data-testid="stAppViewContainer"] {
        font-family: 'Open Sans', sans-serif !important;
        background-color: #313338 !important; 
        color: #FFFFFF !important; 
    }

    /* 2. SIDEBAR & INPUT */
    section[data-testid="stSidebar"] {
        background-color: #2b2d31 !important; 
    }
    input[type="text"], input[type="number"] {
        background-color: #1E1F22 !important;
        color: #FFFFFF !important;
        border: 1px solid #1E1F22 !important;
    }

    /* 3. TABEL GELAP (Header & Isi Putih) */
    div[data-testid="stDataEditor"] {
        background-color: #2b2d31 !important;
        border: 1px solid #1e1f22;
    }
    div[data-testid="stDataEditor"] div[role="columnheader"] {
        background-color: #1E1F22 !important;
        color: #FFFFFF !important;
    }
    div[data-testid="stDataEditor"] div[role="gridcell"] {
        color: #FFFFFF !important;
    }

    /* 4. KECUALI TOMBOL (Biar Hapus tetap Merah, Refresh tetap warnanya) */
    /* Tombol Utama (Save/Simpan) -> Biru Teks Putih */
    .stButton > button[kind="primary"] {
        background-color: #5865F2 !important; 
        color: #FFFFFF !important;
        border: none;
    }

    /* Tombol Secondary (Refresh & Delete) -> Jangan dipaksa putih semua */
    .stButton > button[kind="secondary"] {
        background-color: transparent !important;
        /* Biarkan warna text bawaan (biasanya merah/abu) atau kita atur khusus */
    }

    /* KHUSUS TOMBOL DELETE (Merah) */
    /* Kita akali dengan CSS targeting tombol spesifik jika bisa, 
       tapi karena Streamlit random, kita pastikan border merah teks merah */
    button[kind="secondary"]:hover {
        border-color: #DA373C !important;
        color: #DA373C !important;
    }
    
    /* 5. METRIC CARDS */
    div[data-testid="metric-container"] {
        background-color: #2b2d31; 
        border-left: 5px solid #5865F2; 
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    div[data-testid="metric-container"] label { color: #B5BAC1 !important; }
    div[data-testid="metric-container"] div[data-testid="stMetricValue"] { color: #FFFFFF !important; }
    
    /* JUDUL */
    .main-title { font-weight: 800; font-size: 2.5rem; color: #FFFFFF !important; }
    .sub-title { color: #949BA4 !important; }

</style>
""", unsafe_allow_html=True)

# --- 3. DATABASE CONNECTION ---
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
        st.error(f"Error Koneksi: {str(e)}")
        return None

@st.cache_data(ttl=5)
def load_data():
    try:
        gc = init_gsheet_connection()
        if not gc: return None
        ws = gc.open_by_key(SPREADSHEET_ID).worksheet(WORKSHEET_NAME)
        data = ws.get_all_values()
        
        cols = ['Item', 'Qty', 'Price', 'Total', 'Type', 'Paid', 'Booked']
        if len(data) <= 1: return pd.DataFrame(columns=cols)
        df = pd.DataFrame(data[1:], columns=data[0])
        
        for c in cols:
            if c not in df.columns: df[c] = "FALSE"
        for c in ['Qty', 'Price', 'Total']:
            df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0).astype(int)
        df['Paid'] = df['Paid'].apply(lambda x: str(x).upper() == 'TRUE')
        df['Booked'] = df['Booked'].apply(lambda x: str(x).upper() == 'TRUE')
        return df[cols]
    except Exception as e:
        st.error(f"Error Load Data: {str(e)}")
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

# --- 4. UI ---
st.markdown('<div class="main-title">Bali Trip Planner</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Budget Management Dashboard</div>', unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("### 📝 Input Baru")
    with st.form("add_form", clear_on_submit=True):
        item = st.text_input("Nama Item", placeholder="Contoh: Tiket Pesawat")
        c1, c2 = st.columns(2)
        with c1: qty = st.number_input("Qty", 1, value=1)
        with c2: price = st.number_input("Harga (IDR)", 0, step=50000)
        type_ = st.radio("Tipe", ["Per Unit", "Borongan"])
        st.markdown("---")
        c3, c4 = st.columns(2)
        with c3: paid = st.checkbox("Lunas")
        with c4: booked = st.checkbox("Booking")
        
        if st.form_submit_button("Simpan Item", use_container_width=True):
            if item:
                tot = (price * qty) if type_ == "Per Unit" else price
                typ = "Unit" if type_ == "Per Unit" else "Lump Sum"
                if save_data(item, qty, price, tot, typ, paid, booked):
                    st.success("Tersimpan!")
                    st.rerun()
            else:
                st.warning("Isi nama item.")

# --- DASHBOARD ---
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
    
    # --- TABEL ---
    c_head, c_btn = st.columns([4,1])
    with c_head: st.markdown("#### Rincian Budget")
    with c_btn: 
        if st.button("🔄 Refresh Data", type="secondary"): st.cache_data.clear(); st.rerun()

    if not df.empty:
        df_display = df.copy()
        df_display.insert(0, "Delete", False)

        # === SETTING LEBAR KOLOM BIAR MUAT SEMUA ===
        edited_df = st.data_editor(
            df_display,
            column_config={
                "Delete": st.column_config.CheckboxColumn("🗑️", width="small"),
                "Item": st.column_config.TextColumn("Nama Item", width="medium"), # Medium aja biar cukup
                "Qty": st.column_config.NumberColumn("Qty", width="small"),
                "Price": st.column_config.NumberColumn("Harga", format="Rp %d", width="medium"),
                "Total": st.column_config.NumberColumn("Total", format="Rp %d", width="medium"),
                "Type": st.column_config.TextColumn("Tipe", width="small"),
                "Paid": st.column_config.CheckboxColumn("Lunas", width="small"),
                "Booked": st.column_config.CheckboxColumn("Book", width="small")
            },
            hide_index=True,
            use_container_width=True, # FITUR UTAMA BIAR FULL SCREEN
            num_rows="dynamic"
        )

        col_del, col_space, col_save = st.columns([1.5, 2, 1.5])
        
        with col_del:
            to_del = edited_df[edited_df['Delete'] == True]
            if not to_del.empty:
                # Tombol Hapus pakai 'secondary' biar warnanya beda (merah/abu tergantung hover)
                if st.button(f"🗑️ Hapus {len(to_del)} Item", type="secondary", use_container_width=True):
                    update_data(edited_df[edited_df['Delete'] == False])
                    st.rerun()
            else:
                st.button("🗑️ Hapus", disabled=True, type="secondary", use_container_width=True)
        
        with col_save:
            # Tombol Simpan pakai 'primary' (Biru)
            if st.button("💾 Simpan Perubahan", type="primary", use_container_width=True):
                 for idx, row in edited_df.iterrows():
                    val = row['Price'] * row['Qty'] if row['Type'] == 'Unit' else row['Price']
                    edited_df.at[idx, 'Total'] = val
                 update_data(edited_df)
                 st.success("Data Tersimpan!")
                 st.rerun()
    else:
        st.info("Belum ada data.")
