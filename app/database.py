"""
app/database.py
Database connection and session management.
Provides async SQLAlchemy engine and session factory.
Exposes get_db dependency for use in routers.

Author: Suley Suarez
Issue: #2
"""
import re
import ssl as _ssl

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings


def _build_engine():
    url = settings.DATABASE_URL
    connect_args = {}

    # asyncpg does not accept sslmode in the query string via SQLAlchemy.
    # Strip it and pass SSL through connect_args instead.
    if "sslmode=require" in url:
        url = re.sub(r"[?&]sslmode=require", "", url).rstrip("?")
        connect_args["ssl"] = _ssl.create_default_context()

    return create_async_engine(url, echo=True, connect_args=connect_args)


engine = _build_engine()

AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
