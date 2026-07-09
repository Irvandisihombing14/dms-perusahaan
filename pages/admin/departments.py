"""
Halaman Admin - Manajemen Bidang/Departemen
"""
import streamlit as st
import pandas as pd
from datetime import datetime

from database import (
    get_all_departments, create_department, update_department,
    delete_department, get_users_by_department, create_audit_log
)


def render(user):
    """Render halaman manajemen departemen"""
    st.title("🏢 Manajemen Bidang/Departemen")
    st.markdown("### Kelola Struktur Organisasi")

    tab1, tab2 = st.tabs(["➕ Tambah Bidang", "📋 Daftar Bidang"])

    # ==================== TAB TAMBAH BIDANG ====================
    with tab1:
        st.subheader("Tambah Bidang Baru")
        with st.form("add_dept_form"):
            dept_name = st.text_input("Nama Bidang", placeholder="Contoh: Bidang Keuangan")
            dept_desc = st.text_area("Deskripsi (Opsional)", height=100)
            submit_add = st.form_submit_button("➕ Tambah Bidang", type="primary",
                                               use_container_width=True)

            if submit_add:
                if not dept_name:
                    st.error("❌ Nama bidang harus diisi!")
                else:
                    success, message = create_department(dept_name, dept_desc)
                    if success:
                        create_audit_log(
                            action="CREATE_DEPARTMENT",
                            document_id=None,
                            document_title=f"Bidang: {dept_name}",
                            user_email=user['email'],
                            user_name=user['full_name'],
                            user_role=user['role'],
                            action_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            details=f"Buat bidang baru: {dept_name}",
                            department_id=user['department_id']
                        )
                        st.success(f"✅ {message}")
                        st.rerun()
                    else:
                        st.error(f"❌ {message}")

    # ==================== TAB DAFTAR BIDANG ====================
    with tab2:
        st.subheader("Daftar Bidang")
        departments = get_all_departments()

        if departments:
            df = pd.DataFrame(departments, columns=['ID', 'Nama', 'Deskripsi', 'Dibuat'])

            # Hitung jumlah user per bidang
            user_counts = []
            for dept in departments:
                users = get_users_by_department(dept[0])
                user_counts.append(len(users))

            df['Jumlah User'] = user_counts

            display_df = df[['ID', 'Nama', 'Deskripsi', 'Jumlah User']].copy()
            display_df.columns = ['ID', '🏢 Nama Bidang', '📝 Deskripsi', '👥 Jumlah User']
            st.dataframe(display_df, use_container_width=True, hide_index=True)

            st.markdown("---")
            st.subheader("⚙️ Kelola Bidang")

            dept_options = {f"{row['Nama']} ({row['Jumlah User']} user)": row['ID']
                           for _, row in df.iterrows()}
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
                            action="UPDATE_DEPARTMENT",
                            document_id=None,
                            document_title=f"Bidang: {edit_name}",
                            user_email=user['email'],
                            user_name=user['full_name'],
                            user_role=user['role'],
                            action_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            details=f"Update bidang: {dept_info['Nama']} → {edit_name}",
                            department_id=user['department_id']
                        )

                        st.success("✅ Bidang berhasil diupdate!")
                        st.rerun()

            with col2:
                st.markdown("**🗑️ Hapus Bidang**")
                if dept_info['Jumlah User'] > 0:
                    st.warning(f"⚠️ Tidak bisa menghapus! Masih ada {dept_info['Jumlah User']} user di bidang ini.")
                else:
                    confirm_delete = st.checkbox("⚠️ Saya yakin ingin menghapus bidang ini")
                    if st.button("🗑️ Hapus Bidang", type="secondary", disabled=not confirm_delete):
                        delete_department(selected_dept_id)

                        create_audit_log(
                            action="DELETE_DEPARTMENT",
                            document_id=None,
                            document_title=f"Bidang: {dept_info['Nama']}",
                            user_email=user['email'],
                            user_name=user['full_name'],
                            user_role=user['role'],
                            action_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            details=f"Hapus bidang: {dept_info['Nama']}",
                            department_id=user['department_id']
                        )

                        st.success("✅ Bidang berhasil dihapus!")
                        st.rerun()
        else:
            st.info("Belum ada bidang terdaftar. Tambahkan bidang terlebih dahulu.")