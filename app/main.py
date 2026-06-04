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

# ── Routers ─────────────────────────────────────────────────
app.include_router(producto.router, prefix="/api/v1")
app.include_router(receta.router, prefix="/api/v1")
app.include_router(insumo.router, prefix="/api/v1")
app.include_router(orden_compra.router, prefix="/api/v1")
app.include_router(catalogo_router)
app.include_router(proveedor_router)

@app.get("/health")
def health():
    return {"status": "ok", "project": "Majesa Backend"}