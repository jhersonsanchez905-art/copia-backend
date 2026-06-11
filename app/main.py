"""
app/main.py
Application entry point.
Initializes FastAPI, registers routers and exception handlers.
Author: Suley Suarez/ Johan Valero
Issue: #1, #40
"""

from fastapi import FastAPI
from app.exceptions import MajesaError, majesa_exception_handler
from app.routers import insumo, orden_compra, producto, receta
from app.routers.catalogo import router as catalogo_router
from app.routers.proveedor import router as proveedor_router

app = FastAPI(
    title="Majesa API",
    description="Sistema POS e Inventario — Cafeteria Majesa",
    version="1.0.0",
)

app.add_exception_handler(MajesaError, majesa_exception_handler)

# ── Routers ───────────────────────────────────────────────────────────────────
_V1 = "/api/v1"

app.include_router(auth.router, prefix=_V1)
app.include_router(producto.router, prefix=_V1, tags=["Productos"])
app.include_router(receta.router, prefix=_V1)
app.include_router(insumo.router, prefix=_V1)
app.include_router(orden_compra.router, prefix=_V1, tags=["Ordenes de Compra"])
app.include_router(catalogo.router, prefix=_V1)
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
app.include_router(devolucion.router, prefix=_V1)

@app.get("/health")
def health():
    return {"status": "ok", "project": "Majesa Backend"}