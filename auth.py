"""
Modul Autentikasi - DMS PNS
"""
import hashlib
import secrets
from database import create_user, get_user_by_email
from config import ROLE_PNS


def hash_password(password, salt=None):
    if salt is None:
        salt = secrets.token_hex(16)
    password_hash = hashlib.sha256((salt + password).encode()).hexdigest()
    return f"{salt}${password_hash}"


def verify_password(password, stored_hash):
    try:
        salt, hash_value = stored_hash.split('$')
        password_hash = hashlib.sha256((salt + password).encode()).hexdigest()
        return password_hash == hash_value
    except Exception:
        return False


def register(email, password, full_name, nip, department_id, role=ROLE_PNS):
    if not email or not password or not full_name:
        return False, "Email, password, dan nama harus diisi!"
    if len(password) < 6:
        return False, "Password minimal 6 karakter!"
    if '@' not in email:
        return False, "Format email tidak valid!"
    password_hash = hash_password(password)
    return create_user(email.lower().strip(), password_hash, full_name, nip, department_id, role)


def login(email, password):
    if not email or not password:
        return None, "Email dan password harus diisi!"
    user = get_user_by_email(email.lower().strip())
    if user is None:
        return None, "Email tidak terdaftar!"
    if user[7] == 0:
        return None, "Akun Anda telah dinonaktifkan. Hubungi admin."
    stored_hash = user[2]
    if verify_password(password, stored_hash):
        user_data = {
            'id': user[0],
            'email': user[1],
            'full_name': user[3],
            'nip': user[4],
            'department_id': user[5],
            'department_name': user[9] if user[9] else "Belum diatur",
            'role': user[6],
            'is_active': user[7],
            'created_at': user[8]
        }
        return user_data, "Login berhasil!"
    else:
        return None, "Password salah!"


def is_admin(user_data):
    return user_data and user_data.get('role') == 'admin'


def is_kepala_bidang(user_data):
    return user_data and user_data.get('role') == 'kepala_bidang'


def can_approve(user_data):
    return user_data and user_data.get('role') in ['admin', 'kepala_bidang']