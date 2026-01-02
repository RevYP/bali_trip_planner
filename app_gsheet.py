import streamlit as st
import pandas as pd
from google.oauth2 import service_account
import gspread
from gspread_dataframe import set_with_dataframe
from datetime import datetime

# Page Configuration
st.set_page_config(
    page_title="Trip Budget Manager",
    page_icon="🌴",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    /* Clean modern look */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* Header styling */
    .main-header {
        font-size: 1.8rem;
        font-weight: 600;
        color: #2c3e50;
        margin-bottom: 0.3rem;
    }
    
    .sub-header {
        font-size: 0.95rem;
        color: #7f8c8d;
        margin-bottom: 1.5rem;
    }
    
    /* Metric cards */
    div[data-testid="metric-container"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border: none;
        padding: 1.2rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.07);
    }
    
    div[data-testid="metric-container"] > label {
        color: rgba(255,255,255,0.9) !important;
        font-weight: 500;
    }
    
    div[data-testid="metric-container"] > div {
        color: white !important;
        font-weight: 600;
    }
    
    div[data-testid="metric-container"] [data-testid="metric-container"] {
        color: rgba(255,255,255,0.8) !important;
    }
    
    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #f8f9fa;
    }
    
    /* Form styling */
    .stForm {
        background-color: white;
        padding: 1.5rem;
        border-radius: 8px;
        border: 1px solid #e9ecef;
    }
    
    /* Buttons */
    .stButton > button {
        border-radius: 6px;
        font-weight: 500;
        transition: all 0.2s;
    }
    
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    
    /* Table header */
    .section-header {
        font-size: 1.2rem;
        font-weight: 600;
        color: #2c3e50;
        margin-bottom: 1rem;
    }
    
    /* Delete button styling */
    button[kind="secondary"] {
        color: #e74c3c !important;
        border-color: #e74c3c !important;
    }
    
    button[kind="secondary"]:hover {
        background-color: #ffe8e6 !important;
    }
