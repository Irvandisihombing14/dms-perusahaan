"""
Halaman User - Notifikasi
"""
import streamlit as st
import pandas as pd
from datetime import datetime

from database import (
    get_notifications, mark_notification_read, mark_all_notifications_read,
    count_unread_notifications
)
from utils import format_date


def render(user):
    """Render halaman notifikasi"""
    st.title("🔔 Notifikasi Saya")
    st.markdown("### Pemberitahuan Aktivitas Dokumen")

    # Tombol tandai semua dibaca
    unread_count = count_unread_notifications(user['email'])

    col1, col2 = st.columns([3, 1])
    with col1:
        st.info(f"📊 Anda memiliki **{unread_count}** notifikasi belum dibaca")
    with col2:
        if unread_count > 0:
            if st.button("✅ Tandai Semua Dibaca", use_container_width=True):
                mark_all_notifications_read(user['email'])
                st.success("✅ Semua notifikasi ditandai sudah dibaca!")
                st.rerun()

    st.markdown("---")

    # Daftar notifikasi
    notifications = get_notifications(user['email'])

    if notifications:
        for notif in notifications:
            # notif: (id, user_email, title, message, link, is_read, created_at)
            is_read = notif[5] == 1

            # Styling berdasarkan status
            if is_read:
                bg_color = "#f8f9fa"
                border_color = "#dee2e6"
                icon = "📭"
            else:
                bg_color = "#e7f3ff"
                border_color = "#0d6efd"
                icon = "🔔"

            st.markdown(f"""
            <div style="background: {bg_color}; border-left: 4px solid {border_color};
                        padding: 15px; margin-bottom: 10px; border-radius: 5px;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <h4 style="margin: 0;">{icon} {notif[2]}</h4>
                    <small style="color: #666;">{format_date(notif[6])}</small>
                </div>
                <p style="margin: 10px 0 0 0; color: #333;">{notif[3]}</p>
            </div>
            """, unsafe_allow_html=True)

            # Tombol tandai dibaca
            if not is_read:
                if st.button(f"✅ Tandai Dibaca", key=f"read_{notif[0]}"):
                    mark_notification_read(notif[0])
                    st.rerun()
    else:
        st.info("📭 Belum ada notifikasi.")