import asyncio
import base64
import json

from jwt import ExpiredSignatureError, InvalidTokenError, PyJWKClient
from jwt import decode as jwt_decode
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.database import get_db
from app.models.catalogo import Usuario

_security = HTTPBearer(auto_error=False)

# Cache PyJWKClient by issuer to avoid a new JWKS fetch on every request
_jwks_clients: dict[str, PyJWKClient] = {}


def _get_jwks_client(issuer: str) -> PyJWKClient:
    if issuer not in _jwks_clients:
        _jwks_clients[issuer] = PyJWKClient(
            f"{issuer}/.well-known/jwks.json", cache_keys=True
        )
    return _jwks_clients[issuer]


def _decode_payload_unsafe(token: str) -> dict:
    try:
        payload_b64 = token.split(".")[1]
        payload_b64 += "=" * (-len(payload_b64) % 4)
        return json.loads(base64.urlsafe_b64decode(payload_b64))
    except Exception:
        raise HTTPException(status_code=401, detail="Token malformado")


def _verify_token_sync(token: str) -> str:
    raw = _decode_payload_unsafe(token)
    issuer = raw.get("iss", "")
    jwks_client = _get_jwks_client(issuer)
    signing_key = jwks_client.get_signing_key_from_jwt(token)
    payload = jwt_decode(
        token,
        signing_key.key,
        algorithms=["RS256"],
        options={"verify_aud": False},
        issuer=issuer,
    )
    if payload.get("sts") != "active":
        raise HTTPException(status_code=401, detail="Sesion inactiva")
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
        raise HTTPException(status_code=401, detail=f"Token invalido: {e}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Error verificando token: {e}")


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_security),
    db: AsyncSession = Depends(get_db),
) -> Usuario:
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
