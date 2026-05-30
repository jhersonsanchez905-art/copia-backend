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
    RESEND_API_KEY: str
    CLOUDINARY_URL: str
    CRON_SECRET: str
    GOOGLE_SHEETS_ID: str

    class Config:
        env_file = ".env"

settings = Settings()
