"""
Modul Database - Mengelola semua operasi SQLite
"""
import sqlite3
from config import DB_NAME


def get_connection():
    """Buat koneksi ke database"""
    return sqlite3.connect(DB_NAME)


def init_db():
    """Inisialisasi tabel database"""
    conn = get_connection()
    c = conn.cursor()

    # Tabel Users
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  email TEXT UNIQUE NOT NULL,
                  password_hash TEXT NOT NULL,
                  full_name TEXT NOT NULL,
                  department TEXT NOT NULL,
                  created_at TEXT DEFAULT CURRENT_TIMESTAMP)''')

    # Tabel Documents
    c.execute('''CREATE TABLE IF NOT EXISTS documents
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  title TEXT NOT NULL,
                  original_filename TEXT NOT NULL,
                  filepath TEXT NOT NULL,
                  department TEXT NOT NULL,
                  uploaded_by_email TEXT NOT NULL,
                  uploaded_by_name TEXT NOT NULL,
                  upload_date TEXT NOT NULL,
                  file_size INTEGER DEFAULT 0)''')

    # Index untuk pencarian cepat
    c.execute('''CREATE INDEX IF NOT EXISTS idx_docs_dept
                 ON documents(department)''')
    c.execute('''CREATE INDEX IF NOT EXISTS idx_docs_date
                 ON documents(upload_date)''')

    conn.commit()
    conn.close()


# --- USER OPERATIONS ---
def create_user(email, password_hash, full_name, department):
    """Buat user baru"""
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute("""INSERT INTO users
                     (email, password_hash, full_name, department)
                     VALUES (?,?,?,?)""",
                  (email, password_hash, full_name, department))
        conn.commit()
        return True, "Registrasi berhasil!"
    except sqlite3.IntegrityError:
        return False, "Email sudah terdaftar!"
    finally:
        conn.close()


def get_user_by_email(email):
    """Ambil user berdasarkan email"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE email=?", (email,))
    user = c.fetchone()
    conn.close()
    return user


# --- DOCUMENT OPERATIONS ---
def create_document(title, original_filename, filepath, department,
                    uploaded_by_email, uploaded_by_name, upload_date, file_size):
    """Simpan dokumen baru ke database"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("""INSERT INTO documents
                 (title, original_filename, filepath, department,
                  uploaded_by_email, uploaded_by_name, upload_date, file_size)
                 VALUES (?,?,?,?,?,?,?,?)""",
              (title, original_filename, filepath, department,
               uploaded_by_email, uploaded_by_name, upload_date, file_size))
    doc_id = c.lastrowid
    conn.commit()
    conn.close()
    return doc_id


def get_all_documents():
    """Ambil semua dokumen (terbaru dulu)"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM documents ORDER BY upload_date DESC")
    docs = c.fetchall()
    conn.close()
    return docs


def get_documents_by_department(department):
    """Ambil dokumen berdasarkan departemen"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("""SELECT * FROM documents
                 WHERE department=?
                 ORDER BY upload_date DESC""", (department,))
    docs = c.fetchall()
    conn.close()
    return docs


def get_document_by_id(doc_id):
    """Ambil dokumen berdasarkan ID"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM documents WHERE id=?", (doc_id,))
    doc = c.fetchone()
    conn.close()
    return doc