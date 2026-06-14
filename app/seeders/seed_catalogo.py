"""
seed_catalogo.py
Siembra los datos base del catálogo: roles, unidades de medida,
clasificaciones, categorías, métodos de pago y marcas.

Ejecutar:  python -m app.seeders.seed_catalogo
"""
import asyncio

from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models.catalogo import (
    Categoria,
    Clasificacion,
    Marca,
    MetodoPago,
    Rol,
    UnidadMedida,
)


async def seed_roles(session) -> None:
    roles = [
        {"nombre": "super_admin",   "descripcion": "Acceso total al sistema, incluida la gestión de administradores"},
        {"nombre": "administrador", "descripcion": "Acceso total al sistema"},
        {"nombre": "cajero",        "descripcion": "Opera la caja y registra ventas"},
        {"nombre": "mesero",        "descripcion": "Toma pedidos y gestiona mesas"},
    ]
    for data in roles:
        existe = await session.execute(select(Rol).where(Rol.nombre == data["nombre"]))
        if existe.scalar_one_or_none() is None:
            session.add(Rol(**data))
            print(f"  + rol: {data['nombre']}")
        else:
            print(f"  = rol ya existe: {data['nombre']}")


async def seed_unidades(session) -> None:
    unidades = [
        {"nombre": "Gramo",       "abreviatura": "g"},
        {"nombre": "Kilogramo",   "abreviatura": "kg"},
        {"nombre": "Mililitro",   "abreviatura": "ml"},
        {"nombre": "Litro",       "abreviatura": "l"},
        {"nombre": "Unidad",      "abreviatura": "und"},
        {"nombre": "Porción",     "abreviatura": "porc"},
        {"nombre": "Taza",        "abreviatura": "taza"},
        {"nombre": "Cucharada",   "abreviatura": "cda"},
        {"nombre": "Cucharadita", "abreviatura": "cdta"},
    ]
    for data in unidades:
        existe = await session.execute(select(UnidadMedida).where(UnidadMedida.abreviatura == data["abreviatura"]))
        if existe.scalar_one_or_none() is None:
            session.add(UnidadMedida(**data))
            print(f"  + unidad: {data['abreviatura']}")
        else:
            print(f"  = unidad ya existe: {data['abreviatura']}")


async def seed_clasificaciones(session) -> None:
    clasificaciones = [
        {"nombre": "Perecedero",      "descripcion": "Insumos con fecha de vencimiento corta"},
        {"nombre": "No perecedero",   "descripcion": "Insumos con larga vida útil"},
        {"nombre": "Bebida",          "descripcion": "Líquidos para preparación"},
        {"nombre": "Lácteo",          "descripcion": "Leche, crema, mantequilla y derivados"},
        {"nombre": "Panadería",       "descripcion": "Harinas, panes y masas"},
        {"nombre": "Condimento",      "descripcion": "Especias, salsas y aderezos"},
        {"nombre": "Proteína",        "descripcion": "Carnes, huevos y derivados"},
        {"nombre": "Vegetal",         "descripcion": "Frutas, verduras y hortalizas"},
        {"nombre": "Empaque",         "descripcion": "Vasos, cajas, bolsas y similares"},
    ]
    for data in clasificaciones:
        existe = await session.execute(select(Clasificacion).where(Clasificacion.nombre == data["nombre"]))
        if existe.scalar_one_or_none() is None:
            session.add(Clasificacion(**data))
            print(f"  + clasificacion: {data['nombre']}")
        else:
            print(f"  = clasificacion ya existe: {data['nombre']}")


async def seed_categorias(session) -> None:
    categorias = [
        {"nombre": "Cocina"},
        {"nombre": "Bar"},
        {"nombre": "Panadería"},
    ]
    for data in categorias:
        existe = await session.execute(select(Categoria).where(Categoria.nombre == data["nombre"]))
        if existe.scalar_one_or_none() is None:
            session.add(Categoria(**data))
            print(f"  + categoria: {data['nombre']}")
        else:
            print(f"  = categoria ya existe: {data['nombre']}")


async def seed_metodos_pago(session) -> None:
    metodos = [
        {"nombre": "Efectivo",       "requiere_comprobante": False, "activo": True},
        {"nombre": "Tarjeta débito", "requiere_comprobante": True,  "activo": True},
        {"nombre": "Tarjeta crédito","requiere_comprobante": True,  "activo": True},
        {"nombre": "Transferencia",  "requiere_comprobante": True,  "activo": True},
        {"nombre": "Crédito empleado", "requiere_comprobante": False, "activo": True},
    ]
    for data in metodos:
        existe = await session.execute(select(MetodoPago).where(MetodoPago.nombre == data["nombre"]))
        if existe.scalar_one_or_none() is None:
            session.add(MetodoPago(**data))
            print(f"  + metodo_pago: {data['nombre']}")
        else:
            print(f"  = metodo_pago ya existe: {data['nombre']}")


async def seed_marcas(session) -> None:
    marcas = [
        {"nombre": "Genérico"},
        {"nombre": "Colcafé"},
        {"nombre": "Sello Rojo"},
        {"nombre": "Alpina"},
        {"nombre": "Alquería"},
        {"nombre": "Nestlé"},
        {"nombre": "Quala"},
        {"nombre": "Harinera del Valle"},
    ]
    for data in marcas:
        existe = await session.execute(select(Marca).where(Marca.nombre == data["nombre"]))
        if existe.scalar_one_or_none() is None:
            session.add(Marca(**data))
            print(f"  + marca: {data['nombre']}")
        else:
            print(f"  = marca ya existe: {data['nombre']}")


async def main() -> None:
    print("=== Seeder: catálogo base ===")
    async with AsyncSessionLocal() as session:
        print("\n[Roles]")
        await seed_roles(session)

        print("\n[Unidades de medida]")
        await seed_unidades(session)

        print("\n[Clasificaciones]")
        await seed_clasificaciones(session)

        print("\n[Categorías]")
        await seed_categorias(session)

        print("\n[Métodos de pago]")
        await seed_metodos_pago(session)

        print("\n[Marcas]")
        await seed_marcas(session)

        await session.commit()
    print("\n✓ Seeder completado.")


if __name__ == "__main__":
    asyncio.run(main())
