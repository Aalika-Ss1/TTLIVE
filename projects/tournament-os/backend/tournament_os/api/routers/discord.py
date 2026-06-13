from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from tournament_os.application.discord import DiscordIntegrationService
from tournament_os.database import get_session

router = APIRouter(prefix="/discord", tags=["discord"])


class AdminActionRequest(BaseModel):
    tournament_id: str
    discord_user_id: str


class CheckInSessionRequest(BaseModel):
    tournament_id: str
    action: str
    stage_id: str | None = None


class DiscordRegisterRequest(BaseModel):
    tournament_id: str
    discord_user_id: str
    discord_name: str
    in_game_name: str
    game_id: str
    team_name: str | None = None


class DiscordScoreSubmitRequest(BaseModel):
    tournament_id: str
    discord_user_id: str
    round_name: str
    placement: int
    kills: int
    evidence_uri: str


@router.get("/players/me/status")
def get_discord_player_status(
    tournament_id: str,
    discord_user_id: str,
    session: Session = Depends(get_session),
) -> dict[str, object]:
    return DiscordIntegrationService(session).player_status(tournament_id, discord_user_id)


@router.post("/check-in/{session_id}")
def discord_check_in(
    session_id: str,
    discord_user_id: str,
    session: Session = Depends(get_session),
) -> dict[str, object]:
    check_in = DiscordIntegrationService(session).check_in(session_id, discord_user_id)
    session.commit()
    return {"status": "checked_in", "id": check_in.id}


@router.post("/admin/approve-player")
def admin_approve_player(
    payload: AdminActionRequest,
    session: Session = Depends(get_session),
) -> dict[str, str]:
    registration = DiscordIntegrationService(session).approve_player(
        payload.tournament_id,
        payload.discord_user_id,
    )
    session.commit()
    return {"status": "success", "registration_status": registration.status}


@router.post("/admin/check-in-session")
def admin_manage_checkin(
    payload: CheckInSessionRequest,
    session: Session = Depends(get_session),
) -> dict[str, object]:
    result = DiscordIntegrationService(session).set_check_in_session(
        payload.tournament_id,
        payload.action,
        payload.stage_id,
    )
    session.commit()
    return result


@router.get("/players/me/group")
def get_player_group(
    tournament_id: str,
    discord_user_id: str,
    session: Session = Depends(get_session),
) -> dict[str, object]:
    return DiscordIntegrationService(session).player_group(tournament_id, discord_user_id)


@router.get("/leaderboard")
def get_leaderboard(
    tournament_id: str,
    session: Session = Depends(get_session),
) -> dict[str, object]:
    return DiscordIntegrationService(session).leaderboard(tournament_id)


@router.post("/register")
def discord_register(
    payload: DiscordRegisterRequest,
    session: Session = Depends(get_session),
) -> dict[str, str]:
    registration = DiscordIntegrationService(session).register_player(
        payload.tournament_id,
        payload.discord_user_id,
        payload.discord_name,
        payload.in_game_name,
        payload.game_id,
    )
    session.commit()
    return {"status": "success", "message": "Registration submitted", "registration_id": registration.id}


@router.post("/scores/submit")
def discord_submit_score(
    payload: DiscordScoreSubmitRequest,
    session: Session = Depends(get_session),
) -> dict[str, object]:
    result = DiscordIntegrationService(session).submit_score_from_discord(
        tournament_id=payload.tournament_id,
        discord_user_id=payload.discord_user_id,
        round_name=payload.round_name,
        placement=payload.placement,
        kills=payload.kills,
        evidence_uri=payload.evidence_uri,
    )
    session.commit()
    return result
