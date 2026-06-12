from pathlib import Path

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session

from tournament_os.application.groups import GroupQueryService
from tournament_os.application.leaderboards import LeaderboardQueryService
from tournament_os.database import get_session
from tournament_os.domain.errors import DomainError
from tournament_os.models.competition import (
    CheckInSession,
    Dispute,
    Group,
    Registration,
    Round,
    Score,
    Stage,
)
from tournament_os.models.operations import AuditLog
from tournament_os.models.tournament import Tournament

router = APIRouter(tags=["web"])

templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent / "templates"))


@router.get("/", response_class=HTMLResponse)
def web_home(request: Request, session: Session = Depends(get_session)) -> HTMLResponse:
    tournament = session.scalar(select(Tournament).order_by(Tournament.created_at.desc()).limit(1))
    if tournament is None:
        return templates.TemplateResponse(
            request,
            "empty.html",
            {
                "title": "Tournament OS",
            },
        )
    return web_tournament(tournament.public_slug, request, session)


@router.get("/web/tournaments/{slug}", response_class=HTMLResponse)
def web_tournament(
    slug: str,
    request: Request,
    session: Session = Depends(get_session),
) -> HTMLResponse:
    tournament = session.scalar(select(Tournament).where(Tournament.public_slug == slug))
    if tournament is None:
        raise DomainError("tournament_not_found", "Tournament was not found.")

    stages = list(
        session.scalars(
            select(Stage).where(Stage.tournament_id == tournament.id).order_by(Stage.sequence)
        )
    )
    leaderboard = LeaderboardQueryService(session).public_leaderboard(tournament.id)
    groups = GroupQueryService(session).public_groups(tournament.id)
    final_stage = stages[-1] if stages else None

    winner = leaderboard[0] if leaderboard else None
    return templates.TemplateResponse(
        request,
        "tournament.html",
        {
            "title": tournament.name,
            "tournament": tournament,
            "stages": stages,
            "groups": groups,
            "leaderboard": leaderboard,
            "winner": winner,
            "final_stage": final_stage,
        },
    )


@router.get("/web/admin/tournaments/{slug}", response_class=HTMLResponse)
def web_admin(
    slug: str,
    request: Request,
    session: Session = Depends(get_session),
) -> HTMLResponse:
    tournament = session.scalar(select(Tournament).where(Tournament.public_slug == slug))
    if tournament is None:
        raise DomainError("tournament_not_found", "Tournament was not found.")

    stages = list(
        session.scalars(
            select(Stage).where(Stage.tournament_id == tournament.id).order_by(Stage.sequence)
        )
    )
    registrations = list(
        session.scalars(
            select(Registration)
            .where(Registration.tournament_id == tournament.id)
            .order_by(Registration.created_at.desc())
        )
    )
    groups = GroupQueryService(session).admin_groups(tournament.id)
    checkin_sessions = list(
        session.scalars(
            select(CheckInSession)
            .where(CheckInSession.tournament_id == tournament.id)
            .order_by(CheckInSession.opens_at.desc())
        )
    )
    disputes = list(
        session.scalars(
            select(Dispute)
            .where(Dispute.tournament_id == tournament.id)
            .order_by(Dispute.created_at.desc())
        )
    )
    scores = list(
        session.scalars(
            select(Score)
            .where(Score.tournament_id == tournament.id)
            .where(Score.status.in_(["submitted", "pending_verification"]))
            .order_by(Score.created_at.desc())
        )
    )
    rounds = list(
        session.scalars(
            select(Round).where(Round.tournament_id == tournament.id).order_by(Round.sequence)
        )
    )
    audit_logs = list(
        session.scalars(
            select(AuditLog)
            .where(AuditLog.tournament_id == tournament.id)
            .order_by(AuditLog.created_at.desc())
            .limit(100)
        )
    )
    leaderboard = LeaderboardQueryService(session).public_leaderboard(tournament.id)

    return templates.TemplateResponse(
        request,
        "admin_console.html",
        {
            "title": f"Admin Console - {tournament.name}",
            "tournament": tournament,
            "stages": stages,
            "registrations": registrations,
            "groups": groups,
            "checkin_sessions": checkin_sessions,
            "disputes": disputes,
            "scores": scores,
            "rounds": rounds,
            "audit_logs": audit_logs,
            "leaderboard": leaderboard,
        },
    )


@router.get("/web/tournaments/{slug}/stream", response_class=HTMLResponse)
def web_stream(
    slug: str,
    request: Request,
    session: Session = Depends(get_session),
) -> HTMLResponse:
    tournament = session.scalar(select(Tournament).where(Tournament.public_slug == slug))
    if tournament is None:
        raise DomainError("tournament_not_found", "Tournament was not found.")
    leaderboard = LeaderboardQueryService(session).public_leaderboard(tournament.id)
    return templates.TemplateResponse(
        request,
        "stream.html",
        {
            "title": f"{tournament.name} Stream View",
            "tournament": tournament,
            "leaderboard": leaderboard[:8],
        },
    )

