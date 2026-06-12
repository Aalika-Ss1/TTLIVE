from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from tournament_os.application.advancement import AdvancementService
from tournament_os.database import get_session
from tournament_os.schemas.advancement import AdvancementRead, NextStageAssignmentRead, WinnerRead

router = APIRouter(prefix="/admin", tags=["advancement"])


@router.post("/tournaments/{tournament_id}/stages/{stage_id}/publish-advancement", response_model=AdvancementRead)
def publish_advancement(
    tournament_id: str,
    stage_id: str,
    session: Session = Depends(get_session),
) -> object:
    result = AdvancementService(session).publish_stage_advancement(tournament_id, stage_id)
    session.commit()
    return result


@router.post(
    "/tournaments/{tournament_id}/stages/{stage_id}/assign-next-stage",
    response_model=NextStageAssignmentRead,
)
def assign_next_stage(
    tournament_id: str,
    stage_id: str,
    session: Session = Depends(get_session),
) -> object:
    result = AdvancementService(session).assign_advanced_to_next_stage(tournament_id, stage_id)
    session.commit()
    return result


@router.post(
    "/tournaments/{tournament_id}/stages/{stage_id}/publish-winner",
    response_model=WinnerRead,
)
def publish_winner(
    tournament_id: str,
    stage_id: str,
    session: Session = Depends(get_session),
) -> object:
    result = AdvancementService(session).publish_stage_winner(tournament_id, stage_id)
    session.commit()
    return result
