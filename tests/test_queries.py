from bot.database import queries

class TestWhitelist:
    def test_add_and_is_whitelisted(self):
        queries.add_user("111", "user1", "user")
        assert queries.is_whitelisted("111") is True
        assert queries.is_whitelisted("999") is False

    def test_get_user_role(self):
        queries.add_user("111", "user1", "user")
        assert queries.get_user_role("111") == "user"

    def test_remove_user(self):
        queries.add_user("111", "user1", "user")
        queries.remove_user("111")
        assert queries.is_whitelisted("111") is False

    def test_list_users(self):
        queries.add_user("111", "user1", "user")
        queries.add_user("222", "user2", "user")
        users = queries.list_users()
        assert len(users) >= 2

    def test_multi_tenant_isolation(self):
        queries.add_user("111", "user1", "user")
        queries.add_user("222", "user2", "user")
        queries.insert_transaction("111", "pemasukan", 50000, "makanan", "test", "2025-01-01")
        balance_111 = queries.get_balance("111")
        balance_222 = queries.get_balance("222")
        assert balance_111 == 50000
        assert balance_222 == 0


class TestTransactions:
    def test_insert_and_get_last(self):
        queries.add_user("111", "user1", "user")
        queries.insert_transaction("111", "pengeluaran", 25000, "makanan", "bakso", "2025-01-01")
        last = queries.get_last_transaction("111")
        assert last is not None
        assert last["nominal"] == 25000
        assert last["category"] == "makanan"

    def test_delete_transaction(self):
        queries.add_user("111", "user1", "user")
        queries.insert_transaction("111", "pengeluaran", 15000, "transportasi", "bensin", "2025-01-01")
        last = queries.get_last_transaction("111")
        queries.delete_transaction(last["id"], "111")
        assert queries.get_last_transaction("111") is None

    def test_get_balance(self):
        queries.add_user("111", "user1", "user")
        queries.insert_transaction("111", "pemasukan", 100000, "lainnya", "gaji", "2025-01-01")
        queries.insert_transaction("111", "pengeluaran", 30000, "makanan", "makan siang", "2025-01-01")
        assert queries.get_balance("111") == 70000

    def test_monthly_queries(self):
        queries.add_user("111", "user1", "user")
        queries.insert_transaction("111", "pemasukan", 50000, "lainnya", "test", "2025-01-15")
        rows = queries.get_monthly_transactions("111", 2025, 1)
        assert len(rows) == 1
        summary = queries.get_monthly_summary("111", 2025, 1)
        assert summary["total_income"] == 50000
        assert summary["total_expense"] == 0


class TestRateLimits:
    def test_rate_limit_flow(self):
        queries.add_user("111", "user1", "user")
        record = queries.get_rate_limit("111")
        assert record is None
        queries.upsert_rate_limit("111", 1, "2025-01-01T00:00:00")
        record = queries.get_rate_limit("111")
        assert record["request_count"] == 1

    def test_reset_daily_limits(self):
        queries.add_user("111", "user1", "user")
        queries.upsert_rate_limit("111", 30, "2025-01-01T00:00:00")
        queries.reset_daily_limits()
        record = queries.get_rate_limit("111")
        assert record["request_count"] == 0

    def test_ensure_superadmin(self):
        queries.ensure_superadmin("999", "new_admin")
        assert queries.get_user_role("999") == "superadmin"

    def test_ensure_superadmin_ignores_existing(self):
        queries.add_user("111", "user1", "user")
        queries.ensure_superadmin("111", "user1")
        assert queries.get_user_role("111") == "user"
