from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from tournament_os.application.groups import GroupQueryService
from tournament_os.application.leaderboards import LeaderboardQueryService
from tournament_os.database import get_session
from tournament_os.domain.errors import DomainError
from tournament_os.models.tournament import Tournament

router = APIRouter(prefix="/public", tags=["public"])


@router.get("/tournaments/{slug}")
def public_tournament(slug: str, session: Session = Depends(get_session)) -> dict[str, object]:
    tournament = session.scalar(select(Tournament).where(Tournament.public_slug == slug))
    if tournament is None:
        raise DomainError("tournament_not_found", "Tournament was not found.")
    return {
        "id": tournament.id,
        "name": tournament.name,
        "game": tournament.game,
        "status": tournament.status,
        "public_slug": tournament.public_slug,
    }


@router.get("/tournaments/{slug}/leaderboard")
def public_leaderboard(slug: str, session: Session = Depends(get_session)) -> dict[str, object]:
    tournament = session.scalar(select(Tournament).where(Tournament.public_slug == slug))
    if tournament is None:
        raise DomainError("tournament_not_found", "Tournament was not found.")
    return {
        "tournament": {
            "name": tournament.name,
            "status": tournament.status,
        },
        "leaderboard": LeaderboardQueryService(session).public_leaderboard(tournament.id),
    }


@router.get("/tournaments/{slug}/groups")
def public_groups(slug: str, session: Session = Depends(get_session)) -> dict[str, object]:
    tournament = session.scalar(select(Tournament).where(Tournament.public_slug == slug))
    if tournament is None:
        raise DomainError("tournament_not_found", "Tournament was not found.")
    return {
        "tournament": {
            "name": tournament.name,
            "status": tournament.status,
        },
        "stages": GroupQueryService(session).public_groups(tournament.id),
    }


@router.get("/tournaments/{slug}/stream/leaderboard")
def stream_leaderboard(slug: str, session: Session = Depends(get_session)) -> dict[str, object]:
    data = public_leaderboard(slug, session)
    return {
        "tournament": data["tournament"],
        "overlay": {
            "refresh_after_seconds": 10,
            "safe_for_stream": True,
        },
        "leaderboard": data["leaderboard"],
    }
