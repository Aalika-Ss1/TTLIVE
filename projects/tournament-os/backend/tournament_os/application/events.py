from typing import Any

from sqlalchemy.orm import Session

from tournament_os.models.base import utcnow
from tournament_os.models.operations import AuditLog, EventOutbox


class AuditEventService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def audit(
        self,
        *,
        action: str,
        entity_type: str,
        entity_id: str,
        tournament_id: str | None = None,
        actor_user_id: str | None = None,
        before: dict[str, Any] | None = None,
        after: dict[str, Any] | None = None,
        reason: str | None = None,
    ) -> AuditLog:
        audit_log = AuditLog(
            actor_user_id=actor_user_id,
            tournament_id=tournament_id,
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            before_json=before,
            after_json=after,
            reason=reason,
            created_at=utcnow(),
        )
        self.session.add(audit_log)
        return audit_log

    def event(
        self,
        *,
        event_name: str,
        entity_type: str,
        entity_id: str,
        tournament_id: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> EventOutbox:
        event = EventOutbox(
            tournament_id=tournament_id,
            event_name=event_name,
            entity_type=entity_type,
            entity_id=entity_id,
            payload_json=payload or {},
            status="pending",
            created_at=utcnow(),
        )
        self.session.add(event)
        return event