</style>
""", unsafe_allow_html=True)

# Database Configuration
SPREADSHEET_ID = "1TQAOaIcGsW9SiXySWXhpsABHkMsrPe1yf9x9a9FIZys"
WORKSHEET_NAME = "Sheet1"

@st.cache_resource
def init_connection():
    try:
        creds = service_account.Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=["https://www.googleapis.com/auth/spreadsheets", 
                   "https://www.googleapis.com/auth/drive"]
        )
        return gspread.authorize(creds)
    except Exception as e:
        st.error(f"Connection failed: {str(e)}")
        return None

@st.cache_data(ttl=5)
def load_data():
    try:
        gc = init_connection()
        if not gc: 
            return None
        
        ws = gc.open_by_key(SPREADSHEET_ID).worksheet(WORKSHEET_NAME)
        data = ws.get_all_values()
        
        columns = ['Item', 'Qty', 'Price', 'Total', 'Type', 'Paid', 'Booked']
        
        if len(data) <= 1:
            return pd.DataFrame(columns=columns)
        
        df = pd.DataFrame(data[1:], columns=data[0])
        df = df[df['Item'].str.strip() != ''].dropna(subset=['Item'])
        
        for col in columns:
            if col not in df.columns:
                df[col] = "FALSE"
        
        df['Qty'] = pd.to_numeric(df['Qty'], errors='coerce').fillna(0).astype(int)
        df['Price'] = pd.to_numeric(df['Price'], errors='coerce').fillna(0).astype(int)
        df['Total'] = pd.to_numeric(df['Total'], errors='coerce').fillna(0).astype(int)
        df['Paid'] = df['Paid'].apply(lambda x: str(x).upper() == 'TRUE')
        df['Booked'] = df['Booked'].apply(lambda x: str(x).upper() == 'TRUE')
        
        return df[columns]
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return None

def save_item(item, qty, price, total, type_val, paid, booked):
    try:
        gc = init_connection()
        ws = gc.open_by_key(SPREADSHEET_ID).worksheet(WORKSHEET_NAME)
        ws.append_row([
            item, 
            int(qty), 
            int(price), 
            int(total), 
            type_val, 
            "TRUE" if paid else "FALSE", 
            "TRUE" if booked else "FALSE"
        ])
        st.cache_data.clear()
        return True
    except:
        return False

def update_sheet(df_edited):
    try:
        gc = init_connection()
        ws = gc.open_by_key(SPREADSHEET_ID).worksheet(WORKSHEET_NAME)
        
        df_save = df_edited.copy()
        if 'Delete' in df_save.columns:
            df_save = df_save.drop(columns=['Delete'])
        
        df_save['Paid'] = df_save['Paid'].apply(lambda x: "TRUE" if x else "FALSE")
        df_save['Booked'] = df_save['Booked'].apply(lambda x: "TRUE" if x else "FALSE")
        
        ws.clear()
        set_with_dataframe(ws, df_save)
        st.cache_data.clear()
        return True
    except:
        return False

# Main Interface
st.markdown('<div class="main-header">Bali Trip Budget</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Track expenses and bookings for your trip</div>', unsafe_allow_html=True)

# Sidebar - Add New Item
with st.sidebar:
    st.markdown("### Add Expense")
    
    with st.form("entry_form", clear_on_submit=True):
        item_name = st.text_input("Description", placeholder="Hotel, Flight, Activities...")
        
        col1, col2 = st.columns(2)
        with col1:
            quantity = st.number_input("Quantity", min_value=1, value=1)
        with col2:
            unit_price = st.number_input("Price (IDR)", min_value=0, step=50000)
        
        pricing_type = st.radio("Pricing", ["Per Unit", "Fixed Amount"], horizontal=True)
        
        st.divider()
        
        col3, col4 = st.columns(2)
        with col3:
            is_paid = st.checkbox("✓ Paid")
        with col4:
            is_booked = st.checkbox("✓ Booked")
        
        submit = st.form_submit_button("Add Entry", use_container_width=True, type="primary")
        
        if submit:
            if item_name.strip():
                total_amt = (unit_price * quantity) if pricing_type == "Per Unit" else unit_price
                type_label = "Unit" if pricing_type == "Per Unit" else "Lump Sum"
                
                if save_item(item_name, quantity, unit_price, total_amt, type_label, is_paid, is_booked):
                    st.success("Entry added")
                    st.rerun()
                else:
                    st.error("Failed to save")
            else:
                st.warning("Please enter a description")

# Load Data
df = load_data()

if df is not None:
    # Calculate Summary
    if not df.empty:
        total_budget = df['Total'].sum()
        paid_amount = df[df['Paid']]['Total'].sum()
        remaining = total_budget - paid_amount
        paid_percentage = (paid_amount / total_budget * 100) if total_budget > 0 else 0
    else:
        total_budget = paid_amount = remaining = paid_percentage = 0
    
    # Summary Metrics
    metric1, metric2, metric3 = st.columns(3)
    
    with metric1:
        st.metric(
            "Total Budget", 
            f"Rp {total_budget:,.0f}",
            f"{len(df)} items"
        )
    
    with metric2:
        st.metric(
            "Amount Paid", 
            f"Rp {paid_amount:,.0f}",
            f"{paid_percentage:.1f}% complete"
        )
    
    with metric3:
        st.metric(
            "Balance", 
            f"Rp {remaining:,.0f}",
            f"{(remaining/total_budget*100):.1f}% left" if total_budget > 0 else "0%"
        )
    
    st.divider()
    
    # Data Table Section
    header_col, refresh_col = st.columns([5, 1])
    with header_col:
        st.markdown('<div class="section-header">Expense Details</div>', unsafe_allow_html=True)
    with refresh_col:
        if st.button("↻ Refresh", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    
    if not df.empty:
        df_display = df.copy()
        df_display.insert(0, "Delete", False)
        
        # Editable Table
        edited_data = st.data_editor(
            df_display,
            column_config={
                "Delete": st.column_config.CheckboxColumn("", width="small"),
                "Item": st.column_config.TextColumn("Description", width="medium", required=True),
                "Qty": st.column_config.NumberColumn("Qty", width="small"),
                "Price": st.column_config.NumberColumn("Unit Price", format="Rp %d", width="medium"),
                "Total": st.column_config.NumberColumn("Total Cost", format="Rp %d", width="medium"),
                "Type": st.column_config.TextColumn("Type", width="small", disabled=True),
                "Paid": st.column_config.CheckboxColumn("Paid", width="small"),
                "Booked": st.column_config.CheckboxColumn("Booked", width="small")
            },
            hide_index=True,
            use_container_width=True,
            num_rows="fixed"
        )
        
        # Action Buttons
        btn_col1, btn_spacer, btn_col2 = st.columns([1.5, 2.5, 1.5])
        
        with btn_col1:
            items_to_delete = edited_data[edited_data['Delete'] == True]
            if not items_to_delete.empty:
                if st.button(f"Delete ({len(items_to_delete)})", type="secondary", use_container_width=True):
                    update_sheet(edited_data[edited_data['Delete'] == False])
                    st.rerun()
            else:
                st.button("Delete", disabled=True, type="secondary", use_container_width=True)
        
        with btn_col2:
            if st.button("Save Changes", type="primary", use_container_width=True):
                for idx, row in edited_data.iterrows():
                    calculated_total = row['Price'] * row['Qty'] if row['Type'] == 'Unit' else row['Price']
                    edited_data.at[idx, 'Total'] = calculated_total
                
                if update_sheet(edited_data):
                    st.success("Changes saved")
                    st.rerun()
                else:
                    st.error("Save failed")
    else:
        st.info("No expenses recorded yet. Add your first entry using the form on the left.")
else:
    st.error("Unable to connect to database. Please check your credentials.")
