import asyncio
import base64

from jwt import ExpiredSignatureError, InvalidTokenError, PyJWKClient
from jwt import decode as jwt_decode
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.config import settings
from app.database import get_db
from app.models.catalogo import Usuario

_security = HTTPBearer(auto_error=False)

# Cache PyJWKClient by issuer to avoid a new JWKS fetch on every request
_jwks_clients: dict[str, PyJWKClient] = {}

_issuer: str | None = None


def _expected_issuer() -> str:
    """Frontend API URL de Clerk usada para validar 'iss' y construir la URL JWKS.

    Se toma de CLERK_ISSUER si está configurado explícitamente; de lo contrario
    se deriva de NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY (pk_test_<base64(domain)>$).
    Fijar el issuer aquí (en vez de leerlo del token) evita SSRF con un 'iss'
    arbitrario y rechaza tokens ajenos con un 401 limpio.
    """
    global _issuer
    if _issuer is not None:
        return _issuer

    if settings.CLERK_ISSUER and settings.CLERK_ISSUER != "not-configured":
        _issuer = settings.CLERK_ISSUER.rstrip("/")
        return _issuer

    try:
        encoded = settings.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY.split("_", 2)[2]
        encoded += "=" * (-len(encoded) % 4)
        domain = base64.b64decode(encoded).decode().rstrip("$")
        _issuer = f"https://{domain}"
    except Exception:
        raise HTTPException(status_code=500, detail="Configuracion de Clerk invalida")

    return _issuer


def _get_jwks_client(issuer: str) -> PyJWKClient:
    if issuer not in _jwks_clients:
        _jwks_clients[issuer] = PyJWKClient(
            f"{issuer}/.well-known/jwks.json", cache_keys=True
        )
    return _jwks_clients[issuer]


def _verify_token_sync(token: str) -> str:
    issuer = _expected_issuer()
    jwks_client = _get_jwks_client(issuer)
    signing_key = jwks_client.get_signing_key_from_jwt(token)
    payload = jwt_decode(
        token,
        signing_key.key,
        algorithms=["RS256"],
        options={"verify_aud": False},
        issuer=issuer,
        leeway=30,
    )

    # Clerk no siempre emite 'sts'; solo rechazar si está presente y no activo.
    sts = payload.get("sts")
    if sts is not None and sts != "active":
        raise HTTPException(status_code=401, detail="Sesion inactiva")

    # 'azp' (authorized party) identifica el origen que solicitó el token.
    azp = payload.get("azp")
    if azp is not None and azp not in settings.ALLOWED_ORIGINS:
        raise HTTPException(status_code=401, detail="Origen no autorizado")

    clerk_user_id = payload.get("sub")
    if not clerk_user_id:
        raise HTTPException(status_code=401, detail="Token sin sub")
    return clerk_user_id


async def _verify_session_with_clerk(token: str) -> str:
    try:
        return await asyncio.to_thread(_verify_token_sync, token)
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except InvalidTokenError as e:
        detail = "Token invalido"
        if settings.ENVIRONMENT != "production":
            detail = f"Token invalido: {e}"
        raise HTTPException(status_code=401, detail=detail)
    except HTTPException:
        raise
    except Exception as e:
        detail = "Error verificando token"
        if settings.ENVIRONMENT != "production":
            detail = f"Error verificando token: {e}"
        raise HTTPException(status_code=401, detail=detail)


async def get_authenticated_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_security),
    db: AsyncSession = Depends(get_db),
) -> Usuario:
    """Verifica token, existencia y activo. No exige rol asignado.
    Usar solo en /auth/me para que el frontend detecte el estado pendiente."""
    if credentials is None:
        raise HTTPException(status_code=401, detail="Token de autorizacion requerido")

    clerk_user_id = await _verify_session_with_clerk(credentials.credentials)

    result = await db.execute(
        select(Usuario)
        .options(joinedload(Usuario.rol))
        .where(Usuario.clerk_id == clerk_user_id)
    )
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(status_code=403, detail="Usuario no registrado en el sistema")

    if not user.activo:
        raise HTTPException(status_code=403, detail="Usuario inactivo")

    return user


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_security),
    db: AsyncSession = Depends(get_db),
) -> Usuario:
    """Verifica token, existencia, activo y que tenga rol asignado.
    Usar en todos los endpoints protegidos."""
    user = await get_authenticated_user(credentials, db)

    if user.rol is None:
        raise HTTPException(
            status_code=403,
            detail="Tu cuenta está pendiente de activación. Contacta a un administrador para que te asigne un rol.",
        )

    return user
