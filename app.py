from flask import Flask, render_template, request, redirect, session
import sqlite3
import numpy as np
import pickle
import os
import random
from sklearn.ensemble import IsolationForest

app = Flask(__name__)
app.secret_key = "supersecretkey"

# -----------------------------
# Load ML Model
# -----------------------------
model = None
if os.path.exists("model.pkl"):
    with open("model.pkl", "rb") as f:
        model = pickle.load(f)

# -----------------------------
# Smart Tariff
# -----------------------------
def calculate_bill(units):
    if units <= 100:
        return units * 5
    elif units <= 300:
        return (100 * 5) + (units - 100) * 7
    else:
        return (100 * 5) + (200 * 7) + (units - 300) * 10

# -----------------------------
# ML ANOMALY DETECTION
# -----------------------------
def detect_anomalies(bills):
    if len(bills) < 5:
        return []

    data = np.array([[b[1], b[2]] for b in bills])
    iso = IsolationForest(contamination=0.2)
    preds = iso.fit_predict(data)

    anomalies = []
    for i, p in enumerate(preds):
        if p == -1:
            anomalies.append(f"Anomaly in {bills[i][3]}-{bills[i][4]}")

    return anomalies

# -----------------------------
# HOME
# -----------------------------
@app.route("/")
def home():
    return render_template("index.html")

# -----------------------------
# ADMIN LOGIN
# -----------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        if request.form["username"] == "admin" and request.form["password"] == "admin@123":
            session["admin"] = True
            return redirect("/admin")
        else:
            error = "Invalid Credentials"
    return render_template("login.html", error=error)

# -----------------------------
# LOGOUT
# -----------------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# -----------------------------
# CONSUMER LOGIN
# -----------------------------
@app.route("/consumer_login", methods=["GET", "POST"])
def consumer_login():
    error = None

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
        user = c.fetchone()
        conn.close()

        if user:
            session["consumer"] = username
            return redirect("/consumer_dashboard")
        else:
            error = "Invalid Credentials"

    return render_template("consumer_login.html", error=error)

# -----------------------------
# CONSUMER DASHBOARD
# -----------------------------
@app.route("/consumer_dashboard")
def consumer_dashboard():
    if not session.get("consumer"):
        return redirect("/")

    username = session.get("consumer")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("""
        SELECT consumer_name, units, bill, month, year 
        FROM bills 
        WHERE consumer_name=?
        ORDER BY id
    """, (username,))
    bills = c.fetchall()

    months = [f"{b[3]}-{b[4]}" for b in bills]
    units = [b[1] for b in bills]

    alerts = [f"High bill in {b[3]}-{b[4]}" for b in bills if b[2] > 2000]

    theft_alerts = []
    for i in range(1, len(bills)):
        features = np.array([[bills[i][1], bills[i][2], bills[i-1][1], np.mean(units)]])
        if model and model.predict(features)[0] == 1:
            theft_alerts.append(f"Suspicious usage in {bills[i][3]}-{bills[i][4]}")

    anomalies = detect_anomalies(bills)

    predicted_bill = int(calculate_bill(np.mean(units))) if units else 0

    highest = max(bills, key=lambda x: x[2]) if bills else None
    usage_diff = units[-1] - units[-2] if len(units) >= 2 else 0

    risk_score = len(anomalies)*30 + len(alerts)*20 + len(theft_alerts)*40

    c.execute("SELECT complaint_type, status FROM complaints WHERE consumer_name=?", (username,))
    complaints = c.fetchall()

    conn.close()

    return render_template("consumer_dashboard.html",
        bills=bills,
        months=months,
        units=units,
        alerts=alerts,
        theft_alerts=theft_alerts,
        anomalies=anomalies,
        predicted_bill=predicted_bill,
        highest=highest,
        complaints=complaints,
        usage_diff=usage_diff,
        risk_score=risk_score
    )

# -----------------------------
# REGISTER COMPLAINT
# -----------------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    message = None

    if request.method == "POST":
        name = request.form["name"]
        complaint_type = request.form["type"]
        description = request.form["description"]

        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        c.execute("""
            INSERT INTO complaints (consumer_name, complaint_type, description, status)
            VALUES (?, ?, ?, 'Pending')
        """, (name, complaint_type, description))
        conn.commit()
        conn.close()

        message = "Complaint Registered Successfully!"

    return render_template("register_complaint.html", message=message)

# -----------------------------
# VIEW BILL
# -----------------------------
@app.route("/view_bill", methods=["GET", "POST"])
def view_bill():
    bills = None

    if request.method == "POST":
        name = request.form["name"]

        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        c.execute("SELECT * FROM bills WHERE consumer_name=?", (name,))
        bills = c.fetchall()
        conn.close()

    return render_template("view_bill.html", bills=bills)

# -----------------------------
# PREDICT
# -----------------------------
@app.route("/predict", methods=["GET", "POST"])
def predict():
    result = None
    result_bg = None

    if request.method == "POST":
        units = float(request.form.get("units", 0))
        bill = float(request.form.get("bill", 0))

        if bill / max(units, 1) > 10:
            result = "Suspicious Usage Detected!"
            result_bg = "#dc3545"
        else:
            result = "Normal Usage"
            result_bg = "#28a745"

    return render_template("predict.html", result=result, result_bg=result_bg)

# -----------------------------
# ADMIN DASHBOARD (FINAL)
# -----------------------------
@app.route("/admin")
def admin():
    if not session.get("admin"):
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("SELECT * FROM complaints")
    complaints = c.fetchall()

    c.execute("SELECT COUNT(*) FROM complaints")
    total = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM complaints WHERE status='Pending'")
    pending = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM complaints WHERE status='Resolved'")
    resolved = c.fetchone()[0]

    # ALL BILL DATA
    c.execute("SELECT consumer_name, units, bill FROM bills")
    all_data = c.fetchall()

    users = list(set([x[0] for x in all_data]))
    suspicious_users = []
    map_users = []

    for user in users:
        user_data = [x for x in all_data if x[0] == user]

        if len(user_data) < 3:
            continue

        data = np.array([[x[1], x[2]] for x in user_data])
        iso = IsolationForest(contamination=0.2)
        preds = iso.fit_predict(data)

        risk = "low"
        if -1 in preds:
            suspicious_users.append(user)
            risk = "high"

        # District random coordinates
        lat = random.uniform(22.60, 22.85)
        lng = random.uniform(75.70, 76.00)

        map_users.append({
            "name": user,
            "lat": lat,
            "lng": lng,
            "risk": risk
        })

    avg_bill = int(sum([x[2] for x in all_data]) / len(all_data)) if all_data else 0

    c.execute("""
        SELECT consumer_name, MAX(bill)
        FROM bills
        GROUP BY consumer_name
        ORDER BY MAX(bill) DESC LIMIT 5
    """)
    top_users = c.fetchall()

    conn.close()

    labels = ["Total", "Pending", "Resolved"]
    values = [total, pending, resolved]

    return render_template("admin.html",
        complaints=complaints,
        total=total,
        pending=pending,
        resolved=resolved,
        top_users=top_users,
        labels=labels,
        values=values,
        suspicious_users=suspicious_users,
        avg_bill=avg_bill,
        map_users=map_users   # 🔥 IMPORTANT
    )

# -----------------------------
# UPDATE STATUS
# -----------------------------
@app.route("/update_status/<int:id>")
def update_status(id):
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("UPDATE complaints SET status='Resolved' WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect("/admin")

# -----------------------------
# RUN
# -----------------------------
if __name__ == "__main__":
    app.run(debug=True)