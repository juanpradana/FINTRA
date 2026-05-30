# Fintra — Finance Tracker Telegram Bot

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://python.org)
[![Telegram Bot](https://img.shields.io/badge/Telegram-Bot-26A5E4)](https://core.telegram.org/bots)
[![Gemini AI](https://img.shields.io/badge/Gemini-AI-4285F4)](https://ai.google.dev/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

**Fintra** adalah bot Telegram berbasis AI yang berfungsi sebagai asisten pencatatan keuangan pribadi. Cukup ketik pesan teks biasa, dan AI akan mengekstrak transaksi secara otomatis — tanpa formulir, tanpa ribet.

> ✒️ *Created by Farzani R.B.A.*
>
> 📖 [Product Requirements Document](prd.md) · [Agent Instructions](AGENTS.md)

---

## Fitur

- **🧠 AI-Powered Logging** — Ketik "beli bakso 25 ribu" → otomatis tercatat sebagai pengeluaran
- **🔒 Anti-Abuse** — Rate limiter (5 pesan/menit, 50 transaksi/hari) + strict financial domain enforcer
- **👥 Multi-User** — Whitelist system dengan peran Superadmin & User
- **📊 Laporan Instan** — Generate Excel (.xlsx) & PDF langsung dari Telegram
- **🔄 Auto Backup** — Backup database setiap hari pukul 00:00 WIB
- **💰 Zero Operating Cost** — 100% gratis (Telegram API + Gemini Free Tier + SQLite)

---

## Tech Stack

| Komponen | Teknologi |
|---|---|
| Runtime | Python 3.10+ |
| Bot Framework | python-telegram-bot 21.x |
| AI/NLP | Google Gemini API (gemini-1.5-flash) |
| Database | SQLite (WAL mode) |
| Reports | openpyxl (Excel) + fpdf2 (PDF) |
| Scheduler | APScheduler |
| Deployment | Docker / systemd |

---

## Quick Start

### 1. Setup

```bash
git clone https://github.com/juanpradana/FINTRA.git
cd FINTRA
cp .env.example .env
# Isi .env dengan BOT_TOKEN, GEMINI_API_KEY, SUPERADMIN_ID
```

### 2. Jalankan

**Docker (recommended):**

```bash
docker compose up -d --build
docker compose logs -f
```

**Local:**

```bash
pip install -r requirements.txt
python -m bot
```

### 3. Test

```bash
pytest
```

---

## Commands

| Perintah | Akses | Fungsi |
|---|---|---|
| `/start` | Semua user | Selamat datang & inisialisasi |
| `/help` | Semua user | Dokumentasi & kredit |
| `/saldo` | Semua user | Cek saldo (pemasukan - pengeluaran) |
| `/laporan` | Semua user | Download laporan Excel + PDF |
| `/batal` | Semua user | Hapus transaksi terakhir |
| `/add <id>` | Superadmin | Tambah pengguna ke whitelist |
| `/remove <id>` | Superadmin | Hapus pengguna & datanya |
| `/listuser` | Superadmin | Lihat semua pengguna & kuota |

---

## Struktur Proyek

```
fintra/
├── bot/
│   ├── __main__.py          # Entry point
│   ├── config.py            # Konfigurasi dari .env
│   ├── database/            # SQLite connection & queries
│   ├── services/            # Rate limiter, Gemini client, report generator
│   └── handlers/            # Command & message handlers
├── scripts/
│   ├── backup_db.py         # Database backup
│   └── fintra.service       # Systemd unit file
├── data/                    # SQLite database (persistent)
├── Dockerfile
├── docker-compose.yml
├── AGENTS.md                # Panduan untuk AI agent (OpenCode)
└── prd.md                   # Product Requirements Document
```

---

## Lisensi

MIT — silakan gunakan, modifikasi, dan sebarkan.
