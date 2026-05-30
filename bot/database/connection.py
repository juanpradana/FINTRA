import sqlite3
import os
import bot.config

_connection: sqlite3.Connection | None = None

def get_connection() -> sqlite3.Connection:
    global _connection
    if _connection is None:
        db_path = bot.config.DB_PATH
        os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
        _connection = sqlite3.connect(db_path, check_same_thread=False)
        _connection.row_factory = sqlite3.Row
        _connection.execute("PRAGMA journal_mode=WAL")
        _connection.execute("PRAGMA foreign_keys=ON")
    return _connection

def init_db():
    conn = get_connection()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS whitelist_users (
            telegram_id TEXT PRIMARY KEY,
            username TEXT,
            role TEXT NOT NULL CHECK (role IN ('superadmin', 'user')),
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            telegram_id TEXT,
            type TEXT NOT NULL CHECK (type IN ('pemasukan', 'pengeluaran')),
            nominal INTEGER NOT NULL,
            category TEXT NOT NULL CHECK (category IN ('makanan', 'transportasi', 'hiburan', 'tagihan', 'investasi', 'lainnya')),
            note TEXT,
            transaction_date DATE NOT NULL,
            FOREIGN KEY (telegram_id) REFERENCES whitelist_users(telegram_id)
        );

        CREATE TABLE IF NOT EXISTS rate_limits (
            telegram_id TEXT PRIMARY KEY,
            request_count INTEGER DEFAULT 0,
            last_request TIMESTAMP,
            FOREIGN KEY (telegram_id) REFERENCES whitelist_users(telegram_id)
        );
    """)
    conn.commit()

def close_connection():
    global _connection
    if _connection is not None:
        _connection.close()
        _connection = None
