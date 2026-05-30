# Fintra — Finance Tracker Telegram Bot

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://python.org)
[![Telegram Bot](https://img.shields.io/badge/Telegram-Bot-26A5E4)](https://core.telegram.org/bots)
[![Groq](https://img.shields.io/badge/Groq-LLM-F55036)](https://groq.com)
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
- **💰 Zero Operating Cost** — 100% gratis (Telegram API + Groq Free Tier + SQLite)

---

## Tech Stack

| Komponen | Teknologi |
|---|---|
| Runtime | Python 3.10+ |
| Bot Framework | python-telegram-bot 21.x |
| AI/NLP | Groq LLM (llama-3.1-8b-instant) |
| Database | SQLite (WAL mode) |
| Reports | openpyxl (Excel) + fpdf2 (PDF) |
| Scheduler | APScheduler |
| Deployment | Docker / systemd |

---

## Quick Start

### 0. Dapatkan Kredensial

Sebelum mulai, siapkan 3 kredensial berikut:

| Variabel | Cara Mendapatkan |
|---|---|
| `BOT_TOKEN` | Buka Telegram, cari [@BotFather](https://t.me/BotFather), kirim `/newbot`, ikuti petunjuk, salin token yang diberikan |
| `GROQ_API_KEY` | Buka [Groq Console](https://console.groq.com/keys), klik **Create API Key**, salin key |
| `SUPERADMIN_ID` | Buka Telegram, cari [@userinfobot](https://t.me/userinfobot), kirim `/start`, dapatkan ID numerik Anda (contoh: `123456789`) |

### 1. Setup

```bash
git clone https://github.com/juanpradana/FINTRA.git
cd FINTRA
cp .env.example .env
# Isi .env dengan kredensial dari langkah 0 di atas
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

## Migrasi Database (Pindah Mesin)

SQLite Fintra tersimpan di satu file: `data/fintra.db`. Cukup salin file itu ke mesin baru.

### Backup (dari mesin lama)

```bash
# Docker
cp data/fintra.db data/fintra_backup_$(date +%Y%m%d).db

# Atau jalankan script built-in
python scripts/backup_db.py
```

### Restore (ke mesin baru)

```bash
# 1. Clone & setup seperti Quick Start di atas
git clone https://github.com/juanpradana/FINTRA.git
cd FINTRA
cp .env.example .env
# Isi .env dengan kredensial yang SAMA

# 2. Hentikan bot jika sedang berjalan
docker compose down

# 3. Copy file database lama ke folder data/
cp /path/ke/fintra.db data/fintra.db

# 4. Jalankan ulang bot
docker compose up -d
```

> Semua data transaksi, whitelist user, dan rate limit akan langsung tersedia.

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
