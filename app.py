from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3

app = Flask(__name__)
CORS(app)

DB_NAME = "database.db"


# ==========================================
# Database Connection
# ==========================================
def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


# ==========================================
# Create Tables
# ==========================================
def init_db():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )
    """)

    # NOTE: transactions and profile are now scoped per user via user_id.
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS transactions(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        type TEXT NOT NULL,
        category TEXT NOT NULL,
        amount REAL NOT NULL,
        note TEXT,
        date TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS profile(
        user_id INTEGER PRIMARY KEY,
        name TEXT,
        currency TEXT,
        budget REAL,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    """)

    conn.commit()
    conn.close()


def require_user_id(source):
    """Pull user_id out of query args or JSON body, return int or None."""
    uid = source.get("user_id")
    if uid is None:
        return None
    try:
        return int(uid)
    except (TypeError, ValueError):
        return None


# ==========================================
# SIGNUP
# ==========================================
@app.route("/signup", methods=["POST"])
def signup():

    data = request.get_json()

    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not name or not email or len(password) < 6:
        return jsonify({
            "error": "Name, email, and a password of at least 6 characters are required"
        }), 400

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM users WHERE email=?", (email,))
    if cursor.fetchone():
        conn.close()
        return jsonify({"error": "An account with that email already exists"}), 409

    hashed = generate_password_hash(password)

    cursor.execute(
        "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
        (name, email, hashed)
    )
    user_id = cursor.lastrowid

    # Create a default profile row for the new user
    cursor.execute(
        "INSERT INTO profile (user_id, name, currency, budget) VALUES (?, ?, ?, ?)",
        (user_id, name, "£", 0)
    )

    conn.commit()
    conn.close()

    return jsonify({
        "message": "Account created successfully",
        "user": {"id": user_id, "name": name, "email": email}
    })


# ==========================================
# LOGIN
# ==========================================
@app.route("/login", methods=["POST"])
def login():

    data = request.get_json()

    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE email=?", (email,))
    user = cursor.fetchone()
    conn.close()

    if user and check_password_hash(user["password"], password):
        return jsonify({
            "message": "Login successful",
            "user": {"id": user["id"], "name": user["name"], "email": user["email"]}
        })

    return jsonify({"error": "Invalid email or password"}), 401


# ==========================================
# FORGOT PASSWORD
# ==========================================
@app.route("/forgot-password", methods=["POST"])
def forgot_password():

    data = request.get_json()

    email = (data.get("email") or "").strip().lower()
    new_password = data.get("newPassword") or ""

    if len(new_password) < 6:
        return jsonify({"error": "New password must be at least 6 characters"}), 400

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM users WHERE email=?", (email,))
    user = cursor.fetchone()

    if not user:
        conn.close()
        return jsonify({"error": "Email not found"}), 404

    cursor.execute(
        "UPDATE users SET password=? WHERE email=?",
        (generate_password_hash(new_password), email)
    )
    conn.commit()
    conn.close()

    return jsonify({"message": "Password updated successfully"})


# ==========================================
# GET ALL TRANSACTIONS (scoped to user_id)
# ==========================================
@app.route("/transactions", methods=["GET"])
def get_transactions():

    user_id = require_user_id(request.args)
    if user_id is None:
        return jsonify({"error": "user_id is required"}), 400

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM transactions
        WHERE user_id=?
        ORDER BY date DESC, id DESC
    """, (user_id,))

    rows = cursor.fetchall()
    conn.close()

    return jsonify([dict(row) for row in rows])


# ==========================================
# ADD TRANSACTION
# ==========================================
@app.route("/transactions", methods=["POST"])
def add_transaction():

    data = request.get_json()
    user_id = require_user_id(data)

    if user_id is None:
        return jsonify({"error": "user_id is required"}), 400

    required = ["type", "category", "amount", "date"]
    for field in required:
        if field not in data:
            return jsonify({"error": f"{field} is required"}), 400

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO transactions
        (user_id, type, category, amount, note, date)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        user_id,
        data["type"],
        data["category"],
        float(data["amount"]),
        data.get("note", ""),
        data["date"]
    ))

    conn.commit()
    transaction_id = cursor.lastrowid
    conn.close()

    return jsonify({"message": "Transaction added", "id": transaction_id})


# ==========================================
# UPDATE TRANSACTION (only if it belongs to user_id)
# ==========================================
@app.route("/transactions/<int:id>", methods=["PUT"])
def update_transaction(id):

    data = request.get_json()
    user_id = require_user_id(data)

    if user_id is None:
        return jsonify({"error": "user_id is required"}), 400

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE transactions
        SET type=?, category=?, amount=?, note=?, date=?
        WHERE id=? AND user_id=?
    """, (
        data["type"],
        data["category"],
        float(data["amount"]),
        data.get("note", ""),
        data["date"],
        id,
        user_id
    ))

    conn.commit()

    if cursor.rowcount == 0:
        conn.close()
        return jsonify({"error": "Transaction not found"}), 404

    conn.close()
    return jsonify({"message": "Transaction updated"})


