from pathlib import Path
import os
import httpx

from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session

from tournament_os.application.groups import GroupQueryService
from tournament_os.application.leaderboards import LeaderboardQueryService
from tournament_os.application.registrations import RegistrationService
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
from tournament_os.models.identity import User
from tournament_os.models.tournament import Tournament
from tournament_os.schemas.registration import RegistrationCreate

router = APIRouter(tags=["web"])

templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent / "templates"))

DISCORD_CLIENT_ID = os.getenv("DISCORD_CLIENT_ID", "")
DISCORD_CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET", "")
DISCORD_REDIRECT_URI = os.getenv("DISCORD_REDIRECT_URI", "http://localhost:8011/web/auth/discord/callback")


@router.get("/web/auth/discord/login")
def discord_login(request: Request, tournament_id: str):
    request.session["auth_return_tournament"] = tournament_id
    discord_auth_url = f"https://discord.com/api/oauth2/authorize?client_id={DISCORD_CLIENT_ID}&redirect_uri={DISCORD_REDIRECT_URI}&response_type=code&scope=identify"
    return RedirectResponse(discord_auth_url)


@router.get("/web/auth/discord/callback")
async def discord_callback(request: Request, code: str):
    tournament_id = request.session.get("auth_return_tournament", "")
    data = {
        "client_id": DISCORD_CLIENT_ID,
        "client_secret": DISCORD_CLIENT_SECRET,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": DISCORD_REDIRECT_URI
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    
    async with httpx.AsyncClient() as client:
        token_response = await client.post("https://discord.com/api/oauth2/token", data=data, headers=headers)
        if token_response.status_code == 200:
            token_data = token_response.json()
            access_token = token_data.get("access_token")
            
            user_response = await client.get("https://discord.com/api/users/@me", headers={"Authorization": f"Bearer {access_token}"})
            if user_response.status_code == 200:
                user_data = user_response.json()
                request.session["discord_user_id"] = str(user_data["id"])
                request.session["discord_username"] = user_data["username"]
                request.session["discord_avatar"] = user_data.get("avatar")
                
    return RedirectResponse(url=f"/web/tournaments/{tournament_id}/profile" if tournament_id else "/")


@router.get("/web/auth/logout")
def discord_logout(request: Request, tournament_id: str = ""):
    request.session.clear()
    if tournament_id:
        return RedirectResponse(url=f"/web/tournaments/{tournament_id}/profile")
    return RedirectResponse(url="/")


@router.get("/web/tournaments/{tournament_id}/profile", response_class=HTMLResponse)
def web_player_profile_get(
    tournament_id: str,
    request: Request,
    discord_id: str = None,  # Ignored safely to prevent spoofing
    session: Session = Depends(get_session)
) -> HTMLResponse:
    tournament = session.scalar(select(Tournament).where(Tournament.id == tournament_id))
    if tournament is None:
        raise DomainError("tournament_not_found", "Tournament was not found.")

    discord_user_id = request.session.get("discord_user_id")
    discord_username = request.session.get("discord_username")
    discord_avatar = request.session.get("discord_avatar")

    registration = None
    if discord_user_id:
        registration = session.scalar(
            select(Registration)
            .where(Registration.tournament_id == tournament.id)
            .where(Registration.contact_value == discord_user_id)
        )

    return templates.TemplateResponse(
        request,
        "player_profile.html",
        {
            "title": f"Player Profile - {tournament.name}",
            "tournament": tournament,
            "discord_user_id": discord_user_id,
            "discord_username": discord_username,
            "discord_avatar": discord_avatar,
            "registration": registration,
        },
    )


@router.post("/web/tournaments/{tournament_id}/profile", response_class=HTMLResponse)
def web_player_profile_post(
    tournament_id: str,
    request: Request,
    in_game_name: str = Form(...),
    game_uid: str = Form(...),
    db_session: Session = Depends(get_session)
) -> HTMLResponse:
    discord_user_id = request.session.get("discord_user_id")
    if not discord_user_id:
        raise DomainError("unauthorized", "You must be logged in with Discord to register.")

    user = db_session.get(User, discord_user_id)
    if user is None:
        user = User(
            id=discord_user_id,
            display_name=request.session.get("discord_username") or in_game_name,
            role="player",
        )
        db_session.add(user)
        db_session.flush()

    RegistrationService(db_session).submit_registration(
        tournament_id=tournament_id,
        payload=RegistrationCreate(
            user_id=discord_user_id,
            display_name=in_game_name,
            in_game_name=in_game_name,
            game_uid=game_uid,
            contact_method="discord",
            contact_value=discord_user_id,
        ),
    )
    db_session.commit()
    return RedirectResponse(url=f"/web/tournaments/{tournament_id}/profile", status_code=303)


@router.get('/web/admin/login', response_class=HTMLResponse)
def web_admin_login(request: Request, next: str = '/'):
    return templates.TemplateResponse(
        request,
        'admin_login.html',
        {
            'title': 'Admin Login',
            'next': next,
        },
    )

@router.post('/web/admin/login')
def web_admin_login_submit(request: Request, admin_token: str = Form(...), next: str = '/web/admin/tournaments/demo'):
    response = RedirectResponse(url=next, status_code=302)
    response.set_cookie('admin_token', admin_token, httponly=True)
    return response

@router.get('/web/admin/logout')
def web_admin_logout(request: Request):
    response = RedirectResponse(url='/web/admin/login', status_code=302)
    response.delete_cookie('admin_token')
    return response


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
    
    # Fetch Discord Settings
    from tournament_os.models.competition import DiscordRoleLink
    role_links = list(
        session.scalars(
            select(DiscordRoleLink)
            .where(DiscordRoleLink.tournament_id == tournament.id)
        )
    )
    discord_settings = {
        "guild_id": role_links[0].guild_id if role_links else "",
        "roles": {link.role_type: link.role_id for link in role_links}
    }
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
            "discord_settings": discord_settings,
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

from fastapi import UploadFile, File
import shutil

@router.get('/web/tournaments/{tournament_id}/submit', response_class=HTMLResponse)
def web_submit_score_get(
    tournament_id: str,
    request: Request,
    session: Session = Depends(get_session)
) -> HTMLResponse:
    tournament = session.scalar(select(Tournament).where(Tournament.id == tournament_id))
    if tournament is None:
        raise DomainError('tournament_not_found', 'Tournament was not found.')
    groups = GroupQueryService(session).public_groups(tournament.id)
    return templates.TemplateResponse(
        request,
        'submit_score.html',
        {
            'title': f'Submit Score - {tournament.name}',
            'tournament': tournament,
            'groups': groups,
        },
    )

@router.post('/web/tournaments/{tournament_id}/submit')
async def web_submit_score_post(
    tournament_id: str,
    request: Request,
    group_id: str = Form(...),
    evidence: UploadFile = File(...),
    session: Session = Depends(get_session)
):
    import uuid
    # Save uploaded file
    file_id = str(uuid.uuid4())
    ext = evidence.filename.split('.')[-1]
    filename = f"{file_id}.{ext}"
    upload_dir = Path(__file__).resolve().parents[1] / 'web' / 'static' / 'uploads'
    upload_dir.mkdir(parents=True, exist_ok=True)
    file_path = upload_dir / filename
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(evidence.file, buffer)
        
    # TODO: Create Score/Evidence record in database here
    # Placeholder: Redirect back to tournament page with success
    
    return RedirectResponse(url=f"/web/tournaments/{tournament_id}/submit?success=1", status_code=303)
