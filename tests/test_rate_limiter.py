import time
from bot.services.rate_limiter import check_burst, check_daily, record_request, is_admin_command, BURST_LIMIT, BURST_WINDOW_SECONDS


class TestBurstLimiter:
    def test_allow_within_limit(self):
        assert check_burst("test_user_1") is True

    def test_block_when_exceeded(self):
        uid = "test_user_burst"
        for _ in range(BURST_LIMIT):
            check_burst(uid)
        assert check_burst(uid) is False

    def test_recover_after_window(self):
        uid = "test_user_recover"
        for _ in range(BURST_LIMIT):
            check_burst(uid)
        assert check_burst(uid) is False
        from bot.services.rate_limiter import _burst_buckets
        _burst_buckets[uid] = [t - BURST_WINDOW_SECONDS - 1 for t in _burst_buckets[uid]]
        assert check_burst(uid) is True


class TestAdminCommand:
    def test_admin_commands_exempt(self):
        assert is_admin_command("/add 12345") is True
        assert is_admin_command("/remove 12345") is True
        assert is_admin_command("/listuser") is True
        assert is_admin_command("/saldo") is False
        assert is_admin_command("beli bakso") is False

    def test_case_insensitive(self):
        assert is_admin_command("/ADD 12345") is True


class TestDailyLimiter:
    def test_daily_allow_before_limit(self):
        assert check_daily("new_user_daily") is True

    def test_daily_block_when_exceeded(self):
        uid = "test_daily_full"
        from bot.database import queries
        from datetime import datetime
        queries.add_user(uid, "tester", "user")
        today_str = datetime.now().strftime("%Y-%m-%d")
        queries.upsert_rate_limit(uid, 50, f"{today_str}T12:00:00")
        assert check_daily(uid) is False
