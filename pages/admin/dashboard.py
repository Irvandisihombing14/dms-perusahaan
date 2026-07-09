"""
Admin Dashboard
"""
import streamlit as st
import pandas as pd
from datetime import datetime
import os

from database import (
    get_all_documents, count_all_documents, get_all_audit_logs,
    count_all_audit_logs, get_all_departments, get_all_users,
    get_documents_by_status, get_document_by_id, get_all_categories
)
from utils import format_file_size, format_date, get_status_badge
from config import STATUS_PENDING, STATUS_APPROVED, STATUS_REJECTED, STATUS_DRAFT, ITEMS_PER_PAGE


def render(user):
    """Render dashboard admin"""
    st.title("📊 Dashboard Admin")
    st.markdown("### Ringkasan Sistem DMS Administrasi PNS")

    # Metrics
    total_docs = count_all_documents()
    total_users = len(get_all_users())
    total_depts = len(get_all_departments())
    total_logs = count_all_audit_logs()
    pending_docs = len(get_documents_by_status(STATUS_PENDING))

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("📄 Total Dokumen", total_docs)
    with col2:
        st.metric("👥 Total User", total_users)
    with col3:
        st.metric("🏢 Total Bidang", total_depts)
    with col4:
        st.metric("⏳ Pending Approval", pending_docs)
    with col5:
        st.metric("📝 Total Aktivitas", total_logs)

    st.markdown("---")

    # Status breakdown
    st.subheader("📈 Status Dokumen")
    draft_count = len(get_documents_by_status(STATUS_DRAFT))
    approved_count = len(get_documents_by_status(STATUS_APPROVED))
    rejected_count = len(get_documents_by_status(STATUS_REJECTED))

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📝 Draft", draft_count)
    with col2:
        st.metric("⏳ Pending", pending_docs)
    with col3:
        st.metric("✅ Approved", approved_count)
    with col4:
        st.metric("❌ Rejected", rejected_count)

    st.markdown("---")

    # Aktivitas terbaru
    st.subheader("📈 Aktivitas Terbaru")
    recent_logs = get_all_audit_logs(limit=10)

    if recent_logs:
        log_df = pd.DataFrame(recent_logs, columns=[
            'ID', 'Aksi', 'Doc ID', 'Judul', 'Email', 'Nama', 'Role',
            'Tanggal', 'Detail', 'Dept ID', 'IP', 'Dept Name'
        ])
        display_log = log_df[['Aksi', 'Judul', 'Nama', 'Dept Name', 'Tanggal', 'Detail']]
        display_log['Tanggal'] = display_log['Tanggal'].apply(format_date)
        st.dataframe(display_log, use_container_width=True, hide_index=True)
    else:
        st.info("Belum ada aktivitas.")


