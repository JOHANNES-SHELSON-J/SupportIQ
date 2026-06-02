import sqlite3

conn = sqlite3.connect("tickets.db")

# Check existing columns
cols = [r[1] for r in conn.execute("PRAGMA table_info(tickets)")]

if "username" not in cols:
    conn.execute("ALTER TABLE tickets ADD COLUMN username TEXT")
    print("Added 'username' column.")
else:
    print("'username' column already exists.")

# Fill historical rows that have no username
conn.execute("UPDATE tickets SET username = '(historical)' WHERE username IS NULL")
conn.commit()

# Confirm
final_cols = [r[1] for r in conn.execute("PRAGMA table_info(tickets)")]
print("Columns now:", final_cols)

# Quick count of how many rows got the historical label
count = conn.execute("SELECT COUNT(*) FROM tickets WHERE username = '(historical)'").fetchone()[0]
print(f"Rows labeled '(historical)': {count}")

conn.close()
