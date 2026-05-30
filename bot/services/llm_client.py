import json
import logging
from datetime import datetime
from groq import Groq
from groq.types.chat import ChatCompletion
from bot.config import GROQ_API_KEY, TIMEZONE
import pytz

logger = logging.getLogger(__name__)

REPORT_SYSTEM_PROMPT = """Kamu adalah analis keuangan pribadi untuk FINTRA (Finance Tracker). 
Tugasmu adalah menganalisis laporan keuangan bulanan pengguna dan memberikan insight yang actionable.

Bulan: {month_name}

Data keuangan:
{summary_data}

Beri analisis dalam bahasa Indonesia dengan format:
1. **Ringkasan** — Total pemasukan, pengeluaran, dan saldo bulan ini.
2. **Kategori Terbesar** — Kategori pengeluaran terbesar dan nominalnya.
3. **Pola Belanja** — Observasi singkat tentang kebiasaan finansial pengguna.
4. **Saran Hemat** — 1-2 tips spesifik dan realistis berdasarkan data.

Gunakan gaya bahasa yang ramah, singkat, dan langsung ke point. Jangan gunakan markdown."""

PARSING_SYSTEM_PROMPT_TEMPLATE = """You are a strict, single-purpose financial data extraction engine for FINTRA (Finance Tracker). You are not allowed to chat, converse, or answer questions outside personal financial tracking and financial analysis.
Current Time Context: Today is {current_date_wib} (Format: YYYY-MM-DD HH:MM, Zone: UTC+7).

Task: Parse the user's text input into a clean JSON object.

Strict Domain Guards (Anti-Abuse Rules):
1. If the user input is NOT related to a financial transaction (income/expense logging) or a request for a monthly financial review/analysis, you MUST strictly return exactly: {{"error": "out_of_domain"}}.
2. Do not answer questions like "Who created you?", "Write a python code", "Give me a recipe", or "Hello, how are you?". Treat all of them as out of domain.

Rules for Temporal Logic:
1. Calculate the 'transaction_date' dynamically based on the Current Time Context, output format must be "YYYY-MM-DD HH:MM".
2. If relative time words are used (e.g., 'kemarin'), subtract 1 day from {current_date_wib}. If 'dua hari lalu', subtract 2 days.
3. If the user mentions time (e.g., 'jam 2', 'tadi siang', 'pagi', 'sore'), infer the hour and minute accordingly. If no time is mentioned, use the current time from Current Time Context.

General Output Rules:
1. Do not include any conversational text, explanations, or markdown code block ticks. Return ONLY raw JSON string.

Schema for Valid Transaction:
{{
  "type": "pemasukan" or "pengeluaran",
  "nominal": integer,
  "category": depends on type —
    if type is "pemasukan": "gaji" | "freelance" | "bisnis" | "investasi" | "hadiah" | "lainnya",
    if type is "pengeluaran": "makanan" | "minuman" | "transportasi" | "belanja" | "hiburan" | "tagihan" | "kesehatan" | "investasi" | "lainnya",
  "note": "string detailing the item",
  "transaction_date": "YYYY-MM-DD HH:MM"
}}"""

client = Groq(api_key=GROQ_API_KEY)


def _get_current_date_wib() -> str:
    tz = pytz.timezone(TIMEZONE)
    return datetime.now(tz).strftime("%Y-%m-%d %H:%M")


def parse_transaction(user_text: str) -> dict:
    current_date = _get_current_date_wib()
    system_prompt = PARSING_SYSTEM_PROMPT_TEMPLATE.format(current_date_wib=current_date)

    try:
        response: ChatCompletion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_text},
            ],
            temperature=0.1,
            max_tokens=200,
            response_format={"type": "json_object"},
        )

        raw = response.choices[0].message.content.strip()
        if raw.startswith("```"):
            raw = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()

        return json.loads(raw)

    except Exception as e:
        logger.error(f"LLM error: {e}")
        return {"error": "llm_failed"}


