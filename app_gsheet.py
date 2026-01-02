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
    page_icon="🌴", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS: MODERN DARK THEME (DISCORD COLOR PALETTE) ---
st.markdown("""
<style>
    /* Font Open Sans (Mirip Font Discord/Modern Web) */
    @import url('https://fonts.googleapis.com/css2?family=Open+Sans:wght@400;600;700;800&display=swap');

    html, body, [class*="css"], [data-testid="stAppViewContainer"] {
        font-family: 'Open Sans', 'Helvetica Neue', sans-serif !important;
        background-color: #313338; 
        color: #dbdee1;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #2b2d31; 
        border-right: none;
    }

    /* Header */
    .main-title {
        font-family: 'Open Sans', sans-serif;
        font-weight: 800; 
        font-size: 2.2rem;
        color: #f2f3f5;
        margin-bottom: 0.2rem;
    }
    
    .sub-title {
        font-size: 1rem;
        color: #949ba4;
        font-weight: 500;
        margin-bottom: 2rem;
    }

    /* Cards (Kotak Angka) */
    div[data-testid="metric-container"] {
        background-color: #2b2d31; 
        border-left: 4px solid #5865F2; /* Aksen Biru */
        padding: 15px;
        border-radius: 4px; 
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
    }
    
    div[data-testid="metric-container"] label {
        color: #b5bac1; 
        font-weight: 700;
        font-size: 0.85rem;
        text-transform: uppercase; /* Biar tegas */
    }
    
    div[data-testid="metric-container"] div[data-testid="stMetricValue"] {
        color: #f2f3f5;
        font-weight: 700;
        font-size: 1.6rem;
    }

    /* Tombol Utama (Biru Blurple) */
    .stButton > button {
        background-color: #5865F2; 
        color: white;
        border-radius: 4px;
        border: none;
        padding: 0.6rem 1.2rem;
        font-weight: 600;
        font-size: 0.95rem;
        transition: background-color 0.2s;
    }
    .stButton > button:hover {
        background-color: #4752C4; 
        color: white;
    }

    /* Tombol Delete (Merah) */
    button[kind="secondary"] {
        background-color: transparent;
        color: #DA373C;
        border: 1px solid #DA373C;
    }
    button[kind="secondary"]:hover {
        background-color: #DA373C;
        color: white;
        border: 1px solid #DA373C;
    }

    /* Tabel */
    div[data-testid="stDataEditor"] {
        border-radius: 4px;
        border: 1px solid #1e1f22;
        background-color: #2b2d31;
    }
    
    /* Checkbox agar warnanya gelap pas */
    div[data-baseweb="checkbox"] div {
        background-color: #2b2d31;
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

# --- UI START ---
st.markdown('<div class="main-title">Bali Trip Planner</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Manage your budget efficiently</div>', unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("### 📝 Add New Item")
    with st.form("add_form", clear_on_submit=True):
        item = st.text_input("Item Name", placeholder="e.g. Flight Tickets")
        c1, c2 = st.columns(2)
        with c1: qty = st.number_input("Qty", 1, value=1)
        with c2: price = st.number_input("Price (IDR)", 0, step=50000)
        type_ = st.radio("Type", ["Per Unit", "Lump Sum"])
        
        st.markdown("---")
        paid = st.checkbox("Paid")
        booked = st.checkbox("Booked")
        
        if st.form_submit_button("Save Item", use_container_width=True):
            if item:
                tot = (price * qty) if type_ == "Per Unit" else price
                typ = "Unit" if type_ == "Per Unit" else "Lump Sum"
                if save_data(item, qty, price, tot, typ, paid, booked):
                    st.success("Item saved successfully!")
                    st.rerun()
            else:
                st.warning("Item name is required.")

# --- DASHBOARD ---
df = load_data()
if df is not None:
    if not df.empty:
        total = df['Total'].sum()
        paid = df[df['Paid']]['Total'].sum()
        remain = total - paid
        pct = (paid/total*100) if total > 0 else 0
    else:
        total = paid = remain = pct = 0

    m1, m2, m3 = st.columns(3)
    with m1: st.metric("Total Budget", f"Rp {total:,.0f}", f"{len(df)} Items")
    with m2: st.metric("Paid Amount", f"Rp {paid:,.0f}", f"{pct:.1f}%")
    with m3: st.metric("Remaining", f"Rp {remain:,.0f}", f"- Rp {paid:,.0f}", delta_color="inverse")

    st.markdown("---")
    
    # --- TABLE ---
    c_head, c_btn = st.columns([4,1])
    with c_head: st.markdown("#### Budget Details")
    with c_btn: 
        if st.button("Refresh"): st.cache_data.clear(); st.rerun()

    if not df.empty:
        df_display = df.copy()
        df_display.insert(0, "Delete", False)

        edited_df = st.data_editor(
            df_display,
            column_config={
                "Delete": st.column_config.CheckboxColumn("Del?", width="small"),
                "Paid": st.column_config.CheckboxColumn("Paid"),
                "Booked": st.column_config.CheckboxColumn("Booked"),
                "Item": st.column_config.TextColumn("Item Name", width="large"),
                "Total": st.column_config.NumberColumn("Total", format="Rp %d", disabled=True),
                "Price": st.column_config.NumberColumn("Price", format="Rp %d"),
                "Type": st.column_config.TextColumn("Type", disabled=True)
            },
            hide_index=True,
            use_container_width=True,
            num_rows="dynamic"
        )

        col_del, col_space, col_save = st.columns([1.5, 2, 1.5])
        
        # DELETE BUTTON
        with col_del:
            to_del = edited_df[edited_df['Delete'] == True]
            if not to_del.empty:
                if st.button(f"🗑️ Delete {len(to_del)}", type="secondary", use_container_width=True):
                    update_data(edited_df[edited_df['Delete'] == False])
                    st.rerun()
            else:
                st.button("🗑️ Delete Selected", disabled=True, use_container_width=True)
        
        # SAVE BUTTON
        with col_save:
            if st.button("💾 Save Changes", type="primary", use_container_width=True):
                 for idx, row in edited_df.iterrows():
                    val = row['Price'] * row['Qty'] if row['Type'] == 'Unit' else row['Price']
                    edited_df.at[idx, 'Total'] = val
                 update_data(edited_df)
                 st.success("Changes saved!")
                 st.rerun()
    else:
        st.info("No items yet.")
