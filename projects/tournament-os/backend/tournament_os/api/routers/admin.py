from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from tournament_os.application.registrations import RegistrationService
from tournament_os.application.rules import RuleSetService, validate_rule_set
from tournament_os.application.tournaments import TournamentService
from tournament_os.database import get_session
from tournament_os.models.tournament import Tournament
from tournament_os.schemas.registration import AdminRegistrationRead
from tournament_os.schemas.tournament import (
    RuleSetCreate,
    RuleSetValidationResult,
    TournamentCreate,
    TournamentRead,
)

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/tournaments", response_model=TournamentRead)
def create_tournament(
    payload: TournamentCreate,
    session: Session = Depends(get_session),
) -> Tournament:
    tournament = TournamentService(session).create_tournament(payload)
    session.commit()
    return tournament


@router.post("/tournaments/{tournament_id}/open-registration", response_model=TournamentRead)
def open_registration(
    tournament_id: str,
    session: Session = Depends(get_session),
) -> Tournament:
    tournament = TournamentService(session).open_registration(tournament_id)
    session.commit()
    return tournament


@router.post("/tournaments/{tournament_id}/close-registration", response_model=TournamentRead)
def close_registration(
    tournament_id: str,
    session: Session = Depends(get_session),
) -> Tournament:
    tournament = TournamentService(session).close_registration(tournament_id)
    session.commit()
    return tournament


@router.post("/tournaments/{tournament_id}/rule-set/validate", response_model=RuleSetValidationResult)
def validate_tournament_rule_set(payload: RuleSetCreate) -> RuleSetValidationResult:
    return validate_rule_set(payload)


@router.post("/tournaments/{tournament_id}/rule-set", response_model=dict[str, object])
def create_rule_set(
    tournament_id: str,
    payload: RuleSetCreate,
    session: Session = Depends(get_session),
) -> dict[str, object]:
    rule_set, formula = RuleSetService(session).create_rule_set(tournament_id, payload)
    session.commit()
    return {
        "rule_set_id": rule_set.id,
        "score_formula_id": formula.id,
        "status": rule_set.status,
    }

@router.post("/tournaments/{tournament_id}/rule-set/lock")
def lock_tournament_rule_set(
    tournament_id: str,
    session: Session = Depends(get_session),
) -> dict[str, str]:
    rule_set = RuleSetService(session).lock_rule_set(tournament_id)
    session.commit()
    return {"status": rule_set.status, "rule_set_id": rule_set.id}
