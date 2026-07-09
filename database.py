"""
Modul Database - DMS Administrasi PNS
"""
import sqlite3
from datetime import datetime
from config import DB_NAME, ROLE_PNS, STATUS_DRAFT


def get_connection():
    """Buat koneksi ke database"""
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Inisialisasi semua tabel database"""
    conn = get_connection()
    c = conn.cursor()

    # Tabel Departemen/Bidang
    c.execute('''CREATE TABLE IF NOT EXISTS departments
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT UNIQUE NOT NULL,
                  description TEXT,
                  created_at TEXT DEFAULT CURRENT_TIMESTAMP)''')

    # Tabel Users
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  email TEXT UNIQUE NOT NULL,
                  password_hash TEXT NOT NULL,
                  full_name TEXT NOT NULL,
                  nip TEXT,
                  department_id INTEGER,
                  role TEXT NOT NULL DEFAULT 'pns',
                  is_active INTEGER DEFAULT 1,
                  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (department_id) REFERENCES departments(id))''')

    # Tabel Kategori Dokumen
    c.execute('''CREATE TABLE IF NOT EXISTS categories
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT UNIQUE NOT NULL,
                  description TEXT,
                  require_approval INTEGER DEFAULT 0,
                  created_at TEXT DEFAULT CURRENT_TIMESTAMP)''')

    # Tabel Dokumen
    c.execute('''CREATE TABLE IF NOT EXISTS documents
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  title TEXT NOT NULL,
                  original_filename TEXT NOT NULL,
                  filepath TEXT NOT NULL,
                  department_id INTEGER NOT NULL,
                  category_id INTEGER,
                  status TEXT NOT NULL DEFAULT 'draft',
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
                  file_size INTEGER DEFAULT 0,
                  FOREIGN KEY (department_id) REFERENCES departments(id),
                  FOREIGN KEY (category_id) REFERENCES categories(id))''')

    # Tabel Notifikasi
    c.execute('''CREATE TABLE IF NOT EXISTS notifications
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_email TEXT NOT NULL,
                  title TEXT NOT NULL,
                  message TEXT NOT NULL,
                  link TEXT,
                  is_read INTEGER DEFAULT 0,
                  created_at TEXT DEFAULT CURRENT_TIMESTAMP)''')

    # Tabel Audit Log
    c.execute('''CREATE TABLE IF NOT EXISTS audit_logs
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  action TEXT NOT NULL,
                  document_id INTEGER,
                  document_title TEXT,
                  user_email TEXT NOT NULL,
                  user_name TEXT NOT NULL,
                  user_role TEXT,
                  action_date TEXT NOT NULL,
                  details TEXT,
                  department_id INTEGER,
                  ip_address TEXT)''')

    # Index untuk performa
    c.execute('''CREATE INDEX IF NOT EXISTS idx_docs_dept
                 ON documents(department_id)''')
    c.execute('''CREATE INDEX IF NOT EXISTS idx_docs_date
                 ON documents(upload_date)''')
    c.execute('''CREATE INDEX IF NOT EXISTS idx_docs_status
                 ON documents(status)''')
    c.execute('''CREATE INDEX IF NOT EXISTS idx_docs_category
                 ON documents(category_id)''')
    c.execute('''CREATE INDEX IF NOT EXISTS idx_audit_date
                 ON audit_logs(action_date)''')
    c.execute('''CREATE INDEX IF NOT EXISTS idx_notif_user
                 ON notifications(user_email, is_read)''')

    conn.commit()
    conn.close()


# ==================== DEPARTMENT OPERATIONS ====================
def create_department(name, description=""):
    """Buat departemen baru"""
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute("INSERT INTO departments (name, description) VALUES (?,?)",
                  (name, description))
        conn.commit()
        return True, "Departemen berhasil ditambahkan!"
    except sqlite3.IntegrityError:
        return False, "Departemen sudah ada!"
    finally:
        conn.close()


def get_all_departments():
    """Ambil semua departemen"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM departments ORDER BY name")
    depts = c.fetchall()
    conn.close()
    return depts


