from datetime import date
from bot.database.connection import get_connection

# --- Whitelist Management ---

def add_user(telegram_id: str, username: str, role: str):
    conn = get_connection()
    conn.execute(
        "INSERT OR IGNORE INTO whitelist_users (telegram_id, username, role) VALUES (?, ?, ?)",
        (telegram_id, username, role),
    )
    conn.commit()

def remove_user(telegram_id: str):
    conn = get_connection()
    conn.execute("DELETE FROM rate_limits WHERE telegram_id = ?", (telegram_id,))
    conn.execute("DELETE FROM transactions WHERE telegram_id = ?", (telegram_id,))
    conn.execute("DELETE FROM whitelist_users WHERE telegram_id = ?", (telegram_id,))
    conn.commit()

def list_users():
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT w.telegram_id, w.username, w.role, w.added_at,
               COALESCE(r.request_count, 0) AS daily_usage
        FROM whitelist_users w
        LEFT JOIN rate_limits r ON r.telegram_id = w.telegram_id
        ORDER BY w.added_at DESC
        """
    ).fetchall()
    return [dict(row) for row in rows]

def is_whitelisted(telegram_id: str) -> bool:
    conn = get_connection()
    row = conn.execute(
        "SELECT 1 FROM whitelist_users WHERE telegram_id = ?", (telegram_id,)
    ).fetchone()
    return row is not None

def get_user_role(telegram_id: str) -> str | None:
    conn = get_connection()
    row = conn.execute(
        "SELECT role FROM whitelist_users WHERE telegram_id = ?", (telegram_id,)
    ).fetchone()
    return row["role"] if row else None

# --- Transactions ---

def insert_transaction(telegram_id: str, type_: str, nominal: int, category: str, note: str, transaction_date: str):
    conn = get_connection()
    conn.execute(
        "INSERT INTO transactions (telegram_id, type, nominal, category, note, transaction_date) VALUES (?, ?, ?, ?, ?, ?)",
        (telegram_id, type_, nominal, category, note, transaction_date),
    )
    conn.commit()

def get_last_transaction(telegram_id: str) -> dict | None:
    conn = get_connection()
    row = conn.execute(
        "SELECT id, created_at, type, nominal, category, note, transaction_date "
        "FROM transactions WHERE telegram_id = ? ORDER BY created_at DESC LIMIT 1",
        (telegram_id,),
    ).fetchone()
    return dict(row) if row else None

def delete_transaction(transaction_id: int, telegram_id: str):
    conn = get_connection()
    conn.execute(
        "DELETE FROM transactions WHERE id = ? AND telegram_id = ?",
        (transaction_id, telegram_id),
    )
    conn.commit()

def get_balance(telegram_id: str, year: int, month: int) -> int:
    conn = get_connection()
    row = conn.execute(
        "SELECT COALESCE(SUM(CASE WHEN type = 'pemasukan' THEN nominal ELSE 0 END), 0) - "
        "COALESCE(SUM(CASE WHEN type = 'pengeluaran' THEN nominal ELSE 0 END), 0) AS balance "
        "FROM transactions WHERE telegram_id = ? AND strftime('%Y', transaction_date) = ? "
        "AND strftime('%m', transaction_date) = ?",
        (telegram_id, f"{year:04d}", f"{month:02d}"),
    ).fetchone()
    return row["balance"]

def get_monthly_transactions(telegram_id: str, year: int, month: int):
    conn = get_connection()
    rows = conn.execute(
        "SELECT id, created_at, type, nominal, category, note, transaction_date "
        "FROM transactions WHERE telegram_id = ? AND strftime('%Y', transaction_date) = ? "
        "AND strftime('%m', transaction_date) = ? ORDER BY transaction_date DESC",
        (telegram_id, f"{year:04d}", f"{month:02d}"),
    ).fetchall()
    return [dict(r) for r in rows]

def get_monthly_summary(telegram_id: str, year: int, month: int):
    conn = get_connection()
    row = conn.execute(
        "SELECT COALESCE(SUM(CASE WHEN type = 'pemasukan' THEN nominal ELSE 0 END), 0) AS total_income, "
        "COALESCE(SUM(CASE WHEN type = 'pengeluaran' THEN nominal ELSE 0 END), 0) AS total_expense "
        "FROM transactions WHERE telegram_id = ? AND strftime('%Y', transaction_date) = ? "
        "AND strftime('%m', transaction_date) = ?",
        (telegram_id, f"{year:04d}", f"{month:02d}"),
    ).fetchone()
    return dict(row)

def get_category_summary(telegram_id: str, year: int, month: int):
    conn = get_connection()
    rows = conn.execute(
        "SELECT category, SUM(nominal) AS total FROM transactions "
        "WHERE telegram_id = ? AND type = 'pengeluaran' AND strftime('%Y', transaction_date) = ? "
        "AND strftime('%m', transaction_date) = ? GROUP BY category ORDER BY total DESC",
        (telegram_id, f"{year:04d}", f"{month:02d}"),
    ).fetchall()
    return [dict(r) for r in rows]

# --- Rate Limits ---

def get_rate_limit(telegram_id: str) -> dict | None:
    conn = get_connection()
    row = conn.execute(
        "SELECT request_count, last_request FROM rate_limits WHERE telegram_id = ?",
        (telegram_id,),
    ).fetchone()
    return dict(row) if row else None

def upsert_rate_limit(telegram_id: str, request_count: int, last_request: str):
    conn = get_connection()
    conn.execute(
        "INSERT INTO rate_limits (telegram_id, request_count, last_request) VALUES (?, ?, ?) "
        "ON CONFLICT(telegram_id) DO UPDATE SET request_count = excluded.request_count, last_request = excluded.last_request",
        (telegram_id, request_count, last_request),
    )
    conn.commit()

def reset_daily_limits():
    conn = get_connection()
    conn.execute("UPDATE rate_limits SET request_count = 0")
    conn.commit()

# --- Superadmin bootstrap ---

def ensure_superadmin(telegram_id: str, username: str):
    conn = get_connection()
    conn.execute(
        "INSERT OR IGNORE INTO whitelist_users (telegram_id, username, role) VALUES (?, ?, 'superadmin')",
        (telegram_id, username),
    )
    conn.commit()
