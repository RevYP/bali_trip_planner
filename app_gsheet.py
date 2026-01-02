import streamlit as st
import pandas as pd
from google.oauth2 import service_account
import gspread
from gspread_dataframe import set_with_dataframe
from datetime import datetime
from gspread.utils import rowcol_to_a1

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="Bali Trip Planner",
    page_icon="🌸", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS: PINK, TEAL, & CREAM THEME ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"], [data-testid="stAppViewContainer"] {
        font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text", "Inter", sans-serif !important;
        color: #424242; 
        background-color: #FFFBF5; 
    }

    .stApp { background-color: #FFFBF5; }
    
    section[data-testid="stSidebar"] {
        background-color: #F7F2E8; 
        border-right: 1px solid #E0E0E0;
    }

    .main-title {
        font-size: 2.2rem;
        font-weight: 800;
        letter-spacing: -0.02em;
        color: #D81B60; 
        margin-bottom: 0.2rem;
    }
    
    .sub-title {
        font-size: 1rem;
        color: #00897B; 
        font-weight: 500;
        margin-bottom: 2rem;
    }

    /* Metric Cards */
    div[data-testid="metric-container"] {
        background-color: #FFFFFF;
        border: 1px solid #F8BBD0; 
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 2px 5px rgba(216, 27, 96, 0.05);
    }
    
    div[data-testid="metric-container"] label {
        color: #00796B; 
        font-weight: 600;
        font-size: 0.9rem;
    }
    
    div[data-testid="metric-container"] div[data-testid="stMetricValue"] {
        color: #D81B60;
        font-weight: 700;
        font-size: 1.8rem;
    }

    /* Primary Button (Teal) */
    .stButton > button {
        background-color: #00897B; 
        color: white;
        border-radius: 8px;
        border: none;
        padding: 0.6rem 1.2rem;
        font-weight: 600;
        box-shadow: 0 2px 4px rgba(0, 137, 123, 0.2);
        transition: all 0.2s ease;
    }
    .stButton > button:hover {
        background-color: #00796B; 
        color: white;
        transform: translateY(-1px);
    }

    /* Delete Button Styling (Red) */
    button[kind="secondary"] {
        background-color: white;
        color: #D32F2F;
        border: 1px solid #D32F2F;
    }
    button[kind="secondary"]:hover {
        background-color: #FFEBEE;
        color: #B71C1C;
        border-color: #B71C1C;
    }

    div[data-testid="stDataEditor"] {
        border-radius: 10px;
        border: 1px solid #FFE0B2; 
        overflow: hidden;
        background-color: white;
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
        st.error(f"Connection Error: {str(e)}")
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
        st.error(f"Error loading data: {str(e)}")
        return None

def save_data(item, qty, price, total, type_, paid, booked):
    try:
        gc = init_gsheet_connection()
        ws = gc.open_by_key(SPREADSHEET_ID).worksheet(WORKSHEET_NAME)
        row = [item, int(qty), int(price), int(total), type_, "TRUE" if paid else "FALSE", "TRUE" if booked else "FALSE"]
        ws.append_row(row)
        st.cache_data.clear()
        return True
    except Exception:
        return False

def update_data(df_edited):
    try:
        gc = init_gsheet_connection()
        ws = gc.open_by_key(SPREADSHEET_ID).worksheet(WORKSHEET_NAME)
        
        # Bersihkan kolom 'Delete' sebelum upload ke Google Sheet
        df_up = df_edited.copy()
        if 'Delete' in df_up.columns:
            df_up = df_up.drop(columns=['Delete'])
            
        df_up['Paid'] = df_up['Paid'].apply(lambda x: "TRUE" if x else "FALSE")
        df_up['Booked'] = df_up['Booked'].apply(lambda x: "TRUE" if x else "FALSE")
        
        ws.clear()
        set_with_dataframe(ws, df_up)
        st.cache_data.clear()
        return True
    except Exception:
        return False

# --- UI START ---
st.markdown('<div class="main-title">Bali Trip Planner</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Manage your budget efficiently</div>', unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("### 📝 New Entry")
    with st.form("add_form", clear_on_submit=True):
        item = st.text_input("Item Name", placeholder="e.g. Flight Tickets")
        c1, c2 = st.columns(2)
        with c1: qty = st.number_input("Qty", 1, value=1)
        with c2: price = st.number_input("Price (IDR)", 0, step=50000)
        type_ = st.radio("Pricing Type", ["Per Unit (x Qty)", "Lump Sum (Total)"])
        
        st.markdown("---")
        st.caption("Initial Status")
        paid = st.checkbox("Paid")
        booked = st.checkbox("Booked / Ordered")
        
        if st.form_submit_button("Save Item", use_container_width=True):
            if item:
                total = (price * qty) if type_ == "Per Unit (x Qty)" else price
                type_str = "Unit" if type_ == "Per Unit (x Qty)" else "Lump Sum"
                if save_data(item, qty, price, total, type_str, paid, booked):
                    st.toast("Item saved successfully!", icon="✅")
                    st.rerun()
            else:
                st.toast("Item name is required.", icon="⚠️")

# --- DASHBOARD ---
df = load_data()
if df is not None:
    if not df.empty:
        total_budget = df['Total'].sum()
        total_paid = df[df['Paid']]['Total'].sum()
        remaining = total_budget - total_paid
        pct = (total_paid / total_budget * 100) if total_budget > 0 else 0
    else:
        total_budget = total_paid = remaining = pct = 0

    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric("Total Budget", f"Rp {total_budget:,.0f}", delta=f"{len(df)} Items")
    with m2:
        st.metric("Amount Paid", f"Rp {total_paid:,.0f}", delta=f"{pct:.1f}% Paid")
    with m3:
        st.metric("Remaining", f"Rp {remaining:,.0f}", delta=f"- Rp {total_paid:,.0f}", delta_color="inverse")

    st.markdown("---")
    
    # --- TABLE SECTION ---
    c_head, c_btn = st.columns([4,1])
    with c_head: st.markdown("#### Budget Details")
    with c_btn: 
        if st.button("Refresh Data"): st.cache_data.clear(); st.rerun()

    if not df.empty:
        # Menambahkan kolom "Delete" Virtual di posisi paling kiri
        df_display = df.copy()
        df_display.insert(0, "Delete", False)

        edited_df = st.data_editor(
            df_display,
            column_config={
                "Delete": st.column_config.CheckboxColumn(
                    "Del?",
                    help="Check to delete this item",
                    default=False,
                    width="small"
                ),
                "Paid": st.column_config.CheckboxColumn("Paid", default=False),
                "Booked": st.column_config.CheckboxColumn("Booked", default=False),
                "Item": st.column_config.TextColumn("Item Name", width="large"),
                "Total": st.column_config.NumberColumn("Total", format="Rp %d", disabled=True),
                "Price": st.column_config.NumberColumn("Price", format="Rp %d"),
                "Type": st.column_config.TextColumn("Type", disabled=True)
            },
            hide_index=True,
            use_container_width=True,
            num_rows="dynamic",
            key="data_editor"
        )

        # BUTTONS ACTION
        col_delete, col_space, col_save = st.columns([1.5, 2, 1.5])
        
        # 1. DELETE BUTTON LOGIC
        with col_delete:
            # Hitung berapa yang dicentang delete
            rows_to_delete = edited_df[edited_df['Delete'] == True]
            
            if not rows_to_delete.empty:
                if st.button(f"🗑️ Delete {len(rows_to_delete)} Item(s)", type="secondary", use_container_width=True):
                    # Filter data: Ambil yang 'Delete' nya FALSE
                    df_final = edited_df[edited_df['Delete'] == False]
                    # Update ke Google Sheet
                    if update_data(df_final):
                        st.toast("Selected items deleted!", icon="🗑️")
                        st.rerun()
            else:
                st.button("🗑️ Delete Selected", disabled=True, use_container_width=True)

        # 2. SAVE CHANGES LOGIC
        with col_save:
            # Kita cek apakah ada perubahan selain kolom Delete
            if st.button("💾 Save Changes", type="primary", use_container_width=True):
                # Recalculate totals
                for idx, row in edited_df.iterrows():
                    val = row['Price'] * row['Qty'] if row['Type'] == 'Unit' else row['Price']
                    edited_df.at[idx, 'Total'] = val
                
                if update_data(edited_df):
                    st.toast("All changes saved!", icon="💾")
                    st.rerun()
    else:
        st.info("No data yet. Please add items from the sidebar.")
