from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from tournament_os.application.grouping import GroupGenerationService
from tournament_os.application.groups import GroupQueryService
from tournament_os.database import get_session
from tournament_os.schemas.groups import GenerateGroupsRequest, GenerateGroupsResult

router = APIRouter(prefix="/admin", tags=["groups"])


@router.post("/tournaments/{tournament_id}/generate-groups", response_model=GenerateGroupsResult)
def generate_groups(
    tournament_id: str,
    payload: GenerateGroupsRequest,
    session: Session = Depends(get_session),
) -> object:
    result = GroupGenerationService(session).generate_groups(
        tournament_id,
        strategy=payload.strategy,
        create_check_in_sessions=payload.create_check_in_sessions,
    )
    session.commit()
    return result


@router.get("/tournaments/{tournament_id}/groups")
def admin_groups(
    tournament_id: str,
    session: Session = Depends(get_session),
) -> list[dict[str, object]]:
    return GroupQueryService(session).admin_groups(tournament_id)
