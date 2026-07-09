"""
Helper Functions - DMS PNS
"""
import pandas as pd
from datetime import datetime, timedelta
from config import STATUS_LABELS, STATUS_COLORS, ROLE_LABELS


def format_file_size(size_bytes):
    """Format ukuran file"""
    if not size_bytes:
        return "-"
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.2f} MB"


def format_date(date_str):
    """Format tanggal"""
    if not date_str:
        return "-"
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        return dt.strftime("%d/%m/%Y %H:%M")
    except:
        return date_str


def get_status_badge(status):
    """HTML badge untuk status"""
    label = STATUS_LABELS.get(status, status)
    color = STATUS_COLORS.get(status, "#6c757d")
    return f'<span style="background: {color}; color: white; padding: 4px 10px; border-radius: 12px; font-size: 0.8rem; font-weight: bold;">{label}</span>'


def get_role_badge(role):
    """HTML badge untuk role"""
    label = ROLE_LABELS.get(role, role)
    return f'<span style="background: #6366f1; color: white; padding: 4px 10px; border-radius: 12px; font-size: 0.8rem; font-weight: bold;">{label}</span>'


def export_to_excel(df, filename="export.xlsx"):
    """Export DataFrame ke Excel"""
    output = pd.ExcelWriter(filename, engine='xlsxwriter')
    df.to_excel(output, index=False, sheet_name='Data')
    output.close()
    return filename


def get_expiry_status(expiry_date):
    """Cek status expiry dokumen"""
    if not expiry_date:
        return "normal", ""

    try:
        expiry = datetime.strptime(expiry_date, "%Y-%m-%d")
        today = datetime.now()
        days_left = (expiry - today).days

        if days_left < 0:
            return "expired", f"Kadaluarsa {abs(days_left)} hari lalu"
        elif days_left <= 7:
            return "warning", f"Kadaluarsa dalam {days_left} hari"
        elif days_left <= 30:
            return "soon", f"Kadaluarsa dalam {days_left} hari"
        else:
            return "normal", f"Berlaku hingga {expiry.strftime('%d/%m/%Y')}"
    except:
        return "normal", ""


def parse_tags(tags_string):
    """Parse tags dari string"""
    if not tags_string:
        return []
    return [tag.strip() for tag in tags_string.split(',') if tag.strip()]


def tags_to_string(tags_list):
    """Convert list tags ke string"""
    return ",".join(tags_list)