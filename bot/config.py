import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
SUPERADMIN_ID: str = os.getenv("SUPERADMIN_ID", "")
SUPERADMIN_USERNAME: str = os.getenv("SUPERADMIN_USERNAME", "")
DB_PATH: str = os.getenv("DB_PATH", "data/fintra.db")
BACKUP_DIR: str = os.getenv("BACKUP_DIR", "data/backups")
TIMEZONE: str = os.getenv("TIMEZONE", "Asia/Jakarta")

BURST_LIMIT: int = 5
BURST_WINDOW_SECONDS: int = 60
DAILY_LIMIT: int = 50
