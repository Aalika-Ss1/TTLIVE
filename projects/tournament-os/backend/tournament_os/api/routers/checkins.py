from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from tournament_os.application.checkins import CheckInService
from tournament_os.database import get_session
from tournament_os.models.competition import CheckIn, CheckInSession
from tournament_os.schemas.checkins import CheckInRead, CheckInRequest

router = APIRouter(tags=["check-in"])


@router.post("/admin/check-in-sessions/{session_id}/open")
def open_check_in_session(
    session_id: str,
    session: Session = Depends(get_session),
) -> dict[str, str]:
    check_in_session: CheckInSession = CheckInService(session).open_session(session_id)
    session.commit()
    return {"id": check_in_session.id, "status": check_in_session.status}


@router.post("/admin/check-in-sessions/{session_id}/close")
def close_check_in_session(
    session_id: str,
    session: Session = Depends(get_session),
) -> dict[str, str]:
    check_in_session: CheckInSession = CheckInService(session).close_session(session_id)
    session.commit()
    return {"id": check_in_session.id, "status": check_in_session.status}


@router.post("/tournaments/{tournament_id}/check-in/{session_id}", response_model=CheckInRead)
def player_check_in(
    tournament_id: str,
    session_id: str,
    payload: CheckInRequest,
    session: Session = Depends(get_session),
) -> CheckIn:
    check_in = CheckInService(session).check_in(
        tournament_id,
        session_id,
        payload.registration_id,
        source=payload.source,
    )
    session.commit()
    return check_in