def get_department_by_id(dept_id):
    """Ambil departemen by ID"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM departments WHERE id=?", (dept_id,))
    dept = c.fetchone()
    conn.close()
    return dept


def update_department(dept_id, name, description):
    """Update departemen"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE departments SET name=?, description=? WHERE id=?",
              (name, description, dept_id))
    conn.commit()
    conn.close()


def delete_department(dept_id):
    """Hapus departemen"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM departments WHERE id=?", (dept_id,))
    conn.commit()
    conn.close()


# ==================== USER OPERATIONS ====================
def create_user(email, password_hash, full_name, nip, department_id, role=ROLE_PNS):
    """Buat user baru"""
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute("""INSERT INTO users
                     (email, password_hash, full_name, nip, department_id, role)
                     VALUES (?,?,?,?,?,?)""",
                  (email, password_hash, full_name, nip, department_id, role))
        conn.commit()
        return True, "User berhasil dibuat!"
    except sqlite3.IntegrityError:
        return False, "Email sudah terdaftar!"
    finally:
        conn.close()


def get_user_by_email(email):
    """Ambil user berdasarkan email"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("""SELECT u.*, d.name as department_name
                 FROM users u
                 LEFT JOIN departments d ON u.department_id = d.id
                 WHERE u.email=?""", (email,))
    user = c.fetchone()
    conn.close()
    return user


def get_all_users():
    """Ambil semua user dengan info departemen"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("""SELECT u.id, u.email, u.full_name, u.nip,
                        d.name as department, u.role, u.is_active, u.created_at
                 FROM users u
                 LEFT JOIN departments d ON u.department_id = d.id
                 ORDER BY u.created_at DESC""")
    users = c.fetchall()
    conn.close()
    return users


def update_user(user_id, full_name, nip, department_id, role, is_active):
    """Update user"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("""UPDATE users
                 SET full_name=?, nip=?, department_id=?, role=?, is_active=?
                 WHERE id=?""",
              (full_name, nip, department_id, role, is_active, user_id))
    conn.commit()
    conn.close()


def update_user_password(user_id, password_hash):
    """Update password user"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE users SET password_hash=? WHERE id=?",
              (password_hash, user_id))
    conn.commit()
    conn.close()


def delete_user(user_id):
    """Hapus user"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM users WHERE id=?", (user_id,))
    conn.commit()
    conn.close()


def get_users_by_department(dept_id):
    """Ambil user berdasarkan departemen"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("""SELECT * FROM users
                 WHERE department_id=? AND is_active=1
                 ORDER BY full_name""", (dept_id,))
    users = c.fetchall()
    conn.close()
    return users


def get_approvers_for_department(dept_id):
    """Ambil Kepala Bidang untuk departemen tertentu"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("""SELECT * FROM users
                 WHERE department_id=? AND role='kepala_bidang' AND is_active=1""",
              (dept_id,))
    approvers = c.fetchall()
    conn.close()
    return approvers


# ==================== CATEGORY OPERATIONS ====================
def create_category(name, description="", require_approval=0):
    """Buat kategori dokumen"""
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute("INSERT INTO categories (name, description, require_approval) VALUES (?,?,?)",
                  (name, description, require_approval))
        conn.commit()
        return True, "Kategori berhasil ditambahkan!"
    except sqlite3.IntegrityError:
        return False, "Kategori sudah ada!"
    finally:
        conn.close()


def get_all_categories():
    """Ambil semua kategori"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM categories ORDER BY name")
    cats = c.fetchall()
    conn.close()
    return cats


def get_category_by_id(cat_id):
    """Ambil kategori by ID"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM categories WHERE id=?", (cat_id,))
    cat = c.fetchone()
    conn.close()
    return cat


def update_category(cat_id, name, description, require_approval):
    """Update kategori"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("""UPDATE categories
                 SET name=?, description=?, require_approval=?
                 WHERE id=?""",
              (name, description, require_approval, cat_id))
    conn.commit()
    conn.close()


def delete_category(cat_id):
    """Hapus kategori"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM categories WHERE id=?", (cat_id,))
    conn.commit()
    conn.close()


