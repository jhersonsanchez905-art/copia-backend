"""
app/main.py
Application entry point.
Initializes FastAPI, registers routers, middleware, and exception handlers.

<<<<<<< HEAD
Author: Suley Suarez
=======
Author: Suley Suarez / Johan Valero / Ivan Ospino / Carlos Espinel
>>>>>>> e922ab1babb83a8319efb9d6e49238328f5b17f8
Issue: #1, #40
"""
from fastapi import FastAPI

from app.exceptions import MajesaError, majesa_exception_handler
<<<<<<< HEAD
from app.routers import insumo, orden_compra, producto, receta
=======
from app.middleware.auditoria import AuditoriaMiddleware
from app.routers import (
    ajuste_inventario,
    alerta_perecible,
    auditoria,
    caja,
    catalogo,
    insumo,
    inventario,
    mesa,
    orden_compra,
    pedido,
    producto,
    proveedor,
    receta,
    reserva,
    servicio_adicional,
    stock,
    venta,
)
>>>>>>> e922ab1babb83a8319efb9d6e49238328f5b17f8

app = FastAPI(
    title="Majesa API",
    description="Sistema POS e Inventario — Cafetería Majesa",
    version="1.0.0",
)

# ── Middleware ────────────────────────────────────────────────────────────────
app.add_middleware(AuditoriaMiddleware)

# ── Exception handlers ────────────────────────────────────────────────────────
app.add_exception_handler(MajesaError, majesa_exception_handler)

# ── Routers ───────────────────────────────────────────────────────────────────
_V1 = "/api/v1"

app.include_router(producto.router, prefix=_V1, tags=["Productos"])
app.include_router(receta.router, prefix=_V1)
app.include_router(insumo.router, prefix=_V1)
app.include_router(orden_compra.router, prefix=_V1, tags=["Ordenes de Compra"])
app.include_router(catalogo.router, prefix=_V1, tags=["Catalogo"])
app.include_router(proveedor.router, prefix=_V1, tags=["Proveedores"])
app.include_router(venta.router, prefix=f"{_V1}/ventas", tags=["Ventas"])
app.include_router(caja.router, prefix=f"{_V1}/caja", tags=["Caja"])
app.include_router(inventario.router, prefix=f"{_V1}/inventario", tags=["Inventario"])
app.include_router(ajuste_inventario.router, prefix=_V1)
app.include_router(stock.router, prefix=_V1)
app.include_router(mesa.router, prefix=_V1)
app.include_router(reserva.router, prefix=_V1)
app.include_router(pedido.router, prefix=_V1)
app.include_router(servicio_adicional.router, prefix=_V1)
app.include_router(alerta_perecible.router, prefix=_V1)
app.include_router(auditoria.router, prefix=_V1)


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok", "project": "Majesa Backend"}
<<<<<<< HEAD


app.include_router(insumo.router, prefix="/api/v1")
app.include_router(orden_compra.router, prefix="/api/v1")
app.include_router(producto.router, prefix="/api/v1")
app.include_router(receta.router, prefix="/api/v1")
=======
>>>>>>> e922ab1babb83a8319efb9d6e49238328f5b17f8
