"""
app/middleware/auditoria.py

Starlette middleware that writes one Auditoria record after every successful
POST / PUT / PATCH / DELETE request.

Behaviour:
- Response is sent to the client FIRST; the audit write happens in a
  background task so it never blocks or delays the response.
- Extracts the Clerk JWT from the Authorization header to resolve id_usuario.
  If the token is absent or invalid the audit record is still written with
  id_usuario = None.
- Derives entidad from the request path (first meaningful path segment after
  /api/v1/).
- Derives id_registro from the response body (field id_* or id) when the
  response is JSON.
- Skips audit for responses with status code >= 400 (errors are not audited).
"""
import asyncio
import json
import logging
import re
from typing import Any

import jwt
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.database import AsyncSessionLocal
from app.models.auditoria import Auditoria

logger = logging.getLogger(__name__)

_AUDITED_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
_PATH_RE = re.compile(r"^/api/v\d+/([^/]+)")

_METHOD_TO_ACCION = {
    "POST": "CREATE",
    "PUT": "UPDATE",
    "PATCH": "UPDATE",
    "DELETE": "DELETE",
}


def _entidad_from_path(path: str) -> str:
    m = _PATH_RE.match(path)
    return m.group(1).replace("-", "_") if m else path.strip("/").split("/")[0]


def _id_from_body(body: dict[str, Any]) -> int | None:
    """Pick the first field that looks like a primary key."""
    for key in sorted(body.keys()):
        if key.startswith("id_") or key == "id":
            val = body.get(key)
            if isinstance(val, int):
                return val
    return None


def _clerk_id_from_token(authorization: str | None) -> str | None:
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization.removeprefix("Bearer ")
    try:
        # Decode without verification to extract sub (clerk_id).
        # Full signature verification requires the Clerk public key.
        payload = jwt.decode(token, options={"verify_signature": False})
        return payload.get("sub")
    except Exception:
        return None


async def _resolve_id_usuario(clerk_id: str | None) -> int | None:
    if not clerk_id:
        return None
    try:
        from sqlalchemy import select
        from app.models.catalogo import Usuario

        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Usuario.id_usuario).where(Usuario.clerk_id == clerk_id)
            )
            return result.scalar_one_or_none()
    except Exception:
        return None


async def _write_auditoria(
    entidad: str,
    accion: str,
    id_registro: int | None,
    payload: dict | None,
    ip: str,
    user_agent: str,
    clerk_id: str | None,
) -> None:
    id_usuario = await _resolve_id_usuario(clerk_id)
    try:
        import datetime

        def _now():
            return datetime.datetime.now(datetime.timezone.utc)

        async with AsyncSessionLocal() as session:
            auditoria = Auditoria(
                id_usuario=id_usuario,
                entidad=entidad,
                id_registro=id_registro,
                accion=accion,
                estado="exitoso",
                payload=payload,
                ip=ip,
                user_agent=user_agent,
                fecha=_now(),
            )
            session.add(auditoria)
            await session.commit()
    except Exception as exc:
        logger.warning("AuditoriaMiddleware: failed to write audit record — %s", exc)


class AuditoriaMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        if request.method not in _AUDITED_METHODS:
            return await call_next(request)

        # Buffer request body so we can pass it to the audit writer.
        body_bytes = await request.body()

        # Rebuild the receive channel so FastAPI can still read the body.
        async def _receive():
            return {"type": "http.request", "body": body_bytes, "more_body": False}

        request._receive = _receive  # type: ignore[assignment]

        response = await call_next(request)

        # Only audit successful responses.
        if response.status_code >= 400:
            return response

        # Parse request body for payload (best-effort).
        payload: dict | None = None
        try:
            if body_bytes:
                payload = json.loads(body_bytes)
        except Exception:
            pass

        # Read and re-buffer response body to extract id_registro.
        response_body_chunks = []
        async for chunk in response.body_iterator:
            response_body_chunks.append(chunk)
        response_body = b"".join(response_body_chunks)

        id_registro: int | None = None
        try:
            resp_data = json.loads(response_body)
            if isinstance(resp_data, dict):
                id_registro = _id_from_body(resp_data)
        except Exception:
            pass

        entidad = _entidad_from_path(request.url.path)
        accion = _METHOD_TO_ACCION.get(request.method, "UPDATE")
        ip = request.client.host if request.client else ""
        user_agent = request.headers.get("user-agent", "")
        clerk_id = _clerk_id_from_token(request.headers.get("authorization"))

        # Fire-and-forget — do not await so response is not delayed.
        asyncio.create_task(
            _write_auditoria(entidad, accion, id_registro, payload, ip, user_agent, clerk_id)
        )

        # Return response with re-buffered body.
        from starlette.responses import Response as StarletteResponse

        return StarletteResponse(
            content=response_body,
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type=response.media_type,
        )
