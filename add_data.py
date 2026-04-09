import sqlite3
from faker import Faker
import random

fake = Faker('en_IN')

conn = sqlite3.connect("database.db")
c = conn.cursor()

# Get all users
c.execute("SELECT username FROM users")
users = c.fetchall()

# Agar users nahi hai toh create karo
if len(users) == 0:
    for _ in range(50):
        username = fake.first_name().lower() + str(random.randint(10,99))
        c.execute("INSERT INTO users (username, password, email) VALUES (?, ?, ?)",
                  (username, "pass123", username+"@gmail.com"))

    conn.commit()
    c.execute("SELECT username FROM users")
    users = c.fetchall()

# Bills add karo
for user in users:
    username = user[0]
    for _ in range(5):  # har user ke 5 bills
        units = random.randint(50,500)
        bill = units * random.randint(6,10)

        c.execute("INSERT INTO bills (consumer_name, units, bill) VALUES (?, ?, ?)",
                  (username, units, bill))

# Complaints add karo
complaints = ["Meter Issue", "Bill Issue", "Power Cut"]
status = ["Pending", "Resolved"]

for user in users:
    username = user[0]
    if random.choice([True, False]):
        c.execute("INSERT INTO complaints (consumer_name, complaint_type, description, status)",
                  (username,
                   random.choice(complaints),
                   fake.sentence(),
                   random.choice(status)))

conn.commit()
conn.close()

print("Data Added Successfully!")