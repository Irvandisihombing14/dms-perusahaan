import streamlit as st
import sqlite3
import pandas as pd
import hashlib
import secrets
import smtplib
import os
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

# ============================================================
# KONFIGURASI
# ============================================================
DB_NAME = "dms_pns.db"
UPLOAD_FOLDER = "uploaded_files"
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

STATUS_DRAFT = "draft"
STATUS_PENDING = "pending_approval"
STATUS_APPROVED = "approved"
STATUS_REJECTED = "rejected"
STATUS_LABELS = {
    STATUS_DRAFT: "📝 Draft",
    STATUS_PENDING: "⏳ Menunggu Approval",
    STATUS_APPROVED: "✅ Disetujui",
    STATUS_REJECTED: "❌ Ditolak"
}

# ============================================================
# DATABASE
# ============================================================
def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS departments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        description TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        full_name TEXT NOT NULL,
        nip TEXT,
        department_id INTEGER,
        role TEXT DEFAULT 'pns',
        is_active INTEGER DEFAULT 1,
        FOREIGN KEY (department_id) REFERENCES departments(id)
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        description TEXT,
        require_approval INTEGER DEFAULT 0
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        original_filename TEXT NOT NULL,
        filepath TEXT NOT NULL,
        department_id INTEGER NOT NULL,
        category_id INTEGER,
        status TEXT DEFAULT 'draft',
        tags TEXT,
        description TEXT,
        expiry_date TEXT,
        uploaded_by_email TEXT NOT NULL,
        uploaded_by_name TEXT NOT NULL,
        upload_date TEXT NOT NULL,
        updated_at TEXT,
        approved_by TEXT,
        approved_at TEXT,
        rejection_reason TEXT,
        file_size INTEGER DEFAULT 0
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_email TEXT NOT NULL,
        title TEXT NOT NULL,
        message TEXT NOT NULL,
        is_read INTEGER DEFAULT 0,
        created_at TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        action TEXT NOT NULL,
        document_id INTEGER,
        document_title TEXT,
        user_email TEXT NOT NULL,
        user_name TEXT NOT NULL,
        user_role TEXT,
        action_date TEXT NOT NULL,
        details TEXT,
        department_id INTEGER
    )""")
    conn.commit()
    conn.close()

# ============================================================
# AUTH
# ============================================================
def hash_password(password):
    salt = secrets.token_hex(16)
    hash_val = hashlib.sha256((salt + password).encode()).hexdigest()
    return f"{salt}${hash_val}"

def verify_password(password, stored):
    try:
        salt, hash_val = stored.split('$')
        return hashlib.sha256((salt + password).encode()).hexdigest() == hash_val
    except Exception:
        return False

# ============================================================
# EMAIL
# ============================================================
def send_email_with_pdf(recipient, filepath, filename, uploader, title):
    try:
        sender = st.secrets["SENDER_EMAIL"]
        password = st.secrets["SENDER_PASSWORD"]
        app_name = st.secrets.get("APP_NAME", "DMS PNS")
        
        msg = MIMEMultipart()
        msg['From'] = sender
        msg['To'] = recipient
        msg['Subject'] = f"📄 Dokumen Baru: {title}"
        
        html = f"""<html><body style="font-family: Arial;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 8px;">
            <h2 style="color: #1e3a8a;">🏛️ {app_name}</h2>
            <hr>
            <p>Halo,</p>
            <p>Dokumen baru telah diunggah:</p>
            <table style="width: 100%; border-collapse: collapse;">
                <tr><td style="padding: 8px; background: #f9f9f9; font-weight: bold;">Judul:</td><td style="padding: 8px;">{title}</td></tr>
                <tr><td style="padding: 8px; background: #f9f9f9; font-weight: bold;">File:</td><td style="padding: 8px;">{filename}</td></tr>
                <tr><td style="padding: 8px; background: #f9f9f9; font-weight: bold;">Pengunggah:</td><td style="padding: 8px;">{uploader}</td></tr>
            </table>
            <p><strong>📎 Dokumen terlampir.</strong></p>
        </div></body></html>"""
        
        msg.attach(MIMEText(html, 'html'))
        
        with open(filepath, "rb") as f:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(f.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f'attachment; filename="{filename}"')
        msg.attach(part)
        
        server = smtplib.SMTP(st.secrets["SMTP_SERVER"], int(st.secrets["SMTP_PORT"]))
        server.starttls()
        server.login(sender, password)
        server.send_message(msg)
        server.quit()
        return True, "Email berhasil dikirim!"
    except Exception as e:
        return False, f"Error: {str(e)}"

def send_approval_email(recipient, title, status, approver, reason=""):
    try:
        sender = st.secrets["SENDER_EMAIL"]
        password = st.secrets["SENDER_PASSWORD"]
        app_name = st.secrets.get("APP_NAME", "DMS PNS")
        
        msg = MIMEMultipart()
        msg['From'] = sender
        msg['To'] = recipient
        if status == "approved":
            msg['Subject'] = f"✅ Dokumen Disetujui: {title}"
            color = "#28a745"
            msg_text = f"Dokumen <strong>{title}</strong> telah <strong>disetujui</strong> oleh {approver}."
        else:
            msg['Subject'] = f"❌ Dokumen Ditolak: {title}"
            color = "#dc3545"
            msg_text = f"Dokumen <strong>{title}</strong> telah <strong>ditolak</strong> oleh {approver}.<br><strong>Alasan:</strong> {reason}"
        
        html = f"""<html><body style="font-family: Arial;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 8px;">
            <h2 style="color: {color};">{msg['Subject']}</h2>
            <hr>
            <p>Halo,</p>
            <p>{msg_text}</p>
        </div></body></html>"""
        
        msg.attach(MIMEText(html, 'html'))
        
        server = smtplib.SMTP(st.secrets["SMTP_SERVER"], int(st.secrets["SMTP_PORT"]))
        server.starttls()
        server.login(sender, password)
        server.send_message(msg)
        server.quit()
        return True, "Notifikasi terkirim!"
    except Exception as e:
        return False, f"Error: {str(e)}"

# ============================================================
# HELPER
# ============================================================
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
# INIT
# ============================================================
init_db()
st.set_page_config(page_title="DMS Administrasi PNS", page_icon="🏛️", layout="wide")

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user = None
    st.session_state.page = "dashboard"

# ============================================================
# LOGIN PAGE
# ============================================================
if not st.session_state.logged_in:
    st.title("🏛️ DMS Administrasi PNS")
    st.markdown("### Sistem Manajemen Dokumen Pegawai Negeri Sipil")
    
    tab1, tab2 = st.tabs(["🔐 Login", "📝 Registrasi"])
    
    with tab1:
        with st.form("login_form"):
            email = st.text_input("📧 Email")
            password = st.text_input("🔑 Password", type="password")
            if st.form_submit_button("Login", type="primary", use_container_width=True):
                conn = get_db()
                user = conn.execute("""
                    SELECT u.*, d.name as dept_name 
                    FROM users u 
                    LEFT JOIN departments d ON u.department_id = d.id 
                    WHERE u.email=?
                """, (email.lower(),)).fetchone()
                conn.close()
                
                if user and verify_password(password, user[2]) and user[7] == 1:
                    st.session_state.logged_in = True
                    st.session_state.user = {
                        'id': user[0],
                        'email': user[1],
                        'full_name': user[3],
                        'nip': user[4],
                        'department_id': user[5],
                        'role': user[6],
                        'department_name': user[9] if user[9] else "Belum diatur"
                    }
                    st.success("✅ Login berhasil!")
                    st.rerun()
                else:
                    st.error("❌ Login gagal! Periksa email/password.")
    
    with tab2:
        conn = get_db()
        depts = conn.execute("SELECT * FROM departments").fetchall()
        conn.close()
        
        if not depts:
            st.warning("⚠️ Belum ada departemen. Hubungi admin.")
        else:
            with st.form("register_form"):
                r_name = st.text_input("👤 Nama Lengkap")
                r_nip = st.text_input("🆔 NIP")
                r_email = st.text_input("📧 Email")
                r_pass = st.text_input("🔑 Password (min 6 karakter)", type="password")
                r_dept = st.selectbox("🏢 Bidang", [(d[1], d[0]) for d in depts], format_func=lambda x: x[0])
                
                if st.form_submit_button("Daftar", type="primary", use_container_width=True):
                    if len(r_pass) < 6:
                        st.error("❌ Password minimal 6 karakter!")
                    elif not r_name or not r_email:
                        st.error("❌ Nama dan email wajib diisi!")
                    else:
                        conn = get_db()
                        try:
                            conn.execute("""INSERT INTO users 
                                (email, password_hash, full_name, nip, department_id) 
                                VALUES (?,?,?,?,?)""",
                                (r_email.lower(), hash_password(r_pass), r_name, r_nip, r_dept[1]))
                            conn.commit()
                            st.success("✅ Registrasi berhasil! Silakan login.")
                        except sqlite3.IntegrityError:
                            st.error("❌ Email sudah terdaftar!")
                        finally:
                            conn.close()

# ============================================================
# MAIN APP
# ============================================================
else:
    user = st.session_state.user
    admin_mode = user['role'] == 'admin'
    kabid_mode = user['role'] == 'kepala_bidang'
    
    # SIDEBAR
    with st.sidebar:
        st.success(f"**{user['full_name']}**")
        st.caption(f"📧 {user['email']}")
        st.caption(f"🆔 NIP: {user['nip'] or '-'}")
        st.caption(f"🏢 {user['department_name']}")
        st.caption(f"🎭 {user['role'].upper()}")
        
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.user = None
            st.session_state.page = "dashboard"
            st.rerun()
        
        st.markdown("---")
        st.markdown("### 📋 Menu")
        
        if st.button("📊 Dashboard", use_container_width=True):
            st.session_state.page = "dashboard"; st.rerun()
        if st.button("📄 Dokumen Saya", use_container_width=True):
            st.session_state.page = "my_docs"; st.rerun()
        if admin_mode or kabid_mode:
            if st.button("⏳ Approval", use_container_width=True):
                st.session_state.page = "approvals"; st.rerun()
        if admin_mode:
            if st.button("📁 Semua Dokumen", use_container_width=True):
                st.session_state.page = "all_docs"; st.rerun()
            if st.button("👥 Manajemen User", use_container_width=True):
                st.session_state.page = "users"; st.rerun()
            if st.button("🏢 Bidang", use_container_width=True):
                st.session_state.page = "departments"; st.rerun()
            if st.button("📂 Kategori", use_container_width=True):
                st.session_state.page = "categories"; st.rerun()
            if st.button("📜 Audit Log", use_container_width=True):
                st.session_state.page = "audit"; st.rerun()
        
        st.markdown("---")
        st.markdown("### 📤 Upload Dokumen")
        
        conn = get_db()
        categories = conn.execute("SELECT * FROM categories").fetchall()
        conn.close()
        
        if not categories:
            st.warning("⚠️ Belum ada kategori. Admin perlu tambah kategori.")
        else:
            with st.form("upload_form", clear_on_submit=True):
                uploaded_file = st.file_uploader("File PDF", type=['pdf'])
                doc_title = st.text_input("Judul")
                doc_desc = st.text_area("Deskripsi (opsional)", height=80)
                doc_cat = st.selectbox("Kategori", [(c[1], c[0]) for c in categories], format_func=lambda x: x[0])
                doc_tags = st.text_input("Tag (opsional)")
                send_email_chk = st.checkbox("Kirim email", value=True)
                recipient = st.text_input("Email penerima", value=user['email'] if send_email_chk else "", disabled=not send_email_chk)
                
                if st.form_submit_button("📤 Upload", type="primary", use_container_width=True):
                    if not uploaded_file:
                        st.error("❌ Pilih file PDF!")
                    elif not doc_title:
                        st.error("❌ Judul wajib diisi!")
                    else:
                        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
                        fname = f"{ts}_{uploaded_file.name}"
                        fpath = os.path.join(UPLOAD_FOLDER, fname)
                        with open(fpath, "wb") as f:
                            f.write(uploaded_file.getbuffer())
                        
                        cat_info = next((c for c in categories if c[0] == doc_cat[1]), None)
                        status = STATUS_PENDING if (cat_info and cat_info[3] == 1) else STATUS_DRAFT
                        
                        conn = get_db()
                        c = conn.cursor()
                        c.execute("""INSERT INTO documents 
                            (title, original_filename, filepath, department_id, category_id, 
                             status, tags, description, uploaded_by_email, uploaded_by_name, 
                             upload_date, file_size) 
                            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                            (doc_title, uploaded_file.name, fpath, user['department_id'], 
                             doc_cat[1], status, doc_tags, doc_desc, user['email'], 
                             user['full_name'], datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
                             uploaded_file.size))
                        doc_id = c.lastrowid
                        
                        c.execute("""INSERT INTO audit_logs 
                            (action, document_id, document_title, user_email, user_name, 
                             user_role, action_date, details, department_id) 
                            VALUES (?,?,?,?,?,?,?,?,?)""",
                            ("CREATE", doc_id, doc_title, user['email'], user['full_name'],
                             user['role'], datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                             f"Upload: {uploaded_file.name}", user['department_id']))
                        conn.commit()
                        conn.close()
                        
                        st.success(f"✅ Upload berhasil! (ID: {doc_id})")
                        
                        if status == STATUS_PENDING:
                            conn = get_db()
                            approvers = conn.execute("""SELECT * FROM users 
                                WHERE department_id=? AND role='kepala_bidang' AND is_active=1""",
                                (user['department_id'],)).fetchall()
                            for app in approvers:
                                conn.execute("""INSERT INTO notifications 
                                    (user_email, title, message, created_at) VALUES (?,?,?,?)""",
                                    (app[1], "📋 Dokumen Perlu Approval",
                                     f"{user['full_name']} mengupload '{doc_title}'",
                                     datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                            conn.commit()
                            conn.close()
                        
                        if send_email_chk and recipient:
                            ok, msg = send_email_with_pdf(recipient, fpath, uploaded_file.name, user['full_name'], doc_title)
                            if ok:
                                st.success(f"📧 {msg}")
                            else:
                                st.warning(f"⚠️ {msg}")
    
    # ============================================================
    # PAGE: DASHBOARD
    # ============================================================
    if st.session_state.page == "dashboard":
        st.title(f"📊 Dashboard - {user['full_name']}")
        
        conn = get_db()
        my_docs = conn.execute("SELECT * FROM documents WHERE uploaded_by_email=? ORDER BY upload_date DESC", (user['email'],)).fetchall()
        total_size = sum(d[17] for d in my_docs if d[17]) / (1024*1024)
        
        col1, col2, col3 = st.columns(3)
        with col1: st.metric("📄 Dokumen Saya", len(my_docs))
        with col2: st.metric("💾 Total Ukuran", f"{total_size:.2f} MB")
        with col3:
            pending = len([d for d in my_docs if d[6] == STATUS_PENDING])
            st.metric("⏳ Menunggu Approval", pending)
        
        if my_docs:
            st.subheader("📄 Dokumen Terbaru")
            df = pd.DataFrame(my_docs[:10], columns=[
                'ID', 'Judul', 'File', 'Path', 'DeptID', 'CatID', 'Status', 'Tags',
                'Desc', 'Expiry', 'Email', 'Nama', 'Tanggal', 'Updated', 'AppBy',
                'AppAt', 'Reject', 'Size', 'DeptName', 'CatName'
            ])
            display = df[['Judul', 'Status', 'Tanggal', 'Size']].copy()
            display['Status'] = display['Status'].map(STATUS_LABELS)
            display['Size'] = display['Size'].apply(format_size)
            st.dataframe(display, use_container_width=True, hide_index=True)
        else:
            st.info("Belum ada dokumen. Upload dokumen pertama Anda!")
    
    # ============================================================
    # PAGE: DOKUMEN SAYA
    # ============================================================
    elif st.session_state.page == "my_docs":
        st.title("📄 Dokumen Saya")
        
        conn = get_db()
        my_docs = conn.execute("""SELECT d.*, c.name as cat_name 
            FROM documents d LEFT JOIN categories c ON d.category_id = c.id 
            WHERE d.uploaded_by_email=? ORDER BY d.upload_date DESC""", (user['email'],)).fetchall()
        conn.close()
        
        if my_docs:
            search = st.text_input("🔍 Cari")
            df = pd.DataFrame(my_docs, columns=[
                'ID', 'Judul', 'File', 'Path', 'DeptID', 'CatID', 'Status', 'Tags',
                'Desc', 'Expiry', 'Email', 'Nama', 'Tanggal', 'Updated', 'AppBy',
                'AppAt', 'Reject', 'Size', 'DeptName', 'CatName'
            ])
            
            if search:
                df = df[df['Judul'].str.contains(search, case=False, na=False) |
                        df['Tags'].str.contains(search, case=False, na=False)]
            
            display = df[['ID', 'Judul', 'CatName', 'Status', 'Tanggal', 'Size']].copy()
            display['Status'] = display['Status'].map(STATUS_LABELS)
            display['Size'] = display['Size'].apply(format_size)
            display.columns = ['ID', '📄 Judul', '📂 Kategori', '📊 Status', '📅 Tanggal', '💾 Ukuran']
            st.dataframe(display, use_container_width=True, hide_index=True, height=400)
            
            st.markdown("---")
            st.subheader("⚙️ Kelola Dokumen")
            
            doc_opts = {f"{r['ID']} - {r['📄 Judul']}": r['ID'] for _, r in display.iterrows()}
            if doc_opts:
                sel_label = st.selectbox("Pilih Dokumen", list(doc_opts.keys()))
                sel_id = doc_opts[sel_label]
                doc = next(d for d in my_docs if d[0] == sel_id)
                
                st.markdown(f"""
                **Judul:** {doc[1]}  
                **Kategori:** {doc[19] or '-'}  
                **Status:** {STATUS_LABELS.get(doc[6], doc[6])}  
                **Tanggal:** {format_date(doc[12])}  
                **Ukuran:** {format_size(doc[17])}
                """)
                
                if doc[16]:
                    st.error(f"❌ **Alasan Penolakan:** {doc[16]}")
                
                st.markdown("---")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if doc[6] in [STATUS_DRAFT, STATUS_REJECTED]:
                        st.markdown("**✏️ Edit Judul**")
                        new_title = st.text_input("Judul Baru", value=doc[1])
                        if st.button("💾 Simpan", type="primary", use_container_width=True):
                            if new_title and new_title != doc[1]:
                                conn = get_db()
                                conn.execute("UPDATE documents SET title=?, updated_at=? WHERE id=?",
                                    (new_title, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), sel_id))
                                conn.commit()
                                conn.close()
                                st.success("✅ Judul diupdate!")
                                st.rerun()
                    else:
                        st.info("ℹ️ Edit hanya untuk Draft/Rejected")
                
                with col2:
                    if doc[6] in [STATUS_DRAFT, STATUS_REJECTED]:
                        st.markdown("**📤 Submit Approval**")
                        if st.button("📤 Submit", type="secondary", use_container_width=True):
                            conn = get_db()
                            conn.execute("UPDATE documents SET status=?, updated_at=? WHERE id=?",
                                (STATUS_PENDING, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), sel_id))
                            
                            approvers = conn.execute("""SELECT * FROM users 
                                WHERE department_id=? AND role='kepala_bidang' AND is_active=1""",
                                (user['department_id'],)).fetchall()
                            for app in approvers:
                                conn.execute("""INSERT INTO notifications 
                                    (user_email, title, message, created_at) VALUES (?,?,?,?)""",
                                    (app[1], "📋 Dokumen Perlu Approval",
                                     f"{user['full_name']} mensubmit '{doc[1]}'",
                                     datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                            conn.commit()
                            conn.close()
                            st.success("✅ Disubmit untuk approval!")
                            st.rerun()
                    elif doc[6] == STATUS_PENDING:
                        st.info("⏳ Menunggu approval")
                    elif doc[6] == STATUS_APPROVED:
                        st.success(f"✅ Disetujui {format_date(doc[15])}")
                
                with col3:
                    st.markdown("**📥 Download**")
                    if os.path.exists(doc[3]):
                        with open(doc[3], "rb") as f:
                            st.download_button("📥 Download PDF", data=f.read(),
                                file_name=doc[2], mime="application/pdf",
                                type="primary", use_container_width=True)
                    else:
                        st.error("❌ File tidak ditemukan!")
                
                st.markdown("---")
                if doc[6] in [STATUS_DRAFT, STATUS_REJECTED]:
                    st.markdown("**🗑️ Hapus Dokumen**")
                    confirm = st.checkbox("⚠️ Saya yakin ingin menghapus")
                    if st.button("🗑️ Hapus", disabled=not confirm, type="secondary"):
                        if os.path.exists(doc[3]):
                            os.remove(doc[3])
                        conn = get_db()
                        conn.execute("DELETE FROM documents WHERE id=?", (sel_id,))
                        conn.execute("""INSERT INTO audit_logs 
                            (action, document_id, document_title, user_email, user_name, 
                             user_role, action_date, details, department_id) 
                            VALUES (?,?,?,?,?,?,?,?,?)""",
                            ("DELETE", sel_id, doc[1], user['email'], user['full_name'],
                             user['role'], datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                             f"Hapus: {doc[2]}", user['department_id']))
                        conn.commit()
                        conn.close()
                        st.success("✅ Dokumen dihapus!")
                        st.rerun()
        else:
            st.info("📭 Belum ada dokumen.")
    
    # ============================================================
    # PAGE: APPROVAL
    # ============================================================
    elif st.session_state.page == "approvals":
        st.title("⏳ Approval Dokumen")
        
        conn = get_db()
        if admin_mode:
            pending = conn.execute("""SELECT d.*, c.name as cat_name 
                FROM documents d LEFT JOIN categories c ON d.category_id = c.id 
                WHERE d.status=?""", (STATUS_PENDING,)).fetchall()
        else:
            pending = conn.execute("""SELECT d.*, c.name as cat_name 
                FROM documents d LEFT JOIN categories c ON d.category_id = c.id 
                WHERE d.status=? AND d.department_id=?""",
                (STATUS_PENDING, user['department_id'])).fetchall()
        conn.close()
        
        if pending:
            st.info(f"📊 Ada **{len(pending)}** dokumen menunggu approval")
            
            for doc in pending:
                with st.expander(f"📄 {doc[1]} - oleh {doc[11]}"):
                    col1, col2 = st.columns([2, 1])
                    with col1:
                        st.markdown(f"""
                        **Judul:** {doc[1]}  
                        **Kategori:** {doc[19] or '-'}  
                        **Pengunggah:** {doc[11]} ({doc[10]})  
                        **Tanggal:** {format_date(doc[12])}  
                        **Ukuran:** {format_size(doc[17])}
                        """)
                        if doc[8]:
                            st.markdown(f"**Deskripsi:** {doc[8]}")
                    
                    with col2:
                        if os.path.exists(doc[3]):
                            with open(doc[3], "rb") as f:
                                st.download_button("📥 Download", data=f.read(),
                                    file_name=doc[2], mime="application/pdf",
                                    use_container_width=True)
                    
                    st.markdown("---")
                    col_a1, col_a2 = st.columns(2)
                    
                    with col_a1:
                        if st.button("✅ Approve", key=f"app_{doc[0]}", type="primary", use_container_width=True):
                            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            conn = get_db()
                            conn.execute("""UPDATE documents 
                                SET status=?, approved_by=?, approved_at=?, updated_at=? 
                                WHERE id=?""", (STATUS_APPROVED, user['email'], now, now, doc[0]))
                            conn.execute("""INSERT INTO audit_logs 
                                (action, document_id, document_title, user_email, user_name, 
                                 user_role, action_date, details, department_id) 
                                VALUES (?,?,?,?,?,?,?,?,?)""",
                                ("APPROVE", doc[0], doc[1], user['email'], user['full_name'],
                                 user['role'], now, f"Approve oleh {user['full_name']}",
                                 user['department_id']))
                            conn.execute("""INSERT INTO notifications 
                                (user_email, title, message, created_at) VALUES (?,?,?,?)""",
                                (doc[10], "✅ Dokumen Disetujui",
                                 f"'{doc[1]}' disetujui oleh {user['full_name']}", now))
                            conn.commit()
                            conn.close()
                            
                            send_approval_email(doc[10], doc[1], "approved", user['full_name'])
                            st.success("✅ Approved!")
                            st.rerun()
                    
                    with col_a2:
                        reason = st.text_input("Alasan tolak", key=f"rej_{doc[0]}")
                        if st.button("❌ Reject", key=f"rej_btn_{doc[0]}", use_container_width=True):
                            if reason:
                                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                conn = get_db()
                                conn.execute("""UPDATE documents 
                                    SET status=?, approved_by=?, rejection_reason=?, updated_at=? 
                                    WHERE id=?""",
                                    (STATUS_REJECTED, user['email'], reason, now, doc[0]))
                                conn.execute("""INSERT INTO audit_logs 
                                    (action, document_id, document_title, user_email, user_name, 
                                     user_role, action_date, details, department_id) 
                                    VALUES (?,?,?,?,?,?,?,?,?)""",
                                    ("REJECT", doc[0], doc[1], user['email'], user['full_name'],
                                     user['role'], now, f"Reject: {reason}",
                                     user['department_id']))
                                conn.execute("""INSERT INTO notifications 
                                    (user_email, title, message, created_at) VALUES (?,?,?,?)""",
                                    (doc[10], "❌ Dokumen Ditolak",
                                     f"'{doc[1]}' ditolak. Alasan: {reason}", now))
                                conn.commit()
                                conn.close()
                                
                                send_approval_email(doc[10], doc[1], "rejected", user['full_name'], reason)
                                st.success("❌ Rejected!")
                                st.rerun()
                            else:
                                st.warning("⚠️ Alasan wajib diisi!")
        else:
            st.success("✅ Tidak ada dokumen pending.")
    
    # ============================================================
    # PAGE: SEMUA DOKUMEN (ADMIN)
    # ============================================================
    elif st.session_state.page == "all_docs":
        st.title("📁 Semua Dokumen")
        
        conn = get_db()
        docs = conn.execute("""SELECT d.*, c.name as cat_name, dep.name as dept_name 
            FROM documents d 
            LEFT JOIN categories c ON d.category_id = c.id 
            LEFT JOIN departments dep ON d.department_id = dep.id 
            ORDER BY d.upload_date DESC""").fetchall()
        conn.close()
        
        if docs:
            search = st.text_input("🔍 Cari")
            df = pd.DataFrame(docs, columns=[
                'ID', 'Judul', 'File', 'Path', 'DeptID', 'CatID', 'Status', 'Tags',
                'Desc', 'Expiry', 'Email', 'Nama', 'Tanggal', 'Updated', 'AppBy',
                'AppAt', 'Reject', 'Size', 'CatName', 'DeptName'
            ])
            
            if search:
                df = df[df['Judul'].str.contains(search, case=False, na=False) |
                        df['DeptName'].str.contains(search, case=False, na=False)]
            
            display = df[['ID', 'Judul', 'DeptName', 'CatName', 'Status', 'Nama', 'Tanggal']].copy()
            display['Status'] = display['Status'].map(STATUS_LABELS)
            display.columns = ['ID', '📄 Judul', '🏢 Bidang', '📂 Kategori', '📊 Status', '👤 Upload', '📅 Tanggal']
            st.dataframe(display, use_container_width=True, hide_index=True, height=500)
            
            st.markdown("---")
            st.subheader("📥 Download Dokumen")
            doc_opts = {f"{r['ID']} - {r['📄 Judul']}": r['ID'] for _, r in display.iterrows()}
            if doc_opts:
                sel = st.selectbox("Pilih", list(doc_opts.keys()))
                doc_id = doc_opts[sel]
                doc_info = next(d for d in docs if d[0] == doc_id)
                if os.path.exists(doc_info[3]):
                    with open(doc_info[3], "rb") as f:
                        st.download_button("📥 Download PDF", data=f.read(),
                            file_name=doc_info[2], mime="application/pdf")
        else:
            st.info("Belum ada dokumen.")
    
    # ============================================================
    # PAGE: USER MANAGEMENT
    # ============================================================
    elif st.session_state.page == "users":
        st.title("👥 Manajemen User")
        
        tab1, tab2 = st.tabs(["➕ Tambah User", "📋 Daftar User"])
        
        with tab1:
            conn = get_db()
            depts = conn.execute("SELECT * FROM departments").fetchall()
            conn.close()
            
            if not depts:
                st.warning("⚠️ Tambah bidang dulu.")
            else:
                with st.form("add_user"):
                    c1, c2 = st.columns(2)
                    with c1:
                        n_name = st.text_input("Nama")
                        n_nip = st.text_input("NIP")
                        n_email = st.text_input("Email")
                    with c2:
                        n_pass = st.text_input("Password (min 6)", type="password")
                        n_dept = st.selectbox("Bidang", [(d[1], d[0]) for d in depts], format_func=lambda x: x[0])
                        n_role = st.selectbox("Role", ['pns', 'kepala_bidang', 'admin'])
                    
                    if st.form_submit_button("➕ Buat User", type="primary"):
                        if not all([n_name, n_email, n_pass]):
                            st.error("❌ Nama, email, password wajib!")
                        elif len(n_pass) < 6:
                            st.error("❌ Password min 6 karakter!")
                        else:
                            conn = get_db()
                            try:
                                conn.execute("""INSERT INTO users 
                                    (email, password_hash, full_name, nip, department_id, role) 
                                    VALUES (?,?,?,?,?,?)""",
                                    (n_email.lower(), hash_password(n_pass), n_name, n_nip, n_dept[1], n_role))
                                conn.commit()
                                st.success("✅ User dibuat!")
                                st.rerun()
                            except sqlite3.IntegrityError:
                                st.error("❌ Email sudah terdaftar!")
                            finally:
                                conn.close()
        
        with tab2:
            conn = get_db()
            users = conn.execute("""SELECT u.*, d.name as dept_name 
                FROM users u LEFT JOIN departments d ON u.department_id = d.id 
                ORDER BY u.rowid DESC""").fetchall()
            depts = conn.execute("SELECT * FROM departments").fetchall()
            conn.close()
            
            if users:
                df = pd.DataFrame(users, columns=[
                    'ID', 'Email', 'PassHash', 'Nama', 'NIP', 'DeptID', 'Role', 'Active', 'DeptName'
                ])
                display = df[['ID', 'Nama', 'NIP', 'Email', 'DeptName', 'Role', 'Active']].copy()
                display['Active'] = display['Active'].apply(lambda x: "✅" if x == 1 else "❌")
                display.columns = ['ID', '👤 Nama', '🆔 NIP', '📧 Email', '🏢 Bidang', '🎭 Role', '📊 Status']
                st.dataframe(display, use_container_width=True, hide_index=True)
                
                st.markdown("---")
                st.subheader("⚙️ Kelola User")
                
                user_opts = {f"{r['👤 Nama']} ({r['📧 Email']})": r['ID'] for _, r in display.iterrows()}
                sel = st.selectbox("Pilih User", list(user_opts.keys()))
                sel_id = user_opts[sel]
                u = next(x for x in users if x[0] == sel_id)
                
                c1, c2 = st.columns(2)
                with c1:
                    with st.form("edit_user"):
                        e_name = st.text_input("Nama", value=u[3])
                        e_nip = st.text_input("NIP", value=u[4] or "")
                        dept_names = [d[1] for d in depts]
                        e_dept = st.selectbox("Bidang", dept_names,
                            index=dept_names.index(u[8]) if u[8] in dept_names else 0)
                        e_role = st.selectbox("Role", ['pns', 'kepala_bidang', 'admin'],
                            index=['pns', 'kepala_bidang', 'admin'].index(u[6]))
                        e_active = st.checkbox("Aktif", value=u[7] == 1)
                        
                        if st.form_submit_button("💾 Simpan"):
                            dept_id = next(d[0] for d in depts if d[1] == e_dept)
                            conn = get_db()
                            conn.execute("""UPDATE users 
                                SET full_name=?, nip=?, department_id=?, role=?, is_active=? 
                                WHERE id=?""",
                                (e_name, e_nip, dept_id, e_role, 1 if e_active else 0, sel_id))
                            conn.commit()
                            conn.close()
                            st.success("✅ Diupdate!")
                            st.rerun()
                
                with c2:
                    with st.form("reset_pass"):
                        new_pass = st.text_input("Password Baru", type="password")
                        if st.form_submit_button("🔑 Reset Password"):
                            if new_pass and len(new_pass) >= 6:
                                conn = get_db()
                                conn.execute("UPDATE users SET password_hash=? WHERE id=?",
                                    (hash_password(new_pass), sel_id))
                                conn.commit()
                                conn.close()
                                st.success("✅ Password direset!")
                            else:
                                st.error("❌ Min 6 karakter!")
                    
                    st.markdown("---")
                    st.markdown("**🗑️ Hapus User**")
                    confirm = st.checkbox("⚠️ Yakin hapus?", key="del_user")
                    if st.button("🗑️ Hapus", disabled=not confirm):
                        conn = get_db()
                        conn.execute("DELETE FROM users WHERE id=?", (sel_id,))
                        conn.commit()
                        conn.close()
                        st.success("✅ User dihapus!")
                        st.rerun()
            else:
                st.info("Belum ada user.")
    
    # ============================================================
    # PAGE: DEPARTMENTS
    # ============================================================
    elif st.session_state.page == "departments":
        st.title("🏢 Manajemen Bidang")
        
        tab1, tab2 = st.tabs(["➕ Tambah", "📋 Daftar"])
        
        with tab1:
            with st.form("add_dept"):
                name = st.text_input("Nama Bidang")
                desc = st.text_area("Deskripsi")
                if st.form_submit_button("➕ Tambah", type="primary"):
                    if name:
                        conn = get_db()
                        try:
                            conn.execute("INSERT INTO departments (name, description) VALUES (?,?)",
                                (name, desc))
                            conn.commit()
                            st.success("✅ Ditambahkan!")
                            st.rerun()
                        except sqlite3.IntegrityError:
                            st.error("❌ Sudah ada!")
                        finally:
                            conn.close()
        
        with tab2:
            conn = get_db()
            depts = conn.execute("SELECT * FROM departments ORDER BY name").fetchall()
            conn.close()
            
            if depts:
                df = pd.DataFrame(depts, columns=['ID', 'Nama', 'Desc'])
                st.dataframe(df, use_container_width=True, hide_index=True)
                
                st.markdown("---")
                st.subheader("🗑️ Hapus Bidang")
                dept_opts = {d[1]: d[0] for d in depts}
                sel = st.selectbox("Pilih", list(dept_opts.keys()))
                confirm = st.checkbox("⚠️ Yakin?", key="del_dept")
                if st.button("🗑️ Hapus", disabled=not confirm):
                    conn = get_db()
                    conn.execute("DELETE FROM departments WHERE id=?", (dept_opts[sel],))
                    conn.commit()
                    conn.close()
                    st.success("✅ Dihapus!")
                    st.rerun()
            else:
                st.info("Belum ada bidang.")
    
    # ============================================================
    # PAGE: CATEGORIES
    # ============================================================
    elif st.session_state.page == "categories":
        st.title("📂 Manajemen Kategori")
        
        tab1, tab2 = st.tabs(["➕ Tambah", "📋 Daftar"])
        
        with tab1:
            with st.form("add_cat"):
                name = st.text_input("Nama Kategori")
                desc = st.text_area("Deskripsi")
                need_approval = st.checkbox("Perlu Approval Kabid")
                if st.form_submit_button("➕ Tambah", type="primary"):
                    if name:
                        conn = get_db()
                        try:
                            conn.execute("""INSERT INTO categories 
                                (name, description, require_approval) VALUES (?,?,?)""",
                                (name, desc, 1 if need_approval else 0))
                            conn.commit()
                            st.success("✅ Ditambahkan!")
                            st.rerun()
                        except sqlite3.IntegrityError:
                            st.error("❌ Sudah ada!")
                        finally:
                            conn.close()
        
        with tab2:
            conn = get_db()
            cats = conn.execute("SELECT * FROM categories ORDER BY name").fetchall()
            conn.close()
            
            if cats:
                df = pd.DataFrame(cats, columns=['ID', 'Nama', 'Desc', 'Approval'])
                df['Approval'] = df['Approval'].apply(lambda x: "✅ Ya" if x == 1 else "❌ Tidak")
                df.columns = ['ID', '📂 Nama', '📝 Deskripsi', '🔐 Perlu Approval']
                st.dataframe(df, use_container_width=True, hide_index=True)
                
                st.markdown("---")
                st.subheader("🗑️ Hapus Kategori")
                cat_opts = {c[1]: c[0] for c in cats}
                sel = st.selectbox("Pilih", list(cat_opts.keys()))
                confirm = st.checkbox("⚠️ Yakin?", key="del_cat")
                if st.button("🗑️ Hapus", disabled=not confirm):
                    conn = get_db()
                    conn.execute("DELETE FROM categories WHERE id=?", (cat_opts[sel],))
                    conn.commit()
                    conn.close()
                    st.success("✅ Dihapus!")
                    st.rerun()
            else:
                st.info("Belum ada kategori.")
    
    # ============================================================
    # PAGE: AUDIT LOG
    # ============================================================
    elif st.session_state.page == "audit":
        st.title("📜 Audit Log")
        
        conn = get_db()
        logs = conn.execute("""SELECT a.*, d.name as dept_name 
            FROM audit_logs a 
            LEFT JOIN departments d ON a.department_id = d.id 
            ORDER BY a.action_date DESC LIMIT 500""").fetchall()
        conn.close()
        
        if logs:
            search = st.text_input("🔍 Cari")
            df = pd.DataFrame(logs, columns=[
                'ID', 'Aksi', 'DocID', 'Judul', 'Email', 'Nama', 'Role',
                'Tanggal', 'Detail', 'DeptID', 'DeptName'
            ])
            
            if search:
                df = df[df['Judul'].str.contains(search, case=False, na=False) |
                        df['Nama'].str.contains(search, case=False, na=False) |
                        df['Detail'].str.contains(search, case=False, na=False)]
            
            display = df[['Aksi', 'Judul', 'Nama', 'Role', 'DeptName', 'Tanggal', 'Detail']].copy()
            display.columns = ['🔧 Aksi', '📄 Dokumen', '👤 Pelaku', '🎭 Role', '🏢 Bidang', '📅 Waktu', '📝 Detail']
            st.dataframe(display, use_container_width=True, hide_index=True, height=500)
            
            st.markdown("---")
            if st.button("📊 Export Excel"):
                df.to_excel("audit.xlsx", index=False)
                with open("audit.xlsx", "rb") as f:
                    st.download_button("📥 Download Excel", data=f.read(),
                        file_name=f"audit_{datetime.now().strftime('%Y%m%d')}.xlsx")
        else:
            st.info("Belum ada aktivitas.")