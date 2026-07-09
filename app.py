"""
Aplikasi Utama - Sistem Manajemen Dokumen Online
"""
import streamlit as st
import pandas as pd
import os
from datetime import datetime

from config import DEPARTMENTS, UPLOAD_FOLDER, init_folders
from database import (
    init_db, create_document, get_all_documents,
    get_documents_by_department, get_document_by_id
)
from auth import register, login
from email_service import send_pdf_email

# --- INISIALISASI ---
init_folders()
init_db()

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="DMS Online - Sistem Manajemen Dokumen",
    page_icon="📂",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM CSS ---
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #FF4B4B;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# --- SESSION STATE ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_data = None


# ============================================================
# HALAMAN LOGIN / REGISTER
# ============================================================
if not st.session_state.logged_in:
    st.markdown('<h1 class="main-header">📂 DMS Online</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Sistem Manajemen Dokumen Antar Departemen</p>',
                unsafe_allow_html=True)

    col_left, col_center, col_right = st.columns([1, 2, 1])

    with col_center:
        tab1, tab2 = st.tabs(["🔐 Login", "📝 Registrasi"])

        # --- TAB LOGIN ---
        with tab1:
            with st.form("login_form"):
                st.subheader("Masuk ke Akun Anda")
                l_email = st.text_input("📧 Email", placeholder="nama@perusahaan.com")
                l_pass = st.text_input("🔑 Password", type="password")
                submit_login = st.form_submit_button("Login", type="primary",
                                                     use_container_width=True)

                if submit_login:
                    with st.spinner("Memproses login..."):
                        user_data, message = login(l_email, l_pass)
                        if user_data:
                            st.session_state.logged_in = True
                            st.session_state.user_data = user_data
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)

        # --- TAB REGISTER ---
        with tab2:
            with st.form("register_form"):
                st.subheader("Buat Akun Baru")
                r_name = st.text_input("👤 Nama Lengkap")
                r_email = st.text_input("📧 Email Aktif")
                r_pass = st.text_input("🔑 Password (min. 6 karakter)", type="password")
                r_dept = st.selectbox("🏢 Departemen", DEPARTMENTS)
                submit_register = st.form_submit_button("Daftar", type="primary",
                                                        use_container_width=True)

                if submit_register:
                    with st.spinner("Mendaftarkan akun..."):
                        success, message = register(r_email, r_pass, r_name, r_dept)
                        if success:
                            st.success(f"✅ {message} Silakan Login.")
                        else:
                            st.error(f"❌ {message}")


