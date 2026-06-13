"""
auth.py (router)
Endpoint de registro automático: crea el usuario en pos.usuario la primera
vez que se autentica con Clerk, usando sus datos del perfil de Clerk.
"""
import httpx

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.config import settings
from app.database import get_db
from app.dependencies import get_current_user
from app.dependencies.auth import _verify_session_with_clerk
from app.exceptions import MajesaError
from app.limiter import limiter
from app.models.catalogo import Rol, Usuario
from app.schemas.catalogo_schema import UsuarioOut

router = APIRouter(prefix="/auth", tags=["Auth"])

_security = HTTPBearer(auto_error=False)


@router.get("/me", response_model=UsuarioOut, summary="Usuario autenticado actual")
async def me(current_user: Usuario = Depends(get_current_user)):
    return current_user

@router.post("/register", response_model=UsuarioOut, summary="Registrar usuario desde Clerk")
@limiter.limit("5/minute")
async def register(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_security),
    db: AsyncSession = Depends(get_db),
):
    """
    Llama este endpoint justo después del login con Clerk.
    Si el usuario ya existe en pos.usuario lo devuelve tal cual.
    Si no existe, lo crea usando el nombre y correo del perfil de Clerk.
    El rol debe asignarse después desde el panel de administración.
    """
    if credentials is None:
        raise HTTPException(status_code=401, detail="Token de autorización requerido")

    clerk_user_id = await _verify_session_with_clerk(credentials.credentials)

    # Si ya existe, devolvemos el registro existente
    result = await db.execute(
        select(Usuario)
        .options(joinedload(Usuario.rol))
        .where(Usuario.clerk_id == clerk_user_id)
    )
    user = result.scalar_one_or_none()
    if user is not None:
        return user

    # Obtener datos del perfil desde Clerk
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"https://api.clerk.com/v1/users/{clerk_user_id}",
            headers={"Authorization": f"Bearer {settings.CLERK_SECRET_KEY}"},
            timeout=10.0,
        )

    if resp.status_code != 200:
        raise HTTPException(
            status_code=502,
            detail="No se pudo obtener el perfil de Clerk",
        )

    clerk_data = resp.json()

    first = clerk_data.get("first_name") or ""
    last = clerk_data.get("last_name") or ""
    nombre = f"{first} {last}".strip() or "Sin nombre"

    primary_email_id = clerk_data.get("primary_email_address_id")
    correo = next(
        (e["email_address"] for e in clerk_data.get("email_addresses", []) if e.get("id") == primary_email_id),
        None,
    )
    if correo is None:
        raise HTTPException(status_code=400, detail="El perfil de Clerk no tiene correo registrado")

    count_result = await db.execute(select(func.count()).select_from(Usuario))
    es_primer_usuario = count_result.scalar() == 0

    id_rol: int | None = None
    if es_primer_usuario:
        rol_result = await db.execute(select(Rol).where(Rol.nombre == "administrador"))
        rol_obj = rol_result.scalar_one_or_none()
        if not rol_obj:
            raise MajesaError("Rol 'administrador' no encontrado en el sistema", 500)
        id_rol = rol_obj.id_rol

    new_user = Usuario(
        clerk_id=clerk_user_id,
        nombre=nombre,
        correo=correo,
        id_rol=id_rol,
        activo=True,
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user
