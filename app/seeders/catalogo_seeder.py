"""
app/seeders/catalogo_seeder.py
Initial data seeder for base catalog tables.
Inserts default roles, units of measure, payment methods,
and classifications only if they do not already exist.
Author: charlykj
Issue: #59
"""
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def seed_catalogos(db: AsyncSession) -> None:
    """Run all catalog seeders in order."""
    await seed_roles(db)
    await seed_unidades_medida(db)
    await seed_metodos_pago(db)
    await seed_clasificaciones(db)
    await db.commit()
    print("✅ Seeders ejecutados correctamente.")


async def seed_roles(db: AsyncSession) -> None:
    """Insert default roles if they do not exist."""
    roles = [
        {"nombre": "administrador", "descripcion": "Acceso total al sistema"},
        {"nombre": "cajero", "descripcion": "Acceso a caja y ventas"},
        {"nombre": "mesero", "descripcion": "Acceso a mesas y pedidos"},
    ]
    for rol in roles:
        result = await db.execute(
            text("SELECT id_rol FROM pos.rol WHERE nombre = :nombre"),
            {"nombre": rol["nombre"]},
        )
        if not result.scalar_one_or_none():
            await db.execute(
                text("INSERT INTO pos.rol (nombre, descripcion) VALUES (:nombre, :descripcion)"),
                rol,
            )


async def seed_unidades_medida(db: AsyncSession) -> None:
    """Insert default units of measure if they do not exist."""
    unidades = [
        {"nombre": "unidad", "abreviatura": "und"},
        {"nombre": "gramo", "abreviatura": "g"},
        {"nombre": "kilogramo", "abreviatura": "kg"},
        {"nombre": "mililitro", "abreviatura": "ml"},
        {"nombre": "litro", "abreviatura": "l"},
        {"nombre": "porción", "abreviatura": "por"},
    ]
    for unidad in unidades:
        result = await db.execute(
            text("SELECT id_unidad FROM pos.unidad_medida WHERE nombre = :nombre"),
            {"nombre": unidad["nombre"]},
        )
        if not result.scalar_one_or_none():
            await db.execute(
                text("INSERT INTO pos.unidad_medida (nombre, abreviatura) VALUES (:nombre, :abreviatura)"),
                unidad,
            )


async def seed_metodos_pago(db: AsyncSession) -> None:
    """Insert default payment methods if they do not exist."""
    metodos = [
        {"nombre": "efectivo", "requiere_comprobante": False},
        {"nombre": "nequi", "requiere_comprobante": True},
        {"nombre": "tarjeta", "requiere_comprobante": True},
        {"nombre": "transferencia", "requiere_comprobante": True},
    ]
    for metodo in metodos:
        result = await db.execute(
            text("SELECT id_metodo_pago FROM pos.metodo_pago WHERE nombre = :nombre"),
            {"nombre": metodo["nombre"]},
        )
        if not result.scalar_one_or_none():
            await db.execute(
                text("INSERT INTO pos.metodo_pago (nombre, requiere_comprobante) VALUES (:nombre, :requiere_comprobante)"),
                metodo,
            )


async def seed_clasificaciones(db: AsyncSession) -> None:
    """Insert default classifications if they do not exist."""
    clasificaciones = [
        "proteínas", "lácteos", "frutas",
        "panadería", "bebidas", "condimentos", "otros",
    ]
    for nombre in clasificaciones:
        result = await db.execute(
            text("SELECT id_clasificacion FROM pos.clasificacion WHERE nombre = :nombre"),
            {"nombre": nombre},
        )
        if not result.scalar_one_or_none():
            await db.execute(
                text("INSERT INTO pos.clasificacion (nombre) VALUES (:nombre)"),
                {"nombre": nombre},
            )