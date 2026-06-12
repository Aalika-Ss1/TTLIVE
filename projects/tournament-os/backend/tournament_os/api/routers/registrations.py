from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from tournament_os.application.registrations import RegistrationService
from tournament_os.database import get_session
from tournament_os.models.competition import Registration
from tournament_os.schemas.registration import RegistrationCreate, RegistrationRead

router = APIRouter(tags=["registrations"])


@router.post("/tournaments/{tournament_id}/registrations", response_model=RegistrationRead)
def submit_registration(
    tournament_id: str,
    payload: RegistrationCreate,
    session: Session = Depends(get_session),
) -> Registration:
    registration = RegistrationService(session).submit_registration(tournament_id, payload)
    session.commit()
    return registration

from pydantic import BaseModel

class RejectPayload(BaseModel):
    reason: str

@router.get("/tournaments/{tournament_id}/registrations/me", response_model=RegistrationRead | None)
def get_my_registration(
    tournament_id: str,
    user_id: str,
    session: Session = Depends(get_session),
):
    from sqlalchemy import select
    registration = session.scalar(
        select(Registration).where(
            Registration.tournament_id == tournament_id,
            Registration.user_id == user_id
        )
    )
    return registration

@router.post("/admin/registrations/{registration_id}/approve", response_model=RegistrationRead)
def approve_registration(
    registration_id: str,
    session: Session = Depends(get_session),
) -> Registration:
    registration = RegistrationService(session).approve_registration(registration_id)
    session.commit()
    return registration

@router.post("/admin/registrations/{registration_id}/reject", response_model=RegistrationRead)
def reject_registration(
    registration_id: str,
    payload: RejectPayload,
    session: Session = Depends(get_session),
) -> Registration:
    registration = RegistrationService(session).reject_registration(registration_id, reason=payload.reason)
    session.commit()
    return registration

@router.post("/admin/registrations/{registration_id}/waitlist", response_model=RegistrationRead)
def waitlist_registration(
    registration_id: str,
    session: Session = Depends(get_session),
) -> Registration:
    registration = RegistrationService(session).waitlist_registration(registration_id)
    session.commit()
    return registration
