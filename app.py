"""
Aplikasi Utama - DMS Administrasi PNS (Single File)
Semua fitur: Admin, Kepala Bidang, PNS, Upload, Email, Approval, Audit Log, Notifikasi
"""
import streamlit as st
import pandas as pd
import os
from datetime import datetime

from config import (
    UPLOAD_FOLDER, init_folders, ROLE_ADMIN, ROLE_KABID, ROLE_PNS,
    ROLE_LABELS, STATUS_DRAFT, STATUS_PENDING, STATUS_APPROVED, STATUS_REJECTED,
    STATUS_LABELS, ITEMS_PER_PAGE
)
from database import (
    init_db, create_document, get_all_documents, get_documents_by_department,
    get_documents_by_user, get_document_by_id, update_document, delete_document_record,
    create_audit_log, get_all_audit_logs, get_audit_logs_by_user,
    get_all_departments, get_all_categories, get_category_by_id,
    create_notification, get_notifications, mark_all_notifications_read,
    count_unread_notifications, approve_document, reject_document,
    get_approvers_for_department, create_department, update_department,
    delete_department, create_category, update_category, delete_category,
    create_user, get_all_users, update_user, update_user_password, delete_user,
    count_all_documents, get_documents_by_status, mark_notification_read
)
from auth import register, login, is_admin, is_kepala_bidang, hash_password
from email_service import send_pdf_email, send_approval_notification

init_folders()
init_db()

st.set_page_config(page_title="DMS Administrasi PNS", page_icon="🏛️", layout="wide")

st.markdown("""
<style>
.main-header { font-size: 2.5rem; color: #1e3a8a; text-align: center; margin-bottom: 1rem; }
.sub-header { font-size: 1.2rem; color: #666; text-align: center; margin-bottom: 2rem; }
</style>
""", unsafe_allow_html=True)

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_data = None
    st.session_state.page = "dashboard"


def format_size(size_bytes):
    if not size_bytes:
        return "-"
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.2f} MB"


def format_date(date_str):
    if not date_str:
        return "-"
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        return dt.strftime("%d/%m/%Y %H:%M")
    except Exception:
        return date_str


# ============================================================
# HALAMAN LOGIN / REGISTER
# ============================================================
if not st.session_state.logged_in:
    st.markdown('<h1 class="main-header">🏛️ DMS Administrasi PNS</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Sistem Manajemen Dokumen Administrasi Pegawai Negeri Sipil</p>', unsafe_allow_html=True)

    col_left, col_center, col_right = st.columns([1, 2, 1])
    with col_center:
        tab1, tab2 = st.tabs(["🔐 Login", "📝 Registrasi"])

        with tab1:
            with st.form("login_form"):
                st.subheader("Masuk ke Akun PNS Anda")
                l_email = st.text_input("📧 Email", placeholder="nama@instansi.go.id")
                l_pass = st.text_input("🔑 Password", type="password")
                submit_login = st.form_submit_button("Login", type="primary", use_container_width=True)
                if submit_login:
                    with st.spinner("Memproses login..."):
                        user_data, message = login(l_email, l_pass)
                        if user_data:
                            st.session_state.logged_in = True
                            st.session_state.user_data = user_data
                            st.session_state.page = "dashboard"
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)

        with tab2:
            departments = get_all_departments()
            if not departments:
                st.warning("⚠️ Belum ada departemen. Hubungi admin untuk menambahkan departemen terlebih dahulu.")
            else:
                with st.form("register_form"):
                    st.subheader("Daftar Akun PNS Baru")
                    r_name = st.text_input("👤 Nama Lengkap")
                    r_nip = st.text_input("🆔 NIP (Nomor Induk Pegawai)")
                    r_email = st.text_input("📧 Email Instansi")
                    r_pass = st.text_input("🔑 Password (min. 6 karakter)", type="password")
                    r_dept = st.selectbox("🏢 Bidang/Departemen", [(d[1], d[0]) for d in departments], format_func=lambda x: x[0])
                    submit_register = st.form_submit_button("Daftar", type="primary", use_container_width=True)
                    if submit_register:
                        with st.spinner("Mendaftarkan akun..."):
                            success, message = register(r_email, r_pass, r_name, r_nip, r_dept[1])
                            if success:
                                st.success(f"✅ {message} Silakan Login.")
                            else:
                                st.error(f"❌ {message}")


