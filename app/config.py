import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    APP_API_KEY: str = os.getenv("APP_API_KEY", "change-this-to-a-long-random-string")
    CHROMA_DIR: str = os.getenv("CHROMA_DIR", "/tmp/chroma")
    SQLITE_PATH: str = os.getenv("SQLITE_PATH", "./data/app.db")
    MAX_DISTANCE_THRESHOLD: float = float(os.getenv("MAX_DISTANCE_THRESHOLD", "1.5"))
    MAX_HISTORY_TURNS: int = int(os.getenv("MAX_HISTORY_TURNS", "6"))
    TOP_K: int = int(os.getenv("TOP_K", "4"))


settings = Settings()