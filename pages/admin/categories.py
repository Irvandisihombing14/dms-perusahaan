"""
Halaman Admin - Manajemen Kategori Dokumen
"""
import streamlit as st
import pandas as pd
from datetime import datetime

from database import (
    get_all_categories, create_category, update_category,
    delete_category, create_audit_log
)


def render(user):
    """Render halaman manajemen kategori"""
    st.title("📂 Manajemen Kategori Dokumen")
    st.markdown("### Kelola Kategori Dokumen Administrasi PNS")

    tab1, tab2 = st.tabs(["➕ Tambah Kategori", "📋 Daftar Kategori"])

    # ==================== TAB TAMBAH KATEGORI ====================
    with tab1:
        st.subheader("Tambah Kategori Baru")
        with st.form("add_cat_form"):
            cat_name = st.text_input("Nama Kategori",
                                    placeholder="Contoh: SK (Surat Keputusan)")
            cat_desc = st.text_area("Deskripsi (Opsional)", height=100)
            require_approval = st.checkbox(
                "⚠️ Kategori ini memerlukan approval Kepala Bidang",
                help="Jika dicentang, dokumen dengan kategori ini harus di-approve sebelum published"
            )
            submit_add = st.form_submit_button("➕ Tambah Kategori", type="primary",
                                               use_container_width=True)

            if submit_add:
                if not cat_name:
                    st.error("❌ Nama kategori harus diisi!")
                else:
                    success, message = create_category(
                        cat_name, cat_desc, 1 if require_approval else 0
                    )
                    if success:
                        create_audit_log(
                            action="CREATE_CATEGORY",
                            document_id=None,
                            document_title=f"Kategori: {cat_name}",
                            user_email=user['email'],
                            user_name=user['full_name'],
                            user_role=user['role'],
                            action_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            details=f"Buat kategori baru: {cat_name}",
                            department_id=user['department_id']
                        )
                        st.success(f"✅ {message}")
                        st.rerun()
                    else:
                        st.error(f"❌ {message}")

    # ==================== TAB DAFTAR KATEGORI ====================
    with tab2:
        st.subheader("Daftar Kategori")
        categories = get_all_categories()

        if categories:
            df = pd.DataFrame(categories, columns=['ID', 'Nama', 'Deskripsi', 'Perlu Approval', 'Dibuat'])

            display_df = df[['ID', 'Nama', 'Deskripsi', 'Perlu Approval']].copy()
            display_df['Perlu Approval'] = display_df['Perlu Approval'].apply(
                lambda x: "✅ Ya" if x == 1 else "❌ Tidak"
            )
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
                    edit_approval = st.checkbox("Perlu Approval",
                                               value=cat_info['Perlu Approval'] == 1)
                    submit_edit = st.form_submit_button("💾 Simpan", type="primary")

                    if submit_edit:
                        update_category(
                            selected_cat_id, edit_name, edit_desc,
                            1 if edit_approval else 0
                        )

                        create_audit_log(
                            action="UPDATE_CATEGORY",
                            document_id=None,
                            document_title=f"Kategori: {edit_name}",
                            user_email=user['email'],
                            user_name=user['full_name'],
                            user_role=user['role'],
                            action_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
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
                        action="DELETE_CATEGORY",
                        document_id=None,
                        document_title=f"Kategori: {cat_info['Nama']}",
                        user_email=user['email'],
                        user_name=user['full_name'],
                        user_role=user['role'],
                        action_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        details=f"Hapus kategori: {cat_info['Nama']}",
                        department_id=user['department_id']
                    )

                    st.success("✅ Kategori berhasil dihapus!")
                    st.rerun()
        else:
            st.info("Belum ada kategori terdaftar.")