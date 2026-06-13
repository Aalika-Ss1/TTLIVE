from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from tournament_os.api.auth import enforce_admin_auth
from tournament_os.api.errors import domain_error_handler
from tournament_os.api.routers import (
    admin,
    advancement,
    checkins,
    dashboard,
    disputes,
    exports,
    groups,
    public,
    registrations,
    scores,
    sse,
    discord,
)
from tournament_os.config import settings
from tournament_os.domain.errors import DomainError
from tournament_os.web.routes import router as web_router


from contextlib import asynccontextmanager

def _init_sqlite_dev():
    """Create tables and seed demo data when using SQLite (dev/demo only)."""
    from tournament_os.database import engine, Base
    import tournament_os.models.identity  # noqa: F401
    import tournament_os.models.tournament  # noqa: F401
    import tournament_os.models.competition  # noqa: F401
    import tournament_os.models.operations  # noqa: F401
    import tournament_os.models.overlay  # noqa: F401
    Base.metadata.create_all(engine)

    from tournament_os.database import SessionLocal
    from tournament_os.models.tournament import Tournament
    session = SessionLocal()
    try:
        if not session.get(Tournament, "demo_tournament_1"):
            session.add(Tournament(
                id="demo_tournament_1",
                name="Demo Tournament",
                game="BGMI",
                status="registration_open",
                participant_type="solo",
                max_participants=32,
                public_slug="demo-tournament-1",
            ))
            session.commit()
    finally:
        session.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.database_url.startswith("sqlite"):
        _init_sqlite_dev()
    yield

def create_app() -> FastAPI:
    from starlette.middleware.sessions import SessionMiddleware
    import os
    
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Phase 1 backend foundation for TTLIVE Tournament OS.",
        lifespan=lifespan,
    )
    
    # Required for Discord OAuth2
    app.add_middleware(
        SessionMiddleware,
        secret_key=os.getenv("SESSION_SECRET", "super_secret_for_development"),
        session_cookie="tournament_os_session"
    )
    app.add_exception_handler(DomainError, domain_error_handler)
    app.middleware("http")(enforce_admin_auth)
    app.include_router(admin.router)
    app.include_router(advancement.router)
    app.include_router(dashboard.router)
    app.include_router(registrations.router)
    app.include_router(groups.router)
    app.include_router(checkins.router)
    app.include_router(scores.router)
    app.include_router(disputes.router)
    app.include_router(public.router)
    app.include_router(sse.router)
    app.include_router(discord.router)
    app.include_router(exports.router)
    app.include_router(web_router)
    app.mount(
        "/static",
        StaticFiles(directory=str(Path(__file__).resolve().parents[1] / "web" / "static")),
        name="static",
    )

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
