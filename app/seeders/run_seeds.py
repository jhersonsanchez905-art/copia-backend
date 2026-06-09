"""
app/seeders/run_seeds.py
Script to run all seeders.
Author: charlykj
Issue: #59
"""
import asyncio
from app.database import AsyncSessionLocal
from app.seeders.catalogo_seeder import seed_catalogos


async def main() -> None:
    async with AsyncSessionLocal() as db:
        await seed_catalogos(db)


if __name__ == "__main__":
    asyncio.run(main())