"""
seed_mesas.py
Siembra las mesas del establecimiento.
Ajusta el número y capacidad según el local.

Ejecutar:  python -m app.seeders.seed_mesas
"""
import asyncio

from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models.mesa import Mesa


MESAS = [
    {"numero": "M01", "capacidad": 2, "zona": "Interior"},
    {"numero": "M02", "capacidad": 2, "zona": "Interior"},
    {"numero": "M03", "capacidad": 4, "zona": "Interior"},
    {"numero": "M04", "capacidad": 4, "zona": "Interior"},
    {"numero": "M05", "capacidad": 4, "zona": "Interior"},
    {"numero": "M06", "capacidad": 6, "zona": "Interior"},
    {"numero": "M07", "capacidad": 6, "zona": "Segundo piso"},
    {"numero": "M08", "capacidad": 4, "zona": "Segundo piso"},
    {"numero": "M09", "capacidad": 4, "zona": "Segundo piso"},
    {"numero": "M10", "capacidad": 2, "zona": "Barra"},
]


async def main() -> None:
    print("=== Seeder: mesas ===")
    async with AsyncSessionLocal() as session:
        for data in MESAS:
            existe = await session.execute(select(Mesa).where(Mesa.numero == data["numero"]))
            if existe.scalar_one_or_none() is None:
                session.add(Mesa(estado="disponible", activo=True, **data))
                print(f"  + mesa: {data['numero']} ({data['zona']}, {data['capacidad']} personas)")
            else:
                print(f"  = ya existe: {data['numero']}")
        await session.commit()
    print("\n✓ Seeder completado.")


if __name__ == "__main__":
    asyncio.run(main())
