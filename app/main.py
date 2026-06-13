"""
app/main.py
Application entry point.
Initializes FastAPI, registers routers, middleware, and exception handlers.

Author: Suley Suarez / Johan Valero / Ivan Ospino / Carlos Espinel
Issue: #1, #40
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.limiter import limiter
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
# ── Módulo BI ─────────────────────────────────────────────────────────────────
# BI module router — only the BI team should modify app/bi/
from app.bi import router as bi_router
from app.config import settings
from app.exceptions import MajesaError, majesa_exception_handler
from app.middleware.auditoria import AuditoriaMiddleware
from app.routers import (
    ajuste_inventario,
    alerta_perecible,
    auth,
    auditoria,
    caja,
    catalogo,
    devolucion,
    insumo,
    inventario,
    mesa,
    orden_compra,
    pago,
    pedido,
    producto,
    proveedor,
    receta,
    reserva,
    servicio_adicional,
    stock,
    venta,
)
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response



app = FastAPI(
    title="Majesa API",
    description="Sistema POS e Inventario — Cafetería Majesa",
    version="1.0.0",
)
# ── Rate Limiting ─────────────────────────────────────────────────────────────
# ── Rate Limiting ─────────────────────────────────────────────────────────────
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ── Security Headers ──────────────────────────────────────────────────────────
app.add_middleware(SecurityHeadersMiddleware)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

# ── Middleware ────────────────────────────────────────────────────────────────
app.add_middleware(AuditoriaMiddleware)

# ── Exception handlers ────────────────────────────────────────────────────────
app.add_exception_handler(MajesaError, majesa_exception_handler)

# ── Routers ───────────────────────────────────────────────────────────────────
_V1 = "/api/v1"

app.include_router(auth.router, prefix=_V1)
app.include_router(producto.router, prefix=_V1, tags=["Productos"])
app.include_router(receta.router, prefix=_V1)
app.include_router(insumo.router, prefix=_V1, tags=["Insumos"])
app.include_router(orden_compra.router, prefix=_V1, tags=["Ordenes de Compra"])
app.include_router(catalogo.router, prefix=_V1)
app.include_router(proveedor.router, prefix=_V1, tags=["Proveedores"])
app.include_router(venta.router, prefix=f"{_V1}/ventas", tags=["Ventas"])
app.include_router(pago.router, prefix=f"{_V1}/pagos", tags=["Pagos"])
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

# ── BI Module ─────────────────────────────────────────────────────────────────
# BI module endpoints — only the BI team should modify app/bi/
app.include_router(bi_router.router, prefix=_V1)


# ── Health Check ──────────────────────────────────────────────────────────────
@app.get("/health", tags=["Health"])
def health():
    """Return service health status."""
    return {"status": "ok", "project": "Majesa Backend"}