# ==========================================
# DELETE TRANSACTION (only if it belongs to user_id)
# ==========================================
@app.route("/transactions/<int:id>", methods=["DELETE"])
def delete_transaction(id):

    user_id = require_user_id(request.args)
    if user_id is None:
        return jsonify({"error": "user_id is required"}), 400

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM transactions WHERE id=? AND user_id=?", (id, user_id))
    conn.commit()

    if cursor.rowcount == 0:
        conn.close()
        return jsonify({"error": "Transaction not found"}), 404

    conn.close()
    return jsonify({"message": "Transaction deleted"})


# ==========================================
# GET PROFILE
# ==========================================
@app.route("/profile", methods=["GET"])
def get_profile():

    user_id = require_user_id(request.args)
    if user_id is None:
        return jsonify({"error": "user_id is required"}), 400

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM profile WHERE user_id=?", (user_id,))
    row = cursor.fetchone()
    conn.close()

    if row:
        return jsonify(dict(row))

    return jsonify({"user_id": user_id, "name": "", "currency": "£", "budget": 0})


# ==========================================
# SAVE PROFILE
# ==========================================
@app.route("/profile", methods=["POST"])
def save_profile():

    data = request.get_json()
    user_id = require_user_id(data)

    if user_id is None:
        return jsonify({"error": "user_id is required"}), 400

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT OR REPLACE INTO profile (user_id, name, currency, budget)
        VALUES (?, ?, ?, ?)
    """, (
        user_id,
        data.get("name", ""),
        data.get("currency", "£"),
        float(data.get("budget") or 0)
    ))

    conn.commit()
    conn.close()

    return jsonify({"message": "Profile saved"})


# ==========================================
# DASHBOARD SUMMARY (scoped to user_id)
# ==========================================
@app.route("/dashboard", methods=["GET"])
def dashboard():

    user_id = require_user_id(request.args)
    if user_id is None:
        return jsonify({"error": "user_id is required"}), 400

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            SUM(CASE WHEN type='income' THEN amount ELSE 0 END) AS income,
            SUM(CASE WHEN type='expense' THEN amount ELSE 0 END) AS expense,
            COUNT(*) AS totalEntries
        FROM transactions
        WHERE user_id=?
    """, (user_id,))

    row = cursor.fetchone()
    income = row["income"] or 0
    expense = row["expense"] or 0

    cursor.execute("""
        SELECT category, SUM(amount) total
        FROM transactions
        WHERE type='expense' AND user_id=?
        GROUP BY category
        ORDER BY total DESC
    """, (user_id,))
    category_summary = [dict(r) for r in cursor.fetchall()]

    cursor.execute("""
        SELECT * FROM transactions
        WHERE user_id=?
        ORDER BY date DESC, id DESC
        LIMIT 5
    """, (user_id,))
    recent = [dict(r) for r in cursor.fetchall()]

    conn.close()

    return jsonify({
        "income": income,
        "expense": expense,
        "balance": income - expense,
        "entries": row["totalEntries"],
        "categories": category_summary,
        "recent": recent
    })


# ==========================================
# HEALTH CHECK
# ==========================================
@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "status": "Running",
        "project": "Ledger Finance Tracker API",
        "version": "2.0"
    })


# ==========================================
# START SERVER
# ==========================================
if __name__ == "__main__":

    init_db()

    print("--------------------------------")
    print("Ledger Finance Tracker API")
    print("Running at: http://127.0.0.1:5000")
    print("--------------------------------")

    app.run(host="127.0.0.1", port=5000, debug=True)