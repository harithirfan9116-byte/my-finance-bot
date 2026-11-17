
import os
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(BASE_DIR, ".env")

load_dotenv(ENV_PATH, override=True)

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN tidak dijumpai!")

print("Token berjaya dibaca!")
print("Token length:", len(BOT_TOKEN))
print("Token prefix:", BOT_TOKEN.split(":")[0] if ":" in BOT_TOKEN else "FORMAT SALAH")
