import os
from pathlib import Path
from dotenv import load_dotenv
from google import genai

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
ENV_PATH = BASE_DIR / ".env"
load_dotenv(ENV_PATH) 

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError(f"GEMINI_API_KEY not found. Looked in: {ENV_PATH}")
client = genai.Client(api_key=api_key)