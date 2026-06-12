from sqlalchemy.orm import Session

from tournament_os.application.events import AuditEventService
from tournament_os.domain.enums import TournamentStatus
from tournament_os.domain.errors import DomainError
from tournament_os.domain.state_transitions import ensure_tournament_transition
from tournament_os.models.tournament import Tournament
from tournament_os.schemas.tournament import TournamentCreate


class TournamentService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.audit_events = AuditEventService(session)

    def create_tournament(self, payload: TournamentCreate, created_by_user_id: str | None = None) -> Tournament:
        tournament = Tournament(
            name=payload.name,
            game=payload.game,
            participant_type=payload.participant_type,
            max_participants=payload.max_participants,
            registration_open_at=payload.registration_open_at,
            registration_close_at=payload.registration_close_at,
            public_slug=payload.public_slug,
            created_by_user_id=created_by_user_id,
        )
        self.session.add(tournament)
        self.session.flush()
        return tournament

    def open_registration(self, tournament_id: str, actor_user_id: str | None = None) -> Tournament:
        tournament = self.session.get(Tournament, tournament_id)
        if tournament is None:
            raise DomainError("tournament_not_found", "Tournament was not found.")
        ensure_tournament_transition(
            TournamentStatus(tournament.status),
            TournamentStatus.REGISTRATION_OPEN,
        )
        tournament.status = TournamentStatus.REGISTRATION_OPEN.value
        self.audit_events.audit(
            action="open_registration",
            entity_type="tournament",
            entity_id=tournament_id,
            tournament_id=tournament_id,
            actor_user_id=actor_user_id,
            after={"status": tournament.status},
        )
        self.audit_events.event(
            event_name="tournament.status_changed",
            entity_type="tournament",
            entity_id=tournament_id,
            tournament_id=tournament_id,
            payload={"status": tournament.status},
        )
        self.session.flush()
        return tournament

    def close_registration(self, tournament_id: str, actor_user_id: str | None = None) -> Tournament:
        tournament = self.session.get(Tournament, tournament_id)
        if tournament is None:
            raise DomainError("tournament_not_found", "Tournament was not found.")
        ensure_tournament_transition(
            TournamentStatus(tournament.status),
            TournamentStatus.REGISTRATION_CLOSED,
        )
        tournament.status = TournamentStatus.REGISTRATION_CLOSED.value
        self.audit_events.audit(
            action="close_registration",
            entity_type="tournament",
            entity_id=tournament_id,
            tournament_id=tournament_id,
            actor_user_id=actor_user_id,
            after={"status": tournament.status},
        )
        self.audit_events.event(
            event_name="tournament.status_changed",
            entity_type="tournament",
            entity_id=tournament_id,
            tournament_id=tournament_id,
            payload={"status": tournament.status},
        )
        self.session.flush()
        return tournament
