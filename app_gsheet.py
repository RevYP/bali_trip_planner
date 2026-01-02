import streamlit as st
import pandas as pd
from google.oauth2 import service_account
import gspread
from gspread_dataframe import set_with_dataframe
from datetime import datetime
from gspread.utils import rowcol_to_a1

# --- 1. CONFIG HALAMAN ---
st.set_page_config(
    page_title="Bali Trip Planner",
    page_icon="🌴",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. STYLING "MODERN & CLEAN" (Font Poppins) ---
st.markdown("""
<style>
    /* Import Font Keren (Poppins) */
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap');

    html, body, [class*="css"], [data-testid="stAppViewContainer"] {
        font-family: 'Poppins', sans-serif !important;
    }

    /* Card Dashboard Modern */
    div[data-testid="metric-container"] {
        background-color: #FFFFFF;
        border: 1px solid #F0F0F0;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05); /* Bayangan lembut */
        transition: transform 0.2s;
    }
    div[data-testid="metric-container"]:hover {
        transform: translateY(-2px); /* Efek naik pas di-hover */
        border-color: #1E88E5;
    }

    /* Judul Utama */
    .main-title {
        font-size: 2.5rem;
        font-weight: 700;
        color: #2C3E50;
        margin-top: -20px;
    }
    
    .sub-title {
        font-size: 1rem;
        color: #7F8C8D;
        margin-bottom: 20px;
    }

    /* Tombol Delete Merah Soft */
    button[kind="secondary"] {
        color: #E74C3C !important;
        border-color: #E74C3C !important;
        border-radius: 8px !important;
    }
    button[kind="secondary"]:hover {
        background-color: #FDEDEC !important;
    }

    /* Tombol Simpan Biru Modern */
    .stButton > button[kind="primary"] {
        border-radius: 8px !important;
        font-weight: 600 !important;
        box-shadow: 0 4px 10px rgba(30, 136, 229, 0.3);
    }
    
    /* Progress Bar Custom Color */
    .stProgress > div > div > div > div {
        background-color: #1E88E5;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. KONEKSI DATABASE ---
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
        
        df = df[df['Item'].str.strip() != '']
        df = df.dropna(subset=['Item'])
        
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

# --- 4. TAMPILAN UTAMA ---

# [GAMBAR BANNER] - Ini kuncinya biar gak kaku!
st.image("https://images.unsplash.com/photo-1537996194471-e657df975ab4?q=80&w=1000&auto=format&fit=crop", use_container_width=True)

st.markdown('<div class="main-title">Bali Trip Planner 🌴</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Atur budget liburanmu biar gak boncos!</div>', unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.header("➕ Tambah Item")
    with st.form("add_form", clear_on_submit=True):
        item = st.text_input("Nama Item", placeholder="Contoh: Sewa Motor Nmax")
        c1, c2 = st.columns(2)
        with c1: qty = st.number_input("Qty", 1, value=1)
        with c2: price = st.number_input("Harga (IDR)", 0, step=50000)
        type_ = st.radio("Tipe", ["Per Unit", "Borongan"])
        st.markdown("---")
        c3, c4 = st.columns(2)
        with c3: paid = st.checkbox("Lunas")
        with c4: booked = st.checkbox("Booked")
        
        if st.form_submit_button("Simpan Item", use_container_width=True):
            if item:
                tot = (price * qty) if type_ == "Per Unit" else price
                typ = "Unit" if type_ == "Per Unit" else "Lump Sum"
                if save_data(item, qty, price, tot, typ, paid, booked):
                    st.success("Berhasil Disimpan!")
                    st.rerun()
            else:
                st.warning("Nama item tidak boleh kosong.")

# --- DASHBOARD ---
df = load_data()
if df is not None:
    if not df.empty:
        total = df['Total'].sum()
        paid_amt = df[df['Paid']]['Total'].sum()
        remain = total - paid_amt
        # Persentase Progress Bar (Max 100%)
        pct_val = (paid_amt / total) if total > 0 else 0.0
        pct_display = pct_val * 100
    else:
        total = paid_amt = remain = pct_val = pct_display = 0

    # [METRIC CARDS]
    m1, m2, m3 = st.columns(3)
    with m1: st.metric("💰 Total Budget", f"Rp {total:,.0f}", f"{len(df)} Items")
    with m2: st.metric("✅ Sudah Dibayar", f"Rp {paid_amt:,.0f}", f"{pct_display:.1f}%")
    with m3: st.metric("⚠️ Sisa Tagihan", f"Rp {remain:,.0f}", f"- Rp {paid_amt:,.0f}", delta_color="inverse")

    # [PROGRESS BAR] - Biar kelihatan canggih
    st.markdown("#### Status Pembayaran")
    st.progress(pct_val, text=f"{pct_display:.1f}% Terbayar")

    st.markdown("---")
    
    # --- TABEL ---
    c_head, c_btn = st.columns([4,1])
    with c_head: st.subheader("📋 Rincian Pengeluaran")
    with c_btn: 
        if st.button("🔄 Refresh Data"): st.cache_data.clear(); st.rerun()

    if not df.empty:
        df_display = df.copy()
        df_display.insert(0, "Delete", False)

        edited_df = st.data_editor(
            df_display,
            column_config={
                "Delete": st.column_config.CheckboxColumn("🗑️", width="small"),
                "Item": st.column_config.TextColumn("Nama Item", width="medium", required=True),
                "Qty": st.column_config.NumberColumn("Qty", width="small"),
                "Price": st.column_config.NumberColumn("Harga", format="Rp %d", width="medium"),
                "Total": st.column_config.NumberColumn("Total", format="Rp %d", width="medium"),
                "Type": st.column_config.TextColumn("Tipe", width="small", disabled=True),
                "Paid": st.column_config.CheckboxColumn("Lunas", width="small"),
                "Booked": st.column_config.CheckboxColumn("Book", width="small")
            },
            hide_index=True,
            use_container_width=True,
            num_rows="fixed" 
        )

        col_del, col_space, col_save = st.columns([1.5, 2, 1.5])
        
        with col_del:
            to_del = edited_df[edited_df['Delete'] == True]
            if not to_del.empty:
                if st.button(f"🗑️ Hapus {len(to_del)} Item", type="secondary", use_container_width=True):
                    update_data(edited_df[edited_df['Delete'] == False])
                    st.rerun()
            else:
                st.button("🗑️ Hapus", disabled=True, type="secondary", use_container_width=True)
        
        with col_save:
            if st.button("💾 Simpan Perubahan", type="primary", use_container_width=True):
                 for idx, row in edited_df.iterrows():
                    val = row['Price'] * row['Qty'] if row['Type'] == 'Unit' else row['Price']
                    edited_df.at[idx, 'Total'] = val
                 update_data(edited_df)
                 st.success("Tersimpan!")
                 st.rerun()
    else:
        st.info("Belum ada data. Tambah dulu di sidebar ya!")
