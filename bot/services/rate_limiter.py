import time
from datetime import datetime
from bot.config import BURST_LIMIT, BURST_WINDOW_SECONDS, DAILY_LIMIT, TIMEZONE
from bot.database import queries
import pytz

_burst_buckets: dict[str, list[float]] = {}

ADMIN_COMMANDS = {"/add", "/remove", "/listuser"}

def is_admin_command(text: str) -> bool:
    stripped = text.strip().split()[0].lower()
    return stripped in ADMIN_COMMANDS

def check_burst(telegram_id: str) -> bool:
    now = time.time()
    timestamps = _burst_buckets.get(telegram_id, [])
    timestamps = [t for t in timestamps if now - t < BURST_WINDOW_SECONDS]
    if len(timestamps) >= BURST_LIMIT:
        _burst_buckets[telegram_id] = timestamps
        return False
    timestamps.append(now)
    _burst_buckets[telegram_id] = timestamps
    return True

def _get_today_wib() -> str:
    tz = pytz.timezone(TIMEZONE)
    return datetime.now(tz).strftime("%Y-%m-%d")

def check_daily(telegram_id: str) -> bool:
    record = queries.get_rate_limit(telegram_id)
    today = _get_today_wib()
    if record:
        last_date = record["last_request"]
        if last_date and last_date[:10] == today:
            return record["request_count"] < DAILY_LIMIT
    return True

def record_request(telegram_id: str):
    record = queries.get_rate_limit(telegram_id)
    today = _get_today_wib()
    if record and record["last_request"] and record["last_request"][:10] == today:
        queries.upsert_rate_limit(telegram_id, record["request_count"] + 1, datetime.now().isoformat())
    else:
        queries.upsert_rate_limit(telegram_id, 1, datetime.now().isoformat())

def get_daily_usage(telegram_id: str) -> int:
    record = queries.get_rate_limit(telegram_id)
    today = _get_today_wib()
    if record and record["last_request"] and record["last_request"][:10] == today:
        return record["request_count"]
    return 0
