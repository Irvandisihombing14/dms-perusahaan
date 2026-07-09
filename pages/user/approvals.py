"""
Halaman Kepala Bidang - Approval Dokumen
"""
import streamlit as st
import pandas as pd
import os
from datetime import datetime

from database import (
    get_documents_by_status, get_documents_by_department,
    get_document_by_id, approve_document, reject_document,
    create_audit_log, create_notification
)
from email_service import send_approval_notification
from utils import format_file_size, format_date
from config import STATUS_PENDING, STATUS_LABELS, ITEMS_PER_PAGE


def render(user):
    """Render halaman approval untuk Kepala Bidang"""
    st.title("⏳ Approval Dokumen")
    st.markdown(f"### Dokumen dari Bidang **{user['department_name']}** yang Menunggu Approval")

    # Ambil dokumen pending dari bidang ini
    all_pending = get_documents_by_status(STATUS_PENDING)
    dept_pending = [d for d in all_pending if d[4] == user['department_id']]

    if dept_pending:
        st.info(f"📊 Ada **{len(dept_pending)}** dokumen menunggu approval Anda")

        for doc in dept_pending:
            with st.expander(f"📄 {doc[1]} - oleh {doc[11]}", expanded=False):
                col1, col2 = st.columns([2, 1])

                with col1:
                    st.markdown(f"""
                    **Judul:** {doc[1]}  
                    **Kategori:** {doc[19]}  
                    **Pengunggah:** {doc[11]} ({doc[10]})  
                    **Tanggal Upload:** {format_date(doc[12])}  
                    **Ukuran:** {format_file_size(doc[17])}
                    """)

                    if doc[8]:  # description
                        st.markdown(f"**Deskripsi:** {doc[8]}")
                    if doc[7]:  # tags
                        st.markdown(f"**Tags:** {doc[7]}")

                with col2:
                    if os.path.exists(doc[3]):
                        with open(doc[3], "rb") as file:
                            st.download_button(
                                "📥 Download PDF",
                                data=file,
                                file_name=doc[2],
                                mime="application/pdf",
                                use_container_width=True
                            )

                st.markdown("---")

                # Aksi Approval
                col_a1, col_a2 = st.columns(2)

                with col_a1:
                    if st.button(f"✅ Approve", key=f"approve_{doc[0]}",
                               type="primary", use_container_width=True):
                        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        approve_document(doc[0], user['email'], now)

                        create_audit_log(
                            action="APPROVE",
                            document_id=doc[0],
                            document_title=doc[1],
                            user_email=user['email'],
                            user_name=user['full_name'],
                            user_role=user['role'],
                            action_date=now,
                            details=f"Approve dokumen oleh {user['full_name']}",
                            department_id=user['department_id']
                        )

                        # Notifikasi ke pengunggah
                        create_notification(
                            user_email=doc[10],
                            title="✅ Dokumen Disetujui",
                            message=f"Dokumen '{doc[1]}' Anda telah disetujui oleh {user['full_name']}.",
                            link=""
                        )

                        # Kirim email
                        send_approval_notification(
                            doc[10], doc[1], "approved", user['full_name']
                        )

                        st.success("✅ Dokumen berhasil di-approve!")
                        st.rerun()

                with col_a2:
                    rejection_reason = st.text_input(
                        "Alasan penolakan",
                        key=f"reason_{doc[0]}",
                        placeholder="Jelaskan alasan penolakan..."
                    )
                    if st.button(f"❌ Reject", key=f"reject_{doc[0]}",
                               use_container_width=True):
                        if rejection_reason:
                            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            reject_document(doc[0], user['email'], rejection_reason, now)

                            create_audit_log(
                                action="REJECT",
                                document_id=doc[0],
                                document_title=doc[1],
                                user_email=user['email'],
                                user_name=user['full_name'],
                                user_role=user['role'],
                                action_date=now,
                                details=f"Reject: {rejection_reason}",
                                department_id=user['department_id']
                            )

                            # Notifikasi ke pengunggah
                            create_notification(
                                user_email=doc[10],
                                title="❌ Dokumen Ditolak",
                                message=f"Dokumen '{doc[1]}' Anda ditolak. Alasan: {rejection_reason}",
                                link=""
                            )

                            # Kirim email
                            send_approval_notification(
                                doc[10], doc[1], "rejected",
                                user['full_name'], rejection_reason
                            )

                            st.success("❌ Dokumen ditolak!")
                            st.rerun()
                        else:
                            st.warning("⚠️ Alasan penolakan harus diisi!")
    else:
        st.success("✅ Tidak ada dokumen yang menunggu approval Anda. Semua dokumen sudah diproses!")