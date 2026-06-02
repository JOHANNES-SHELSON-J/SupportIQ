import sqlite3
import bcrypt

def hash_password(plain_password):
    return bcrypt.hashpw(plain_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

conn = sqlite3.connect("tickets.db")

# Rebuild the users table around email
conn.execute("DROP TABLE IF EXISTS users")
conn.execute("""
    CREATE TABLE users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL
    )
""")

# Pre-load staff accounts (emails + strong passwords meeting the rules)
staff_accounts = [
    ("admin@supportiq.com", "Admin@123", "staff"),
    ("manager@supportiq.com", "Manager@123", "staff"),
]

for email, password, role in staff_accounts:
    conn.execute(
        "INSERT INTO users (email, password_hash, role) VALUES (?, ?, ?)",
        (email, hash_password(password), role)
    )
    print(f"Created staff user: {email}")

conn.commit()

print("\nCurrent users:")
for row in conn.execute("SELECT email, role FROM users"):
    print(f"  {row[0]}  ({row[1]})")

conn.close()