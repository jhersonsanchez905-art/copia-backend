"""
app/config.py

Application settings loaded from environment variables.
Uses pydantic-settings to validate all required variables on startup.

Author: Suley Suarez
Issue: #2
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    CLERK_SECRET_KEY: str
    RESEND_API_KEY: str = "not-configured"
    CLOUDINARY_URL: str = "not-configured"
    CRON_SECRET: str = "not-configured"
    GOOGLE_SHEETS_ID: str = "not-configured"
    ALLOWED_ORIGINS: list[str] = ["http://localhost:3000"]

    # ── Módulo BI ─────────────────────────────────────────────
    # URL del webhook de Vercel para purgar el caché al terminar el ETL
    VERCEL_REVALIDATE_URL: str = "not-configured"
    # Secreto compartido con Vercel para validar el webhook
    REVALIDATE_SECRET: str = "not-configured"

    class Config:
        env_file = ".env"


settings = Settings()