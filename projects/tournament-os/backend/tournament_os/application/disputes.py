from sqlalchemy.orm import Session

from tournament_os.application.events import AuditEventService
from tournament_os.domain.enums import DisputeStatus, ScoreStatus
from tournament_os.domain.errors import DomainError
from tournament_os.domain.evidence import validate_evidence_uri
from tournament_os.models.competition import Dispute, Score


class DisputeService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.audit_events = AuditEventService(session)

    def open_dispute(
        self,
        score_id: str,
        registration_id: str,
        reason: str,
        *,
        opened_by_user_id: str,
        evidence_uri: str | None = None,
    ) -> Dispute:
        score = self.session.get(Score, score_id)
        if score is None:
            raise DomainError("score_not_found", "Score was not found.")
        if score.registration_id != registration_id:
            raise DomainError("score_not_owned", "Players can dispute only their own score.")
        if score.status not in {ScoreStatus.APPROVED.value, ScoreStatus.FINAL.value}:
            raise DomainError("score_not_disputable", "Only approved or final scores can be disputed.")

        dispute = Dispute(
            tournament_id=score.tournament_id,
            score_id=score_id,
            registration_id=registration_id,
            status=DisputeStatus.OPEN.value,
            reason=reason,
            evidence_uri=validate_evidence_uri(evidence_uri),
            opened_by_user_id=opened_by_user_id,
        )
        score.status = ScoreStatus.DISPUTED.value
        self.session.add(dispute)
        self.session.flush()
        self.audit_events.event(
            event_name="dispute.opened",
            entity_type="dispute",
            entity_id=dispute.id,
            tournament_id=score.tournament_id,
            payload={"score_id": score_id, "registration_id": registration_id},
        )
        self.session.flush()
        return dispute

    def resolve_dispute(
        self,
        dispute_id: str,
        status: DisputeStatus,
        *,
        resolved_by_user_id: str | None = None,
        resolved_note: str | None = None,
    ) -> Dispute:
        if status not in {DisputeStatus.UNDER_REVIEW, DisputeStatus.ACCEPTED, DisputeStatus.REJECTED}:
            raise DomainError("dispute_status_invalid", "Unsupported dispute resolution status.")

        dispute = self.session.get(Dispute, dispute_id)
        if dispute is None:
            raise DomainError("dispute_not_found", "Dispute was not found.")

        dispute.status = status.value
        dispute.resolved_by_user_id = resolved_by_user_id
        dispute.resolved_note = resolved_note
        self.audit_events.audit(
            action=f"{status.value}_dispute",
            entity_type="dispute",
            entity_id=dispute_id,
            tournament_id=dispute.tournament_id,
            actor_user_id=resolved_by_user_id,
            after={"status": status.value},
            reason=resolved_note,
        )
        self.audit_events.event(
            event_name=f"dispute.{status.value}",
            entity_type="dispute",
            entity_id=dispute_id,
            tournament_id=dispute.tournament_id,
        )
        self.session.flush()
        return dispute
