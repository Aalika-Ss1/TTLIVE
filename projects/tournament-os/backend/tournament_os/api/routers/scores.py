from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from tournament_os.application.scoring import ScoreEntryService
from tournament_os.database import get_session
from tournament_os.models.competition import Score
from tournament_os.schemas.scoring import ScoreCreate, ScoreRead

router = APIRouter(prefix="/admin", tags=["scores"])


@router.post("/rounds/{round_id}/scores", response_model=list[ScoreRead])
def create_scores(
    round_id: str,
    tournament_id: str,
    stage_id: str,
    group_id: str,
    payload: ScoreCreate,
    session: Session = Depends(get_session),
) -> list[Score]:
    service = ScoreEntryService(session)
    scores = [
        service.create_score(
            tournament_id=tournament_id,
            stage_id=stage_id,
            group_id=group_id,
            round_id=round_id,
            payload=item,
        )
        for item in payload.scores
    ]
    session.commit()
    return scores


from tournament_os.api.routers.sse import broadcaster

@router.post("/scores/{score_id}/approve", response_model=ScoreRead)
async def approve_score(
    score_id: str,
    session: Session = Depends(get_session),
) -> Score:
    score = ScoreEntryService(session).approve_score(score_id)
    session.commit()
    await broadcaster.publish("score_update", {"score_id": score_id, "status": "approved"})
    return score

@router.post("/scores/{score_id}/reject", response_model=ScoreRead)
async def reject_score(
    score_id: str,
    session: Session = Depends(get_session),
) -> Score:
    score = ScoreEntryService(session).reject_score(score_id)
    session.commit()
    await broadcaster.publish("score_update", {"score_id": score_id, "status": "rejected"})
    return score
