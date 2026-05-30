# Product Requirement Document (PRD)

## Project Name: Fintra - Finance Tracker Telegram Bot

**Author:** Farzani R.B.A.

**Status:** Approved / Core Engineering Spec

**Version:** 1.6 (Strict Domain Enforcer, Rate Limiting, & DB Spec Update)

**Target Launch:** Q3 2026

---

## 1. Executive Summary & Objectives

### 1.1 Project Overview

**Fintra** adalah bot Telegram berbasis AI yang berfungsi sebagai asisten pencatatan keuangan pribadi sekaligus *multi-user platform* terbatas. Bot ini dirancang untuk menyederhanakan proses pencatatan pemasukan dan pengeluaran menggunakan pemrosesan bahasa alami (Natural Language Processing). Pengguna cukup mengetikkan pesan teks kasual, dan AI akan mengekstrak data tersebut menjadi catatan terstruktur, menganalisis pola keuangan, serta menyediakan laporan instan dalam format Excel dan PDF. Untuk melindungi kuota API, privasi data, dan stabilitas server, bot ini dilengkapi dengan sistem keamanan *whitelist*, batas kuota percakapan (*rate limiter*), serta penyaringan domain input yang ketat agar AI hanya memproses topik finansial.

### 1.2 Core Objectives

* **Zero Friction Logging:** Menghilangkan keharusan mengisi formulir rumit; pencatatan dilakukan via chat teks biasa secara instan tanpa awalan perintah.
* **Strict Financial Domain Enforcement:** Memaksa AI untuk menolak segala bentuk obrolan di luar topik pencatatan keuangan, investasi, dan analisis anggaran (anti-abuse).
* **Rate Limiting:** Membatasi jumlah pesan per pengguna per menit/hari untuk mencegah eksploitasi kuota API gratis Gemini.
* **Data Isolation (Privacy):** Memastikan data keuangan antar pengguna terisolasi secara mutlak di dalam database menggunakan SQLite/PostgreSQL terpusat.
* **Temporal Accuracy (UTC+7):** Menjamin seluruh pencatatan waktu transaksi presisi sesuai Zona Waktu Indonesia Barat (WIB), termasuk pemrosesan kata penunjuk waktu relatif.
* **Zero Operating Cost:** Memanfaatkan infrastruktur gratis (*Free Tier*) dari Telegram Bot API, Google AI Studio (Gemini), dan penyimpanan data lokal/cloud yang efisien.

---

## 2. Target Audience & User Persona

* **Superadmin:** Pemilik sistem (Muhammad Juan Pradana) yang memiliki otoritas penuh untuk memberikan/mencabut akses bot, memantau *rate limit*, dan mengaudit performa database.
* **Whitelisted User:** Pengguna terbatas yang ditambahkan oleh Superadmin. Memiliki kebutuhan mobilitas tinggi, ingin mencatat keuangan tanpa iklan, dan membutuhkan laporan instan via Telegram.

---

## 3. Analisis Kelayakan Database: Apakah SQLite Masih Cocok?

**Ya, SQLite masih SANGAT COCOK, dengan catatan:** Penggunaan bot ini bersifat personal, keluarga, atau tim kecil (di bawah 20 pengguna aktif).

### Mengapa SQLite Sangat Bagus untuk Fintra?

1. **Zero Cost & Zero Maintenance:** Tidak memerlukan server database terpisah (seperti PostgreSQL/MySQL). Database disimpan dalam satu file lokal (`fintra.db`), sehingga 100% gratis selamanya.
2. **Kecepatan Operasional:** Untuk aplikasi dengan jumlah penulisan data yang tidak dilakukan secara bersamaan dalam mili-detik yang sama (*low concurrency*), SQLite jauh lebih cepat daripada database cloud karena tidak ada latensi jaringan (*network latency*).
3. **Portabilitas Tinggi:** Sangat mudah di-backup. Anda hanya perlu menyalin file `fintra.db` ke cloud storage (Google Drive/Dropbox) secara berkala lewat script backend.

### Kapan Anda Harus Pindah ke Supabase (PostgreSQL)?