def render_all_docs(user):
    """Render semua dokumen"""
    st.title("📁 Semua Dokumen")
    st.markdown("### Daftar Seluruh Dokumen dari Semua Bidang")

    # Filter
    col_f1, col_f2, col_f3, col_f4 = st.columns([2, 2, 2, 1])

    with col_f1:
        departments = get_all_departments()
        dept_options = [("Semua", 0)] + [(d[1], d[0]) for d in departments]
        selected_dept = st.selectbox("🏢 Filter Bidang", dept_options,
                                    format_func=lambda x: x[0])

    with col_f2:
        categories = get_all_categories()
        cat_options = [("Semua", 0)] + [(c[1], c[0]) for c in categories]
        selected_cat = st.selectbox("📂 Filter Kategori", cat_options,
                                   format_func=lambda x: x[0])

    with col_f3:
        search_term = st.text_input("🔍 Cari Dokumen")

    with col_f4:
        sort_order = st.radio("⬆️⬇️", ["Terbaru", "Terlama"], horizontal=True)

    # Load data
    all_docs = get_all_documents()

    df = pd.DataFrame(all_docs, columns=[
        'ID', 'Judul', 'Nama File', 'Path', 'Dept ID', 'Cat ID', 'Status',
        'Tags', 'Deskripsi', 'Expiry', 'Email', 'Nama', 'Tanggal', 'Updated',
        'Approved By', 'Approved At', 'Rejection', 'Ukuran', 'Dept Name', 'Cat Name'
    ])

    if not df.empty:
        filtered = df.copy()

        if selected_dept[1] != 0:
            filtered = filtered[filtered['Dept ID'] == selected_dept[1]]
        if selected_cat[1] != 0:
            filtered = filtered[filtered['Cat ID'] == selected_cat[1]]
        if search_term:
            filtered = filtered[
                filtered['Judul'].str.contains(search_term, case=False, na=False) |
                filtered['Nama File'].str.contains(search_term, case=False, na=False) |
                filtered['Tags'].str.contains(search_term, case=False, na=False)
            ]

        filtered = filtered.sort_values('Tanggal', ascending=(sort_order == "Terlama"))

        # Pagination
        total_items = len(filtered)
        total_pages = (total_items + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE

        if total_pages > 1:
            page = st.number_input("Halaman", min_value=1, max_value=total_pages, value=1)
            start_idx = (page - 1) * ITEMS_PER_PAGE
            end_idx = start_idx + ITEMS_PER_PAGE
            filtered = filtered.iloc[start_idx:end_idx]

        # Display
        display_df = filtered[['ID', 'Judul', 'Dept Name', 'Cat Name', 'Status',
                              'Nama', 'Tanggal', 'Ukuran']].copy()
        display_df['Tanggal'] = display_df['Tanggal'].apply(format_date)
        display_df['Ukuran'] = display_df['Ukuran'].apply(format_file_size)
        display_df.columns = ['ID', '📄 Judul', '🏢 Bidang', '📂 Kategori', '📊 Status',
                             '👤 Pengunggah', '📅 Tanggal', '💾 Ukuran']

        st.dataframe(display_df, use_container_width=True, hide_index=True, height=500)

        # Export
        if st.button("📊 Export ke Excel"):
            export_df = filtered[['ID', 'Judul', 'Dept Name', 'Cat Name', 'Status',
                                 'Nama', 'Tanggal', 'Ukuran']].copy()
            export_df.to_excel("export_dokumen.xlsx", index=False)
            with open("export_dokumen.xlsx", "rb") as file:
                st.download_button("📥 Download Excel", data=file,
                                  file_name="dokumen_pns.xlsx",
                                  mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

        # Preview dokumen
        st.markdown("---")
        st.subheader("👀 Preview Dokumen")

        doc_options = {f"{row['ID']} - {row['Judul']}": row['ID']
                      for _, row in filtered.iterrows()}
        if doc_options:
            selected_doc_label = st.selectbox("Pilih Dokumen untuk Preview",
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

                # Preview PDF
                st.markdown("### 📄 Preview PDF")
                with open(doc_info[3], "rb") as file:
                    base64_pdf = st._utils.generate_download_link(
                        file.read(), doc_info[2], "application/pdf"
                    )
                    st.markdown(
                        f'<iframe src="data:application/pdf;base64,{base64_pdf}" '
                        f'width="100%" height="600" type="application/pdf"></iframe>',
                        unsafe_allow_html=True
                    )
    else:
        st.info("Belum ada dokumen.")


def render_approvals(user):
    """Render halaman approval"""
    st.title("⏳ Approval Dokumen")
    st.markdown("### Dokumen yang Menunggu Approval")

    pending_docs = get_documents_by_status(STATUS_PENDING)

    if pending_docs:
        for doc in pending_docs:
            with st.expander(f"📄 {doc[1]} - {doc[18]}"):
                col1, col2 = st.columns([2, 1])

                with col1:
                    st.markdown(f"**Judul:** {doc[1]}")
                    st.markdown(f"**Kategori:** {doc[19]}")
                    st.markdown(f"**Bidang:** {doc[18]}")
                    st.markdown(f"**Pengunggah:** {doc[11]} ({doc[10]})")
                    st.markdown(f"**Tanggal Upload:** {format_date(doc[12])}")
                    if doc[8]:
                        st.markdown(f"**Deskripsi:** {doc[8]}")
                    if doc[7]:
                        st.markdown(f"**Tags:** {doc[7]}")

                with col2:
                    if os.path.exists(doc[3]):
                        with open(doc[3], "rb") as file:
                            st.download_button(
                                "📥 Download PDF",
                                data=file,
                                file_name=doc[2],
                                mime="application/pdf"
                            )

                st.markdown("---")

                col_a1, col_a2 = st.columns(2)
                with col_a1:
                    if st.button(f"✅ Approve - {doc[0]}", key=f"approve_{doc[0]}",
                               type="primary"):
                        approve_document(
                            doc[0],
                            user['email'],
                            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        )
                        st.success("✅ Dokumen di-approve!")
                        st.rerun()

                with col_a2:
                    rejection_reason = st.text_input("Alasan penolakan",
                                                    key=f"reason_{doc[0]}")
                    if st.button(f"❌ Reject - {doc[0]}", key=f"reject_{doc[0]}"):
                        if rejection_reason:
                            reject_document(
                                doc[0],
                                user['email'],
                                rejection_reason,
                                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            )
                            send_approval_notification(
                                doc[10], doc[1], "rejected",
                                user['full_name'], rejection_reason
                            )
                            st.success("❌ Dokumen ditolak!")
                            st.rerun()
                        else:
                            st.warning("⚠️ Alasan penolakan harus diisi!")
    else:
        st.info("✅ Tidak ada dokumen yang menunggu approval.")