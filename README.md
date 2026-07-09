# 📂 DMS Online - Sistem Manajemen Dokumen

Aplikasi web untuk mengelola dokumen PDF antar departemen dengan fitur lengkap.

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.31-red.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

## ✨ Fitur Utama

- 🔐 **Autentikasi Aman**: Login/Register dengan email + password hashing
- 📤 **Upload PDF**: Upload dan simpan dokumen secara terpusat
- 📧 **Notifikasi Email**: Kirim PDF otomatis ke email penerima
- 🔍 **Pencarian**: Cari dokumen berdasarkan judul atau nama file
- 🏢 **Filter Departemen**: Lihat dokumen per departemen
- ⬆️⬇️ **Sorting**: Urutkan dari terbaru/terlama
- 📥 **Download**: Download PDF langsung dari aplikasi
- 📊 **Dashboard**: Statistik dokumen real-time
- 🌐 **Online**: Bisa diakses dari mana saja

## 🚀 Quick Start

### Instalasi Lokal

```bash
# Clone repository
git clone https://github.com/username/dms-perusahaan.git
cd dms-perusahaan

# Buat virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Setup konfigurasi
cp secrets.toml.example .streamlit/secrets.toml
# Edit .streamlit/secrets.toml dengan data Anda

# Jalankan aplikasi
streamlit run app.py
```

### Deploy ke Streamlit Cloud

1. Push kode ke GitHub
2. Buka [share.streamlit.io](https://share.streamlit.io/)
3. Klik "New App" → pilih repository ini
4. Tambahkan secrets di Settings > Secrets
5. Deploy!

## 📧 Setup Email (Gmail)

1. Aktifkan **2-Step Verification** di akun Google
2. Buka https://myaccount.google.com/apppasswords
3. Buat App Password baru (16 karakter)
4. Gunakan sebagai `SENDER_PASSWORD` di secrets

## 📁 Struktur Proyek

```
dms-perusahaan/
├── app.py              # Entry point aplikasi
├── database.py         # Modul database
├── email_service.py    # Modul pengiriman email
├── auth.py             # Modul autentikasi
├── config.py           # Konfigurasi global
├── requirements.txt    # Dependencies
└── .streamlit/
    └── config.toml     # Konfigurasi Streamlit
```

## 🛠️ Teknologi

- **Python 3.9+**
- **Streamlit** - Framework web app
- **SQLite** - Database
- **SMTP** - Email service
- **Pandas** - Data manipulation

## ⚠️ Catatan Penting tentang Storage

**Streamlit Community Cloud** memiliki storage **sementara (ephemeral)**.
File PDF yang diupload akan hilang jika aplikasi di-restart.

### Solusi untuk Production:

1. **Sewa VPS** (DigitalOcean, Niagahoster, AWS EC2 ~$5/bulan)
2. **Gunakan Cloud Storage** (AWS S3, Google Cloud Storage)

## 📝 Lisensi

MIT License - Bebas digunakan untuk keperluan komersial maupun non-komersial.