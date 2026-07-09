"""
Aplikasi Utama - DMS Administrasi PNS
"""
import streamlit as st
import os
from datetime import datetime

from config import (
    DEPARTMENTS, UPLOAD_FOLDER, init_folders, ROLE_ADMIN, ROLE_KABID, ROLE_PNS,
    ROLE_LABELS, DOCUMENT_CATEGORIES, STATUS_DRAFT, STATUS_PENDING,
    STATUS_APPROVED, STATUS_REJECTED, STATUS_LABELS, ITEMS_PER_PAGE
)
from database import (
    init_db, create_document, get_all_documents, get_documents_by_department,
    get_documents_by_user, get_document_by_id, update_document, delete_document_record,
    create_audit_log, get_all_audit_logs, get_audit_logs_by_user,
    get_all_departments, get_all_categories, get_department_by_id,
    get_category_by_id, create_notification, get_notifications,
    mark_all_notifications_read, count_unread_notifications, approve_document,
    reject_document, get_approvers_for_department
)
from auth import register, login, is_admin, is_kepala_bidang, can_approve
from email_service import send_pdf_email, send_approval_notification
from utils import format_file_size, format_date, get_status_badge

# --- INISIALISASI ---
init_folders()
init_db()

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="DMS Administrasi PNS",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM CSS ---
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1e3a8a;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .notification-badge {
        background: #dc3545;
        color: white;
        border-radius: 50%;
        padding: 2px 8px;
        font-size: 0.7rem;
        font-weight: bold;
        margin-left: 5px;
    }
