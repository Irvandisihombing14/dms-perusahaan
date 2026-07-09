"""
Konfigurasi Global - DMS Administrasi PNS
"""
import streamlit as st
import os

# --- DATABASE ---
DB_NAME = "dms_pns.db"
UPLOAD_FOLDER = "uploaded_files"

# --- ROLE USER (Hierarki) ---
ROLE_ADMIN = "admin"              # Admin sistem
ROLE_KABID = "kepala_bidang"      # Kepala Bidang (approver)
ROLE_PNS = "pns"                  # Pegawai PNS biasa

ROLES = [ROLE_ADMIN, ROLE_KABID, ROLE_PNS]
ROLE_LABELS = {
    ROLE_ADMIN: "👑 Admin",
    ROLE_KABID: "⭐ Kepala Bidang",
    ROLE_PNS: "👤 PNS"
}

# --- KATEGORI DOKUMEN PNS ---
DOCUMENT_CATEGORIES = [
    "SK (Surat Keputusan)",
    "Laporan Kinerja",
    "Surat Cuti",
    "Kenaikan Pangkat",
    "Surat Tugas",
    "Surat Perintah Perjalanan Dinas (SPPD)",
    "Surat Keterangan",
    "Laporan Bulanan",
    "Laporan Tahunan",
    "Surat Undangan",
    "Nota Dinas",
    "Memo",
    "Lainnya"
]

# --- STATUS DOKUMEN (Approval Workflow) ---
STATUS_DRAFT = "draft"
STATUS_PENDING = "pending_approval"
STATUS_APPROVED = "approved"
STATUS_REJECTED = "rejected"

STATUS_LABELS = {
    STATUS_DRAFT: "📝 Draft",
    STATUS_PENDING: "⏳ Menunggu Approval",
    STATUS_APPROVED: "✅ Disetujui",
    STATUS_REJECTED: "❌ Ditolak"
}

STATUS_COLORS = {
    STATUS_DRAFT: "#6c757d",
    STATUS_PENDING: "#ffc107",
    STATUS_APPROVED: "#28a745",
    STATUS_REJECTED: "#dc3545"
}

# --- KONFIGURASI EMAIL ---
def get_email_config():
    """Ambil konfigurasi email dari Streamlit Secrets"""
    try:
        return {
            "SMTP_SERVER": st.secrets["SMTP_SERVER"],
            "SMTP_PORT": int(st.secrets["SMTP_PORT"]),
            "SENDER_EMAIL": st.secrets["SENDER_EMAIL"],
            "SENDER_PASSWORD": st.secrets["SENDER_PASSWORD"],
            "APP_NAME": st.secrets.get("APP_NAME", "DMS Administrasi PNS")
        }
    except Exception:
        return {
            "SMTP_SERVER": os.getenv("SMTP_SERVER", "smtp.gmail.com"),
            "SMTP_PORT": int(os.getenv("SMTP_PORT", 587)),
            "SENDER_EMAIL": os.getenv("SENDER_EMAIL", ""),
            "SENDER_PASSWORD": os.getenv("SENDER_PASSWORD", ""),
            "APP_NAME": os.getenv("APP_NAME", "DMS Administrasi PNS")
        }

def init_folders():
    """Buat folder yang dibutuhkan"""
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)

# --- PAGINATION ---
ITEMS_PER_PAGE = 20