import os
from pathlib import Path
from dotenv import load_dotenv

# .env faylini yuklash
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

BOT_TOKEN: str = os.getenv("BOT_TOKEN", "8878067530:AAHNyoNrslabqqbb6aJ2vUM5qCn3hUBKwiE")
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "AQ.Ab8RN6LvRMqTY8wF1XKsOpAY3r1Qd4liEN-Yu9UQ9JgZL6uJlQ")
DB_NAME: str = os.getenv("DB_NAME", "assalomu_xizmat.db")
DB_PATH: Path = BASE_DIR / DB_NAME
GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")

if not BOT_TOKEN:
    print("[OGOHLANTIRISH] BOT_TOKEN o'rnatilmagan! .env faylini tekshiring.")

if not GEMINI_API_KEY:
    print("[OGOHLANTIRISH] GEMINI_API_KEY o'rnatilmagan! .env faylini tekshiring.")
