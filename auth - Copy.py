import sqlite3
import bcrypt
import re

DB = "tickets.db"

def hash_password(plain_password):
    return bcrypt.hashpw(plain_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def verify_password(plain_password, stored_hash):
    return bcrypt.checkpw(plain_password.encode("utf-8"), stored_hash.encode("utf-8"))

def is_valid_email(email):
    # Basic but solid email pattern
    pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
    return re.match(pattern, email) is not None

def password_problems(password):
    """Returns a list of unmet requirements (empty list means password is valid)."""
    problems = []
    if len(password) < 8:
        problems.append("at least 8 characters")
    if not re.search(r"[A-Z]", password):
        problems.append("one uppercase letter")
    if not re.search(r"[a-z]", password):
        problems.append("one lowercase letter")
    if not re.search(r"[0-9]", password):
        problems.append("one number")
    if not re.search(r"[^A-Za-z0-9]", password):
        problems.append("one special character")
    return problems

def get_user(email):
    conn = sqlite3.connect(DB)
    row = conn.execute(
        "SELECT email, password_hash, role FROM users WHERE email = ?",
        (email,)
    ).fetchone()
    conn.close()
    return row  # (email, password_hash, role) or None

def create_customer(email, password):
    """Returns (success, message)."""
    email = email.strip().lower()
    if not email or not password:
        return False, "Email and password cannot be empty."
    if not is_valid_email(email):
        return False, "Please enter a valid email address."
    problems = password_problems(password)
    if problems:
        return False, "Password must contain " + ", ".join(problems) + "."
    if get_user(email):
        return False, "An account with that email already exists."
    conn = sqlite3.connect(DB)
    conn.execute(
        "INSERT INTO users (email, password_hash, role) VALUES (?, ?, ?)",
        (email, hash_password(password), "customer")
    )
    conn.commit()
    conn.close()
    return True, "Account created! You can now log in."

def authenticate(email, password):
    """Returns (success, role_or_message)."""
    email = email.strip().lower()
    user = get_user(email)
    if not user:
        return False, "No account found with that email."
    stored_email, stored_hash, role = user
    if verify_password(password, stored_hash):
        return True, role
    return False, "Incorrect password."