"""
app/exceptions.py

Domain exceptions for Majesa backend.
All business errors inherit from MajesaError.
Global exception handler converts them to HTTP responses.

Author: Suley Suarez
Issue: #2
"""
from fastapi import Request
from fastapi.responses import JSONResponse

class MajesaError(Exception):
    def __init__(self, message: str, code: int = 400):
        self.message = message
        self.code = code

class InsumoInsuficienteError(MajesaError):
    pass

class VentaNoEncontradaError(MajesaError):
    def __init__(self, venta_id: int):
        super().__init__(f'Venta {venta_id} no encontrada', 404)

class PermisoDenegadoError(MajesaError):
    def __init__(self):
        super().__init__('Acceso no autorizado', 403)

class AjustePendienteError(MajesaError):
    pass

async def majesa_exception_handler(request: Request, exc: MajesaError):
    return JSONResponse(
        status_code=exc.code,
        content={'error': exc.message}
    )