* Jika bot ini digunakan oleh ratusan orang secara bersamaan, SQLite akan memicu error `database is locked` karena SQLite mengunci seluruh file saat terjadi proses penulisan (*write operation*).
* Jika Anda mendeploy backend bot ini di platform *Serverless* (seperti Vercel / AWS Lambda) atau Docker Container di cloud yang bersifat *ephemeral* (datanya terhapus otomatis saat restart).
* **Rekomendasi:** Mulai dengan **SQLite**. Jika pengguna bertambah banyak, Anda tinggal memindahkan datanya ke PostgreSQL karena struktur tabel yang dirancang di bawah ini sudah standar SQL universal.

---

## 4. Functional Requirements (Fitur Utama)

### 4.1 Feature Group 1: Anti-Abuse Rate Limiter (Token Bucket Algorithm)

Sistem backend wajib membatasi jumlah interaksi pengguna sebelum memproses teks ke Gemini API.

* **FR-1.1 (Burst Limit):** Pengguna maksimal hanya dapat mengirimkan **5 pesan per menit**. Jika melanggar, bot akan mengirimkan peringatan: *"Mencatat terlalu cepat. Silakan tunggu beberapa detik."*
* **FR-1.2 (Daily Limit):** Pengguna maksimal hanya memiliki kuota **50 transaksi per hari**. Batasan ini akan di-reset otomatis setiap pukul 00:00 WIB.
* **FR-1.3 (Exemption):** Perintah administratif milik Superadmin (`/add`, `/remove`, `/listuser`) tidak terkena aturan *rate limit*.

### 4.2 Feature Group 2: Strict Financial Domain Enforcement

Sistem harus menolak teks input dari pengguna yang mencoba menggunakan AI untuk kebutuhan non-keuangan (misal: meminta resep masakan, menulis kode pemrograman, atau sekadar mengobrol biasa).

* **FR-2.1 (NLU Filter):** *System Prompt* Gemini dikonfigurasi secara agresif untuk mendeteksi intensi transaksi. Jika teks input terdeteksi berada di luar ruang lingkup pencatatan atau analisis keuangan, AI wajib mengembalikan kode error JSON tertentu.
* **FR-2.2 (Fallback Block):** Backend yang menerima kode error tersebut akan langsung menghentikan proses eksekusi dan mengirimkan pesan penolakan standar ke Telegram tanpa menyimpan data apa pun ke database.

### 4.3 Feature Group 3: Explicit Command Routing Engine

Sistem mengeksekusi fungsi spesifik berdasarkan perintah garis miring (`/`) yang dikirim oleh pengguna sesuai hak aksesnya.

#### A. Superadmin Commands

* **FR-3.1 (`/add`):** Mendaftarkan pengguna baru ke tabel `whitelist_users`.
* **FR-3.2 (`/remove`):** Mencabut akses pengguna secara instan dari database.
* **FR-3.3 (`/listuser`):** Menampilkan daftar pengguna beserta status penggunaan kuota harian mereka.

#### B. Whitelisted User Commands

* **FR-3.4 (`/start`):** Mengaktifkan bot, menginisialisasi sesi pengguna, dan menampilkan pesan selamat datang.
* **FR-3.5 (`/help`):** Menampilkan dokumentasi kategori valid, batas limit harian, serta atribusi pencipta sistem (*"Created by Farzani R.B.A."*).
* **FR-3.6 (`/saldo`):** Melakukan agregasi matematika instan: $\text{Saldo} = \sum \text{Pemasukan} - \sum \text{Pengeluaran}$.
* **FR-3.7 (`/laporan`):** Menghasilkan laporan berkas `.xlsx` dan `.pdf` berisi ringkasan finansial dan grafik pengeluaran berdasarkan data historis pengguna.
* **FR-3.8 (`/batal`):** Menghapus satu baris transaksi terakhir yang dimasukkan oleh pengguna berdasarkan timestamp terbaru (*quick-undo*).

---

## 5. Database Schema Specifications (SQLite Compatible)

### 5.1 Tabel: `whitelist_users`

```sql
CREATE TABLE whitelist_users (
    telegram_id TEXT PRIMARY KEY,
    username TEXT,
    role TEXT NOT NULL CHECK (role IN ('superadmin', 'user')),
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

```

### 5.2 Tabel: `transactions`

```sql
CREATE TABLE transactions (
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

```

### 5.3 Tabel: `rate_limits` (Untuk melacak kuota harian)

```sql
CREATE TABLE rate_limits (
    telegram_id TEXT PRIMARY KEY,
    request_count INTEGER DEFAULT 0,
    last_request TIMESTAMP,
    FOREIGN KEY (telegram_id) REFERENCES whitelist_users(telegram_id)
);

```

---

