from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from tournament_os.application.disputes import DisputeService
from tournament_os.database import get_session
from tournament_os.domain.enums import DisputeStatus
from tournament_os.models.competition import Dispute
from tournament_os.schemas.disputes import DisputeCreate, DisputeRead, DisputeResolve

router = APIRouter(tags=["disputes"])


@router.post("/scores/{score_id}/disputes", response_model=DisputeRead)
def open_dispute(
    score_id: str,
    payload: DisputeCreate,
    session: Session = Depends(get_session),
) -> Dispute:
    dispute = DisputeService(session).open_dispute(
        score_id,
        payload.registration_id,
        payload.reason,
        opened_by_user_id=payload.opened_by_user_id,
        evidence_uri=payload.evidence_uri,
    )
    session.commit()
    return dispute


@router.post("/admin/disputes/{dispute_id}/review", response_model=DisputeRead)
def review_dispute(
    dispute_id: str,
    payload: DisputeResolve,
    session: Session = Depends(get_session),
) -> Dispute:
    dispute = DisputeService(session).resolve_dispute(
        dispute_id,
        DisputeStatus.UNDER_REVIEW,
        resolved_by_user_id=payload.resolved_by_user_id,
        resolved_note=payload.resolved_note,
    )
    session.commit()
    return dispute


@router.post("/admin/disputes/{dispute_id}/accept", response_model=DisputeRead)
def accept_dispute(
    dispute_id: str,
    payload: DisputeResolve,
    session: Session = Depends(get_session),
) -> Dispute:
    dispute = DisputeService(session).resolve_dispute(
        dispute_id,
        DisputeStatus.ACCEPTED,
        resolved_by_user_id=payload.resolved_by_user_id,
        resolved_note=payload.resolved_note,
    )
    session.commit()
    return dispute


@router.post("/admin/disputes/{dispute_id}/reject", response_model=DisputeRead)
def reject_dispute(
    dispute_id: str,
    payload: DisputeResolve,
    session: Session = Depends(get_session),
) -> Dispute:
    dispute = DisputeService(session).resolve_dispute(
        dispute_id,
        DisputeStatus.REJECTED,
        resolved_by_user_id=payload.resolved_by_user_id,
        resolved_note=payload.resolved_note,
    )
    session.commit()
    return dispute
