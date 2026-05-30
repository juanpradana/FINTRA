import json
from google import genai
from google.genai import types
from datetime import datetime
from bot.config import GEMINI_API_KEY, TIMEZONE
import pytz

SYSTEM_PROMPT_TEMPLATE = """Context: You are a strict, single-purpose financial data extraction engine. You are not allowed to chat, converse, or answer questions outside personal financial tracking and financial analysis.
Current Time Context: Today is {current_date_wib} (Format: YYYY-MM-DD, Zone: UTC+7).

Task: Parse the user's text input into a clean JSON object.

Strict Domain Guards (Anti-Abuse Rules):
1. If the user input is NOT related to a financial transaction (income/expense logging) or a request for a monthly financial review/analysis, you MUST strictly return exactly: {{"error": "out_of_domain"}}.
2. Do not answer questions like "Who created you?", "Write a python code", "Give me a recipe", or "Hello, how are you?". Treat all of them as out of domain.

Rules for Temporal Logic:
1. Calculate the 'transaction_date' dynamically based on the Current Time Context.
2. If relative time words are used (e.g., 'kemarin'), subtract 1 day from {current_date_wib}. If 'dua hari lalu', subtract 2 days.

General Output Rules:
1. Do not include any conversational text, explanations, or markdown code block ticks. Return ONLY raw JSON string.

Schema for Valid Transaction:
{{
  "type": "pemasukan" or "pengeluaran",
  "nominal": integer,
  "category": "makanan" | "transportasi" | "hiburan" | "tagihan" | "investasi" | "lainnya",
  "note": "string detailing the item",
  "transaction_date": "YYYY-MM-DD"
}}"""

def _get_current_date_wib() -> str:
    tz = pytz.timezone(TIMEZONE)
    return datetime.now(tz).strftime("%Y-%m-%d")

def parse_transaction(user_text: str) -> dict:
    client = genai.Client(api_key=GEMINI_API_KEY)

    current_date = _get_current_date_wib()
    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(current_date_wib=current_date)

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=user_text,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=0.1,
            max_output_tokens=200,
        ),
    )

    raw = response.text.strip()
    if raw.startswith("```"):
        raw = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"error": "parse_failed", "raw": raw}
