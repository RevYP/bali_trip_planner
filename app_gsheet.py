import streamlit as st
import pandas as pd
from google.oauth2.service_account import Credentials
import gspread
from datetime import datetime
import json

# Page config
st.set_page_config(
    page_title="Bali Trip Budget Planner",
    page_icon="✈️",
    layout="wide"
)

# Clean, minimalist CSS
st.markdown("""
<style>
    /* Remove default Streamlit padding */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* Clean header styling */
    h1 {
        color: #1f2937;
        font-weight: 600;
        margin-bottom: 2rem;
    }
    
    h2, h3 {
        color: #374151;
        font-weight: 500;
    }
    
    /* Clean table styling */
    .dataframe {
        border: 1px solid #e5e7eb;
        font-size: 0.9rem;
    }
    
    .dataframe thead th {
        background-color: #f9fafb;
        color: #374151;
        font-weight: 500;
        border-bottom: 2px solid #e5e7eb;
    }
    
    /* Clean button styling */
    .stButton > button {
        background-color: #ffffff;
        border: 1px solid #d1d5db;
        color: #374151;
        font-weight: 400;
        padding: 0.5rem 1rem;
        transition: all 0.15s;
    }
    
    .stButton > button:hover {
        border-color: #9ca3af;
        background-color: #f9fafb;
    }
    
    /* Primary action button */
    .stButton > button[kind="primary"] {
        background-color: #3b82f6;
        border-color: #3b82f6;
        color: white;
    }
    
    .stButton > button[kind="primary"]:hover {
        background-color: #2563eb;
        border-color: #2563eb;
    }
    
    /* Clean input fields */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stSelectbox > div > div > select {
        border: 1px solid #d1d5db;
        border-radius: 0.375rem;
    }
    
    /* Clean metrics */
    [data-testid="stMetricValue"] {
        color: #1f2937;
        font-size: 1.5rem;
    }
    
    [data-testid="stMetricLabel"] {
        color: #6b7280;
        font-size: 0.875rem;
    }
    
    /* Clean divider */
    hr {
        margin: 2rem 0;
        border: none;
        border-top: 1px solid #e5e7eb;
    }
    
    /* Clean success/error messages */
    .stSuccess {
        background-color: #f0fdf4;
        border-left: 3px solid #22c55e;
        color: #166534;
    }
    
    .stError {
        background-color: #fef2f2;
        border-left: 3px solid #ef4444;
        color: #991b1b;
    }
    
    .stWarning {
        background-color: #fffbeb;
        border-left: 3px solid #f59e0b;
        color: #92400e;
    }
    
    .stInfo {
        background-color: #eff6ff;
        border-left: 3px solid #3b82f6;
        color: #1e40af;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Google Sheets connection
@st.cache_resource
def init_gsheet_connection():
    try:
        credentials_dict = json.loads(st.secrets["gcp_service_account"])
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        credentials = Credentials.from_service_account_info(credentials_dict, scopes=scopes)
        client = gspread.authorize(credentials)
        return client
    except Exception as e:
        st.error(f"Error connecting to Google Sheets: {str(e)}")
        return None

# Load data from Google Sheets
@st.cache_data(ttl=60)
def load_data():
    try:
        client = init_gsheet_connection()
        if client is None:
            return pd.DataFrame()
        
        spreadsheet = client.open("Bali Trip Budget")
        worksheet = spreadsheet.worksheet("Expenses")
        data = worksheet.get_all_records()
        
        if not data:
            return pd.DataFrame(columns=['Tanggal', 'Kategori', 'Deskripsi', 'Jumlah', 'Mata Uang', 'Keterangan'])
        
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return pd.DataFrame()

# Add expense to Google Sheets
def add_expense(tanggal, kategori, deskripsi, jumlah, mata_uang, keterangan=""):
    try:
        client = init_gsheet_connection()
        if client is None:
            return False
        
        spreadsheet = client.open("Bali Trip Budget")
        worksheet = spreadsheet.worksheet("Expenses")
        
        new_row = [
            tanggal.strftime("%Y-%m-%d"),
            kategori,
            deskripsi,
            jumlah,
            mata_uang,
            keterangan
        ]
        
        worksheet.append_row(new_row)
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"Error adding expense: {str(e)}")
        return False

# Delete expense from Google Sheets
def delete_expense(row_index):
    try:
        client = init_gsheet_connection()
        if client is None:
            return False
        
        spreadsheet = client.open("Bali Trip Budget")
        worksheet = spreadsheet.worksheet("Expenses")
        
        # row_index + 2 because: +1 for header, +1 for 0-based to 1-based indexing
        worksheet.delete_rows(row_index + 2)
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"Error deleting expense: {str(e)}")
        return False

# Main app
def main():
    st.title("Bali Trip Budget Planner")
    
    # Load data
    df = load_data()
    
    # Sidebar - Add Expense
    with st.sidebar:
        st.header("Add Expense")
        
        with st.form("expense_form", clear_on_submit=True):
            tanggal = st.date_input("Date", datetime.now())
            kategori = st.selectbox(
                "Category",
                ["Akomodasi", "Transportasi", "Makanan", "Aktivitas", "Belanja", "Lain-lain"]
            )
            deskripsi = st.text_input("Description")
            
            col1, col2 = st.columns(2)
            with col1:
                jumlah = st.number_input("Amount", min_value=0.0, step=0.01)
            with col2:
                mata_uang = st.selectbox("Currency", ["IDR", "USD", "EUR"])
            
            keterangan = st.text_area("Notes", height=80)
            
            submitted = st.form_submit_button("Add Expense", type="primary", use_container_width=True)
            
            if submitted:
                if deskripsi and jumlah > 0:
                    if add_expense(tanggal, kategori, deskripsi, jumlah, mata_uang, keterangan):
                        st.success("Expense added successfully")
                        st.rerun()
                    else:
                        st.error("Failed to add expense")
                else:
                    st.warning("Please fill in all required fields")
    
    # Main content
    if df.empty:
        st.info("No expenses recorded yet. Add your first expense using the sidebar.")
    else:
        # Summary metrics
        st.subheader("Summary")
        
        # Calculate totals by currency
        currency_totals = df.groupby('Mata Uang')['Jumlah'].sum()
        
        cols = st.columns(len(currency_totals))
        for idx, (currency, total) in enumerate(currency_totals.items()):
            with cols[idx]:
                st.metric(
                    label=f"Total ({currency})",
                    value=f"{total:,.2f}"
                )
        
        st.divider()
        
        # Category breakdown
        st.subheader("Breakdown by Category")
        
        category_summary = df.groupby(['Kategori', 'Mata Uang'])['Jumlah'].sum().reset_index()
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Display category table
            for currency in df['Mata Uang'].unique():
                currency_data = category_summary[category_summary['Mata Uang'] == currency]
                if not currency_data.empty:
                    st.write(f"**{currency}**")
                    st.dataframe(
                        currency_data[['Kategori', 'Jumlah']].rename(columns={'Kategori': 'Category', 'Jumlah': 'Amount'}),
                        hide_index=True,
                        use_container_width=True
                    )
        
        with col2:
            # Category distribution
            category_totals = df.groupby('Kategori')['Jumlah'].sum().sort_values(ascending=False)
            st.write("**Distribution**")
            for cat, amount in category_totals.items():
                percentage = (amount / df['Jumlah'].sum()) * 100
                st.write(f"{cat}: {percentage:.1f}%")
        
        st.divider()
        
        # Detailed expenses
        st.subheader("All Expenses")
        
        # Display options
        col1, col2 = st.columns([3, 1])
        with col1:
            filter_category = st.multiselect(
                "Filter by category",
                options=df['Kategori'].unique(),
                default=df['Kategori'].unique()
            )
        with col2:
            sort_order = st.selectbox("Sort by", ["Date (newest)", "Date (oldest)", "Amount (high)", "Amount (low)"])
        
        # Filter data
        filtered_df = df[df['Kategori'].isin(filter_category)].copy()
        
        # Sort data
        if sort_order == "Date (newest)":
            filtered_df = filtered_df.sort_values('Tanggal', ascending=False)
        elif sort_order == "Date (oldest)":
            filtered_df = filtered_df.sort_values('Tanggal', ascending=True)
        elif sort_order == "Amount (high)":
            filtered_df = filtered_df.sort_values('Jumlah', ascending=False)
        else:
            filtered_df = filtered_df.sort_values('Jumlah', ascending=True)
        
        # Display expenses with delete option
        for idx, row in filtered_df.iterrows():
            with st.container():
                col1, col2, col3, col4, col5 = st.columns([2, 2, 3, 2, 1])
                
                with col1:
                    st.write(f"**{row['Tanggal']}**")
                with col2:
                    st.write(f"*{row['Kategori']}*")
                with col3:
                    st.write(row['Deskripsi'])
                with col4:
                    st.write(f"{row['Jumlah']:,.2f} {row['Mata Uang']}")
                with col5:
                    if st.button("🗑️", key=f"del_{idx}"):
                        original_index = df[df['Tanggal'] == row['Tanggal']].index[0]
                        if delete_expense(original_index):
                            st.success("Expense deleted")
                            st.rerun()
                
                if row.get('Keterangan'):
                    st.caption(f"Note: {row['Keterangan']}")
                
                st.divider()

if __name__ == "__main__":
    main()
