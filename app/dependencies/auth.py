import base64
import json

import httpx
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.config import settings
from app.database import get_db
from app.models.catalogo import Usuario

_security = HTTPBearer(auto_error=False)


def _decode_payload_unsafe(token: str) -> dict:
    """Extract JWT payload without signature verification — only used to read sid."""
    try:
        payload_b64 = token.split(".")[1]
        payload_b64 += "=" * (-len(payload_b64) % 4)
        return json.loads(base64.urlsafe_b64decode(payload_b64))
    except Exception:
        raise HTTPException(status_code=401, detail="Token malformado")


async def _verify_session_with_clerk(token: str) -> str:
    """
    Calls Clerk's session verify endpoint to validate the JWT and check the
    session is still active. Returns the Clerk user ID on success.
    """
    payload = _decode_payload_unsafe(token)
    session_id = payload.get("sid")
    if not session_id:
        raise HTTPException(status_code=401, detail="Token sin session ID")

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"https://api.clerk.com/v1/sessions/{session_id}/verify",
            json={"token": token},
            headers={"Authorization": f"Bearer {settings.CLERK_SECRET_KEY}"},
            timeout=10.0,
        )

    if resp.status_code != 200:
        raise HTTPException(status_code=401, detail="Sesión inválida o expirada")

    return resp.json()["user_id"]


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_security),
    db: AsyncSession = Depends(get_db),
) -> Usuario:
    if credentials is None:
        raise HTTPException(status_code=401, detail="Token de autorización requerido")

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
