import sqlite3
import random

conn = sqlite3.connect("database.db")
c = conn.cursor()

# 🔥 DROP old bills table (taaki structure clean ho)
c.execute("DROP TABLE IF EXISTS bills")

# ---------------- USERS TABLE ----------------
c.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT,
    email TEXT
)
""")

# ---------------- NEW BILLS TABLE ----------------
c.execute("""
CREATE TABLE bills (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    consumer_name TEXT,
    units INTEGER,
    bill INTEGER,
    month TEXT,
    year INTEGER
)
""")

# ---------------- COMPLAINTS TABLE ----------------
c.execute("""
CREATE TABLE IF NOT EXISTS complaints (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    consumer_name TEXT,
    complaint_type TEXT,
    description TEXT,
    status TEXT
)
""")

# ---------------- ADD USER ----------------
c.execute("INSERT OR IGNORE INTO users (username, password, email) VALUES (?, ?, ?)",
          ("palak", "palak123", "palak@gmail.com"))

# ---------------- MONTHS ----------------
months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# ---------------- INSERT DATA ----------------
for i in range(12):  # 12 months data
    units = random.randint(50, 300)
    bill = units * random.randint(6, 9)
    month = months[i]
    year = 2025

    c.execute("""
        INSERT INTO bills (consumer_name, units, bill, month, year)
        VALUES (?, ?, ?, ?, ?)
    """, ("palak", units, bill, month, year))

# ---------------- SAMPLE COMPLAINT ----------------
c.execute("""
INSERT INTO complaints (consumer_name, complaint_type, description, status)
VALUES (?, ?, ?, ?)
""", ("palak", "Bill Issue", "High bill detected", "Pending"))

conn.commit()
conn.close()

print("✅ Month + Year Data Added Successfully!")