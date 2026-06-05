"""
app/main.py

Application entry point.
Initializes FastAPI, registers routers and exception handlers.

Author: Suley Suarez / Johan Valero / Ivan Ospino / Carlos Espinel
Issue: #1, #40
"""
from fastapi import FastAPI
from app.exceptions import MajesaError, majesa_exception_handler
from app.routers import insumo, orden_compra, producto, receta, venta, caja, inventario, proveedor, catalogo


app = FastAPI(
    title="Majesa API",
    description="Sistema POS e Inventario — Cafeteria Majesa",
    version="1.0.0",
)

app.add_exception_handler(MajesaError, majesa_exception_handler)

app.include_router(producto.router, prefix="/api/v1", tags=["Productos"])
app.include_router(receta.router, prefix="/api/v1", tags=["Recetas"])
app.include_router(insumo.router, prefix="/api/v1", tags=["Insumos"])
app.include_router(orden_compra.router, prefix="/api/v1", tags=["Ordenes de Compra"])
app.include_router(catalogo.router, prefix="/api/v1", tags=["Catalogo"])
app.include_router(proveedor.router, prefix="/api/v1", tags=["Proveedores"])
app.include_router(venta.router, prefix="/api/v1/ventas", tags=["Ventas"])
app.include_router(caja.router, prefix="/api/v1/caja", tags=["Caja"])
app.include_router(inventario.router, prefix="/api/v1/inventario", tags=["Inventario"])


@app.get("/health")
def health():
    """Health check endpoint."""
    return {"status": "ok", "project": "Majesa Backend"}