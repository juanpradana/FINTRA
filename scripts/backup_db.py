import shutil
import os
from datetime import datetime

DB_PATH = os.getenv("DB_PATH", "data/fintra.db")
BACKUP_DIR = os.getenv("BACKUP_DIR", "data/backups")

def backup_database():
    os.makedirs(BACKUP_DIR, exist_ok=True)
    if not os.path.exists(DB_PATH):
        print("Database file not found, skipping backup.")
        return
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"fintra_{timestamp}.db"
    backup_path = os.path.join(BACKUP_DIR, backup_name)
    shutil.copy2(DB_PATH, backup_path)
    print(f"Database backed up to {backup_path}")

if __name__ == "__main__":
    backup_database()