# ==================== DOCUMENT OPERATIONS ====================
def create_document(title, original_filename, filepath, department_id, category_id,
                    status, tags, description, expiry_date, uploaded_by_email,
                    uploaded_by_name, upload_date, file_size):
    """Simpan dokumen baru"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("""INSERT INTO documents
                 (title, original_filename, filepath, department_id, category_id,
                  status, tags, description, expiry_date, uploaded_by_email,
                  uploaded_by_name, upload_date, file_size)
                 VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
              (title, original_filename, filepath, department_id, category_id,
               status, tags, description, expiry_date, uploaded_by_email,
               uploaded_by_name, upload_date, file_size))
    doc_id = c.lastrowid
    conn.commit()
    conn.close()
    return doc_id


def get_all_documents(limit=None, offset=0):
    """Ambil semua dokumen dengan info lengkap"""
    conn = get_connection()
    c = conn.cursor()
    query = """SELECT d.*, dep.name as department_name, cat.name as category_name
               FROM documents d
               LEFT JOIN departments dep ON d.department_id = dep.id
               LEFT JOIN categories cat ON d.category_id = cat.id
               ORDER BY d.upload_date DESC"""
    if limit:
        query += f" LIMIT {limit} OFFSET {offset}"
    c.execute(query)
    docs = c.fetchall()
    conn.close()
    return docs


def count_all_documents():
    """Hitung total dokumen"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM documents")
    count = c.fetchone()[0]
    conn.close()
    return count


def get_documents_by_department(dept_id, limit=None, offset=0):
    """Ambil dokumen berdasarkan departemen"""
    conn = get_connection()
    c = conn.cursor()
    query = """SELECT d.*, dep.name as department_name, cat.name as category_name
               FROM documents d
               LEFT JOIN departments dep ON d.department_id = dep.id
               LEFT JOIN categories cat ON d.category_id = cat.id
               WHERE d.department_id=?
               ORDER BY d.upload_date DESC"""
    if limit:
        query += f" LIMIT {limit} OFFSET {offset}"
    c.execute(query, (dept_id,))
    docs = c.fetchall()
    conn.close()
    return docs


def get_documents_by_user(email, limit=None, offset=0):
    """Ambil dokumen berdasarkan user"""
    conn = get_connection()
    c = conn.cursor()
    query = """SELECT d.*, dep.name as department_name, cat.name as category_name
               FROM documents d
               LEFT JOIN departments dep ON d.department_id = dep.id
               LEFT JOIN categories cat ON d.category_id = cat.id
               WHERE d.uploaded_by_email=?
               ORDER BY d.upload_date DESC"""
    if limit:
        query += f" LIMIT {limit} OFFSET {offset}"
    c.execute(query, (email,))
    docs = c.fetchall()
    conn.close()
    return docs


def get_documents_by_status(status, limit=None, offset=0):
    """Ambil dokumen berdasarkan status"""
    conn = get_connection()
    c = conn.cursor()
    query = """SELECT d.*, dep.name as department_name, cat.name as category_name
               FROM documents d
               LEFT JOIN departments dep ON d.department_id = dep.id
               LEFT JOIN categories cat ON d.category_id = cat.id
               WHERE d.status=?
               ORDER BY d.upload_date DESC"""
    if limit:
        query += f" LIMIT {limit} OFFSET {offset}"
    c.execute(query, (status,))
    docs = c.fetchall()
    conn.close()
    return docs


def get_document_by_id(doc_id):
    """Ambil dokumen berdasarkan ID"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("""SELECT d.*, dep.name as department_name, cat.name as category_name
                 FROM documents d
                 LEFT JOIN departments dep ON d.department_id = dep.id
                 LEFT JOIN categories cat ON d.category_id = cat.id
                 WHERE d.id=?""", (doc_id,))
    doc = c.fetchone()
    conn.close()
    return doc


def update_document(doc_id, **kwargs):
    """Update dokumen"""
    conn = get_connection()
    c = conn.cursor()
    set_clause = ", ".join([f"{k}=?" for k in kwargs.keys()])
    values = list(kwargs.values()) + [doc_id]
    c.execute(f"UPDATE documents SET {set_clause} WHERE id=?", values)
    conn.commit()
    conn.close()


def delete_document_record(doc_id):
    """Hapus record dokumen"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM documents WHERE id=?", (doc_id,))
    conn.commit()
    conn.close()