# ============================================================
# HALAMAN UTAMA (SETELAH LOGIN)
# ============================================================
else:
    user = st.session_state.user_data

    # --- SIDEBAR ---
    with st.sidebar:
        st.markdown("### 👤 Profil")
        st.success(f"**{user['full_name']}**")
        st.caption(f"📧 {user['email']}")
        st.caption(f"🏢 {user['department']}")

        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.user_data = None
            st.rerun()

        st.markdown("---")
        st.markdown("### 📤 Upload Dokumen")

        with st.form("upload_form", clear_on_submit=True):
            uploaded_file = st.file_uploader("Pilih File PDF", type=['pdf'])
            doc_title = st.text_input("Judul Dokumen",
                                      placeholder="Contoh: Laporan Q1 2026")
            send_email = st.checkbox("Kirim notifikasi via email", value=True)
            recipient_email = st.text_input(
                "Email Penerima",
                value=user['email'] if send_email else "",
                disabled=not send_email
            )

            submit_upload = st.form_submit_button(
                "📤 Upload & Kirim",
                type="primary",
                use_container_width=True
            )

            if submit_upload:
                if uploaded_file is None:
                    st.error("❌ Pilih file PDF terlebih dahulu!")
                elif not doc_title:
                    st.error("❌ Judul dokumen harus diisi!")
                else:
                    # Generate nama file unik
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    safe_filename = f"{timestamp}_{uploaded_file.name}"
                    filepath = os.path.join(UPLOAD_FOLDER, safe_filename)

                    # Simpan file fisik
                    with open(filepath, "wb") as f:
                        f.write(uploaded_file.getbuffer())

                    # Simpan ke database
                    doc_id = create_document(
                        title=doc_title,
                        original_filename=uploaded_file.name,
                        filepath=filepath,
                        department=user['department'],
                        uploaded_by_email=user['email'],
                        uploaded_by_name=user['full_name'],
                        upload_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        file_size=uploaded_file.size
                    )

                    st.success(f"✅ Dokumen berhasil diupload! (ID: {doc_id})")

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

    # --- MAIN CONTENT ---
    st.title(f"📂 Arsip Dokumen - {user['department']}")

    # Metrics
    all_docs = get_all_documents()
    dept_docs = get_documents_by_department(user['department'])

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📊 Total Dokumen", len(all_docs))
    with col2:
        st.metric("🏢 Dokumen Dept Anda", len(dept_docs))
    with col3:
        total_size = sum(doc[8] for doc in all_docs if doc[8]) / (1024 * 1024)
        st.metric("💾 Total Ukuran", f"{total_size:.2f} MB")
    with col4:
        today = datetime.now().strftime("%Y-%m-%d")
        today_docs = [d for d in all_docs if d[7].startswith(today)]
        st.metric("📅 Upload Hari Ini", len(today_docs))

    st.markdown("---")

    # --- FILTER & SEARCH ---
    col_filter1, col_filter2, col_filter3 = st.columns([2, 2, 1])

    with col_filter1:
        if user['department'] == 'IT':  # Admin bisa lihat semua
            depts = ["Semua"] + list(set([d[4] for d in all_docs]))
            selected_dept = st.selectbox("🏢 Filter Departemen", depts)
        else:
            selected_dept = user['department']
            st.text_input("🏢 Departemen", value=user['department'], disabled=True)

    with col_filter2:
        search_term = st.text_input("🔍 Cari Dokumen",
                                    placeholder="Ketik judul dokumen...")

    with col_filter3:
        sort_order = st.radio("⬆️⬇️ Urutan",
                              ["Terbaru", "Terlama"],
                              horizontal=True)

    # --- DATA PROCESSING ---
    df = pd.DataFrame(all_docs, columns=[
        'ID', 'Judul', 'Nama File Asli', 'Path', 'Departemen',
        'Email Pengunggah', 'Nama Pengunggah', 'Tanggal Upload', 'Ukuran'
    ])

    if not df.empty:
        # Filter
        filtered = df.copy()
        if selected_dept != "Semua":
            filtered = filtered[filtered['Departemen'] == selected_dept]
        if search_term:
            filtered = filtered[
                filtered['Judul'].str.contains(search_term, case=False, na=False) |
                filtered['Nama File Asli'].str.contains(search_term, case=False, na=False)
            ]

        # Sort
        filtered = filtered.sort_values(
            'Tanggal Upload',
            ascending=(sort_order == "Terlama")
        )

        # Display
        if not filtered.empty:
            display_df = filtered[['ID', 'Judul', 'Departemen', 'Nama Pengunggah',
                                   'Tanggal Upload', 'Ukuran']].copy()
            display_df['Ukuran'] = display_df['Ukuran'].apply(
                lambda x: f"{x / 1024:.1f} KB" if x else "-"
            )
            display_df.columns = ['ID', '📄 Judul', '🏢 Dept', '👤 Pengunggah',
                                  '📅 Tanggal', '💾 Ukuran']

            st.dataframe(
                display_df,
                use_container_width=True,
                hide_index=True,
                height=400
            )

            # Download Section
            st.markdown("---")
            st.subheader("📥 Download Dokumen")

            col_dl1, col_dl2 = st.columns([2, 1])
            with col_dl1:
                doc_options = {f"{row['ID']} - {row['Judul']}": row['ID']
                               for _, row in filtered.iterrows()}
                selected_doc = st.selectbox(
                    "Pilih Dokumen",
                    options=list(doc_options.keys())
                )

            with col_dl2:
                st.write("")
                st.write("")
                if st.button("🔄 Muat File", type="secondary",
                             use_container_width=True):
                    st.session_state['selected_doc_id'] = doc_options[selected_doc]
                    st.rerun()

            # Tampilkan tombol download jika file sudah dimuat
            if 'selected_doc_id' in st.session_state:
                doc_id = st.session_state['selected_doc_id']
                doc_info = get_document_by_id(doc_id)

                if doc_info and os.path.exists(doc_info[3]):
                    with open(doc_info[3], "rb") as file:
                        st.download_button(
                            label=f"📥 Download: {doc_info[2]}",
                            data=file.read(),
                            file_name=doc_info[2],
                            mime="application/pdf",
                            type="primary",
                            use_container_width=True
                        )
                else:
                    st.error("❌ File tidak ditemukan di server!")
        else:
            st.info("ℹ️ Tidak ada dokumen yang sesuai dengan filter.")
    else:
        st.info("📭 Belum ada dokumen yang terupload. Mulai upload dokumen pertama Anda!")