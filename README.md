# 🏛️ DMS Administrasi PNS

Sistem Manajemen Dokumen Administrasi Pegawai Negeri Sipil dengan fitur lengkap.

## ✨ Fitur

### 👑 Admin
- 📊 Dashboard statistik sistem
- 📁 Lihat semua dokumen dari semua bidang
- ⏳ Approval dokumen
- 👥 Manajemen User (CRUD, reset password)
- 🏢 Manajemen Bidang
- 📂 Manajemen Kategori Dokumen
- 📜 Audit Log lengkap
- 📊 Export ke Excel

### ⭐ Kepala Bidang
- 📊 Dashboard bidang
- 📁 Lihat semua dokumen bidang
- ⏳ Approval dokumen dari anggota
- 📄 Kelola dokumen pribadi

### 👤 PNS
- 📊 Dashboard pribadi
- 📄 Kelola dokumen (edit, hapus, submit approval)
- 🔔 Notifikasi real-time
- 📤 Upload PDF dengan kategori & tag

### 🌟 Fitur Umum
- 🔐 Login/Register berbasis email + NIP
- 📤 Upload PDF dengan kategori & tag
- ✅ Approval Workflow (Draft → Pending → Approved/Rejected)
- 🔍 Pencarian & filter
- 📧 Kirim PDF otomatis ke email
- 📝 Audit trail untuk semua aktivitas
- 📅 Expiry date
- 🔔 Notifikasi in-app

## 🚀 Deploy

### Step 1: Push ke GitHub
```bash
git init
git add .
git commit -m "Initial commit: DMS Administrasi PNS"
git branch -M main
git remote add origin https://github.com/Irvandisihombing14/dms-perusahaan.git
git push -u origin main
```

### Step 2: Deploy ke Streamlit Cloud
1. Buka https://share.streamlit.io/
2. Login dengan GitHub
3. Klik **New App**
4. Isi:
   - Repository: `Irvandisihombing14/dms-perusahaan`
   - Branch: `main`
   - Main file path: `app.py`
5. Klik **Deploy**

### Step 3: Tambahkan Secrets
Di Settings → Secrets:
```toml
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "email_anda@gmail.com"
SENDER_PASSWORD = "app_password_16_digit"
APP_NAME = "DMS Administrasi PNS"
```

## 👑 Membuat Admin Pertama

Setelah deploy, jalankan script ini sekali:
```python
from database import get_connection
conn = get_connection()
conn.execute("UPDATE users SET role = 'admin' WHERE email = 'email_anda@gmail.com'")
conn.commit()
conn.close()
```

## 📝 Lisensi
MIT License