from collections.abc import Callable

from fastapi import Depends, HTTPException

from app.dependencies.auth import get_current_user
from app.models.catalogo import Usuario


def require_rol(*roles: str) -> Callable:
    """
    Dependency factory that enforces role-based access control.

    Usage:
        current_user: Usuario = Depends(require_rol("administrador"))
        current_user: Usuario = Depends(require_rol("cajero", "administrador"))

    Returns the authenticated Usuario so the endpoint can access it directly.
    Raises 403 if the user's role is not in the allowed list.
    """
    async def _check(current_user: Usuario = Depends(get_current_user)) -> Usuario:
        rol_nombre = current_user.rol.nombre if current_user.rol else None
        if rol_nombre not in roles:
            raise HTTPException(
                status_code=403,
                detail=f"Acceso denegado. Se requiere uno de: {', '.join(roles)}",
            )
        return current_user

    return _check
