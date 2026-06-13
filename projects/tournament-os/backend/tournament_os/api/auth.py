from __future__ import annotations

from hmac import compare_digest
from os import getenv

from fastapi import Request
from starlette.responses import JSONResponse, Response


ADMIN_AUTH_HEADER = "x-admin-token"
ADMIN_TOKEN_ENV = "TOURNAMENT_OS_ADMIN_TOKEN"
ADMIN_PROTECTED_PREFIXES = ("/admin", "/api/admin", "/web/admin")


def admin_auth_required(path: str) -> bool:
    return path.startswith(ADMIN_PROTECTED_PREFIXES)


def _authorization_bearer_token(request: Request) -> str | None:
    authorization = request.headers.get("authorization")
    if authorization is None:
        return None
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        return None
    return token


def _admin_request_token(request: Request) -> str | None:
    return request.headers.get(ADMIN_AUTH_HEADER) or _authorization_bearer_token(request)


def admin_token_is_valid(request: Request) -> bool:
    configured_token = getenv(ADMIN_TOKEN_ENV)
    request_token = _admin_request_token(request)
    if not configured_token or not request_token:
        return False
    return compare_digest(configured_token, request_token)


async def enforce_admin_auth(request: Request, call_next) -> Response:
    if admin_auth_required(request.url.path) and not admin_token_is_valid(request):
        return JSONResponse(
            status_code=403,
            content={"detail": "Admin authentication required."},
        )
    return await call_next(request)
