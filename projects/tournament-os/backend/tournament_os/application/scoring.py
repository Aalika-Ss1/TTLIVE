from sqlalchemy.orm import Session

from tournament_os.application.events import AuditEventService
from tournament_os.domain.evidence import validate_evidence_uri
from tournament_os.domain.enums import ScoreStatus
from tournament_os.domain.errors import DomainError
from tournament_os.domain.scoring import ScoreFormula, ScoreInput, calculate_score
from tournament_os.models.competition import Score
from tournament_os.models.tournament import ScoreFormulaModel, Tournament
from tournament_os.schemas.scoring import ScoreCreateItem


class ScoreEntryService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.audit_events = AuditEventService(session)

    def create_score(
        self,
        tournament_id: str,
        stage_id: str,
        group_id: str,
        round_id: str,
        payload: ScoreCreateItem,
        submitted_by_user_id: str | None = None,
    ) -> Score:
        tournament = self.session.get(Tournament, tournament_id)
        if tournament is None or tournament.active_score_formula_id is None:
            raise DomainError("score_formula_missing", "Tournament does not have an active score formula.")

        formula_model = self.session.get(ScoreFormulaModel, tournament.active_score_formula_id)
        if formula_model is None:
            raise DomainError("score_formula_missing", "Score formula was not found.")

        formula = ScoreFormula(
            placement_points={int(k): int(v) for k, v in formula_model.placement_points_json.items()},
            bonus_enabled=bool(formula_model.bonus_rules_json.get("enabled", False)),
            bye_points_default=int(formula_model.bye_rule_json.get("default_points", 0)),
        )
        calculated = calculate_score(
            ScoreInput(
                placement=payload.placement,
                bonus_points=payload.bonus_points,
                penalty_points=payload.penalty_points,
                penalty_reason=payload.penalty_reason,
            ),
            formula,
        )
        score = Score(
            tournament_id=tournament_id,
            stage_id=stage_id,
            group_id=group_id,
            round_id=round_id,
            registration_id=payload.registration_id,
            placement=calculated.placement,
            placement_points=calculated.placement_points,
            bonus_points=calculated.bonus_points,
            penalty_points=calculated.penalty_points,
            bye_points=calculated.bye_points,
            total_points=calculated.total_points,
            status=ScoreStatus.DRAFT.value,
            evidence_uri=validate_evidence_uri(payload.evidence_uri),
            submitted_by_user_id=submitted_by_user_id,
            formula_snapshot_json=calculated.formula_snapshot,
        )
        self.session.add(score)
        self.session.flush()
        self.audit_events.event(
            event_name="score.created",
            entity_type="score",
            entity_id=score.id,
            tournament_id=tournament_id,
            payload={"round_id": round_id, "registration_id": payload.registration_id},
        )
        self.session.flush()
        return score

    def approve_score(self, score_id: str, actor_user_id: str | None = None) -> Score:
        score = self.session.get(Score, score_id)
        if score is None:
            raise DomainError("score_not_found", "Score was not found.")
        if score.status != ScoreStatus.PENDING_VERIFICATION.value:
            raise DomainError("score_state_invalid", "Score cannot be approved from its current state.")

        score.status = ScoreStatus.APPROVED.value
        score.approved_by_user_id = actor_user_id
        from datetime import datetime, timezone

        score.approved_at = datetime.now(timezone.utc)
        self.audit_events.audit(
            action="approve_score",
            entity_type="score",
            entity_id=score_id,
            tournament_id=score.tournament_id,
            actor_user_id=actor_user_id,
            after={"status": score.status, "total_points": score.total_points},
        )
        self.audit_events.event(
            event_name="score.approved",
            entity_type="score",
            entity_id=score_id,
            tournament_id=score.tournament_id,
            payload={"registration_id": score.registration_id, "total_points": score.total_points},
        )
        self.session.flush()
        return score

    def reject_score(self, score_id: str, actor_user_id: str | None = None) -> Score:
        score = self.session.get(Score, score_id)
        if score is None:
            raise DomainError("score_not_found", "Score was not found.")
        
        if score.status not in {ScoreStatus.DRAFT.value, ScoreStatus.SUBMITTED.value, ScoreStatus.PENDING_VERIFICATION.value}:
            raise DomainError("score_state_invalid", "Score cannot be rejected from its current state.")

        score.status = ScoreStatus.REJECTED.value

        self.audit_events.audit(
            action="reject_score",
            entity_type="score",
            entity_id=score_id,
            tournament_id=score.tournament_id,
            actor_user_id=actor_user_id,
            after={"status": score.status},
        )
        self.audit_events.event(
            event_name="score.rejected",
            entity_type="score",
            entity_id=score_id,
            tournament_id=score.tournament_id,
            payload={"registration_id": score.registration_id},
        )
        self.session.flush()
        return score

    def submit_score(self, score_id: str, actor_user_id: str | None = None) -> Score:
        score = self.session.get(Score, score_id)
        if score is None:
            raise DomainError("score_not_found", "Score was not found.")
        if score.status not in {ScoreStatus.DRAFT.value, ScoreStatus.REJECTED.value}:
            raise DomainError("score_state_invalid", "Score cannot be submitted from its current state.")

        score.status = ScoreStatus.SUBMITTED.value
        self.audit_events.audit(
            action="submit_score",
            entity_type="score",
            entity_id=score_id,
            tournament_id=score.tournament_id,
            actor_user_id=actor_user_id,
            after={"status": score.status},
        )
        self.audit_events.event(
            event_name="score.submitted",
            entity_type="score",
            entity_id=score_id,
            tournament_id=score.tournament_id,
            payload={"registration_id": score.registration_id},
        )
        self.session.flush()
        return score

    def verify_score(self, score_id: str, actor_user_id: str | None = None) -> Score:
        score = self.session.get(Score, score_id)
        if score is None:
            raise DomainError("score_not_found", "Score was not found.")
        if score.status != ScoreStatus.SUBMITTED.value:
            raise DomainError("score_state_invalid", "Score cannot be verified from its current state.")

        score.status = ScoreStatus.PENDING_VERIFICATION.value
        self.audit_events.audit(
            action="verify_score",
            entity_type="score",
            entity_id=score_id,
            tournament_id=score.tournament_id,
            actor_user_id=actor_user_id,
            after={"status": score.status},
        )
        self.audit_events.event(
            event_name="score.verified",
            entity_type="score",
            entity_id=score_id,
            tournament_id=score.tournament_id,
            payload={"registration_id": score.registration_id},
        )
        self.session.flush()
        return score

    def mark_score_final(self, score_id: str, actor_user_id: str | None = None) -> Score:
        score = self.session.get(Score, score_id)
        if score is None:
            raise DomainError("score_not_found", "Score was not found.")
        if score.status not in {ScoreStatus.APPROVED.value, ScoreStatus.CORRECTED.value}:
            raise DomainError("score_state_invalid", "Score cannot be marked final from its current state.")

        score.status = ScoreStatus.FINAL.value
        self.audit_events.audit(
            action="mark_score_final",
            entity_type="score",
            entity_id=score_id,
            tournament_id=score.tournament_id,
            actor_user_id=actor_user_id,
            after={"status": score.status},
        )
        self.audit_events.event(
            event_name="score.finalized",
            entity_type="score",
            entity_id=score_id,
            tournament_id=score.tournament_id,
            payload={"registration_id": score.registration_id},
        )
        self.session.flush()
        return score

    def correct_score(
        self,
        score_id: str,
        payload: ScoreCreateItem,
        actor_user_id: str | None = None,
        reason: str | None = None,
    ) -> Score:
        score = self.session.get(Score, score_id)
        if score is None:
            raise DomainError("score_not_found", "Score was not found.")
        if reason is None or not reason.strip():
            raise DomainError("score_correction_reason_required", "Score correction requires a reason.")
            
        if score.registration_id != payload.registration_id:
            raise DomainError("invalid_registration", "Corrected score payload registration_id must match the original score.")
        
        tournament = self.session.get(Tournament, score.tournament_id)
        if tournament is None or tournament.active_score_formula_id is None:
            raise DomainError("score_formula_missing", "Tournament does not have an active score formula.")

        formula_model = self.session.get(ScoreFormulaModel, tournament.active_score_formula_id)
        if formula_model is None:
            raise DomainError("score_formula_missing", "Score formula was not found.")

        formula = ScoreFormula(
            placement_points={int(k): int(v) for k, v in formula_model.placement_points_json.items()},
            bonus_enabled=bool(formula_model.bonus_rules_json.get("enabled", False)),
            bye_points_default=int(formula_model.bye_rule_json.get("default_points", 0)),
        )
        calculated = calculate_score(
            ScoreInput(
                placement=payload.placement,
                bonus_points=payload.bonus_points,
                penalty_points=payload.penalty_points,
                penalty_reason=payload.penalty_reason,
            ),
            formula,
        )

        before_state = {
            "status": score.status,
            "total_points": score.total_points,
            "placement": score.placement,
        }

        score.placement = calculated.placement
        score.placement_points = calculated.placement_points
        score.bonus_points = calculated.bonus_points
        score.penalty_points = calculated.penalty_points
        score.bye_points = calculated.bye_points
        score.total_points = calculated.total_points
        score.formula_snapshot_json = calculated.formula_snapshot
        score.status = ScoreStatus.CORRECTED.value
        
        if payload.evidence_uri:
            score.evidence_uri = validate_evidence_uri(payload.evidence_uri)

        self.audit_events.audit(
            action="correct_score",
            entity_type="score",
            entity_id=score_id,
            tournament_id=score.tournament_id,
            actor_user_id=actor_user_id,
            before=before_state,
            after={
                "status": score.status,
                "total_points": score.total_points,
                "placement": score.placement,
            },
            reason=reason,
        )
        self.audit_events.event(
            event_name="score.corrected",
            entity_type="score",
            entity_id=score_id,
            tournament_id=score.tournament_id,
            payload={
                "registration_id": score.registration_id,
                "total_points": score.total_points,
                "before": before_state,
            },
        )
        self.session.flush()
        return score