# ============================================================
# HALAMAN UTAMA (SETELAH LOGIN)
# ============================================================
else:
    user = st.session_state.user_data
    admin_mode = is_admin(user)
    kabid_mode = is_kepala_bidang(user)

    with st.sidebar:
        st.markdown("### 👤 Profil")
        st.success(f"**{user['full_name']}**")
        st.caption(f"📧 {user['email']}")
        st.caption(f"🆔 NIP: {user['nip'] or '-'}")
        st.caption(f"🏢 {user['department_name']}")
        st.markdown(f'{ROLE_LABELS.get(user["role"], user["role"])}')

        unread_count = count_unread_notifications(user['email'])
        if unread_count > 0:
            st.markdown(f"🔔 **{unread_count}** notifikasi baru")

        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.user_data = None
            st.session_state.page = "dashboard"
            st.rerun()

        st.markdown("---")
        st.markdown("### 📋 Menu")

        if admin_mode:
            if st.button("📊 Dashboard Admin", use_container_width=True):
                st.session_state.page = "dashboard"
                st.rerun()
            if st.button("📁 Semua Dokumen", use_container_width=True):
                st.session_state.page = "all_docs"
                st.rerun()
            if st.button("⏳ Approval Pending", use_container_width=True):
                st.session_state.page = "approvals"
                st.rerun()
            if st.button("👥 Manajemen User", use_container_width=True):
                st.session_state.page = "users"
                st.rerun()
            if st.button("🏢 Manajemen Bidang", use_container_width=True):
                st.session_state.page = "departments"
                st.rerun()
            if st.button("📂 Kategori Dokumen", use_container_width=True):
                st.session_state.page = "categories"
                st.rerun()
            if st.button("📜 Audit Log", use_container_width=True):
                st.session_state.page = "audit_log"
                st.rerun()
            if st.button("🔔 Notifikasi", use_container_width=True):
                st.session_state.page = "notifications"
                st.rerun()
        elif kabid_mode:
            if st.button("📊 Dashboard", use_container_width=True):
                st.session_state.page = "dashboard"
                st.rerun()
            if st.button("📁 Dokumen Bidang", use_container_width=True):
                st.session_state.page = "dept_docs"
                st.rerun()
            if st.button("⏳ Approval Pending", use_container_width=True):
                st.session_state.page = "approvals"
                st.rerun()
            if st.button("📄 Dokumen Saya", use_container_width=True):
                st.session_state.page = "my_docs"
                st.rerun()
            if st.button("🔔 Notifikasi", use_container_width=True):
                st.session_state.page = "notifications"
                st.rerun()
        else:
            if st.button("📊 Dashboard Saya", use_container_width=True):
                st.session_state.page = "dashboard"
                st.rerun()
            if st.button("📄 Dokumen Saya", use_container_width=True):
                st.session_state.page = "my_docs"
                st.rerun()
            if st.button("🔔 Notifikasi", use_container_width=True):
                st.session_state.page = "notifications"
                st.rerun()

        st.markdown("---")
        st.markdown("### 📤 Upload Dokumen")

        departments = get_all_departments()
        categories = get_all_categories()

        if not departments or not categories:
            st.warning("⚠️ Hubungi admin untuk setup departemen dan kategori.")
        else:
            with st.form("upload_form", clear_on_submit=True):
                uploaded_file = st.file_uploader("Pilih File PDF", type=['pdf'])
                doc_title = st.text_input("Judul Dokumen", placeholder="Contoh: Laporan Kinerja Triwulan I")
                doc_desc = st.text_area("Deskripsi (Opsional)", height=80)
                doc_category = st.selectbox("Kategori", [(c[1], c[0]) for c in categories], format_func=lambda x: x[0])
                doc_tags = st.text_input("Tag (pisahkan dengan koma)", placeholder="laporan, kinerja, 2026")
                doc_expiry = st.date_input("Tanggal Kadaluarsa (Opsional)", min_value=datetime.now(), value=None)
                send_email = st.checkbox("Kirim notifikasi via email", value=True)
                recipient_email = st.text_input("Email Penerima", value=user['email'] if send_email else "", disabled=not send_email)
                submit_upload = st.form_submit_button("📤 Upload", type="primary", use_container_width=True)

                if submit_upload:
                    if uploaded_file is None:
                        st.error("❌ Pilih file PDF terlebih dahulu!")
                    elif not doc_title:
                        st.error("❌ Judul dokumen harus diisi!")
                    else:
                        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                        safe_filename = f"{timestamp}_{uploaded_file.name}"
                        filepath = os.path.join(UPLOAD_FOLDER, safe_filename)
                        with open(filepath, "wb") as f:
                            f.write(uploaded_file.getbuffer())

                        category_info = get_category_by_id(doc_category[1])
                        status = STATUS_DRAFT
                        if category_info and category_info[3] == 1:
                            status = STATUS_PENDING

                        expiry_date = doc_expiry.strftime("%Y-%m-%d") if doc_expiry else None

                        doc_id = create_document(
                            title=doc_title, original_filename=uploaded_file.name,
                            filepath=filepath, department_id=user['department_id'],
                            category_id=doc_category[1], status=status, tags=doc_tags,
                            description=doc_desc, expiry_date=expiry_date,
                            uploaded_by_email=user['email'], uploaded_by_name=user['full_name'],
                            upload_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            file_size=uploaded_file.size
                        )

                        create_audit_log(
                            action="CREATE", document_id=doc_id, document_title=doc_title,
                            user_email=user['email'], user_name=user['full_name'],
                            user_role=user['role'], action_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            details=f"Upload file: {uploaded_file.name}", department_id=user['department_id']
                        )

                        st.success(f"✅ Dokumen berhasil diupload! (ID: {doc_id})")

                        if status == STATUS_PENDING:
                            approvers = get_approvers_for_department(user['department_id'])
                            for approver in approvers:
                                create_notification(
                                    user_email=approver[1], title="📋 Dokumen Perlu Approval",
                                    message=f"{user['full_name']} mengupload dokumen '{doc_title}' yang perlu Anda approve."
                                )

                        if send_email and recipient_email:
                            with st.spinner("Mengirim email..."):
                                success, message = send_pdf_email(
                                    recipient_email, filepath, uploaded_file.name, user['full_name'], doc_title
                                )
                                if success:
                                    st.success(f"📧 {message}")
                                else:
                                    st.warning(f"⚠️ {message}")
    # ============================================================
    # HALAMAN: DASHBOARD
    # ============================================================
    if st.session_state.page == "dashboard":
        if admin_mode:
            st.title("📊 Dashboard Admin")
            st.markdown("### Ringkasan Sistem DMS Administrasi PNS")

            total_docs = count_all_documents()
            total_users = len(get_all_users())
            total_depts = len(get_all_departments())
            total_logs = len(get_all_audit_logs())
            pending_docs = len(get_documents_by_status(STATUS_PENDING))

            col1, col2, col3, col4, col5 = st.columns(5)
            with col1: st.metric("📄 Total Dokumen", total_docs)
            with col2: st.metric("👥 Total User", total_users)
            with col3: st.metric("🏢 Total Bidang", total_depts)
            with col4: st.metric("⏳ Pending Approval", pending_docs)
            with col5: st.metric("📝 Total Aktivitas", total_logs)

            st.markdown("---")
            st.subheader("📈 Status Dokumen")
            draft_count = len(get_documents_by_status(STATUS_DRAFT))
            approved_count = len(get_documents_by_status(STATUS_APPROVED))
            rejected_count = len(get_documents_by_status(STATUS_REJECTED))

            col1, col2, col3, col4 = st.columns(4)
            with col1: st.metric("📝 Draft", draft_count)
            with col2: st.metric("⏳ Pending", pending_docs)
            with col3: st.metric("✅ Approved", approved_count)
            with col4: st.metric("❌ Rejected", rejected_count)

            st.markdown("---")
            st.subheader("📈 Aktivitas Terbaru")
            recent_logs = get_all_audit_logs()[:10]
            if recent_logs:
                log_df = pd.DataFrame(recent_logs, columns=[
                    'ID', 'Aksi', 'DocID', 'Judul', 'Email', 'Nama', 'Role', 'Tanggal', 'Detail', 'DeptID', 'DeptName'
                ])
                display_log = log_df[['Aksi', 'Judul', 'Nama', 'DeptName', 'Tanggal', 'Detail']].copy()
                display_log['Tanggal'] = display_log['Tanggal'].apply(format_date)
                st.dataframe(display_log, use_container_width=True, hide_index=True)
            else:
                st.info("Belum ada aktivitas.")
        else:
            st.title(f"📊 Dashboard - {user['full_name']}")
            st.markdown(f"### Selamat datang di **{user['department_name']}**")

            my_docs = get_documents_by_user(user['email'])
            my_logs = get_audit_logs_by_user(user['email'])
            unread_notifs = count_unread_notifications(user['email'])

            col1, col2, col3, col4 = st.columns(4)
            with col1: st.metric("📄 Dokumen Saya", len(my_docs))
            with col2:
                total_size = sum(doc[17] for doc in my_docs if doc[17]) / (1024 * 1024)
                st.metric("💾 Total Ukuran", f"{total_size:.2f} MB")
            with col3: st.metric("📝 Aktivitas Saya", len(my_logs))
            with col4: st.metric("🔔 Notifikasi", unread_notifs)

            st.markdown("---")
            st.subheader("📈 Status Dokumen Saya")
            draft_count = len([d for d in my_docs if d[6] == STATUS_DRAFT])
            pending_count = len([d for d in my_docs if d[6] == STATUS_PENDING])
            approved_count = len([d for d in my_docs if d[6] == STATUS_APPROVED])
            rejected_count = len([d for d in my_docs if d[6] == STATUS_REJECTED])

            col1, col2, col3, col4 = st.columns(4)
            with col1: st.metric("📝 Draft", draft_count)
            with col2: st.metric("⏳ Pending", pending_count)
            with col3: st.metric("✅ Approved", approved_count)
            with col4: st.metric("❌ Rejected", rejected_count)

            st.markdown("---")
            st.subheader("📄 Dokumen Terbaru Saya")
            if my_docs:
                recent_docs = my_docs[:5]
                doc_df = pd.DataFrame(recent_docs, columns=[
                    'ID', 'Judul', 'File', 'Path', 'DeptID', 'CatID', 'Status', 'Tags',
                    'Desc', 'Expiry', 'Email', 'Nama', 'Tanggal', 'Updated', 'AppBy',
                    'AppAt', 'Reject', 'Size', 'DeptName', 'CatName'
                ])
                display_doc = doc_df[['Judul', 'CatName', 'Status', 'Tanggal', 'Size']].copy()
                display_doc['Tanggal'] = display_doc['Tanggal'].apply(format_date)
                display_doc['Size'] = display_doc['Size'].apply(format_size)
                st.dataframe(display_doc, use_container_width=True, hide_index=True)
            else:
                st.info("Belum ada dokumen. Upload dokumen pertama Anda!")

    # ============================================================
    # HALAMAN: SEMUA DOKUMEN (ADMIN)
    # ============================================================
    elif st.session_state.page == "all_docs":
        st.title("📁 Semua Dokumen")
        st.markdown("### Daftar Seluruh Dokumen dari Semua Bidang")

        col_f1, col_f2, col_f3, col_f4 = st.columns([2, 2, 2, 1])
        with col_f1:
            departments = get_all_departments()
            dept_options = [("Semua", 0)] + [(d[1], d[0]) for d in departments]
            selected_dept = st.selectbox("🏢 Filter Bidang", dept_options, format_func=lambda x: x[0])
        with col_f2:
            categories = get_all_categories()
            cat_options = [("Semua", 0)] + [(c[1], c[0]) for c in categories]
            selected_cat = st.selectbox("📂 Filter Kategori", cat_options, format_func=lambda x: x[0])
        with col_f3:
            search_term = st.text_input("🔍 Cari Dokumen")
        with col_f4:
            sort_order = st.radio("⬆️⬇️", ["Terbaru", "Terlama"], horizontal=True)

        all_docs = get_all_documents()
        if all_docs:
            df = pd.DataFrame(all_docs, columns=[
                'ID', 'Judul', 'NamaFile', 'Path', 'DeptID', 'CatID', 'Status',
                'Tags', 'Deskripsi', 'Expiry', 'Email', 'Nama', 'Tanggal', 'Updated',
                'ApprovedBy', 'ApprovedAt', 'Rejection', 'Ukuran', 'DeptName', 'CatName'
            ])
            filtered = df.copy()
            if selected_dept[1] != 0:
                filtered = filtered[filtered['DeptID'] == selected_dept[1]]
            if selected_cat[1] != 0:
                filtered = filtered[filtered['CatID'] == selected_cat[1]]
            if search_term:
                filtered = filtered[
                    filtered['Judul'].str.contains(search_term, case=False, na=False) |
                    filtered['NamaFile'].str.contains(search_term, case=False, na=False) |
                    filtered['Tags'].str.contains(search_term, case=False, na=False)
                ]
            filtered = filtered.sort_values('Tanggal', ascending=(sort_order == "Terlama"))

            display_df = filtered[['ID', 'Judul', 'DeptName', 'CatName', 'Status', 'Nama', 'Tanggal', 'Ukuran']].copy()
            display_df['Tanggal'] = display_df['Tanggal'].apply(format_date)
            display_df['Ukuran'] = display_df['Ukuran'].apply(format_size)
            display_df.columns = ['ID', '📄 Judul', '🏢 Bidang', '📂 Kategori', '📊 Status', '👤 Pengunggah', '📅 Tanggal', '💾 Ukuran']
            st.dataframe(display_df, use_container_width=True, hide_index=True, height=500)

            st.markdown("---")
            st.subheader("👀 Download Dokumen")
            doc_options = {f"{row['ID']} - {row['📄 Judul']}": row['ID'] for _, row in filtered.iterrows()}
            if doc_options:
                selected_doc_label = st.selectbox("Pilih Dokumen", options=list(doc_options.keys()))
                doc_id = doc_options[selected_doc_label]
                doc_info = get_document_by_id(doc_id)
                if doc_info and os.path.exists(doc_info[3]):
                    with open(doc_info[3], "rb") as file:
                        st.download_button(label=f"📥 Download: {doc_info[2]}", data=file.read(), file_name=doc_info[2], mime="application/pdf")
        else:
            st.info("Belum ada dokumen.")

    # ============================================================
    # HALAMAN: APPROVAL (ADMIN & KABID)
    # ============================================================
    elif st.session_state.page == "approvals":
        st.title("⏳ Approval Dokumen")

        all_pending = get_documents_by_status(STATUS_PENDING)
        if admin_mode:
            dept_pending = all_pending
        else:
            dept_pending = [d for d in all_pending if d[4] == user['department_id']]

        if dept_pending:
            st.info(f"📊 Ada **{len(dept_pending)}** dokumen menunggu approval")
            for doc in dept_pending:
                with st.expander(f"📄 {doc[1]} - oleh {doc[11]}"):
                    col1, col2 = st.columns([2, 1])
                    with col1:
                        st.markdown(f"**Judul:** {doc[1]}")
                        st.markdown(f"**Kategori:** {doc[19]}")
                        st.markdown(f"**Pengunggah:** {doc[11]} ({doc[10]})")
                        st.markdown(f"**Tanggal Upload:** {format_date(doc[12])}")
                        st.markdown(f"**Ukuran:** {format_size(doc[17])}")
                        if doc[8]:
                            st.markdown(f"**Deskripsi:** {doc[8]}")
                        if doc[7]:
                            st.markdown(f"**Tags:** {doc[7]}")
                    with col2:
                        if os.path.exists(doc[3]):
                            with open(doc[3], "rb") as file:
                                st.download_button("📥 Download PDF", data=file.read(), file_name=doc[2], mime="application/pdf", use_container_width=True)

                    st.markdown("---")
                    col_a1, col_a2 = st.columns(2)
                    with col_a1:
                        if st.button(f"✅ Approve", key=f"approve_{doc[0]}", type="primary", use_container_width=True):
                            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            approve_document(doc[0], user['email'], now)
                            create_audit_log(
                                action="APPROVE", document_id=doc[0], document_title=doc[1],
                                user_email=user['email'], user_name=user['full_name'],
                                user_role=user['role'], action_date=now,
                                details=f"Approve dokumen oleh {user['full_name']}",
                                department_id=user['department_id']
                            )
                            create_notification(
                                user_email=doc[10], title="✅ Dokumen Disetujui",
                                message=f"Dokumen '{doc[1]}' Anda telah disetujui oleh {user['full_name']}."
                            )
                            send_approval_notification(doc[10], doc[1], "approved", user['full_name'])
                            st.success("✅ Dokumen berhasil di-approve!")
                            st.rerun()
                    with col_a2:
                        rejection_reason = st.text_input("Alasan penolakan", key=f"reason_{doc[0]}", placeholder="Jelaskan alasan penolakan...")
                        if st.button(f"❌ Reject", key=f"reject_{doc[0]}", use_container_width=True):
                            if rejection_reason:
                                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                reject_document(doc[0], user['email'], rejection_reason, now)
                                create_audit_log(
                                    action="REJECT", document_id=doc[0], document_title=doc[1],
                                    user_email=user['email'], user_name=user['full_name'],
                                    user_role=user['role'], action_date=now,
                                    details=f"Reject: {rejection_reason}",
                                    department_id=user['department_id']
                                )
                                create_notification(
                                    user_email=doc[10], title="❌ Dokumen Ditolak",
                                    message=f"Dokumen '{doc[1]}' Anda ditolak. Alasan: {rejection_reason}"
                                )
                                send_approval_notification(doc[10], doc[1], "rejected", user['full_name'], rejection_reason)
                                st.success("❌ Dokumen ditolak!")
                                st.rerun()
                            else:
                                st.warning("⚠️ Alasan penolakan harus diisi!")
        else:
            st.success("✅ Tidak ada dokumen yang menunggu approval.")

    # ============================================================
    # HALAMAN: DOKUMEN SAYA (USER & KABID)
    # ============================================================
    elif st.session_state.page == "my_docs":
        st.title("📄 Dokumen Saya")
        st.markdown("### Kelola Dokumen yang Anda Upload")

        my_docs = get_documents_by_user(user['email'])
        col_f1, col_f2, col_f3 = st.columns([2, 1, 1])
        with col_f1:
            search_term = st.text_input("🔍 Cari Dokumen")
        with col_f2:
            status_filter = st.multiselect("📊 Filter Status", options=list(STATUS_LABELS.keys()), default=list(STATUS_LABELS.keys()), format_func=lambda x: STATUS_LABELS[x])
        with col_f3:
            sort_order = st.radio("⬆️⬇️", ["Terbaru", "Terlama"], horizontal=True)

        if my_docs:
            df = pd.DataFrame(my_docs, columns=[
                'ID', 'Judul', 'NamaFile', 'Path', 'DeptID', 'CatID', 'Status', 'Tags',
                'Desc', 'Expiry', 'Email', 'Nama', 'Tanggal', 'Updated', 'AppBy',
                'AppAt', 'Reject', 'Size', 'DeptName', 'CatName'
            ])
            filtered = df.copy()
            if search_term:
                filtered = filtered[
                    filtered['Judul'].str.contains(search_term, case=False, na=False) |
                    filtered['NamaFile'].str.contains(search_term, case=False, na=False) |
                    filtered['Tags'].str.contains(search_term, case=False, na=False)
                ]
            if status_filter:
                filtered = filtered[filtered['Status'].isin(status_filter)]
            filtered = filtered.sort_values('Tanggal', ascending=(sort_order == "Terlama"))

            if not filtered.empty:
                st.info(f"📊 Menampilkan **{len(filtered)}** dokumen")
                display_df = filtered[['ID', 'Judul', 'CatName', 'Status', 'Tanggal', 'Size', 'Tags']].copy()
                display_df['Tanggal'] = display_df['Tanggal'].apply(format_date)
                display_df['Size'] = display_df['Size'].apply(format_size)
                display_df.columns = ['ID', '📄 Judul', '📂 Kategori', '📊 Status', '📅 Tanggal', '💾 Ukuran', '🏷️ Tags']
                st.dataframe(display_df, use_container_width=True, hide_index=True, height=350)

                st.markdown("---")
                st.subheader("⚙️ Kelola Dokumen")
                doc_options = {f"{row['ID']} - {row['📄 Judul']}": row['ID'] for _, row in filtered.iterrows()}
                selected_doc_label = st.selectbox("Pilih Dokumen", options=list(doc_options.keys()))
                selected_doc_id = doc_options[selected_doc_label]
                doc_info = get_document_by_id(selected_doc_id)

                if doc_info:
                    st.markdown(f"""
                    **Judul:** {doc_info[1]}  
                    **Kategori:** {doc_info[19]}  
                    **Status:** {STATUS_LABELS.get(doc_info[6], doc_info[6])}  
                    **Tanggal Upload:** {format_date(doc_info[12])}  
                    **Ukuran:** {format_size(doc_info[17])}
                    """)
                    if doc_info[16]:
                        st.error(f"❌ **Alasan Penolakan:** {doc_info[16]}")

                    st.markdown("---")
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        if doc_info[6] in [STATUS_DRAFT, STATUS_REJECTED]:
                            st.markdown("**✏️ Edit Judul**")
                            new_title = st.text_input("Judul Baru", value=doc_info[1], key=f"edit_title_{doc_info[0]}")
                            if st.button("💾 Simpan Perubahan", type="primary", use_container_width=True, key=f"save_{doc_info[0]}"):
                                if new_title and new_title != doc_info[1]:
                                    update_document(selected_doc_id, title=new_title, updated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                                    create_audit_log(
                                        action="UPDATE", document_id=selected_doc_id, document_title=new_title,
                                        user_email=user['email'], user_name=user['full_name'],
                                        user_role=user['role'], action_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
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
                        if doc_info[6] in [STATUS_DRAFT, STATUS_REJECTED]:
                            st.markdown("**📤 Submit untuk Approval**")
                            if st.button("📤 Submit ke Kepala Bidang", type="secondary", use_container_width=True, key=f"submit_{doc_info[0]}"):
                                update_document(selected_doc_id, status=STATUS_PENDING, updated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                                approvers = get_approvers_for_department(user['department_id'])
                                for approver in approvers:
                                    create_notification(
                                        user_email=approver[1], title="📋 Dokumen Perlu Approval",
                                        message=f"{user['full_name']} mensubmit dokumen '{doc_info[1]}' untuk approval Anda."
                                    )
                                create_audit_log(
                                    action="UPDATE", document_id=selected_doc_id, document_title=doc_info[1],
                                    user_email=user['email'], user_name=user['full_name'],
                                    user_role=user['role'], action_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                    details="Submit untuk approval", department_id=user['department_id']
                                )
                                st.success("✅ Dokumen disubmit untuk approval!")
                                st.rerun()
                        elif doc_info[6] == STATUS_PENDING:
                            st.info("⏳ Menunggu approval Kepala Bidang")
                        elif doc_info[6] == STATUS_APPROVED:
                            st.success(f"✅ Disetujui pada {format_date(doc_info[15])}")

                    with col3:
                        st.markdown("**📥 Download**")
                        if os.path.exists(doc_info[3]):
                            with open(doc_info[3], "rb") as file:
                                st.download_button(label="📥 Download PDF", data=file.read(), file_name=doc_info[2], mime="application/pdf", type="primary", use_container_width=True, key=f"download_{doc_info[0]}")
                        else:
                            st.error("❌ File tidak ditemukan!")

                    st.markdown("---")
                    if doc_info[6] in [STATUS_DRAFT, STATUS_REJECTED]:
                        st.markdown("**🗑️ Hapus Dokumen**")
                        confirm_delete = st.checkbox("⚠️ Saya yakin ingin menghapus dokumen ini", key=f"confirm_del_{doc_info[0]}")
                        if st.button("🗑️ Hapus Dokumen", type="secondary", disabled=not confirm_delete, key=f"delete_{doc_info[0]}"):
                            if os.path.exists(doc_info[3]):
                                os.remove(doc_info[3])
                            delete_document_record(selected_doc_id)
                            create_audit_log(
                                action="DELETE", document_id=selected_doc_id, document_title=doc_info[1],
                                user_email=user['email'], user_name=user['full_name'],
                                user_role=user['role'], action_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                details=f"Hapus file: {doc_info[2]}", department_id=user['department_id']
                            )
                            st.success("✅ Dokumen berhasil dihapus!")
                            st.rerun()
                    else:
                        st.info("ℹ️ Hapus hanya tersedia untuk dokumen Draft/Rejected")
            else:
                st.info("Tidak ada dokumen yang sesuai dengan filter.")
        else:
            st.info("📭 Anda belum upload dokumen.")

    # ============================================================
    # HALAMAN: DOKUMEN BIDANG (KABID)
    # ============================================================
    elif st.session_state.page == "dept_docs":
        st.title(f"📁 Dokumen Bidang {user['department_name']}")
        st.markdown("### Daftar Dokumen dari Seluruh Anggota Bidang")

        dept_docs = get_documents_by_department(user['department_id'])
        col_f1, col_f2 = st.columns([2, 1])
        with col_f1:
            search_term = st.text_input("🔍 Cari Dokumen")
        with col_f2:
            sort_order = st.radio("⬆️⬇️ Urutan", ["Terbaru", "Terlama"], horizontal=True)

        if dept_docs:
            df = pd.DataFrame(dept_docs, columns=[
                'ID', 'Judul', 'NamaFile', 'Path', 'DeptID', 'CatID', 'Status', 'Tags',
                'Desc', 'Expiry', 'Email', 'Nama', 'Tanggal', 'Updated', 'AppBy',
                'AppAt', 'Reject', 'Size', 'DeptName', 'CatName'
            ])
            filtered = df.copy()
            if search_term:
                filtered = filtered[
                    filtered['Judul'].str.contains(search_term, case=False, na=False) |
                    filtered['NamaFile'].str.contains(search_term, case=False, na=False) |
                    filtered['Nama'].str.contains(search_term, case=False, na=False)
                ]
            filtered = filtered.sort_values('Tanggal', ascending=(sort_order == "Terlama"))

            display_df = filtered[['ID', 'Judul', 'CatName', 'Status', 'Nama', 'Tanggal', 'Size']].copy()
            display_df['Tanggal'] = display_df['Tanggal'].apply(format_date)
            display_df['Size'] = display_df['Size'].apply(format_size)
            display_df.columns = ['ID', '📄 Judul', '📂 Kategori', '📊 Status', '👤 Pengunggah', '📅 Tanggal', '💾 Ukuran']
            st.dataframe(display_df, use_container_width=True, hide_index=True, height=400)

            st.markdown("---")
            st.subheader("👀 Download Dokumen")
            doc_options = {f"{row['ID']} - {row['📄 Judul']}": row['ID'] for _, row in filtered.iterrows()}
            if doc_options:
                selected_doc_label = st.selectbox("Pilih Dokumen", options=list(doc_options.keys()))
                doc_id = doc_options[selected_doc_label]
                doc_info = get_document_by_id(doc_id)
                if doc_info and os.path.exists(doc_info[3]):
                    with open(doc_info[3], "rb") as file:
                        st.download_button(label=f"📥 Download: {doc_info[2]}", data=file.read(), file_name=doc_info[2], mime="application/pdf")
        else:
            st.info("Belum ada dokumen di bidang ini.")

    # ============================================================
    # HALAMAN: MANAJEMEN USER (ADMIN)
    # ============================================================
    elif st.session_state.page == "users":
        st.title("👥 Manajemen User")
        st.markdown("### Kelola Akun PNS dan Kepala Bidang")

        tab1, tab2 = st.tabs(["➕ Tambah User Baru", "📋 Daftar User"])

        with tab1:
            st.subheader("Buat Akun Baru")
            departments = get_all_departments()
            if not departments:
                st.warning("⚠️ Belum ada departemen. Tambahkan departemen terlebih dahulu.")
            else:
                with st.form("add_user_form"):
                    col1, col2 = st.columns(2)
                    with col1:
                        new_name = st.text_input("👤 Nama Lengkap")
                        new_nip = st.text_input("🆔 NIP")
                        new_email = st.text_input("📧 Email")
                    with col2:
                        new_password = st.text_input("🔑 Password (min. 6 karakter)", type="password")
                        new_dept = st.selectbox("🏢 Bidang", [(d[1], d[0]) for d in departments], format_func=lambda x: x[0])
                        new_role = st.selectbox("🎭 Role", ['pns', 'kepala_bidang', 'admin'], format_func=lambda x: ROLE_LABELS.get(x, x))
                    submit_add = st.form_submit_button("➕ Buat User", type="primary", use_container_width=True)
                    if submit_add:
                        if not all([new_name, new_email, new_password]):
                            st.error("❌ Nama, email, dan password wajib diisi!")
                        elif len(new_password) < 6:
                            st.error("❌ Password minimal 6 karakter!")
                        else:
                            password_hash = hash_password(new_password)
                            success, message = create_user(new_email.lower().strip(), password_hash, new_name, new_nip, new_dept[1], new_role)
                            if success:
                                create_audit_log(
                                    action="CREATE_USER", document_id=None, document_title=f"User: {new_name}",
                                    user_email=user['email'], user_name=user['full_name'],
                                    user_role=user['role'], action_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                    details=f"Buat user baru: {new_email} ({new_role})",
                                    department_id=user['department_id']
                                )
                                st.success(f"✅ {message}")
                                st.rerun()
                            else:
                                st.error(f"❌ {message}")

        with tab2:
            st.subheader("Daftar Semua User")
            users = get_all_users()
            if users:
                search_term = st.text_input("🔍 Cari User (nama/email/NIP)")
                df = pd.DataFrame(users, columns=['ID', 'Email', 'Nama', 'NIP', 'Bidang', 'Role', 'Status', 'Dibuat'])
                if search_term:
                    df = df[
                        df['Nama'].str.contains(search_term, case=False, na=False) |
                        df['Email'].str.contains(search_term, case=False, na=False) |
                        df['NIP'].str.contains(search_term, case=False, na=False)
                    ]
                display_df = df[['ID', 'Nama', 'NIP', 'Email', 'Bidang', 'Role', 'Status']].copy()
                display_df['Status'] = display_df['Status'].apply(lambda x: "✅ Aktif" if x == 1 else "❌ Nonaktif")
                st.dataframe(display_df, use_container_width=True, hide_index=True, height=400)

                st.markdown("---")
                st.subheader("⚙️ Kelola User")
                user_options = {f"{row['Nama']} ({row['Email']})": row['ID'] for _, row in df.iterrows()}
                selected_user_label = st.selectbox("Pilih User", options=list(user_options.keys()))
                selected_user_id = user_options[selected_user_label]
                user_info = df[df['ID'] == selected_user_id].iloc[0]

                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**Edit Data User**")
                    departments = get_all_departments()
                    dept_dict = {d[1]: d[0] for d in departments}
                    with st.form("edit_user_form"):
                        edit_name = st.text_input("Nama Lengkap", value=user_info['Nama'])
                        edit_nip = st.text_input("NIP", value=user_info['NIP'])
                        st.text_input("Email", value=user_info['Email'], disabled=True)
                        dept_names = [d[1] for d in departments]
                        current_dept_idx = dept_names.index(user_info['Bidang']) if user_info['Bidang'] in dept_names else 0
                        edit_dept = st.selectbox("Bidang", dept_names, index=current_dept_idx)
                        roles = ['pns', 'kepala_bidang', 'admin']
                        edit_role = st.selectbox("Role", roles, index=roles.index(user_info['Role']), format_func=lambda x: ROLE_LABELS.get(x, x))
                        edit_active = st.checkbox("Aktif", value=user_info['Status'] == 1)
                        submit_edit = st.form_submit_button("💾 Simpan Perubahan", type="primary")
                        if submit_edit:
                            dept_id = dept_dict.get(edit_dept)
                            update_user(selected_user_id, edit_name, edit_nip, dept_id, edit_role, 1 if edit_active else 0)
                            create_audit_log(
                                action="UPDATE_USER", document_id=None, document_title=f"User: {edit_name}",
                                user_email=user['email'], user_name=user['full_name'],
                                user_role=user['role'], action_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                details=f"Update user: {user_info['Email']}",
                                department_id=user['department_id']
                            )
                            st.success("✅ Data user berhasil diupdate!")
                            st.rerun()

                with col2:
                    st.markdown("**Reset Password**")
                    with st.form("reset_password_form"):
                        new_password = st.text_input("Password Baru", type="password")
                        confirm_password = st.text_input("Konfirmasi Password", type="password")
                        submit_reset = st.form_submit_button("🔑 Reset Password", type="secondary")
                        if submit_reset:
                            if not new_password:
                                st.error("❌ Password baru harus diisi!")
                            elif new_password != confirm_password:
                                st.error("❌ Konfirmasi password tidak cocok!")
                            elif len(new_password) < 6:
                                st.error("❌ Password minimal 6 karakter!")
                            else:
                                password_hash = hash_password(new_password)
                                update_user_password(selected_user_id, password_hash)
                                create_audit_log(
                                    action="RESET_PASSWORD", document_id=None, document_title=f"User: {user_info['Nama']}",
                                    user_email=user['email'], user_name=user['full_name'],
                                    user_role=user['role'], action_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                    details=f"Reset password: {user_info['Email']}",
                                    department_id=user['department_id']
                                )
                                st.success("✅ Password berhasil direset!")

                    st.markdown("---")
                    st.markdown("**🗑️ Hapus User**")
                    confirm_delete = st.checkbox("⚠️ Saya yakin ingin menghapus user ini")
                    if st.button("🗑️ Hapus User", type="secondary", disabled=not confirm_delete):
                        delete_user(selected_user_id)
                        create_audit_log(
                            action="DELETE_USER", document_id=None, document_title=f"User: {user_info['Nama']}",
                            user_email=user['email'], user_name=user['full_name'],
                            user_role=user['role'], action_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            details=f"Hapus user: {user_info['Email']}",
                            department_id=user['department_id']
                        )
                        st.success("✅ User berhasil dihapus!")
                        st.rerun()
            else:
                st.info("Belum ada user terdaftar.")

    # ============================================================
    # HALAMAN: MANAJEMEN BIDANG (ADMIN)
    # ============================================================
    elif st.session_state.page == "departments":
        st.title("🏢 Manajemen Bidang/Departemen")
        st.markdown("### Kelola Struktur Organisasi")

        tab1, tab2 = st.tabs(["➕ Tambah Bidang", "📋 Daftar Bidang"])

        with tab1:
            st.subheader("Tambah Bidang Baru")
            with st.form("add_dept_form"):
                dept_name = st.text_input("Nama Bidang", placeholder="Contoh: Bidang Keuangan")
                dept_desc = st.text_area("Deskripsi (Opsional)", height=100)
                submit_add = st.form_submit_button("➕ Tambah Bidang", type="primary", use_container_width=True)
                if submit_add:
                    if not dept_name:
                        st.error("❌ Nama bidang harus diisi!")
                    else:
                        success, message = create_department(dept_name, dept_desc)
                        if success:
                            create_audit_log(
                                action="CREATE_DEPARTMENT", document_id=None, document_title=f"Bidang: {dept_name}",
                                user_email=user['email'], user_name=user['full_name'],
                                user_role=user['role'], action_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                details=f"Buat bidang baru: {dept_name}",
                                department_id=user['department_id']
                            )
                            st.success(f"✅ {message}")
                            st.rerun()
                        else:
                            st.error(f"❌ {message}")

        with tab2:
            st.subheader("Daftar Bidang")
            departments = get_all_departments()
            if departments:
                df = pd.DataFrame(departments, columns=['ID', 'Nama', 'Deskripsi', 'Dibuat'])
                display_df = df[['ID', 'Nama', 'Deskripsi']].copy()
                display_df.columns = ['ID', '🏢 Nama Bidang', '📝 Deskripsi']
                st.dataframe(display_df, use_container_width=True, hide_index=True)

                st.markdown("---")
                st.subheader("⚙️ Kelola Bidang")
                dept_options = {row['Nama']: row['ID'] for _, row in df.iterrows()}
                selected_dept_label = st.selectbox("Pilih Bidang", options=list(dept_options.keys()))
                selected_dept_id = dept_options[selected_dept_label]
                dept_info = df[df['ID'] == selected_dept_id].iloc[0]

                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**Edit Bidang**")
                    with st.form("edit_dept_form"):
                        edit_name = st.text_input("Nama Bidang", value=dept_info['Nama'])
                        edit_desc = st.text_area("Deskripsi", value=dept_info['Deskripsi'] or "", height=100)
                        submit_edit = st.form_submit_button("💾 Simpan", type="primary")
                        if submit_edit:
                            update_department(selected_dept_id, edit_name, edit_desc)
                            create_audit_log(
                                action="UPDATE_DEPARTMENT", document_id=None, document_title=f"Bidang: {edit_name}",
                                user_email=user['email'], user_name=user['full_name'],
                                user_role=user['role'], action_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                details=f"Update bidang: {dept_info['Nama']} → {edit_name}",
                                department_id=user['department_id']
                            )
                            st.success("✅ Bidang berhasil diupdate!")
                            st.rerun()

                with col2:
                    st.markdown("**🗑️ Hapus Bidang**")
                    confirm_delete = st.checkbox("⚠️ Saya yakin ingin menghapus bidang ini")
                    if st.button("🗑️ Hapus Bidang", type="secondary", disabled=not confirm_delete):
                        delete_department(selected_dept_id)
                        create_audit_log(
                            action="DELETE_DEPARTMENT", document_id=None, document_title=f"Bidang: {dept_info['Nama']}",
                            user_email=user['email'], user_name=user['full_name'],
                            user_role=user['role'], action_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            details=f"Hapus bidang: {dept_info['Nama']}",
                            department_id=user['department_id']
                        )
                        st.success("✅ Bidang berhasil dihapus!")
                        st.rerun()
            else:
                st.info("Belum ada bidang terdaftar.")

    # ============================================================
    # HALAMAN: MANAJEMEN KATEGORI (ADMIN)
    # ============================================================
    elif st.session_state.page == "categories":
        st.title("📂 Manajemen Kategori Dokumen")
        st.markdown("### Kelola Kategori Dokumen Administrasi PNS")

        tab1, tab2 = st.tabs(["➕ Tambah Kategori", "📋 Daftar Kategori"])

        with tab1:
            st.subheader("Tambah Kategori Baru")
            with st.form("add_cat_form"):
                cat_name = st.text_input("Nama Kategori", placeholder="Contoh: SK (Surat Keputusan)")
                cat_desc = st.text_area("Deskripsi (Opsional)", height=100)
                require_approval = st.checkbox("⚠️ Kategori ini memerlukan approval Kepala Bidang", help="Jika dicentang, dokumen dengan kategori ini harus di-approve")
                submit_add = st.form_submit_button("➕ Tambah Kategori", type="primary", use_container_width=True)
                if submit_add:
                    if not cat_name:
                        st.error("❌ Nama kategori harus diisi!")
                    else:
                        success, message = create_category(cat_name, cat_desc, 1 if require_approval else 0)
                        if success:
                            create_audit_log(
                                action="CREATE_CATEGORY", document_id=None, document_title=f"Kategori: {cat_name}",
                                user_email=user['email'], user_name=user['full_name'],
                                user_role=user['role'], action_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                details=f"Buat kategori baru: {cat_name}",
                                department_id=user['department_id']
                            )
                            st.success(f"✅ {message}")
                            st.rerun()
                        else:
                            st.error(f"❌ {message}")

        with tab2:
            st.subheader("Daftar Kategori")
            categories = get_all_categories()
            if categories:
                df = pd.DataFrame(categories, columns=['ID', 'Nama', 'Deskripsi', 'PerluApproval', 'Dibuat'])
                display_df = df[['ID', 'Nama', 'Deskripsi', 'PerluApproval']].copy()
                display_df['PerluApproval'] = display_df['PerluApproval'].apply(lambda x: "✅ Ya" if x == 1 else "❌ Tidak")
                display_df.columns = ['ID', '📂 Nama Kategori', '📝 Deskripsi', '🔐 Perlu Approval']
                st.dataframe(display_df, use_container_width=True, hide_index=True)

                st.markdown("---")
                st.subheader("⚙️ Kelola Kategori")
                cat_options = {row['Nama']: row['ID'] for _, row in df.iterrows()}
                selected_cat_label = st.selectbox("Pilih Kategori", options=list(cat_options.keys()))
                selected_cat_id = cat_options[selected_cat_label]
                cat_info = df[df['ID'] == selected_cat_id].iloc[0]

                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**Edit Kategori**")
                    with st.form("edit_cat_form"):
                        edit_name = st.text_input("Nama Kategori", value=cat_info['Nama'])
                        edit_desc = st.text_area("Deskripsi", value=cat_info['Deskripsi'] or "", height=100)
                        edit_approval = st.checkbox("Perlu Approval", value=cat_info['PerluApproval'] == 1)
                        submit_edit = st.form_submit_button("💾 Simpan", type="primary")
                        if submit_edit:
                            update_category(selected_cat_id, edit_name, edit_desc, 1 if edit_approval else 0)
                            create_audit_log(
                                action="UPDATE_CATEGORY", document_id=None, document_title=f"Kategori: {edit_name}",
                                user_email=user['email'], user_name=user['full_name'],
                                user_role=user['role'], action_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                details=f"Update kategori: {cat_info['Nama']} → {edit_name}",
                                department_id=user['department_id']
                            )
                            st.success("✅ Kategori berhasil diupdate!")
                            st.rerun()

                with col2:
                    st.markdown("**🗑️ Hapus Kategori**")
                    confirm_delete = st.checkbox("⚠️ Saya yakin ingin menghapus kategori ini")
                    if st.button("🗑️ Hapus Kategori", type="secondary", disabled=not confirm_delete):
                        delete_category(selected_cat_id)
                        create_audit_log(
                            action="DELETE_CATEGORY", document_id=None, document_title=f"Kategori: {cat_info['Nama']}",
                            user_email=user['email'], user_name=user['full_name'],
                            user_role=user['role'], action_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            details=f"Hapus kategori: {cat_info['Nama']}",
                            department_id=user['department_id']
                        )
                        st.success("✅ Kategori berhasil dihapus!")
                        st.rerun()
            else:
                st.info("Belum ada kategori terdaftar.")

    # ============================================================
    # HALAMAN: AUDIT LOG (ADMIN)
    # ============================================================
    elif st.session_state.page == "audit_log":
        st.title("📜 Audit Log Sistem")
        st.markdown("### Catatan Seluruh Aktivitas di Sistem")

        col_f1, col_f2 = st.columns([1, 1])
        with col_f1:
            action_filter = st.multiselect("🔍 Filter Aksi", options=["CREATE", "UPDATE", "DELETE", "APPROVE", "REJECT", "CREATE_USER", "UPDATE_USER", "DELETE_USER", "RESET_PASSWORD", "CREATE_DEPARTMENT", "UPDATE_DEPARTMENT", "DELETE_DEPARTMENT", "CREATE_CATEGORY", "UPDATE_CATEGORY", "DELETE_CATEGORY"], default=["CREATE", "UPDATE", "DELETE", "APPROVE", "REJECT"])
        with col_f2:
            search_log = st.text_input("🔍 Cari di Log")

        all_logs = get_all_audit_logs()
        if all_logs:
            df = pd.DataFrame(all_logs, columns=['ID', 'Aksi', 'DocID', 'Judul', 'Email', 'Nama', 'Role', 'Tanggal', 'Detail', 'DeptID', 'DeptName'])
            filtered = df.copy()
            if action_filter:
                filtered = filtered[filtered['Aksi'].isin(action_filter)]
            if search_log:
                filtered = filtered[
                    filtered['Judul'].str.contains(search_log, case=False, na=False) |
                    filtered['Nama'].str.contains(search_log, case=False, na=False) |
                    filtered['Detail'].str.contains(search_log, case=False, na=False) |
                    filtered['Email'].str.contains(search_log, case=False, na=False)
                ]

            st.info(f"📊 Menampilkan **{len(filtered)}** aktivitas")

            if not filtered.empty:
                display_df = filtered[['Aksi', 'Judul', 'Nama', 'Role', 'DeptName', 'Tanggal', 'Detail']].copy()
                display_df['Tanggal'] = display_df['Tanggal'].apply(format_date)
                display_df.columns = ['🔧 Aksi', '📄 Dokumen/User', '👤 Pelaku', '🎭 Role', '🏢 Bidang', '📅 Waktu', '📝 Detail']
                st.dataframe(display_df, use_container_width=True, hide_index=True, height=500)

                st.markdown("---")
                if st.button("📊 Export Audit Log ke Excel"):
                    export_df = filtered[['Aksi', 'Judul', 'Nama', 'Role', 'DeptName', 'Tanggal', 'Detail']].copy()
                    export_filename = f"audit_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                    export_df.to_excel(export_filename, index=False)
                    with open(export_filename, "rb") as file:
                        st.download_button("📥 Download Excel", data=file.read(), file_name=export_filename, mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            else:
                st.info("Tidak ada aktivitas yang sesuai dengan filter.")
        else:
            st.info("Belum ada aktivitas tercatat di sistem.")

    # ============================================================
    # HALAMAN: NOTIFIKASI (SEMUA USER)
    # ============================================================
    elif st.session_state.page == "notifications":
        st.title("🔔 Notifikasi Saya")
        st.markdown("### Pemberitahuan Aktivitas Dokumen")

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
        notifications = get_notifications(user['email'])
        if notifications:
            for notif in notifications:
                is_read = notif[5] == 1
                if is_read:
                    bg_color = "#f8f9fa"
                    border_color = "#dee2e6"
                    icon = "📭"
                else:
                    bg_color = "#e7f3ff"
                    border_color = "#0d6efd"
                    icon = "🔔"

                st.markdown(f"""
                <div style="background: {bg_color}; border-left: 4px solid {border_color}; padding: 15px; margin-bottom: 10px; border-radius: 5px;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <h4 style="margin: 0;">{icon} {notif[2]}</h4>
                        <small style="color: #666;">{format_date(notif[6])}</small>
                    </div>
                    <p style="margin: 10px 0 0 0; color: #333;">{notif[3]}</p>
                </div>
                """, unsafe_allow_html=True)

                if not is_read:
                    if st.button(f"✅ Tandai Dibaca", key=f"read_{notif[0]}"):
                        mark_notification_read(notif[0])
                        st.rerun()
        else:
            st.info("📭 Belum ada notifikasi.")