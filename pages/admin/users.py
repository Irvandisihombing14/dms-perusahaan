"""
Halaman Admin - Manajemen User
"""
import streamlit as st
import pandas as pd
from datetime import datetime

from database import (
    get_all_users, get_all_departments, update_user, delete_user,
    update_user_password, create_audit_log
)
from auth import hash_password
from config import ROLES, ROLE_LABELS
from utils import format_date, get_role_badge


def render(user):
    """Render halaman manajemen user"""
    st.title("👥 Manajemen User")
    st.markdown("### Kelola Akun PNS dan Kepala Bidang")

    # Tab untuk Tambah User dan Daftar User
    tab1, tab2 = st.tabs(["➕ Tambah User Baru", "📋 Daftar User"])

    # ==================== TAB TAMBAH USER ====================
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
                    new_dept = st.selectbox("🏢 Bidang",
                                           [(d[1], d[0]) for d in departments],
                                           format_func=lambda x: x[0])
                    new_role = st.selectbox("🎭 Role", ROLES,
                                           format_func=lambda x: ROLE_LABELS.get(x, x))

                submit_add = st.form_submit_button("➕ Buat User", type="primary",
                                                   use_container_width=True)

                if submit_add:
                    if not all([new_name, new_email, new_password]):
                        st.error("❌ Nama, email, dan password wajib diisi!")
                    elif len(new_password) < 6:
                        st.error("❌ Password minimal 6 karakter!")
                    else:
                        from database import create_user
                        password_hash = hash_password(new_password)
                        success, message = create_user(
                            new_email.lower().strip(),
                            password_hash,
                            new_name,
                            new_nip,
                            new_dept[1],
                            new_role
                        )

                        if success:
                            # Audit log
                            create_audit_log(
                                action="CREATE_USER",
                                document_id=None,
                                document_title=f"User: {new_name}",
                                user_email=user['email'],
                                user_name=user['full_name'],
                                user_role=user['role'],
                                action_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                details=f"Buat user baru: {new_email} ({new_role})",
                                department_id=user['department_id']
                            )
                            st.success(f"✅ {message}")
                            st.rerun()
                        else:
                            st.error(f"❌ {message}")

    # ==================== TAB DAFTAR USER ====================
    with tab2:
        st.subheader("Daftar Semua User")

        users = get_all_users()

        if users:
            # Search
            search_term = st.text_input("🔍 Cari User (nama/email/NIP)")

            df = pd.DataFrame(users, columns=[
                'ID', 'Email', 'Nama', 'NIP', 'Bidang', 'Role', 'Status', 'Dibuat'
            ])

            if search_term:
                df = df[
                    df['Nama'].str.contains(search_term, case=False, na=False) |
                    df['Email'].str.contains(search_term, case=False, na=False) |
                    df['NIP'].str.contains(search_term, case=False, na=False)
                ]

            # Tampilkan tabel
            display_df = df[['ID', 'Nama', 'NIP', 'Email', 'Bidang', 'Role', 'Status']].copy()
            display_df['Status'] = display_df['Status'].apply(
                lambda x: "✅ Aktif" if x == 1 else "❌ Nonaktif"
            )
            st.dataframe(display_df, use_container_width=True, hide_index=True, height=400)

            st.markdown("---")
            st.subheader("⚙️ Kelola User")

            # Pilih user untuk diedit
            user_options = {f"{row['Nama']} ({row['Email']})": row['ID']
                           for _, row in df.iterrows()}
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
                    edit_email_display = st.text_input("Email", value=user_info['Email'], disabled=True)
                    edit_dept = st.selectbox(
                        "Bidang",
                        options=[d[1] for d in departments],
                        index=[d[1] for d in departments].index(user_info['Bidang']) if user_info['Bidang'] in [d[1] for d in departments] else 0
                    )
                    edit_role = st.selectbox(
                        "Role",
                        ROLES,
                        index=ROLES.index(user_info['Role']),
                        format_func=lambda x: ROLE_LABELS.get(x, x)
                    )
                    edit_active = st.checkbox("Aktif", value=user_info['Status'] == 1)

                    submit_edit = st.form_submit_button("💾 Simpan Perubahan", type="primary")

                    if submit_edit:
                        dept_id = dept_dict.get(edit_dept)
                        update_user(
                            selected_user_id,
                            edit_name,
                            edit_nip,
                            dept_id,
                            edit_role,
                            1 if edit_active else 0
                        )

                        create_audit_log(
                            action="UPDATE_USER",
                            document_id=None,
                            document_title=f"User: {edit_name}",
                            user_email=user['email'],
                            user_name=user['full_name'],
                            user_role=user['role'],
                            action_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
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
                                action="RESET_PASSWORD",
                                document_id=None,
                                document_title=f"User: {user_info['Nama']}",
                                user_email=user['email'],
                                user_name=user['full_name'],
                                user_role=user['role'],
                                action_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
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
                        action="DELETE_USER",
                        document_id=None,
                        document_title=f"User: {user_info['Nama']}",
                        user_email=user['email'],
                        user_name=user['full_name'],
                        user_role=user['role'],
                        action_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        details=f"Hapus user: {user_info['Email']}",
                        department_id=user['department_id']
                    )

                    st.success("✅ User berhasil dihapus!")
                    st.rerun()
        else:
            st.info("Belum ada user terdaftar.")