## 6. Prompt Engineering Specification (Core Enforcer)

```text
Context: You are a strict, single-purpose financial data extraction engine. You are not allowed to chat, converse, or answer questions outside personal financial tracking and financial analysis.
Current Time Context: Today is {{ CURRENT_DATE_WIB }} (Format: YYYY-MM-DD, Zone: UTC+7).

Task: Parse the user's text input into a clean JSON object.

Strict Domain Guards (Anti-Abuse Rules):
1. If the user input is NOT related to a financial transaction (income/expense logging) or a request for a monthly financial review/analysis, you MUST strictly return exactly: {"error": "out_of_domain"}.
2. Do not answer questions like "Who created you?", "Write a python code", "Give me a recipe", or "Hello, how are you?". Treat all of them as out of domain.

Rules for Temporal Logic:
1. Calculate the 'transaction_date' dynamically based on the Current Time Context.
2. If relative time words are used (e.g., 'kemarin'), subtract 1 day from {{ CURRENT_DATE_WIB }}. If 'dua hari lalu', subtract 2 days.

General Output Rules:
1. Do not include any conversational text, explanations, or markdown code block ticks. Return ONLY raw JSON string.

Schema for Valid Transaction:
{
  "type": "pemasukan" or "pengeluaran",
  "nominal": integer,
  "category": "makanan" | "transportasi" | "hiburan" | "tagihan" | "investasi" | "lainnya",
  "note": "string detailing the item",
  "transaction_date": "YYYY-MM-DD"
}

```

---

## 7. User Interface Flow & Command UX

### 7.1 Deteksi Out of Domain (Percobaan Penyalahgunaan AI)

* **User:** *"Tuliskan kode python untuk kalkulator"*
* **Backend System:** Gemini mendeteksi pelanggaran aturan dan mengembalikan `{"error": "out_of_domain"}`.
* **Bot:** "❌ **Akses Ditolak.** Sistem Fintra hanya menerima input terkait pencatatan transaksi keuangan dan analisis anggaran."

### 7.2 Deteksi Rate Limit (Abuse Prevention)

* *(User mengirim pesan pencatatan ke-6 dalam waktu kurang dari 1 menit)*
* **Bot:** "⚠️ **Mencatat Terlalu Cepat!** Batas maksimal input adalah 5 pesan per menit untuk menjaga stabilitas sistem. Silakan tunggu beberapa saat lagi."

### 7.3 Tampilan Perintah /help & Tampilan Kredit Author (Whitelisted User)

* **User:** `/help`
* **Bot:**
"ℹ️ **Fintra Help Desk & Documentation**\n\n"
"Cukup ketik pesan teks biasa tanpa command untuk mencatat keuangan secara otomatis.\n\n"
"🔒 **Batasan Penggunaan (Anti-Spam):**\n"
"• Maksimal 5 pesan / menit.\n"
"• Maksimal 50 transaksi / hari.\n\n"
"💡 **Contoh Input:**\n"
"• *'beli bakso 25 ribu tadi siang'*\n"
"• *'kemarin sore bayar cicilan motor 1.5 juta'*\n\n"
"📂 **Kategori Valid:**\n"
"`makanan`, `transportasi`, `hiburan`, `tagihan`, `investasi`, `lainnya`.\n\n"
"🛠️ **Daftar Perintah:**\n"
"/saldo - Cek akumulasi sisa dana saat ini.\n"
"/laporan - Unduh rekap laporan Excel & PDF bulan berjalan.\n"
"/batal - Menghapus catatan transaksi terakhir Anda.\n"
"---------------------------------------\n"
"✒️ *Fintra Version 1.6 | Created by Farzani R.B.A.*"

---

## 8. Non-Functional Requirements & Security Guardrails

* **Multi-Tenant Isolation Protection:** Filter query SQL wajib menggunakan klausa `WHERE telegram_id = ?` pada setiap fungsi baca/tulis guna menghindari kebocoran data finansial antar-user.
* **SQLite Database Backups:** Backend harus dikonfigurasi untuk mengekspor atau menduplikasi file `fintra.db` secara berkala (misal setiap jam 23:59 WIB) ke direktori cadangan eksternal demi keamanan data.
* **Quota Optimization Gate:** Lapisan pengecekan *rate limit* lokal dijalankan di memori backend sebelum melakukan *hit* ke API Gemini, mengamankan batas kuota harian *Free Tier* Anda secara efisien.