def generate_report_analysis(summary: dict, category_summary: list[dict], month_name: str) -> str:
    lines = [f"Total Pemasukan: Rp{summary['total_income']:,}", f"Total Pengeluaran: Rp{summary['total_expense']:,}"]
    balance = summary["total_income"] - summary["total_expense"]
    lines.append(f"Saldo Akhir: Rp{balance:,}")
    lines.append("")
    lines.append("Pengeluaran per Kategori:")
    for cs in category_summary:
        lines.append(f"- {cs['category']}: Rp{cs['total']:,}")

    summary_data = "\n".join(lines)

    system_prompt = REPORT_SYSTEM_PROMPT.format(month_name=month_name, summary_data=summary_data)

    try:
        response: ChatCompletion = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": "Beri analisis laporan keuangan saya."},
            ],
            temperature=0.2,
            max_tokens=600,
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        logger.error(f"Report analysis LLM error: {e}")
        return "⚠️ Analisis AI tidak tersedia saat ini. Silakan coba lagi nanti."


MULTI_MONTH_PROMPT = """Kamu adalah analis keuangan pribadi untuk FINTRA (Finance Tracker).
Tugasmu menganalisis tren keuangan multi-bulan dan memberikan insight actionable.

Data transaksi {num_months} bulan terakhir ({months_range}):

{summary_data}

Beri analisis dalam bahasa Indonesia dengan format:
1. **Ringkasan Multi-Bulan** — Total pemasukan, pengeluaran, dan saldo per bulan.
2. **Tren Pengeluaran** — Apakah pengeluaran membaik atau memburuk? Identifikasi pola.
3. **Kategori Bocor Halus** — Kategori pengeluaran tertinggi secara konsisten.
4. **Rekomendasi Konkret** — 2-3 saran spesifik untuk bulan depan berdasarkan data.

Gunakan gaya ramah, singkat, langsung ke point. Jangan gunakan markdown."""


def generate_multi_month_analysis(monthly_data: list[dict]) -> str:
    lines = []
    for md in monthly_data:
        s = md["summary"]
        balance = s["total_income"] - s["total_expense"]
        lines.append(f"{md['month']}:")
        lines.append(f"  Pemasukan: Rp{s['total_income']:,} | Pengeluaran: Rp{s['total_expense']:,} | Saldo: Rp{balance:,}")
        if md["categories"]:
            cats = ", ".join(f"{c['category']} (Rp{c['total']:,})" for c in md["categories"])
            lines.append(f"  Kategori: {cats}")
        lines.append("")

    summary_data = "\n".join(lines).strip()
    months_range = f"{monthly_data[0]['month']} - {monthly_data[-1]['month']}"
    num_months = len(monthly_data)

    system_prompt = MULTI_MONTH_PROMPT.format(
        num_months=num_months, months_range=months_range, summary_data=summary_data
    )

    try:
        response: ChatCompletion = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": "Beri analisis tren keuangan 3 bulan saya."},
            ],
            temperature=0.2,
            max_tokens=800,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Multi-month LLM error: {e}")
        return "⚠️ Analisis AI tidak tersedia saat ini. Silakan coba lagi nanti."


DATE_PARSE_PROMPT = """Hari ini adalah {current_date_wib} (Format: YYYY-MM-DD, Zone: UTC+7).

Tugasmu adalah mengekstrak bulan dan tahun dari chat user yang meminta laporan keuangan.

Aturan:
1. Jika user menyebut nama bulan (e.g., "januari", "feb", "maret"), konversi ke angka (1-12).
2. Jika user menyebut tahun, gunakan tahun tersebut.
3. Jika user TIDAK menyebut tahun, gunakan tahun sekarang ({current_year}).
4. Jika user bilang "bulan lalu" atau "kemarin", hitung relative dari hari ini.
5. Jika tidak ada informasi bulan sama sekali, gunakan bulan dan tahun sekarang.

Output HARUS berupa JSON murni:
{{"bulan": integer_1_sampai_12, "tahun": integer_tahun}}"""


def parse_report_date(user_text: str) -> dict:
    current_date = _get_current_date_wib()
    current_year = current_date[:4]
    system_prompt = DATE_PARSE_PROMPT.format(
        current_date_wib=current_date, current_year=current_year
    )
    try:
        response: ChatCompletion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_text},
            ],
            temperature=0.0,
            max_tokens=50,
            response_format={"type": "json_object"},
        )
        raw = response.choices[0].message.content.strip()
        return json.loads(raw)
    except Exception as e:
        logger.error(f"Date parse LLM error: {e}")
        from datetime import datetime
        import pytz
        tz = pytz.timezone(TIMEZONE)
        now = datetime.now(tz)
        return {"bulan": now.month, "tahun": now.year}
