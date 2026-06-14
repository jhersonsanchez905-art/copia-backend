"""
app/config.py

Application settings loaded from environment variables.
Uses pydantic-settings to validate all required variables on startup.

Author: Suley Suarez
Issue: #2
"""

from typing import Annotated

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode


class Settings(BaseSettings):
    DATABASE_URL: str
    CLERK_SECRET_KEY: str
    NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY: str = "not-configured"
    # Frontend API URL de Clerk usado para validar el claim 'iss' del JWT.
    # Si no se define, se deriva de NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY.
    CLERK_ISSUER: str = "not-configured"
    RESEND_API_KEY: str = "not-configured"
    CLOUDINARY_URL: str = "not-configured"
    CRON_SECRET: str = "not-configured"
    GOOGLE_SHEETS_ID: str = "not-configured"
    ENVIRONMENT: str = "development"
    # Orígenes permitidos para CORS y para validar el claim 'azp' del JWT
    # de Clerk. En producción debe incluir el dominio del frontend
    # desplegado (ej. "https://majesa.vercel.app"), o tanto CORS como la
    # verificación de token rechazarán al frontend real.
    # Acepta una lista JSON (["https://a.com","https://b.com"]) o una
    # cadena separada por comas (https://a.com,https://b.com).
    ALLOWED_ORIGINS: Annotated[list[str], NoDecode] = [
        "http://localhost:3000",
        "http://localhost:5173",
    ]

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def _split_allowed_origins(cls, value):
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    # ── Módulo BI ─────────────────────────────────────────────
    # URL del webhook de Vercel para purgar el caché al terminar el ETL
    VERCEL_REVALIDATE_URL: str = "not-configured"
    # Secreto compartido con Vercel para validar el webhook
    REVALIDATE_SECRET: str = "not-configured"

    class Config:
        env_file = ".env"


settings = Settings()