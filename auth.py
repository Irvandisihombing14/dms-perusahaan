"""
Modul Autentikasi - Login, Register, dan Password Hashing
"""
import hashlib
import secrets
from database import create_user, get_user_by_email


def hash_password(password, salt=None):
    """Hash password dengan SHA-256 + salt"""
    if salt is None:
        salt = secrets.token_hex(16)
    password_hash = hashlib.sha256((salt + password).encode()).hexdigest()
    return f"{salt}${password_hash}"


def verify_password(password, stored_hash):
    """Verifikasi password dengan hash yang tersimpan"""
    try:
        salt, hash_value = stored_hash.split('$')
        password_hash = hashlib.sha256((salt + password).encode()).hexdigest()
        return password_hash == hash_value
    except Exception:
        return False


def register(email, password, full_name, department):
    """Registrasi user baru"""
    if not email or not password or not full_name:
        return False, "Semua field harus diisi!"

    if len(password) < 6:
        return False, "Password minimal 6 karakter!"

    if '@' not in email:
        return False, "Format email tidak valid!"

    password_hash = hash_password(password)
    return create_user(email.lower().strip(), password_hash, full_name, department)


def login(email, password):
    """Login user"""
    if not email or not password:
        return None, "Email dan password harus diisi!"

    user = get_user_by_email(email.lower().strip())

    if user is None:
        return None, "Email tidak terdaftar!"

    # user: (id, email, password_hash, full_name, department, created_at)
    stored_hash = user[2]

    if verify_password(password, stored_hash):
        user_data = {
            'id': user[0],
            'email': user[1],
            'full_name': user[3],
            'department': user[4],
            'created_at': user[5]
        }
        return user_data, "Login berhasil!"
    else:
        return None, "Password salah!"