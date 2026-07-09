"""
Konfigurasi Global Aplikasi DMS
"""
import streamlit as st
import os

# --- DATABASE ---
DB_NAME = "dokumen_app.db"
UPLOAD_FOLDER = "uploaded_files"

# --- DAFTAR DEPARTEMEN ---
DEPARTMENTS = [
    "Keuangan",
    "HRD",
    "IT",
    "Operasional",
    "Marketing",
    "Produksi",
    "Logistik"
]

# --- KONFIGURASI EMAIL ---
def get_email_config():
    """Ambil konfigurasi email dari Streamlit Secrets atau Environment"""
    try:
        return {
            "SMTP_SERVER": st.secrets["SMTP_SERVER"],
            "SMTP_PORT": int(st.secrets["SMTP_PORT"]),
            "SENDER_EMAIL": st.secrets["SENDER_EMAIL"],
            "SENDER_PASSWORD": st.secrets["SENDER_PASSWORD"],
            "APP_NAME": st.secrets.get("APP_NAME", "DMS Perusahaan")
        }
    except Exception:
        # Fallback untuk testing lokal
        return {
            "SMTP_SERVER": os.getenv("SMTP_SERVER", "smtp.gmail.com"),
            "SMTP_PORT": int(os.getenv("SMTP_PORT", 587)),
            "SENDER_EMAIL": os.getenv("SENDER_EMAIL", ""),
            "SENDER_PASSWORD": os.getenv("SENDER_PASSWORD", ""),
            "APP_NAME": os.getenv("APP_NAME", "DMS Perusahaan")
        }

# --- INISIALISASI FOLDER ---
def init_folders():
    """Buat folder yang dibutuhkan jika belum ada"""
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)