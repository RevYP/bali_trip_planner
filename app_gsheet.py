import streamlit as st
import pandas as pd
from google.oauth2 import service_account
from google.auth.transport.requests import Request
import gspread
from gspread_dataframe import set_with_dataframe
import json
from datetime import datetime

# Konfigurasi halaman
st.set_page_config(
    page_title="Bali Trip Budget Planner",
    page_icon="🌴",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS styling
st.markdown("""
<style>
    .main-title {
        text-align: center;
        color: #64B5F6;
        margin-bottom: 10px;
    }
    .subtitle {
        text-align: center;
        color: #888;
        font-size: 14px;
        margin-bottom: 30px;
    }
    .grand-total {
        text-align: center;
        font-size: 36px;
        font-weight: bold;
        color: #64B5F6;
        padding: 20px;
        background-color: rgba(100, 181, 246, 0.1);
        border-radius: 10px;
        margin: 20px 0;
        border: 2px solid #64B5F6;
    }
    .success-box {
        padding: 15px;
        border-radius: 8px;
        background-color: rgba(76, 175, 80, 0.1);
        border-left: 4px solid #4CAF50;
        color: #4CAF50;
    }
    .error-box {
        padding: 15px;
        border-radius: 8px;
        background-color: rgba(244, 67, 54, 0.1);
        border-left: 4px solid #F44336;
        color: #F44336;
    }
</style>
""", unsafe_allow_html=True)

# Google Sheets Configuration
SPREADSHEET_ID = "1TQAOaIcGsW9SiXySWXhpsABHkMsrPe1yf9x9a9FIZys"
WORKSHEET_NAME = "Sheet1"

@st.cache_resource
def init_gsheet_connection():
    """Initialize Google Sheets connection"""
    try:
        credentials_dict = st.secrets["gcp_service_account"]
        credentials = service_account.Credentials.from_service_account_info(
            credentials_dict,
            scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        )
        gc = gspread.authorize(credentials)
        return gc
    except Exception as e:
        st.error(f"❌ Gagal koneksi ke Google Sheets: {str(e)}")
        st.info("Pastikan `secrets.toml` sudah dikonfigurasi dengan benar di folder `.streamlit/`")
        return None

@st.cache_data(ttl=60)
def load_data_from_sheet():
    """Load data from Google Sheet"""
    try:
        gc = init_gsheet_connection()
        if gc is None:
            return None
        
        spreadsheet = gc.open_by_key(SPREADSHEET_ID)
        worksheet = spreadsheet.worksheet(WORKSHEET_NAME)
        
        # Get all values
        data = worksheet.get_all_values()
        
        if len(data) <= 1:
            # Hanya header atau kosong
            return pd.DataFrame(columns=['Nama Barang', 'Qty', 'Harga Input', 'Total Akhir', 'Tipe'])
        
        # Konversi ke dataframe
        df = pd.DataFrame(data[1:], columns=data[0])
        
        # Convert numeric columns
        df['Qty'] = pd.to_numeric(df['Qty'], errors='coerce').fillna(0).astype(int)
        df['Harga Input'] = pd.to_numeric(df['Harga Input'], errors='coerce').fillna(0).astype(int)
        df['Total Akhir'] = pd.to_numeric(df['Total Akhir'], errors='coerce').fillna(0).astype(int)
        
        return df
    
    except Exception as e:
        st.error(f"❌ Gagal load data: {str(e)}")
        return None

def append_to_sheet(nama_barang, qty, harga, total_akhir, tipe):
    """Append new row to Google Sheet"""
    try:
        gc = init_gsheet_connection()
        if gc is None:
            return False
        
        spreadsheet = gc.open_by_key(SPREADSHEET_ID)
        worksheet = spreadsheet.worksheet(WORKSHEET_NAME)
        
        # New row data
        new_row = [nama_barang, int(qty), int(harga), int(total_akhir), tipe]
        
        # Append row
        worksheet.append_row(new_row)
        
        # Clear cache after appending
        st.cache_data.clear()
        
        return True
    
    except Exception as e:
        st.error(f"❌ Gagal menyimpan ke Google Sheets: {str(e)}")
        return False

# Header
st.markdown('<h1 class="main-title">🌴 Bali Trip Budget Planner 🌴</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Rencana Budget Perjalanan Anda (Real-time Sync)</p>', unsafe_allow_html=True)

# Sidebar - Input Form
with st.sidebar:
    st.markdown("### 📝 Tambah Item Baru")
    st.markdown("---")
    
    with st.form("form_tambah_item"):
        nama_barang = st.text_input(
            "Nama Barang",
            placeholder="Contoh: Hotel 3 malam",
            key="input_nama"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            qty = st.number_input("Qty", min_value=1, value=1, step=1, key="input_qty")
        
        with col2:
            harga = st.number_input(
                "Harga",
                min_value=0,
                value=0,
                step=10000,
                key="input_harga"
            )
        
        tipe_harga = st.radio(
            "Tipe Harga",
            ["Harga Satuan", "Harga Total/Borongan"],
            key="input_tipe"
        )
        
        st.markdown("")
        submit = st.form_submit_button("✅ Simpan Item", use_container_width=True)
    
    # Process form submission
    if submit:
        if not nama_barang or nama_barang.strip() == "":
            st.error("❌ Nama Barang tidak boleh kosong!")
        elif qty <= 0:
            st.error("❌ Qty harus lebih dari 0!")
        elif harga < 0:
            st.error("❌ Harga tidak boleh negatif!")
        else:
            # Calculate total
            if tipe_harga == "Harga Satuan":
                total_akhir = harga * qty
            else:
                total_akhir = harga
            
            # Save to sheet
            if append_to_sheet(nama_barang.strip(), qty, harga, total_akhir, tipe_harga):
                st.markdown(f'<div class="success-box">✅ Item "{nama_barang}" berhasil disimpan!</div>', unsafe_allow_html=True)
                st.balloons()
            else:
                st.markdown(f'<div class="error-box">❌ Gagal menyimpan item</div>', unsafe_allow_html=True)

# Main Content
col1, col2 = st.columns([3, 1])

with col1:
    st.markdown("### 📊 Data Budget Perjalanan")

with col2:
    if st.button("🔄 Refresh Data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

st.markdown("---")

# Load and display data
df = load_data_from_sheet()

if df is not None and len(df) > 0:
    # Display Grand Total
    grand_total = df['Total Akhir'].sum()
    st.markdown(f'<div class="grand-total">💰 Rp {int(grand_total):,}</div>', unsafe_allow_html=True)
    
    # Display table with formatting
    st.markdown("#### Daftar Item")
    
    # Create display dataframe with formatted currency
    display_df = df.copy()
    display_df['Harga Input'] = display_df['Harga Input'].apply(lambda x: f"Rp {int(x):,}")
    display_df['Total Akhir'] = display_df['Total Akhir'].apply(lambda x: f"Rp {int(x):,}")
    
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Nama Barang": st.column_config.TextColumn(width="medium"),
            "Qty": st.column_config.NumberColumn(width="small"),
            "Harga Input": st.column_config.TextColumn(width="medium"),
            "Total Akhir": st.column_config.TextColumn(width="medium"),
            "Tipe": st.column_config.TextColumn(width="medium")
        }
    )
    
    # Summary statistics
    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📦 Total Item", len(df))
    
    with col2:
        total_qty = df['Qty'].sum()
        st.metric("🔢 Total Qty", int(total_qty))
    
    with col3:
        avg_harga = df['Harga Input'].mean()
        st.metric("📈 Rata-rata Harga", f"Rp {int(avg_harga):,}")
    
    with col4:
        st.metric("💰 Grand Total", f"Rp {int(grand_total):,}")
    
    # Export options
    st.markdown("---")
    st.markdown("### 📥 Export Data")
    
    col1, col2 = st.columns(2)
    
    with col1:
        csv = df.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="📄 Download CSV",
            data=csv,
            file_name=f"Bali_Trip_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    with col2:
        excel_buffer = None
        try:
            from openpyxl import Workbook
            from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
            
            wb = Workbook()
            ws = wb.active
            ws.title = "Bali Trip"
            
            # Headers
            headers = ['Nama Barang', 'Qty', 'Harga Input', 'Total Akhir', 'Tipe']
            for col_idx, header in enumerate(headers, 1):
                cell = ws.cell(row=1, column=col_idx)
                cell.value = header
                cell.font = Font(bold=True, color="FFFFFF")
                cell.fill = PatternFill(start_color="1F4788", end_color="1F4788", fill_type="solid")
                cell.alignment = Alignment(horizontal="center", vertical="center")
            
            # Data rows
            for row_idx, row in enumerate(df.values, 2):
                for col_idx, value in enumerate(row, 1):
                    cell = ws.cell(row=row_idx, column=col_idx)
                    cell.value = value
                    if col_idx in [2, 3, 4]:
                        cell.alignment = Alignment(horizontal="right")
            
            # Total row
            total_row = len(df) + 2
            ws.cell(row=total_row, column=1).value = "GRAND TOTAL"
            ws.cell(row=total_row, column=1).font = Font(bold=True)
            ws.cell(row=total_row, column=4).value = grand_total
            ws.cell(row=total_row, column=4).font = Font(bold=True)
            
            # Column widths
            ws.column_dimensions['A'].width = 25
            ws.column_dimensions['B'].width = 8
            ws.column_dimensions['C'].width = 15
            ws.column_dimensions['D'].width = 15
            ws.column_dimensions['E'].width = 20
            
            # Save to buffer
            from io import BytesIO
            excel_buffer = BytesIO()
            wb.save(excel_buffer)
            excel_buffer.seek(0)
            
            st.download_button(
                label="📊 Download Excel",
                data=excel_buffer.getvalue(),
                file_name=f"Bali_Trip_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        except ImportError:
            st.info("💡 Install openpyxl untuk export Excel: `pip install openpyxl`")

else:
    st.info("📝 Belum ada item. Tambahkan item di sidebar untuk memulai perencanaan budget!")
    st.markdown(f'<div class="grand-total">💰 Rp 0</div>', unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #888; font-size: 12px;'>
    <p>Bali Trip Budget Planner © 2026</p>
    <p>💾 Data disimpan secara real-time ke Google Sheets</p>
</div>
""", unsafe_allow_html=True)
