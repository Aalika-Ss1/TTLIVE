from sqlalchemy import func, select
from sqlalchemy.orm import Session

from tournament_os.domain.enums import DisputeStatus, ScoreStatus
from tournament_os.domain.errors import DomainError
from tournament_os.models.competition import CheckIn, CheckInSession, Dispute, Registration, Score, Stage
from tournament_os.models.tournament import Tournament


class DashboardQueryService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def admin_dashboard(self, tournament_id: str) -> dict[str, object]:
        tournament = self.session.get(Tournament, tournament_id)
        if tournament is None:
            raise DomainError("tournament_not_found", "Tournament was not found.")

        registration_counts = {
            status: count
            for status, count in self.session.execute(
                select(Registration.status, func.count(Registration.id))
                .where(Registration.tournament_id == tournament_id)
                .group_by(Registration.status)
            ).all()
        }

        current_stage = self.session.scalar(
            select(Stage)
            .where(Stage.tournament_id == tournament_id)
            .order_by(Stage.sequence)
            .limit(1)
        )
        current_check_in = self.session.scalar(
            select(CheckInSession)
            .where(CheckInSession.tournament_id == tournament_id)
            .order_by(CheckInSession.opens_at)
            .limit(1)
        )

        check_in_counts: dict[str, int] = {}
        if current_check_in is not None:
            check_in_counts = {
                status: count
                for status, count in self.session.execute(
                    select(CheckIn.status, func.count(CheckIn.id))
                    .where(CheckIn.check_in_session_id == current_check_in.id)
                    .group_by(CheckIn.status)
                ).all()
            }

        pending_score_count = self.session.scalar(
            select(func.count(Score.id)).where(
                Score.tournament_id == tournament_id,
                Score.status.in_(
                    [
                        ScoreStatus.SUBMITTED.value,
                        ScoreStatus.PENDING_VERIFICATION.value,
                        ScoreStatus.DISPUTED.value,
                    ]
                ),
            )
        )
        open_dispute_count = self.session.scalar(
            select(func.count(Dispute.id)).where(
                Dispute.tournament_id == tournament_id,
                Dispute.status.in_([DisputeStatus.OPEN.value, DisputeStatus.UNDER_REVIEW.value]),
            )
        )

        return {
            "tournament": {
                "id": tournament.id,
                "name": tournament.name,
                "status": tournament.status,
            },
            "registration_counts": registration_counts,
            "current_stage": None
            if current_stage is None
            else {
                "id": current_stage.id,
                "name": current_stage.name,
                "status": current_stage.status,
            },
            "current_check_in": None
            if current_check_in is None
            else {
                "session_id": current_check_in.id,
                "status": current_check_in.status,
                "counts": check_in_counts,
            },
            "pending_score_count": pending_score_count or 0,
            "open_dispute_count": open_dispute_count or 0,
            "next_action": self._next_action(
                tournament.status,
                registration_counts,
                pending_score_count or 0,
                open_dispute_count or 0,
            ),
        }

    def _next_action(
        self,
        tournament_status: str,
        registration_counts: dict[str, int],
        pending_score_count: int,
        open_dispute_count: int,
    ) -> str:
        if tournament_status == "draft":
            return "lock_rules_and_open_registration"
        if tournament_status == "registration_open":
            return "review_registrations"
        if tournament_status == "registration_closed":
            return "generate_groups"
        if pending_score_count:
            return "review_scores"
        if open_dispute_count:
            return "review_disputes"
        if registration_counts.get("approved", 0) == 0:
            return "approve_registrations"
        return "continue_tournament"
