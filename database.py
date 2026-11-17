
import sqlite3
import os
from datetime import date

# Lokasi database
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "expenses.db")


def connect_db():
    return sqlite3.connect(DB_NAME)


# Create table
def create_table():
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            transaction_type TEXT NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            description TEXT,
            date TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


# Add income or expense
def add_transaction(user_id, transaction_type, amount,
                    category, description="", transaction_date=None):

    if transaction_date is None:
        transaction_date = date.today().isoformat()

    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO transactions
        (user_id, transaction_type, amount, category, description, date)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        user_id,
        transaction_type,
        amount,
        category,
        description,
        transaction_date
    ))

    conn.commit()
    conn.close()


# Get all transactions for one user
def get_transactions(user_id):
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM transactions
        WHERE user_id = ?
        ORDER BY date DESC, id DESC
    """, (user_id,))

    data = cursor.fetchall()
    conn.close()

    return data


# Calculate total income and expense
def get_summary(user_id):
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT transaction_type, SUM(amount)
        FROM transactions
        WHERE user_id = ?
        GROUP BY transaction_type
    """, (user_id,))

    results = cursor.fetchall()
    conn.close()

    income = 0
    expense = 0

    for transaction_type, total in results:
        if transaction_type == "income":
            income = total or 0
        elif transaction_type == "expense":
            expense = total or 0

    return income, expense


# Get monthly report for one user
def get_monthly_report(user_id, year_month=None):

    if year_month is None:
        year_month = date.today().strftime("%Y-%m")

    conn = connect_db()
    cursor = conn.cursor()

    # Calculate monthly income and expense
    cursor.execute("""
        SELECT
            transaction_type,
            SUM(amount)
        FROM transactions
        WHERE user_id = ?
        AND date LIKE ?
        GROUP BY transaction_type
    """, (user_id, f"{year_month}%"))

    results = cursor.fetchall()

    income = 0
    expense = 0

    for transaction_type, total in results:
        if transaction_type == "income":
            income = total or 0
        elif transaction_type == "expense":
            expense = total or 0

    # Find highest expense category
    cursor.execute("""
        SELECT category, SUM(amount) AS total
        FROM transactions
        WHERE user_id = ?
        AND transaction_type = 'expense'
        AND date LIKE ?
        GROUP BY category
        ORDER BY total DESC
        LIMIT 1
    """, (user_id, f"{year_month}%"))

    top_category = cursor.fetchone()

    conn.close()

    if top_category:
        category_name = top_category[0]
        category_amount = top_category[1]
    else:
        category_name = "None"
        category_amount = 0

    balance = income - expense

    return income, expense, balance, category_name, category_amount


# Reset all transactions for one user
def reset_transactions(user_id):
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM transactions
        WHERE user_id = ?
    """, (user_id,))

    deleted_count = cursor.rowcount

    conn.commit()
    conn.close()

    return deleted_count


# Delete one transaction belonging to a user
def delete_transaction(transaction_id, user_id):
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM transactions
        WHERE id = ? AND user_id = ?
    """, (transaction_id, user_id))

    deleted_count = cursor.rowcount

    conn.commit()
    conn.close()

    return deleted_count


# Create table automatically
create_table()

print("Database ready!")
