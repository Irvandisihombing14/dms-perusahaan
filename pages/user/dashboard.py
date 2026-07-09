"""
Halaman User - Dashboard
"""
import streamlit as st
import pandas as pd
import os
from datetime import datetime

from database import (
    get_documents_by_user, get_documents_by_department, get_audit_logs_by_user,
    get_all_documents, get_document_by_id, get_documents_by_status,
    count_unread_notifications
)
from utils import format_file_size, format_date
from config import STATUS_PENDING, STATUS_APPROVED, STATUS_DRAFT, STATUS_REJECTED, ITEMS_PER_PAGE


def render(user):
    """Render dashboard user (PNS biasa)"""
    st.title(f"📊 Dashboard - {user['full_name']}")
    st.markdown(f"### Selamat datang di **{user['department_name']}**")

    # Metrics
    my_docs = get_documents_by_user(user['email'])
    my_logs = get_audit_logs_by_user(user['email'])
    unread_notifs = count_unread_notifications(user['email'])

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📄 Dokumen Saya", len(my_docs))
    with col2:
        total_size = sum(doc[17] for doc in my_docs if doc[17]) / (1024 * 1024)
        st.metric("💾 Total Ukuran", f"{total_size:.2f} MB")
    with col3:
        st.metric("📝 Aktivitas Saya", len(my_logs))
    with col4:
        st.metric("🔔 Notifikasi", unread_notifs)

    st.markdown("---")

    # Status breakdown dokumen saya
    st.subheader("📈 Status Dokumen Saya")
    draft_count = len([d for d in my_docs if d[6] == STATUS_DRAFT])
    pending_count = len([d for d in my_docs if d[6] == STATUS_PENDING])
    approved_count = len([d for d in my_docs if d[6] == STATUS_APPROVED])
    rejected_count = len([d for d in my_docs if d[6] == STATUS_REJECTED])

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📝 Draft", draft_count)
    with col2:
        st.metric("⏳ Pending", pending_count)
    with col3:
        st.metric("✅ Approved", approved_count)
    with col4:
        st.metric("❌ Rejected", rejected_count)

    st.markdown("---")

    # Aktivitas terbaru
    st.subheader("📈 Aktivitas Terbaru Saya")
    if my_logs:
        recent_logs = my_logs[:5]
        log_df = pd.DataFrame(recent_logs, columns=[
            'ID', 'Aksi', 'Doc ID', 'Judul', 'Email', 'Nama', 'Role',
            'Tanggal', 'Detail', 'Dept ID', 'IP'
        ])
        display_log = log_df[['Aksi', 'Judul', 'Tanggal', 'Detail']].copy()
        display_log['Tanggal'] = display_log['Tanggal'].apply(format_date)
        st.dataframe(display_log, use_container_width=True, hide_index=True)
    else:
        st.info("Belum ada aktivitas.")

    # Dokumen terbaru
    st.markdown("---")
    st.subheader("📄 Dokumen Terbaru Saya")
    if my_docs:
        recent_docs = my_docs[:5]
        doc_df = pd.DataFrame(recent_docs, columns=[
            'ID', 'Judul', 'Nama File', 'Path', 'Dept ID', 'Cat ID', 'Status',
            'Tags', 'Deskripsi', 'Expiry', 'Email', 'Nama', 'Tanggal', 'Updated',
            'Approved By', 'Approved At', 'Rejection', 'Ukuran', 'Dept Name', 'Cat Name'
        ])
        display_doc = doc_df[['Judul', 'Cat Name', 'Status', 'Tanggal', 'Ukuran']].copy()
        display_doc['Tanggal'] = display_doc['Tanggal'].apply(format_date)
        display_doc['Ukuran'] = display_doc['Ukuran'].apply(format_file_size)
        st.dataframe(display_doc, use_container_width=True, hide_index=True)
    else:
        st.info("Belum ada dokumen. Upload dokumen pertama Anda!")


def render_dept_docs(user):
    """Render dokumen seluruh bidang (untuk Kepala Bidang)"""
    st.title(f"📁 Dokumen Bidang {user['department_name']}")
    st.markdown("### Daftar Dokumen dari Seluruh Anggota Bidang")

    dept_docs = get_documents_by_department(user['department_id'])

    # Filter
    col_f1, col_f2 = st.columns([2, 1])
    with col_f1:
        search_term = st.text_input("🔍 Cari Dokumen")
    with col_f2:
        sort_order = st.radio("⬆️⬇️ Urutan", ["Terbaru", "Terlama"], horizontal=True)

    if dept_docs:
        df = pd.DataFrame(dept_docs, columns=[
            'ID', 'Judul', 'Nama File', 'Path', 'Dept ID', 'Cat ID', 'Status',
            'Tags', 'Deskripsi', 'Expiry', 'Email', 'Nama', 'Tanggal', 'Updated',
            'Approved By', 'Approved At', 'Rejection', 'Ukuran', 'Dept Name', 'Cat Name'
        ])

        filtered = df.copy()
        if search_term:
            filtered = filtered[
                filtered['Judul'].str.contains(search_term, case=False, na=False) |
                filtered['Nama File'].str.contains(search_term, case=False, na=False) |
                filtered['Nama'].str.contains(search_term, case=False, na=False)
            ]

        filtered = filtered.sort_values('Tanggal', ascending=(sort_order == "Terlama"))

        # Pagination
        total_items = len(filtered)
        total_pages = max(1, (total_items + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE)

        if total_pages > 1:
            page = st.number_input("Halaman", min_value=1, max_value=total_pages, value=1)
            start_idx = (page - 1) * ITEMS_PER_PAGE
            end_idx = start_idx + ITEMS_PER_PAGE
            filtered = filtered.iloc[start_idx:end_idx]

        # Display
        display_df = filtered[['ID', 'Judul', 'Cat Name', 'Status', 'Nama',
                              'Tanggal', 'Ukuran']].copy()
        display_df['Tanggal'] = display_df['Tanggal'].apply(format_date)
        display_df['Ukuran'] = display_df['Ukuran'].apply(format_file_size)
        display_df.columns = ['ID', '📄 Judul', '📂 Kategori', '📊 Status',
                             '👤 Pengunggah', '📅 Tanggal', '💾 Ukuran']

        st.dataframe(display_df, use_container_width=True, hide_index=True, height=400)

        # Preview
        st.markdown("---")
        st.subheader("👀 Preview Dokumen")

        doc_options = {f"{row['ID']} - {row['Judul']}": row['ID']
                      for _, row in filtered.iterrows()}
        if doc_options:
            selected_doc_label = st.selectbox("Pilih Dokumen",
                                             options=list(doc_options.keys()))
            doc_id = doc_options[selected_doc_label]
            doc_info = get_document_by_id(doc_id)

            if doc_info and os.path.exists(doc_info[3]):
                with open(doc_info[3], "rb") as file:
                    st.download_button(
                        label=f"📥 Download: {doc_info[2]}",
                        data=file,
                        file_name=doc_info[2],
                        mime="application/pdf"
                    )
    else:
        st.info("Belum ada dokumen di bidang ini.")