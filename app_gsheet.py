import streamlit as st
import pandas as pd
from google.oauth2 import service_account
import gspread
from gspread_dataframe import set_with_dataframe
from datetime import datetime
from gspread.utils import rowcol_to_a1
import plotly.express as px
import plotly.graph_objects as go

# --- KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="Bali Trip Budget Planner",
    page_icon="🌴",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- MODERN CSS STYLING ---
st.markdown("""
<style>
    /* Global Styles */
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap');
    
    * {
        font-family: 'Poppins', sans-serif;
    }
    
    .main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
    }
    
    .block-container {
        padding-top: 1rem;
        padding-bottom: 3rem;
        background: rgba(255, 255, 255, 0.95);
        border-radius: 20px;
        box-shadow: 0 20px 60px rgba(0,0,0,0.3);
    }
    
    /* Header Styling */
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 15px;
        margin-bottom: 2rem;
        box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);
    }
    
    .main-title {
        font-size: 3rem;
        font-weight: 700;
        color: white;
        margin: 0;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
    }
    
    .main-subtitle {
        font-size: 1.2rem;
        color: rgba(255,255,255,0.9);
        margin-top: 0.5rem;
        font-weight: 300;
    }
    
    /* Metric Cards */
    div[data-testid="metric-container"] {
        background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
        border: none;
        padding: 1.5rem;
        border-radius: 15px;
        box-shadow: 0 8px 24px rgba(0,0,0,0.12);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    
    div[data-testid="metric-container"]:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 32px rgba(0,0,0,0.18);
    }
    
    div[data-testid="metric-container"] > div {
        text-align: center;
    }
    
    [data-testid="stMetricLabel"] {
        font-size: 1rem;
        font-weight: 600;
        color: #4a5568;
    }
    
    [data-testid="stMetricValue"] {
        font-size: 2rem;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
        padding: 2rem 1rem;
    }
    
    section[data-testid="stSidebar"] h2 {
        color: white;
        font-weight: 600;
        text-align: center;
        margin-bottom: 1.5rem;
    }
    
    section[data-testid="stSidebar"] .stTextInput label,
    section[data-testid="stSidebar"] .stNumberInput label,
    section[data-testid="stSidebar"] .stRadio label,
    section[data-testid="stSidebar"] .stCheckbox label {
        color: white !important;
        font-weight: 500;
    }
    
    section[data-testid="stSidebar"] input {
        border-radius: 10px;
        border: 2px solid rgba(255,255,255,0.3);
        background: rgba(255,255,255,0.95);
    }
    
    /* Buttons */
    .stButton > button {
        width: 100%;
        border-radius: 12px;
        font-weight: 600;
        padding: 0.75rem 2rem;
        border: none;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
        transition: all 0.3s ease;
        font-size: 1rem;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 28px rgba(102, 126, 234, 0.6);
    }
    
    .stButton > button:active {
        transform: translateY(0px);
    }
    
    /* Form Submit Button */
    .stFormSubmitButton > button {
        background: white !important;
        color: #667eea !important;
        font-weight: 700;
        border: 2px solid white;
    }
    
    .stFormSubmitButton > button:hover {
        background: rgba(255,255,255,0.9) !important;
        transform: scale(1.05);
    }
    
    /* Data Editor */
    div[data-testid="stDataEditor"] {
        border-radius: 15px;
        overflow: hidden;
        box-shadow: 0 8px 24px rgba(0,0,0,0.1);
    }
    
    div[data-testid="stDataEditor"] table {
        font-size: 0.95rem;
    }
    
    div[data-testid="stDataEditor"] th {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        font-weight: 600;
        padding: 1rem !important;
    }
    
    div[data-testid="stDataEditor"] td {
        padding: 0.75rem !important;
    }
    
    /* Section Headers */
    .section-header {
        font-size: 1.5rem;
        font-weight: 600;
        color: #2d3748;
        margin: 2rem 0 1rem 0;
        padding-bottom: 0.5rem;
        border-bottom: 3px solid #667eea;
        display: inline-block;
    }
    
    /* Status Badges */
    .status-badge {
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        display: inline-block;
    }
    
    .status-paid {
        background: #48bb78;
        color: white;
    }
    
    .status-unpaid {
        background: #f56565;
        color: white;
    }
    
    .status-bought {
        background: #4299e1;
        color: white;
    }
    
    /* Alert Boxes */
    .stAlert {
        border-radius: 12px;
        border: none;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    
    /* Progress Bar */
    .progress-container {
        background: #e2e8f0;
        border-radius: 10px;
        height: 30px;
        margin: 1rem 0;
        overflow: hidden;
        box-shadow: inset 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .progress-bar {
        height: 100%;
        background: linear-gradient(90deg, #48bb78 0%, #38a169 100%);
        border-radius: 10px;
        transition: width 0.5s ease;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-weight: 600;
    }
    
    /* Tab Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: transparent;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: white;
        border-radius: 10px 10px 0 0;
        padding: 1rem 2rem;
        font-weight: 600;
        border: none;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
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

@st.cache_data(ttl=5)
def load_data_from_sheet():
    try:
        gc = init_gsheet_connection()
        if gc is None: return None
        
        spreadsheet = gc.open_by_key(SPREADSHEET_ID)
        worksheet = spreadsheet.worksheet(WORKSHEET_NAME)
        
        data = worksheet.get_all_values()
        
        expected_cols = ['Nama Barang', 'Qty', 'Harga Input', 'Total Akhir', 'Tipe', 'Status Bayar', 'Status Beli']
        
        if len(data) <= 1:
            return pd.DataFrame(columns=expected_cols)
        
        df = pd.DataFrame(data[1:], columns=data[0])
        
        for col in expected_cols:
            if col not in df.columns:
                df[col] = "FALSE"
        
        df['Qty'] = pd.to_numeric(df['Qty'], errors='coerce').fillna(0).astype(int)
        df['Harga Input'] = pd.to_numeric(df['Harga Input'], errors='coerce').fillna(0).astype(int)
        df['Total Akhir'] = pd.to_numeric(df['Total Akhir'], errors='coerce').fillna(0).astype(int)
        
        df['Status Bayar'] = df['Status Bayar'].apply(lambda x: True if str(x).upper() == 'TRUE' else False)
        df['Status Beli'] = df['Status Beli'].apply(lambda x: True if str(x).upper() == 'TRUE' else False)
        
        return df[expected_cols]
    
    except Exception as e:
        st.error(f"❌ Gagal load data: {str(e)}")
        return None

def append_to_sheet(nama, qty, harga, total, tipe, lunas, terbeli):
    try:
        gc = init_gsheet_connection()
        if gc is None: return False
        
        spreadsheet = gc.open_by_key(SPREADSHEET_ID)
        worksheet = spreadsheet.worksheet(WORKSHEET_NAME)
        
        str_lunas = "TRUE" if lunas else "FALSE"
        str_terbeli = "TRUE" if terbeli else "FALSE"
        
        new_row = [nama, int(qty), int(harga), int(total), tipe, str_lunas, str_terbeli]
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
        df_upload['Status Bayar'] = df_upload['Status Bayar'].apply(lambda x: "TRUE" if x else "FALSE")
        df_upload['Status Beli'] = df_upload['Status Beli'].apply(lambda x: "TRUE" if x else "FALSE")
        
        worksheet.clear()
        set_with_dataframe(worksheet, df_upload)
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"❌ Gagal update: {str(e)}")
        return False

# --- UI HEADER ---
st.markdown('''
<div class="main-header">
    <h1 class="main-title">🌴 Bali Trip Budget Planner</h1>
    <p class="main-subtitle">Kelola Budget Liburan Bali dengan Mudah & Profesional</p>
</div>
''', unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("## 📝 Tambah Item Baru")
    st.markdown("---")
    
    with st.form("form_add", clear_on_submit=True):
        nama = st.text_input("🏷️ Nama Item", placeholder="Contoh: Sewa Motor, Hotel, Tiket Masuk")
        
        col_s1, col_s2 = st.columns(2)
        with col_s1: 
            qty = st.number_input("🔢 Jumlah", min_value=1, value=1)
        with col_s2: 
            harga = st.number_input("💵 Harga (Rp)", min_value=0, step=10000, format="%d")
        
        tipe = st.radio("📊 Tipe Perhitungan", 
                       ["Satuan (x Qty)", "Borongan (Total)"],
                       help="Satuan: Harga dikali jumlah | Borongan: Harga total langsung")
        
        st.markdown("---")
        st.markdown("**✅ Status Item:**")
        
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            lunas = st.checkbox("💸 Lunas", value=False, help="Uang sudah keluar")
        with col_c2:
            terbeli = st.checkbox("📦 Aman", value=False, help="Sudah dibooking/dibeli")
        
        btn_add = st.form_submit_button("➕ Tambah Item", use_container_width=True)

    if btn_add:
        if not nama:
            st.warning("⚠️ Nama item wajib diisi!")
        else:
            total = (harga * qty) if tipe == "Satuan (x Qty)" else harga
            tipe_str = "Satuan" if tipe == "Satuan (x Qty)" else "Borongan"
            
            if append_to_sheet(nama, qty, harga, total, tipe_str, lunas, terbeli):
                st.success(f"✅ {nama} berhasil ditambahkan!")
                st.balloons()
                st.rerun()
    
    st.markdown("---")
    st.markdown("### 🔄 Data Management")
    if st.button("🔄 Refresh Data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# --- MAIN CONTENT ---
df = load_data_from_sheet()

if df is not None:
    # PERHITUNGAN STATISTIK
    if not df.empty:
        total_rencana = df['Total Akhir'].sum()
        uang_keluar = df[df['Status Bayar'] == True]['Total Akhir'].sum()
        sisa_bayar = df[df['Status Bayar'] == False]['Total Akhir'].sum()
        item_terbeli = df['Status Beli'].sum()
        total_item = len(df)
        
        persen_bayar = (uang_keluar/total_rencana*100) if total_rencana > 0 else 0
        persen_beli = (item_terbeli/total_item*100) if total_item > 0 else 0
    else:
        total_rencana = uang_keluar = sisa_bayar = 0
        item_terbeli = total_item = 0
        persen_bayar = persen_beli = 0

    # DASHBOARD METRICS
    st.markdown('<p class="section-header">📊 Dashboard Ringkasan</p>', unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="💰 Total Budget",
            value=f"Rp {total_rencana:,.0f}",
            delta=f"{total_item} items"
        )
    
    with col2:
        st.metric(
            label="💸 Sudah Dibayar",
            value=f"Rp {uang_keluar:,.0f}",
            delta=f"{persen_bayar:.1f}% Lunas"
        )
    
    with col3:
        st.metric(
            label="⏳ Belum Dibayar",
            value=f"Rp {sisa_bayar:,.0f}",
            delta=f"{100-persen_bayar:.1f}% Tersisa",
            delta_color="inverse"
        )
    
    with col4:
        st.metric(
            label="📦 Item Terbeli",
            value=f"{item_terbeli} / {total_item}",
            delta=f"{persen_beli:.0f}% Complete"
        )
    
    # PROGRESS BAR
    st.markdown("### 📈 Progress Pembayaran")
    st.markdown(f'''
    <div class="progress-container">
        <div class="progress-bar" style="width: {persen_bayar}%;">
            {persen_bayar:.1f}% Terbayar
        </div>
    </div>
    ''', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # TABS untuk Visualisasi dan Data
    tab1, tab2, tab3 = st.tabs(["📋 Data Budget", "📊 Visualisasi", "📈 Analisis"])
    
    with tab1:
        st.markdown('<p class="section-header">📋 Rincian Budget Detail</p>', unsafe_allow_html=True)
        
        if not df.empty:
            # Filter Options
            col_f1, col_f2, col_f3 = st.columns(3)
            with col_f1:
                filter_status = st.selectbox("Filter Status Bayar", ["Semua", "Sudah Lunas", "Belum Lunas"])
            with col_f2:
                filter_beli = st.selectbox("Filter Status Beli", ["Semua", "Sudah Dibeli", "Belum Dibeli"])
            with col_f3:
                filter_tipe = st.selectbox("Filter Tipe", ["Semua", "Satuan", "Borongan"])
            
            # Apply Filters
            df_filtered = df.copy()
            if filter_status == "Sudah Lunas":
                df_filtered = df_filtered[df_filtered['Status Bayar'] == True]
            elif filter_status == "Belum Lunas":
                df_filtered = df_filtered[df_filtered['Status Bayar'] == False]
                
            if filter_beli == "Sudah Dibeli":
                df_filtered = df_filtered[df_filtered['Status Beli'] == True]
            elif filter_beli == "Belum Dibeli":
                df_filtered = df_filtered[df_filtered['Status Beli'] == False]
                
            if filter_tipe != "Semua":
                df_filtered = df_filtered[df_filtered['Tipe'] == filter_tipe]
            
            st.info(f"📊 Menampilkan {len(df_filtered)} dari {len(df)} item")
            
            edited_df = st.data_editor(
                df_filtered,
                column_config={
                    "Nama Barang": st.column_config.TextColumn(
                        "🏷️ Nama Item",
                        width="large",
                        help="Nama barang/jasa yang akan dibeli"
                    ),
                    "Qty": st.column_config.NumberColumn(
                        "🔢 Qty",
                        width="small",
                        help="Jumlah item"
                    ),
                    "Harga Input": st.column_config.NumberColumn(
                        "💵 Harga",
                        format="Rp %d",
                        help="Harga per item atau harga total"
                    ),
                    "Total Akhir": st.column_config.NumberColumn(
                        "💰 Total",
                        format="Rp %d",
                        disabled=True,
                        help="Total biaya (otomatis)"
                    ),
                    "Tipe": st.column_config.SelectboxColumn(
                        "📊 Tipe",
                        options=["Satuan", "Borongan"],
                        help="Satuan: dikalikan Qty | Borongan: langsung total"
                    ),
                    "Status Bayar": st.column_config.CheckboxColumn(
                        "💸 Lunas?",
                        help="✅ = Uang sudah keluar",
                        default=False
                    ),
                    "Status Beli": st.column_config.CheckboxColumn(
                        "📦 Aman?",
                        help="✅ = Sudah dibooking/dibeli",
                        default=False
                    )
                },
                hide_index=True,
                use_container_width=True,
                num_rows="dynamic",
                key="editor_utama"
            )
            
            # Save Button
            col_save1, col_save2, col_save3 = st.columns([2, 1, 2])
            with col_save2:
                if st.button("💾 Simpan Semua Perubahan", type="primary", use_container_width=True):
                    # Recalculate totals
                    for idx, row in edited_df.iterrows():
                        if row['Tipe'] == 'Satuan':
                            edited_df.at[idx, 'Total Akhir'] = row['Harga Input'] * row['Qty']
                        else:
                            edited_df.at[idx, 'Total Akhir'] = row['Harga Input']
                    
                    if update_sheet_data(edited_df):
                        st.success("✅ Data berhasil disimpan ke Google Sheets!")
                        st.balloons()
                        st.rerun()
        else:
            st.info("📝 Belum ada data. Silakan tambahkan item melalui sidebar!")
    
    with tab2:
        st.markdown('<p class="section-header">📊 Visualisasi Budget</p>', unsafe_allow_html=True)
        
        if not df.empty:
            col_v1, col_v2 = st.columns(2)
            
            with col_v1:
                # Pie Chart - Status Pembayaran
                st.markdown("#### 💸 Breakdown Pembayaran")
                fig_payment = go.Figure(data=[go.Pie(
                    labels=['Sudah Dibayar', 'Belum Dibayar'],
                    values=[uang_keluar, sisa_bayar],
                    hole=.4,
                    marker_colors=['#48bb78', '#f56565']
                )])
                fig_payment.update_layout(
                    showlegend=True,
                    height=350,
                    margin=dict(t=0, b=0, l=0, r=0)
                )
                st.plotly_chart(fig_payment, use_container_width=True)
            
            with col_v2:
                # Pie Chart - Status Pembelian
                st.markdown("#### 📦 Status Pembelian")
                item_belum = total_item - item_terbeli
                fig_purchase = go.Figure(data=[go.Pie(
                    labels=['Sudah Dibeli', 'Belum Dibeli'],
                    values=[item_terbeli, item_belum],
                    hole=.4,
                    marker_colors=['#4299e1', '#ed8936']
                )])
                fig_purchase.update_layout(
                    showlegend=True,
                    height=350,
                    margin=dict(t=0, b=0, l=0, r=0)
                )
                st.plotly_chart(fig_purchase, use_container_width=True)
            
            # Bar Chart - Top 10 Pengeluaran
            st.markdown("#### 💰 Top 10 Pengeluaran Terbesar")
            df_top = df.nlargest(10, 'Total Akhir')
            fig_bar = px.bar(
                df_top,
                x='Total Akhir',
                y='Nama Barang',
                orientation='h',
                color='Status Bayar',
                color_discrete_map={True: '#48bb78', False: '#f56565'},
                labels={'Total Akhir': 'Total (Rp)', 'Nama Barang': 'Item'}
            )
            fig_bar.update_layout(height=400, showlegend=True)
            st.plotly_chart(fig_bar, use_container_width=True)
            
        else:
            st.info("📊 Visualisasi akan muncul setelah ada data")
    
    with tab3:
        st.markdown('<p class="section-header">📈 Analisis Budget</p>', unsafe_allow_html=True)
        
        if not df.empty:
            col_a1, col_a2 = st.columns(2)
            
            with col_a1:
                st.markdown("#### 💡 Insights")
                st.markdown(f"""
                - **Rata-rata per item**: Rp {(total_rencana/total_item):,.0f}
                - **Item termahal**: {df.loc[df['Total Akhir'].idxmax(), 'Nama Barang']} 
                  (Rp {df['Total Akhir'].max():,.0f})
                - **Item termurah**: {df.loc[df['Total Akhir'].idxmin(), 'Nama Barang']} 
                  (Rp {df['Total Akhir'].min():,.0f})
                - **Progress pembayaran**: {persen_bayar:.1f}%
                - **Progress pembelian**: {persen_beli:.1f}%
                """)
            
            with col_a2:
                st.markdown("#### 🎯 Rekomendasi")
                recommendations = []
                
                if persen_bayar < 50:
                    recommendations.append("⚠️ Kurang dari 50% budget terbayar. Segera lunasi!")
                if persen_beli < 50:
                    recommendations.append("📦 Kurang dari 50% item terbeli. Segera booking!")
                if sisa_bayar > uang_keluar:
                    recommendations.append("💸 Sisa pembayaran lebih besar dari yang sudah dibayar")
                if persen_bayar >= 80:
                    recommendations.append("✅ Pembayaran hampir selesai! Tinggal sedikit lagi!")
                if persen_beli >= 80:
                    recommendations.append("🎉 Pembelian hampir lengkap! Good job!")
                
                if recommendations:
                    for rec in recommendations:
                        st.markdown(f"- {rec}")
                else:
                    st.success("✨ Semua terlihat baik! Keep it up!")
        else:
            st.info("📈 Analisis akan muncul setelah ada data")

else:
    st.error("❌ Tidak dapat memuat data dari Google Sheets")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #718096; padding: 2rem 0;'>
    <p>🌴 <strong>Bali Trip Budget Planner</strong> | Made with ❤️ using Streamlit</p>
    <p style='font-size: 0.85rem;'>© 2026 | Data tersimpan aman di Google Sheets</p>
</div>
""", unsafe_allow_html=True)
