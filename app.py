from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
import os
from datetime import datetime, timedelta

# --------------------------------------------------
# APP CONFIGURATION
# --------------------------------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "investment.db")

# IMPORTANT:
# Render/Gunicorn looks for an object called "app"
app = Flask(__name__)
app.secret_key = os.environ.get(
    "SECRET_KEY",
    "change-this-secret-key"
)


# --------------------------------------------------
# DATABASE
# --------------------------------------------------

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS investments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            amount REAL NOT NULL,
            profit_rate REAL NOT NULL,
            expected_profit REAL NOT NULL,
            total_return REAL NOT NULL,
            created_at TEXT NOT NULL,
            maturity_at TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'ACTIVE'
        )
    """)

    conn.commit()
    conn.close()


# Initialize the database when the application starts
init_db()


# --------------------------------------------------
# HOME PAGE
# --------------------------------------------------

@app.route("/")
def home():
    conn = get_db()

    investments = conn.execute("""
        SELECT *
        FROM investments
        ORDER BY id DESC
    """).fetchall()

    conn.close()

    return render_template(
        "index.html",
        investments=investments
    )


# --------------------------------------------------
# CREATE DEMO INVESTMENT
# --------------------------------------------------

@app.route("/invest", methods=["POST"])
def invest():

    name = request.form.get("name", "").strip()
    amount_text = request.form.get("amount", "").strip()

    if not name:
        flash("Please enter your name.")
        return redirect(url_for("home"))

    try:
        amount = float(amount_text)
    except (ValueError, TypeError):
        flash("Please enter a valid amount.")
        return redirect(url_for("home"))

    if amount <= 0:
        flash("Amount must be greater than zero.")
        return redirect(url_for("home"))

    # DEMO profit rate only
    profit_rate = 10.0

    expected_profit = amount * (profit_rate / 100)
    total_return = amount + expected_profit

    created_at = datetime.now()
    maturity_at = created_at + timedelta(days=3)

    conn = get_db()

    conn.execute("""
        INSERT INTO investments (
            name,
            amount,
            profit_rate,
            expected_profit,
            total_return,
            created_at,
            maturity_at,
            status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        name,
        amount,
        profit_rate,
        expected_profit,
        total_return,
        created_at.strftime("%Y-%m-%d %H:%M:%S"),
        maturity_at.strftime("%Y-%m-%d %H:%M:%S"),
        "ACTIVE"
    ))

    conn.commit()
    conn.close()

    flash("Demo investment created successfully.")

    return redirect(url_for("home"))


# --------------------------------------------------
# INVESTMENT DETAILS
# --------------------------------------------------

@app.route("/investment/<int:investment_id>")
def investment_details(investment_id):

    conn = get_db()

    investment = conn.execute("""
        SELECT *
        FROM investments
        WHERE id = ?
    """, (investment_id,)).fetchone()

    conn.close()

    if investment is None:
        return "Investment not found", 404

    return render_template(
        "investment.html",
        investment=investment
    )


# --------------------------------------------------
# ADMIN / RECORDS PAGE
# --------------------------------------------------

@app.route("/records")
def records():

    conn = get_db()

    investments = conn.execute("""
        SELECT *
        FROM investments
        ORDER BY id DESC
    """).fetchall()

    total_invested = conn.execute("""
        SELECT COALESCE(SUM(amount), 0)
        FROM investments
    """).fetchone()[0]

    total_profit = conn.execute("""
        SELECT COALESCE(SUM(expected_profit), 0)
        FROM investments
    """).fetchone()[0]

    conn.close()

    return render_template(
        "records.html",
        investments=investments,
        total_invested=total_invested,
        total_profit=total_profit
    )


# --------------------------------------------------
# HEALTH CHECK
# --------------------------------------------------

@app.route("/health")
def health():
    return {
        "status": "ok",
        "application": "Investment Demo",
        "database": "connected"
    }


# --------------------------------------------------
# RUN LOCALLY
# --------------------------------------------------

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )
