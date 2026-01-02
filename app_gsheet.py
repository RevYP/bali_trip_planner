import streamlit as st
import pandas as pd
from google.oauth2 import service_account
import gspread
from gspread_dataframe import set_with_dataframe
from datetime import datetime

# --- KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="Bali Trip Budget Planner",
    page_icon="🌴",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CLEAN CSS STYLING ---
st.markdown("""
<style>
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    h1 {
        color: #1f2937;
        font-weight: 600;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    h2, h3 {
        color: #374151;
        font-weight: 500;
    }
    
    [data-testid="stMetricValue"] {
        color: #1f2937;
        font-size: 1.5rem;
    }
    
    [data-testid="stMetricLabel"] {
        color: #6b7280;
        font-size: 0.875rem;
    }
    
    div[data-testid="metric-container"] {
        background-color: #ffffff;
        border: 1px solid #e5e7eb;
        padding: 1rem;
        border-radius: 0.5rem;
    }
    
    .stButton > button {
        background-color: #ffffff;
        border: 1px solid #d1d5db;
        color: #374151;
        font-weight: 400;
        border-radius: 0.375rem;
    }
    
    .stButton > button:hover {
        border-color: #9ca3af;
        background-color: #f9fafb;
    }
    
    .stButton > button[kind="primary"] {
        background-color: #374151;
        border-color: #374151;
        color: white;
    }
    
    .stButton > button[kind="primary"]:hover {
        background-color: #1f2937;
    }
    
    hr {
        border: none;
        border-top: 1px solid #e5e7eb;
        margin: 2rem 0;
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
        st.error(f"Error connecting to Google Sheets: {str(e)}")
        return None

@st.cache_data(ttl=60)
def load_data_from_sheet():
    try:
        gc = init_gsheet_connection()
        if gc is None: return None
        
        spreadsheet = gc.open_by_key(SPREADSHEET_ID)
        worksheet = spreadsheet.worksheet(WORKSHEET_NAME)
        
        data = worksheet.get_all_values()
        
        expected_cols = ['Nama Barang', 'Qty', 'Harga Input', 'Total Akhir', 'Tipe', 'Status']
        
        if len(data) <= 1:
            return pd.DataFrame(columns=expected_cols)
        
        df = pd.DataFrame(data[1:], columns=data[0])
        
        if 'Status' not in df.columns:
            df['Status'] = "FALSE"
        
        df['Qty'] = pd.to_numeric(df['Qty'], errors='coerce').fillna(0).astype(int)
        df['Harga Input'] = pd.to_numeric(df['Harga Input'], errors='coerce').fillna(0).astype(int)
        df['Total Akhir'] = pd.to_numeric(df['Total Akhir'], errors='coerce').fillna(0).astype(int)
        
        df['Status'] = df['Status'].apply(lambda x: True if str(x).upper() == 'TRUE' else False)
        
        df = df[expected_cols]
        
        return df
    
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return None

def append_to_sheet(nama_barang, qty, harga, total_akhir, tipe, status):
    try:
        gc = init_gsheet_connection()
        if gc is None: return False
        
        spreadsheet = gc.open_by_key(SPREADSHEET_ID)
        worksheet = spreadsheet.worksheet(WORKSHEET_NAME)
        
        status_str = "TRUE" if status else "FALSE"
        new_row = [nama_barang, int(qty), int(harga), int(total_akhir), tipe, status_str]
        
        worksheet.append_row(new_row)
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"Error saving: {str(e)}")
        return False

def update_sheet_data(df_edited):
    try:
        gc = init_gsheet_connection()
        if gc is None: return False
        
        spreadsheet = gc.open_by_key(SPREADSHEET_ID)
        worksheet = spreadsheet.worksheet(WORKSHEET_NAME)
        
        df_upload = df_edited.copy()
        df_upload['Status'] = df_upload['Status'].astype(str).str.upper()
        
        worksheet.clear()
        set_with_dataframe(worksheet, df_upload)
        
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"Error updating data: {str(e)}")
        return False

# --- HEADER ---
st.title("🌴 Bali Trip Budget Planner")

# --- SIDEBAR: INPUT ---
with st.sidebar:
    st.header("Add Item")
    
    with st.form("form_tambah_item", clear_on_submit=True):
        nama_barang = st.text_input("Item Name", placeholder="e.g., Flight Ticket")
        
        col_side1, col_side2 = st.columns(2)
        with col_side1:
            qty = st.number_input("Quantity", min_value=1, value=1)
        with col_side2:
            harga = st.number_input("Price (Rp)", min_value=0, value=0, step=10000)
        
        tipe_harga = st.radio("Calculation Method", ["Unit Price (x Qty)", "Fixed Total"])
        is_purchased = st.checkbox("Already Paid?", value=False)
        
        submitted = st.form_submit_button("Add Item", use_container_width=True)

    if submitted:
        if not nama_barang:
            st.warning("Item name is required")
        else:
            total_akhir = (harga * qty) if tipe_harga == "Unit Price (x Qty)" else harga
            tipe_str = "Satuan" if tipe_harga == "Unit Price (x Qty)" else "Borongan"
            
            if append_to_sheet(nama_barang, qty, harga, total_akhir, tipe_str, is_purchased):
                st.success(f"{nama_barang} added successfully")
                st.rerun()

# --- MAIN CONTENT ---

df = load_data_from_sheet()

if df is not None:
    if not df.empty:
        total_estimasi = df['Total Akhir'].sum()
        uang_terpakai = df[df['Status'] == True]['Total Akhir'].sum()
        uang_dibutuhkan = df[df['Status'] == False]['Total Akhir'].sum()
        persen_terpakai = (uang_terpakai / total_estimasi * 100) if total_estimasi > 0 else 0
    else:
        total_estimasi = 0
        uang_terpakai = 0
        uang_dibutuhkan = 0
        persen_terpakai = 0

    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric("Total Budget", f"Rp {total_estimasi:,.0f}")
    with m2:
        st.metric("Paid", f"Rp {uang_terpakai:,.0f}", f"{persen_terpakai:.1f}%")
    with m3:
        st.metric("Remaining", f"Rp {uang_dibutuhkan:,.0f}")

    st.markdown("---")

    col_header, col_refresh = st.columns([4, 1])
    with col_header:
        st.subheader("Items")
    with col_refresh:
        if st.button("Refresh", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

    if not df.empty:
        edited_df = st.data_editor(
            df,
            column_config={
                "Status": st.column_config.CheckboxColumn(
                    "Paid?",
                    help="Check if paid",
                    default=False,
                ),
                "Nama Barang": st.column_config.TextColumn("Item", width="large"),
                "Qty": st.column_config.NumberColumn("Qty", width="small"),
                "Harga Input": st.column_config.NumberColumn("Price", format="Rp %d"),
                "Total Akhir": st.column_config.NumberColumn("Total", format="Rp %d", disabled=True),
                "Tipe": st.column_config.TextColumn("Type", width="small", disabled=True),
            },
            hide_index=True,
            use_container_width=True,
            num_rows="dynamic",
            key="data_editor"
        )
        
        col_left, col_right = st.columns([3, 1])
        with col_right:
            if st.button("Save Changes", type="primary", use_container_width=True):
                for index, row in edited_df.iterrows():
                     if row['Tipe'] == 'Satuan':
                         edited_df.at[index, 'Total Akhir'] = row['Harga Input'] * row['Qty']
                     else:
                         edited_df.at[index, 'Total Akhir'] = row['Harga Input']

                if update_sheet_data(edited_df):
                    st.success("Data saved successfully")
                    st.rerun()

        st.markdown("### Export")
        col_ex1, col_ex2 = st.columns(2)
        
        csv = edited_df.to_csv(index=False).encode('utf-8-sig')
        col_ex1.download_button(
            "Download CSV",
            csv,
            f"Budget_Bali_{datetime.now().strftime('%Y%m%d')}.csv",
            "text/csv",
            use_container_width=True
        )

    else:
        st.info("No data yet. Add items using the sidebar.")
