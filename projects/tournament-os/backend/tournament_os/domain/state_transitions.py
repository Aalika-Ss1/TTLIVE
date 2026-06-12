from collections.abc import Mapping

from tournament_os.domain.enums import (
    RegistrationStatus,
    ScoreStatus,
    TournamentStatus,
)
from tournament_os.domain.errors import DomainError


TOURNAMENT_TRANSITIONS: Mapping[TournamentStatus, set[TournamentStatus]] = {
    TournamentStatus.DRAFT: {TournamentStatus.REGISTRATION_OPEN},
    TournamentStatus.REGISTRATION_OPEN: {TournamentStatus.REGISTRATION_CLOSED},
    TournamentStatus.REGISTRATION_CLOSED: {TournamentStatus.GROUPING},
    TournamentStatus.GROUPING: {TournamentStatus.READY},
    TournamentStatus.READY: {TournamentStatus.LIVE},
    TournamentStatus.LIVE: {TournamentStatus.SCORING, TournamentStatus.REVIEW},
    TournamentStatus.SCORING: {TournamentStatus.REVIEW},
    TournamentStatus.REVIEW: {TournamentStatus.FINALIZED, TournamentStatus.SCORING},
    TournamentStatus.FINALIZED: {TournamentStatus.ARCHIVED},
    TournamentStatus.ARCHIVED: set(),
}

REGISTRATION_TRANSITIONS: Mapping[RegistrationStatus, set[RegistrationStatus]] = {
    RegistrationStatus.DRAFT: {RegistrationStatus.SUBMITTED, RegistrationStatus.WITHDRAWN},
    RegistrationStatus.SUBMITTED: {
        RegistrationStatus.APPROVED,
        RegistrationStatus.REJECTED,
        RegistrationStatus.WAITLISTED,
        RegistrationStatus.WITHDRAWN,
    },
    RegistrationStatus.APPROVED: {
        RegistrationStatus.WAITLISTED,
        RegistrationStatus.WITHDRAWN,
    },
    RegistrationStatus.REJECTED: set(),
    RegistrationStatus.WAITLISTED: {
        RegistrationStatus.APPROVED,
        RegistrationStatus.WITHDRAWN,
    },
    RegistrationStatus.WITHDRAWN: set(),
}

SCORE_TRANSITIONS: Mapping[ScoreStatus, set[ScoreStatus]] = {
    ScoreStatus.DRAFT: {ScoreStatus.SUBMITTED},
    ScoreStatus.SUBMITTED: {ScoreStatus.PENDING_VERIFICATION},
    ScoreStatus.PENDING_VERIFICATION: {ScoreStatus.APPROVED, ScoreStatus.DISPUTED},
    ScoreStatus.APPROVED: {ScoreStatus.DISPUTED, ScoreStatus.FINAL},
    ScoreStatus.DISPUTED: {ScoreStatus.CORRECTED},
    ScoreStatus.CORRECTED: {ScoreStatus.APPROVED},
    ScoreStatus.FINAL: set(),
}


def ensure_transition_allowed(
    current_status: str,
    next_status: str,
    transitions: Mapping[str, set[str]],
) -> None:
    allowed_next = transitions.get(current_status, set())
    if next_status not in allowed_next:
        raise DomainError(
            "invalid_state_transition",
            f"Cannot transition from {current_status} to {next_status}.",
        )


def ensure_tournament_transition(
    current_status: TournamentStatus,
    next_status: TournamentStatus,
) -> None:
    ensure_transition_allowed(current_status, next_status, TOURNAMENT_TRANSITIONS)


def ensure_registration_transition(
    current_status: RegistrationStatus,
    next_status: RegistrationStatus,
) -> None:
    ensure_transition_allowed(current_status, next_status, REGISTRATION_TRANSITIONS)


def ensure_score_transition(
    current_status: ScoreStatus,
    next_status: ScoreStatus,
) -> None:
    ensure_transition_allowed(current_status, next_status, SCORE_TRANSITIONS)