</style>
""", unsafe_allow_html=True)

# --- SESSION STATE ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_data = None
    st.session_state.page = "dashboard"


# ============================================================
# HALAMAN LOGIN / REGISTER
# ============================================================
if not st.session_state.logged_in:
    st.markdown('<h1 class="main-header">🏛️ DMS Administrasi PNS</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Sistem Manajemen Dokumen Administrasi Pegawai Negeri Sipil</p>',
                unsafe_allow_html=True)

    col_left, col_center, col_right = st.columns([1, 2, 1])

    with col_center:
        tab1, tab2 = st.tabs(["🔐 Login", "📝 Registrasi"])

        with tab1:
            with st.form("login_form"):
                st.subheader("Masuk ke Akun PNS Anda")
                l_email = st.text_input("📧 Email", placeholder="nama@instansi.go.id")
                l_pass = st.text_input("🔑 Password", type="password")
                submit_login = st.form_submit_button("Login", type="primary",
                                                     use_container_width=True)

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
                    r_dept = st.selectbox("🏢 Bidang/Departemen",
                                         [(d[1], d[0]) for d in departments],
                                         format_func=lambda x: x[0])
                    submit_register = st.form_submit_button("Daftar", type="primary",
                                                            use_container_width=True)

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

    # --- SIDEBAR ---
    with st.sidebar:
        st.markdown("### 👤 Profil")
        st.success(f"**{user['full_name']}**")
        st.caption(f"📧 {user['email']}")
        st.caption(f"🆔 NIP: {user['nip'] or '-'}")
        st.caption(f"🏢 {user['department_name']}")
        st.markdown(f'{ROLE_LABELS.get(user["role"], user["role"])}')

        # Notifikasi
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
                doc_title = st.text_input("Judul Dokumen",
                                          placeholder="Contoh: Laporan Kinerja Triwulan I")
                doc_desc = st.text_area("Deskripsi (Opsional)", height=80)
                doc_category = st.selectbox("Kategori",
                                           [(c[1], c[0]) for c in categories],
                                           format_func=lambda x: x[0])
                doc_tags = st.text_input("Tag (pisahkan dengan koma)",
                                        placeholder="laporan, kinerja, 2026")
                doc_expiry = st.date_input("Tanggal Kadaluarsa (Opsional)",
                                          min_value=datetime.now(),
                                          value=None)

                send_email = st.checkbox("Kirim notifikasi via email", value=True)
                recipient_email = st.text_input(
                    "Email Penerima",
                    value=user['email'] if send_email else "",
                    disabled=not send_email
                )

                submit_upload = st.form_submit_button(
                    "📤 Upload",
                    type="primary",
                    use_container_width=True
                )

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

                        # Tentukan status berdasarkan kategori
                        category_info = get_category_by_id(doc_category[1])
                        status = STATUS_DRAFT
                        if category_info and category_info[3] == 1:  # require_approval
                            status = STATUS_PENDING

                        expiry_date = doc_expiry.strftime("%Y-%m-%d") if doc_expiry else None

                        doc_id = create_document(
                            title=doc_title,
                            original_filename=uploaded_file.name,
                            filepath=filepath,
                            department_id=user['department_id'],
                            category_id=doc_category[1],
                            status=status,
                            tags=doc_tags,
                            description=doc_desc,
                            expiry_date=expiry_date,
                            uploaded_by_email=user['email'],
                            uploaded_by_name=user['full_name'],
                            upload_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            file_size=uploaded_file.size
                        )

                        # Audit log
                        create_audit_log(
                            action="CREATE",
                            document_id=doc_id,
                            document_title=doc_title,
                            user_email=user['email'],
                            user_name=user['full_name'],
                            user_role=user['role'],
                            action_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            details=f"Upload file: {uploaded_file.name}",
                            department_id=user['department_id']
                        )

                        st.success(f"✅ Dokumen berhasil diupload! (ID: {doc_id})")

                        # Notifikasi ke Kepala Bidang jika perlu approval
                        if status == STATUS_PENDING:
                            approvers = get_approvers_for_department(user['department_id'])
                            for approver in approvers:
                                create_notification(
                                    user_email=approver[1],
                                    title="📋 Dokumen Perlu Approval",
                                    message=f"{user['full_name']} mengupload dokumen '{doc_title}' yang perlu Anda approve.",
                                    link=f"?doc_id={doc_id}"
                                )

                        # Kirim email
                        if send_email and recipient_email:
                            with st.spinner("Mengirim email..."):
                                success, message = send_pdf_email(
                                    recipient_email, filepath,
                                    uploaded_file.name, user['full_name'], doc_title
                                )
                                if success:
                                    st.success(f"📧 {message}")
                                else:
                                    st.warning(f"⚠️ {message}")


    # ============================================================
    # MAIN CONTENT
    # ============================================================
    # Import halaman berdasarkan role
    if admin_mode:
        from pages.admin import dashboard as admin_dashboard
        from pages.admin import users as admin_users
        from pages.admin import departments as admin_departments
        from pages.admin import categories as admin_categories
        from pages.admin import audit_log as admin_audit_log

        if st.session_state.page == "dashboard":
            admin_dashboard.render(user)
        elif st.session_state.page == "all_docs":
            admin_dashboard.render_all_docs(user)
        elif st.session_state.page == "approvals":
            admin_dashboard.render_approvals(user)
        elif st.session_state.page == "users":
            admin_users.render(user)
        elif st.session_state.page == "departments":
            admin_departments.render(user)
        elif st.session_state.page == "categories":
            admin_categories.render(user)
        elif st.session_state.page == "audit_log":
            admin_audit_log.render(user)

    elif kabid_mode:
        from pages.user import dashboard as user_dashboard
        from pages.user import my_docs as user_my_docs
        from pages.user import approvals as user_approvals

        if st.session_state.page == "dashboard":
            user_dashboard.render(user)
        elif st.session_state.page == "dept_docs":
            user_dashboard.render_dept_docs(user)
        elif st.session_state.page == "approvals":
            user_approvals.render(user)
        elif st.session_state.page == "my_docs":
            user_my_docs.render(user)

    else:
        from pages.user import dashboard as user_dashboard
        from pages.user import my_docs as user_my_docs
        from pages.user import notifications as user_notifications

        if st.session_state.page == "dashboard":
            user_dashboard.render(user)
        elif st.session_state.page == "my_docs":
            user_my_docs.render(user)
        elif st.session_state.page == "notifications":
            user_notifications.render(user)