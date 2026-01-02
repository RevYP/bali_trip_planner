# 🌴 Bali Trip Budget Planner - Web App

Aplikasi Streamlit untuk merencanakan dan mengelola budget perjalanan ke Bali dengan sinkronisasi real-time ke Google Sheets.

## 📋 Spesifikasi

- **Frontend:** Streamlit (Web UI)
- **Backend:** Python
- **Database:** Google Sheets (Real-time Sync)
- **Fitur:** Input item, kalkulasi otomatis, grand total, export CSV/Excel

## 🚀 Instalasi & Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Setup Google Sheets API

#### Langkah A: Buat Google Cloud Project
1. Buka [Google Cloud Console](https://console.cloud.google.com/)
2. Buat project baru atau gunakan project yang sudah ada
3. Catat **Project ID**

#### Langkah B: Buat Service Account
1. Di sidebar, pilih **APIs & Services** → **Credentials**
2. Klik **Create Credentials** → **Service Account**
3. Isi nama service account, lalu **Create and Continue**
4. Di tab **Keys**, klik **Add Key** → **Create new key** → **JSON**
5. File JSON akan otomatis download - **Simpan dengan baik!**

#### Langkah C: Share Google Sheet dengan Service Account
1. Buka Google Sheet: `https://docs.google.com/spreadsheets/d/1TQAOaIcGsW9SiXySWXhpsABHkMsrPe1yf9x9a9FIZys/`
2. Klik **Share**
3. Copy **client_email** dari file JSON yang didownload (format: `xxx@xxx.iam.gserviceaccount.com`)
4. Paste email tersebut di bagian share
5. Pilih **Editor** → **Share**

#### Langkah D: Update `secrets.toml`
1. Buka file JSON yang didownload tadi
2. Copy seluruh isi JSON
3. Update file `.streamlit/secrets.toml` dengan isi JSON tersebut
4. Struktur harus seperti:
```toml
[gcp_service_account]
type = "service_account"
project_id = "..."
private_key_id = "..."
private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
client_email = "..."
client_id = "..."
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "..."
```

### 3. Pastikan Google Sheet Format Benar

Header di baris 1 harus:
```
Nama Barang | Qty | Harga Input | Total Akhir | Tipe
```

### 4. Jalankan Aplikasi

```bash
streamlit run app_gsheet.py
```

Aplikasi akan membuka di `http://localhost:8501`

## 📱 Fitur Aplikasi

### Input Item (Sidebar)
- **Nama Barang:** Text input (wajib)
- **Qty:** Number input (default 1)
- **Harga:** Number input (default 0)
- **Tipe Harga:** Radio button
  - "Harga Satuan" → Total = Harga × Qty
  - "Harga Total/Borongan" → Total = Harga (abaikan Qty)
- **Tombol Simpan:** Append ke Google Sheet

### Tampilan Utama
- **Grand Total:** Jumlah seluruh `Total Akhir` (format Rupiah, Rp xxx,xxx)
- **Tabel Data:** Display real-time dari Google Sheet
- **Statistik:** Total item, qty, rata-rata harga
- **Tombol Refresh:** Manual refresh data
- **Export:** Download CSV atau Excel

### Error Handling
- ✅ Validasi input (tidak boleh kosong, harus angka)
- ✅ Try-catch untuk koneksi Google Sheets
- ✅ Pesan error yang informatif
- ✅ Fallback jika secrets tidak ditemukan

## 🔄 Real-time Sync

Data otomatis tersinkronisasi dengan Google Sheet:
- Setiap item baru langsung append ke Sheet
- Refresh data setiap 60 detik (cache)
- Bisa dibuka di beberapa device bersamaan

## 📊 Export Format

### CSV
- Format UTF-8 dengan BOM (bisa dibuka Excel Indonesia)
- Separator: Comma
- Nama file: `Bali_Trip_YYYYMMDD_HHMMSS.csv`

### Excel (.xlsx)
- Header dengan styling (biru, bold, white text)
- Data rows dengan format currency
- Grand total row dengan style khusus
- Nama file: `Bali_Trip_YYYYMMDD_HHMMSS.xlsx`

## 🐛 Troubleshooting

### Error: "Gagal koneksi ke Google Sheets"
- Pastikan `secrets.toml` sudah dikonfigurasi
- Pastikan Service Account sudah di-share ke Google Sheet
- Pastikan private_key di `secrets.toml` tidak terpotong

### Error: "Spreadsheet tidak ditemukan"
- Pastikan Spreadsheet ID benar: `1TQAOaIcGsW9SiXySWXhpsABHkMsrPe1yf9x9a9FIZys`
- Pastikan worksheet name benar: `Sheet1`

### Data tidak muncul
- Klik tombol **Refresh Data**
- Pastikan format Google Sheet benar (header di baris 1)

## 📝 Struktur Folder

```
bali_trip_planner/
├── app_gsheet.py          # Main aplikasi Streamlit
├── requirements.txt       # Dependencies
├── .streamlit/
│   └── secrets.toml      # Google Sheets API credentials
└── README.md             # File ini
```

## 📄 Lisensi

Open source untuk keperluan personal.

---

**Happy Budget Planning! 🌴💰**
