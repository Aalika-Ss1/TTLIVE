from __future__ import annotations

from hmac import compare_digest
from os import getenv

from fastapi import Request
from starlette.responses import JSONResponse, Response, RedirectResponse


ADMIN_AUTH_HEADER = "x-admin-token"
ADMIN_TOKEN_ENV = "TOURNAMENT_OS_ADMIN_TOKEN"
ADMIN_PROTECTED_PREFIXES = ("/admin", "/api/admin", "/web/admin")
ADMIN_EXCLUDED_PATHS = ("/web/admin/login", "/web/admin/logout")


def admin_auth_required(path: str) -> bool:
    if path in ADMIN_EXCLUDED_PATHS:
        return False
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
    return (
        request.headers.get(ADMIN_AUTH_HEADER)
        or _authorization_bearer_token(request)
        or request.cookies.get("admin_token")
    )


def admin_token_is_valid(request: Request) -> bool:
    # If database is SQLite (local dev/demo), bypass authentication completely (except during tests)
    testing = getenv("TOURNAMENT_OS_TESTING")
    if testing != "true":
        from tournament_os.config import settings
        if settings.database_url.startswith("sqlite"):
            return True

    configured_token = getenv(ADMIN_TOKEN_ENV)
    request_token = _admin_request_token(request)
    if not configured_token or not request_token:
        return False
    return compare_digest(configured_token, request_token)


async def enforce_admin_auth(request: Request, call_next) -> Response:
    if admin_auth_required(request.url.path) and not admin_token_is_valid(request):
        accept_header = request.headers.get("accept", "")
        if "text/html" in accept_header and request.url.path.startswith("/web/admin"):
            return RedirectResponse(url=f"/web/admin/login?next={request.url.path}", status_code=302)
            
        return JSONResponse(
            status_code=403,
            content={"detail": "Admin authentication required."},
        )
    return await call_next(request)
