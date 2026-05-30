import pytest
import os
import tempfile

@pytest.fixture(autouse=True)
def use_temp_db(monkeypatch):
    import bot.config
    from bot.database.connection import close_connection, init_db
    close_connection()
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    monkeypatch.setattr(bot.config, "DB_PATH", db_path)
    monkeypatch.setattr(bot.config, "SUPERADMIN_ID", "12345")
    monkeypatch.setattr(bot.config, "SUPERADMIN_USERNAME", "superadmin")
    init_db()
    yield
    close_connection()
    os.close(db_fd)
    os.unlink(db_path)
