"""
Halaman User - Dokumen Saya (dengan Edit, Delete, Submit for Approval)
"""
import streamlit as st
import pandas as pd
import os
from datetime import datetime

from database import (
    get_documents_by_user, get_document_by_id, update_document,
    delete_document_record, create_audit_log, create_notification,
    get_approvers_for_department
)
from email_service import send_approval_notification
from utils import format_file_size, format_date
from config import (
    STATUS_DRAFT, STATUS_PENDING, STATUS_APPROVED, STATUS_REJECTED,
    STATUS_LABELS, STATUS_COLORS, ITEMS_PER_PAGE
)


def render(user):
    """Render halaman dokumen saya"""
    st.title("📄 Dokumen Saya")
    st.markdown("### Kelola Dokumen yang Anda Upload")

    my_docs = get_documents_by_user(user['email'])

    # Filter & Search
    col_f1, col_f2, col_f3 = st.columns([2, 1, 1])
    with col_f1:
        search_term = st.text_input("🔍 Cari Dokumen")
    with col_f2:
        status_filter = st.multiselect(
            "📊 Filter Status",
            options=list(STATUS_LABELS.keys()),
            default=list(STATUS_LABELS.keys()),
            format_func=lambda x: STATUS_LABELS[x]
        )
    with col_f3:
        sort_order = st.radio("⬆️⬇️", ["Terbaru", "Terlama"], horizontal=True)

    if my_docs:
        df = pd.DataFrame(my_docs, columns=[
            'ID', 'Judul', 'Nama File', 'Path', 'Dept ID', 'Cat ID', 'Status',
            'Tags', 'Deskripsi', 'Expiry', 'Email', 'Nama', 'Tanggal', 'Updated',
            'Approved By', 'Approved At', 'Rejection', 'Ukuran', 'Dept Name', 'Cat Name'
        ])

        filtered = df.copy()
        if search_term:
            filtered = filtered[
                filtered['Judul'].str.contains(search_term, case=False, na=False) |
                filtered['Nama File'].str.contains(search_term, case=False, na=False) |
                filtered['Tags'].str.contains(search_term, case=False, na=False)
            ]
        if status_filter:
            filtered = filtered[filtered['Status'].isin(status_filter)]

        filtered = filtered.sort_values('Tanggal', ascending=(sort_order == "Terlama"))

        if not filtered.empty:
            # Info
            st.info(f"📊 Menampilkan **{len(filtered)}** dokumen")

            # Pagination
            total_items = len(filtered)
            total_pages = max(1, (total_items + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE)

            if total_pages > 1:
                page = st.number_input("Halaman", min_value=1, max_value=total_pages, value=1)
                start_idx = (page - 1) * ITEMS_PER_PAGE
                end_idx = start_idx + ITEMS_PER_PAGE
                filtered = filtered.iloc[start_idx:end_idx]

            # Tampilkan tabel
            display_df = filtered[['ID', 'Judul', 'Cat Name', 'Status', 'Tanggal',
                                  'Ukuran', 'Tags']].copy()
            display_df['Tanggal'] = display_df['Tanggal'].apply(format_date)
            display_df['Ukuran'] = display_df['Ukuran'].apply(format_file_size)
            display_df.columns = ['ID', '📄 Judul', '📂 Kategori', '📊 Status',
                                 '📅 Tanggal', '💾 Ukuran', '🏷️ Tags']

            st.dataframe(display_df, use_container_width=True, hide_index=True, height=350)

            st.markdown("---")
            st.subheader("⚙️ Kelola Dokumen")

            # Pilih dokumen
            doc_options = {f"{row['ID']} - {row['Judul']} [{STATUS_LABELS.get(row['Status'], row['Status'])}]": row['ID']
                          for _, row in filtered.iterrows()}
            selected_doc_label = st.selectbox("Pilih Dokumen", options=list(doc_options.keys()))
            selected_doc_id = doc_options[selected_doc_label]

            doc_info = get_document_by_id(selected_doc_id)

            if doc_info:
                # Info dokumen
                st.markdown(f"""
                **Judul:** {doc_info[1]}  
                **Kategori:** {doc_info[19]}  
                **Status:** {STATUS_LABELS.get(doc_info[6], doc_info[6])}  
                **Tanggal Upload:** {format_date(doc_info[12])}  
                **Ukuran:** {format_file_size(doc_info[17])}
                """)

                if doc_info[16]:  # rejection_reason
                    st.error(f"❌ **Alasan Penolakan:** {doc_info[16]}")

                st.markdown("---")

                # Aksi berdasarkan status
                col1, col2, col3 = st.columns(3)

                with col1:
                    # EDIT (hanya untuk draft atau rejected)
                    if doc_info[6] in [STATUS_DRAFT, STATUS_REJECTED]:
                        st.markdown("**✏️ Edit Judul**")
                        new_title = st.text_input("Judul Baru", value=doc_info[1],
                                                 key=f"edit_title_{doc_info[0]}")
                        if st.button("💾 Simpan Perubahan", type="primary",
                                   use_container_width=True, key=f"save_{doc_info[0]}"):
                            if new_title and new_title != doc_info[1]:
                                update_document(
                                    selected_doc_id,
                                    title=new_title,
                                    updated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                )
                                create_audit_log(
                                    action="UPDATE",
                                    document_id=selected_doc_id,
                                    document_title=new_title,
                                    user_email=user['email'],
                                    user_name=user['full_name'],
                                    user_role=user['role'],
                                    action_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                    details=f"Edit judul: '{doc_info[1]}' → '{new_title}'",
                                    department_id=user['department_id']
                                )
                                st.success("✅ Judul berhasil diubah!")
                                st.rerun()
                            else:
                                st.warning("⚠️ Judul tidak berubah.")
                    else:
                        st.info("ℹ️ Edit hanya tersedia untuk dokumen Draft/Rejected")

                with col2:
                    # SUBMIT FOR APPROVAL (hanya untuk draft/rejected)
                    if doc_info[6] in [STATUS_DRAFT, STATUS_REJECTED]:
                        st.markdown("**📤 Submit untuk Approval**")
                        if st.button("📤 Submit ke Kepala Bidang", type="secondary",
                                   use_container_width=True, key=f"submit_{doc_info[0]}"):
                            update_document(
                                selected_doc_id,
                                status=STATUS_PENDING,
                                updated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            )

                            # Notifikasi ke Kepala Bidang
                            approvers = get_approvers_for_department(user['department_id'])
                            for approver in approvers:
                                create_notification(
                                    user_email=approver[1],
                                    title="📋 Dokumen Perlu Approval",
                                    message=f"{user['full_name']} mensubmit dokumen '{doc_info[1]}' untuk approval Anda.",
                                    link=f"?doc_id={doc_info[0]}"
                                )

                            create_audit_log(
                                action="UPDATE",
                                document_id=selected_doc_id,
                                document_title=doc_info[1],
                                user_email=user['email'],
                                user_name=user['full_name'],
                                user_role=user['role'],
                                action_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                details="Submit untuk approval",
                                department_id=user['department_id']
                            )

                            st.success("✅ Dokumen disubmit untuk approval!")
                            st.rerun()
                    elif doc_info[6] == STATUS_PENDING:
                        st.info("⏳ Menunggu approval Kepala Bidang")
                    elif doc_info[6] == STATUS_APPROVED:
                        st.success(f"✅ Disetujui pada {format_date(doc_info[15])}")

                with col3:
                    # DOWNLOAD
                    st.markdown("**📥 Download**")
                    if os.path.exists(doc_info[3]):
                        with open(doc_info[3], "rb") as file:
                            st.download_button(
                                label="📥 Download PDF",
                                data=file.read(),
                                file_name=doc_info[2],
                                mime="application/pdf",
                                type="primary",
                                use_container_width=True,
                                key=f"download_{doc_info[0]}"
                            )
                    else:
                        st.error("❌ File tidak ditemukan!")

                st.markdown("---")

                # DELETE
                if doc_info[6] in [STATUS_DRAFT, STATUS_REJECTED]:
                    st.markdown("**🗑️ Hapus Dokumen**")
                    confirm_delete = st.checkbox("⚠️ Saya yakin ingin menghapus dokumen ini",
                                                key=f"confirm_del_{doc_info[0]}")
                    if st.button("🗑️ Hapus Dokumen", type="secondary",
                               disabled=not confirm_delete, key=f"delete_{doc_info[0]}"):
                        # Hapus file fisik
                        if os.path.exists(doc_info[3]):
                            os.remove(doc_info[3])

                        # Hapus dari database
                        delete_document_record(selected_doc_id)

                        create_audit_log(
                            action="DELETE",
                            document_id=selected_doc_id,
                            document_title=doc_info[1],
                            user_email=user['email'],
                            user_name=user['full_name'],
                            user_role=user['role'],
                            action_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            details=f"Hapus file: {doc_info[2]}",
                            department_id=user['department_id']
                        )

                        st.success("✅ Dokumen berhasil dihapus!")
                        st.rerun()
                else:
                    st.info("ℹ️ Hapus hanya tersedia untuk dokumen Draft/Rejected")
        else:
            st.info("Tidak ada dokumen yang sesuai dengan filter.")
    else:
        st.info("📭 Anda belum upload dokumen. Gunakan form di sidebar untuk upload!")