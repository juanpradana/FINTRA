# Fintra — Finance Tracker Telegram Bot

## Stack
Python 3.10+, python-telegram-bot 21.x, Groq LLM API, SQLite, APScheduler.

## Hybrid LLM Architecture
Two Groq models for different tasks (maximize free tier quotas):

| Task | Model | Rationale |
|---|---|---|
| Daily transaction parsing | `llama-3.1-8b-instant` | 14.4K req/day (user sends many messages), 6K TPM (enough for short text) |
| Monthly AI report analysis | `meta-llama/llama-4-scout-17b-16e-instruct` | 30K TPM (fits aggregated monthly data), 1K req/day (on-demand only) |

Data sent to report model is **pre-aggregated by category** in Python, not raw rows.

## Entrypoint
```
python -m bot
```
Registered in `bot/__main__.py`. All handlers wired there.

## Repo Map
| Path | Purpose |
|---|---|
| `bot/__main__.py` | App bootstrap, handler registration, scheduler |
| `bot/config.py` | Env-based config (`.env` file) |
| `bot/database/connection.py` | SQLite init + singleton connection (WAL mode) |
| `bot/database/queries.py` | All parameterized SQL — **every read/write has `WHERE telegram_id = ?`** (multi-tenant isolation) |
| `bot/services/rate_limiter.py` | In-memory token bucket (burst) + DB-backed daily counter |
| `bot/services/llm_client.py` | Groq calls — `parse_transaction` (8B) + `generate_report_analysis` (17B) |
| `bot/services/report.py` | Excel (openpyxl) + PDF (fpdf2) generator |
| `bot/handlers/` | Command & message handlers |
| `scripts/backup_db.py` | Standalone DB backup script |

## Rate Limiter Rules
- **Burst:** 5 messages / 60s per user (in-memory dict, resets on inactivity)
- **Daily:** 50 transactions / day per user (DB `rate_limits` table)
- **Exempt:** `/add`, `/remove`, `/listuser` (admin commands only)
- Reset daily limits + backup DB at 00:00 WIB (APScheduler cron)

## LLM Prompts
- **Parsing prompt** in `llm_client.py` from PRD Section 6. Key behaviors:
  - Rejects non-financial input → returns `{"error": "out_of_domain"}`
  - Parses relative dates ("kemarin", "dua hari lalu") relative to UTC+7 today
  - Output: raw JSON only (`{"type","nominal","category","note","transaction_date"}`) — kategori: makanan, minuman, transportasi, belanja, hiburan, tagihan, kesehatan, investasi, lainnya
- **Report prompt** in `llm_client.py` — sends aggregated category data to 17B model for analysis in Bahasa Indonesia (ringkasan, kategori terbesar, pola belanja, saran hemat).

## Database
3 tables: `whitelist_users`, `transactions`, `rate_limits`.
SQLite file at `data/fintra.db` (configurable via `DB_PATH` env).

## Commands
| Command | Who | What |
|---|---|---|
| `/start` | All whitelisted | Welcome + init |
| `/help` | All whitelisted | Usage doc + credits |
| `/saldo` | All whitelisted | Balance = income - expense (current month) |
| `/laporan` | All whitelisted | AI analysis + XLSX + PDF |
| `/laporan3` | All whitelisted | AI analysis 3-month trend |
| `/batal` | All whitelisted | Delete last transaction |
| `/add <id> [username]` | Superadmin only | Whitelist user |
| `/remove <id>` | Superadmin only | Remove user + all their data |
| `/listuser` | Superadmin only | List users + daily quota usage |

## Dev Commands
```bash
python -m bot              # Run bot (needs .env with BOT_TOKEN)
pytest                     # All tests
pytest tests/test_file.py  # Single test file
```

## Verification Order
1. `pytest`
2. `python -m bot` (smoke test — bot connects and responds)

## Superadmin
Bootstrapped automatically on `/start` from `SUPERADMIN_ID` env var. Ignored if already exists.

## Deployment

### Docker (recommended)
```bash
docker compose up -d --build
# Logs:
docker compose logs -f
# Stop:
docker compose down
```
SQLite DB persists in `data/` via bind mount (defined in `docker-compose.yml`).
Rebuild after code changes: `docker compose up -d --build`.

### VPS (systemd)
- Python 3.10+, `.env` in project root
- Systemd service in `scripts/fintra.service`
- Run: `python -m bot` behind systemd or tmux
- Backup: `python scripts/backup_db.py`

## PRD
`prd.md` in repo root — the authoritative spec. Consult before adding features.