def approve_document(doc_id, approver_email, approved_at):
    """Approve dokumen"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("""UPDATE documents
                 SET status='approved', approved_by=?, approved_at=?, updated_at=?
                 WHERE id=?""",
              (approver_email, approved_at, approved_at, doc_id))
    conn.commit()
    conn.close()


def reject_document(doc_id, approver_email, rejection_reason, rejected_at):
    """Reject dokumen"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("""UPDATE documents
                 SET status='rejected', approved_by=?, rejection_reason=?, updated_at=?
                 WHERE id=?""",
              (approver_email, rejection_reason, rejected_at, doc_id))
    conn.commit()
    conn.close()


# ==================== NOTIFICATION OPERATIONS ====================
def create_notification(user_email, title, message, link=""):
    """Buat notifikasi"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("""INSERT INTO notifications
                 (user_email, title, message, link)
                 VALUES (?,?,?,?)""",
              (user_email, title, message, link))
    conn.commit()
    conn.close()


def get_notifications(user_email, unread_only=False):
    """Ambil notifikasi user"""
    conn = get_connection()
    c = conn.cursor()
    if unread_only:
        c.execute("""SELECT * FROM notifications
                     WHERE user_email=? AND is_read=0
                     ORDER BY created_at DESC""", (user_email,))
    else:
        c.execute("""SELECT * FROM notifications
                     WHERE user_email=?
                     ORDER BY created_at DESC
                     LIMIT 50""", (user_email,))
    notifs = c.fetchall()
    conn.close()
    return notifs


def mark_notification_read(notif_id):
    """Tandai notifikasi sudah dibaca"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE notifications SET is_read=1 WHERE id=?", (notif_id,))
    conn.commit()
    conn.close()


def mark_all_notifications_read(user_email):
    """Tandai semua notifikasi sudah dibaca"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE notifications SET is_read=1 WHERE user_email=?", (user_email,))
    conn.commit()
    conn.close()


def count_unread_notifications(user_email):
    """Hitung notifikasi belum dibaca"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("""SELECT COUNT(*) FROM notifications
                 WHERE user_email=? AND is_read=0""", (user_email,))
    count = c.fetchone()[0]
    conn.close()
    return count


# ==================== AUDIT LOG OPERATIONS ====================
def create_audit_log(action, document_id, document_title, user_email,
                     user_name, user_role, action_date, details="",
                     department_id=None, ip_address=""):
    """Catat aktivitas ke audit log"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("""INSERT INTO audit_logs
                 (action, document_id, document_title, user_email, user_name,
                  user_role, action_date, details, department_id, ip_address)
                 VALUES (?,?,?,?,?,?,?,?,?,?)""",
              (action, document_id, document_title, user_email, user_name,
               user_role, action_date, details, department_id, ip_address))
    conn.commit()
    conn.close()


def get_all_audit_logs(limit=None, offset=0):
    """Ambil semua audit log"""
    conn = get_connection()
    c = conn.cursor()
    query = """SELECT a.*, d.name as department_name
               FROM audit_logs a
               LEFT JOIN departments d ON a.department_id = d.id
               ORDER BY a.action_date DESC"""
    if limit:
        query += f" LIMIT {limit} OFFSET {offset}"
    c.execute(query)
    logs = c.fetchall()
    conn.close()
    return logs


def count_all_audit_logs():
    """Hitung total audit log"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM audit_logs")
    count = c.fetchone()[0]
    conn.close()
    return count


def get_audit_logs_by_user(email, limit=None, offset=0):
    """Ambil audit log berdasarkan user"""
    conn = get_connection()
    c = conn.cursor()
    query = """SELECT a.*, d.name as department_name
               FROM audit_logs a
               LEFT JOIN departments d ON a.department_id = d.id
               WHERE a.user_email=?
               ORDER BY a.action_date DESC"""
    if limit:
        query += f" LIMIT {limit} OFFSET {offset}"
    c.execute(query, (email,))
    logs = c.fetchall()
    conn.close()
    return logs