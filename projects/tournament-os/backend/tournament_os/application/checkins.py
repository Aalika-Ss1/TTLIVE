from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from tournament_os.application.events import AuditEventService
from tournament_os.domain.enums import CheckInSessionStatus, CheckInStatus, RegistrationStatus
from tournament_os.domain.errors import DomainError
from tournament_os.models.competition import CheckIn, CheckInSession, Registration


class CheckInService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.audit_events = AuditEventService(session)

    def open_session(self, session_id: str, actor_user_id: str | None = None) -> CheckInSession:
        check_in_session = self.session.get(CheckInSession, session_id)
        if check_in_session is None:
            raise DomainError("check_in_session_not_found", "Check-in session was not found.")
        check_in_session.status = CheckInSessionStatus.OPEN.value
        self.audit_events.event(
            event_name="check_in.opened",
            entity_type="check_in_session",
            entity_id=session_id,
            tournament_id=check_in_session.tournament_id,
        )
        self.session.flush()
        return check_in_session

    def close_session(self, session_id: str, actor_user_id: str | None = None) -> CheckInSession:
        check_in_session = self.session.get(CheckInSession, session_id)
        if check_in_session is None:
            raise DomainError("check_in_session_not_found", "Check-in session was not found.")
        check_in_session.status = CheckInSessionStatus.CLOSED.value
        self.audit_events.event(
            event_name="check_in.closed",
            entity_type="check_in_session",
            entity_id=session_id,
            tournament_id=check_in_session.tournament_id,
        )
        self.session.flush()
        return check_in_session

    def check_in(
        self,
        tournament_id: str,
        session_id: str,
        registration_id: str,
        *,
        source: str = "web",
        actor_user_id: str | None = None,
    ) -> CheckIn:
        check_in_session = self.session.get(CheckInSession, session_id)
        if check_in_session is None or check_in_session.tournament_id != tournament_id:
            raise DomainError("check_in_session_not_found", "Check-in session was not found.")
        if check_in_session.status != CheckInSessionStatus.OPEN.value:
            raise DomainError("check_in_not_open", "Check-in session is not open.")
        now = datetime.now(timezone.utc)
        opens_at = _as_aware_utc(check_in_session.opens_at)
        closes_at = _as_aware_utc(check_in_session.closes_at)
        if now < opens_at:
            raise DomainError("check_in_not_open", "Check-in session is not open yet.")
        if now > closes_at:
            raise DomainError("check_in_closed", "Check-in session is closed.")

        registration = self.session.get(Registration, registration_id)
        if registration is None or registration.tournament_id != tournament_id:
            raise DomainError("registration_not_found", "Registration was not found.")
        if registration.status != RegistrationStatus.APPROVED.value:
            raise DomainError("registration_not_eligible", "Only approved registrations can check in.")

        existing = self.session.scalar(
            select(CheckIn).where(
                CheckIn.check_in_session_id == session_id,
                CheckIn.registration_id == registration_id,
            )
        )
        if existing is not None:
            return existing

        check_in = CheckIn(
            check_in_session_id=session_id,
            tournament_id=tournament_id,
            registration_id=registration_id,
            status=CheckInStatus.CHECKED_IN.value,
            checked_in_at=datetime.now(timezone.utc),
            checked_in_by_user_id=actor_user_id,
            source=source,
        )
        self.session.add(check_in)
        self.session.flush()
        self.audit_events.event(
            event_name="check_in.completed",
            entity_type="check_in",
            entity_id=check_in.id,
            tournament_id=tournament_id,
            payload={"registration_id": registration_id, "session_id": session_id},
        )
        self.session.flush()
        return check_in


def _as_aware_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)
