import os
from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Database
    DATABASE_URL: str = "postgresql://querypilot:querypilot_password@localhost:5432/querypilot_app"
    
    # LLM Settings
    LLM_PROVIDER: Literal["openai", "groq", "gemini", "mock"] = "openai"
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.0-flash"

    # Server & UI
    BACKEND_PORT: int = 8000
    FRONTEND_URL: str = "http://localhost:3000"
    DEFAULT_CURRENCY_SYMBOL: str = "₹"
    MAX_ROWS: int = 100
    QUERY_TIMEOUT_SECONDS: int = 15


settings = Settings()
