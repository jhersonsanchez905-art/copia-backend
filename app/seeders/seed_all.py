"""
seed_all.py
Ejecuta todos los seeders en orden.

Ejecutar:  python -m app.seeders.seed_all
"""
import asyncio

from app.seeders.seed_catalogo import main as seed_catalogo
from app.seeders.seed_mesas import main as seed_mesas


async def main() -> None:
    await seed_catalogo()
    print()
    await seed_mesas()
    print("\n=== Todos los seeders completados ===")


if __name__ == "__main__":
    asyncio.run(main())
