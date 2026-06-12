from sqlalchemy import select
from sqlalchemy.orm import Session

from tournament_os.models.operations import AuditLog, EventOutbox


class AuditQueryService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def audit_logs(self, tournament_id: str, limit: int = 100) -> list[dict[str, object]]:
        rows = self.session.scalars(
            select(AuditLog)
            .where(AuditLog.tournament_id == tournament_id)
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
        )
        return [
            {
                "id": row.id,
                "actor_user_id": row.actor_user_id,
                "entity_type": row.entity_type,
                "entity_id": row.entity_id,
                "action": row.action,
                "reason": row.reason,
                "created_at": row.created_at,
            }
            for row in rows
        ]

    def event_outbox(self, tournament_id: str, limit: int = 100) -> list[dict[str, object]]:
        rows = self.session.scalars(
            select(EventOutbox)
            .where(EventOutbox.tournament_id == tournament_id)
            .order_by(EventOutbox.created_at.desc())
            .limit(limit)
        )
        return [
            {
                "id": row.id,
                "event_name": row.event_name,
                "entity_type": row.entity_type,
                "entity_id": row.entity_id,
                "status": row.status,
                "created_at": row.created_at,
            }
            for row in rows
        ]
